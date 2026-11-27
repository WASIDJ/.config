#!/usr/bin/env python3
"""Unit and real-tmux integration tests for assign-pane-colors.py."""
from __future__ import annotations

import concurrent.futures
import fcntl
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "assign-pane-colors.py"
TMUX_CONF_PATH = Path(__file__).resolve().parent.parent.parent / "tmux.conf"


def load_module():
    spec = importlib.util.spec_from_file_location("assign_pane_colors", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_pane_rows(mod):
    sample = "\n".join(
        [
            "@1\t%1\t#89dceb",
            "@1\t%2\t",
            "",
            "malformed-line",
            "@1\tnot-a-pane\t#ffffff",
            "@2\t%3\t  #a6e3a1  ",
            "@2\t%4",
        ]
    )
    parsed = mod.parse_pane_rows(sample)
    assert parsed == {
        "@1": [("%1", "#89dceb"), ("%2", "")],
        "@2": [("%3", "#a6e3a1"), ("%4", "")],
    }, f"unexpected parse result: {parsed}"


def test_pick_color_and_fallback(mod):
    used = {"#89dceb"}
    assert mod.pick_color(used) == "#a6e3a1"

    # Case-insensitive matching.
    used_upper = {c.upper() for c in mod.PALETTE}
    fallback_colors = set()
    used_all = set(c.lower() for c in used_upper)
    for _ in range(20):
        c = mod.pick_color(used_all)
        assert c.startswith("#") and len(c) == 7
        assert c.lower() not in used_all
        used_all.add(c.lower())
        fallback_colors.add(c.lower())
    assert len(fallback_colors) == 20


def test_compute_assignments_preserves_existing_and_scopes_per_window(mod):
    windows = {
        "@1": [("%1", "#A6E3A1"), ("%2", ""), ("%3", "")],
        "@2": [("%4", ""), ("%5", "")],
    }
    assignments = mod.compute_assignments(windows)
    assert assignments == [
        ("%2", "#89dceb"),
        ("%3", "#fab387"),
        ("%4", "#89dceb"),
        ("%5", "#a6e3a1"),
    ], f"unexpected assignments: {assignments}"


def test_lock_timeout_does_not_hang(mod):
    tmp_dir = tempfile.mkdtemp(prefix="tmux-color-lock-test-")
    try:
        env = {"XDG_RUNTIME_DIR": tmp_dir}
        key = f"test-socket-{os.getpid()}"
        uid = os.getuid()
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        lock_path = os.path.join(tmp_dir, f"tmux-pane-colors-{uid}-{digest}.lock")

        with open(lock_path, "a+") as holder:
            fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            start = time.monotonic()
            with mod.acquire_server_lock(key, timeout=0.15, env=env) as locked:
                elapsed = time.monotonic() - start
                assert locked is False, "expected lock acquisition to time out"
                assert elapsed < 1.0, f"lock wait took too long: {elapsed:.2f}s"
            fcntl.flock(holder.fileno(), fcntl.LOCK_UN)

        with mod.acquire_server_lock(key, timeout=0.5, env=env) as locked:
            assert locked is True, "expected lock acquisition after release"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_missing_server_exits_cleanly():
    missing_sock = os.path.join(tempfile.gettempdir(), f"tmux-nonexistent-{os.getpid()}.sock")
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "-S", missing_sock],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert res.returncode == 0, f"expected clean exit 0, got {res.returncode}: {res.stderr}"
    assert res.stderr == "", f"unexpected stderr: {res.stderr}"


def test_real_tmux_integration_and_hooks(mod):
    tmux_bin = mod.resolve_tmux_binary()
    assert tmux_bin is not None, "tmux binary not found for integration test"

    tmp_dir = Path(tempfile.mkdtemp(prefix="tmux-assign-colors-e2e-"))
    sock = str(tmp_dir / "sock")
    env = dict(os.environ)
    env["TMUX"] = f"{sock},0,0"

    def tm(*args: str) -> str:
        out = subprocess.check_output([tmux_bin, "-S", sock, *args], env=env, text=True)
        return out.strip()

    try:
        # Extract the exact hook lines from tmux.conf to verify real quoting/execution.
        hook_lines = [
            line
            for line in TMUX_CONF_PATH.read_text(encoding="utf-8").splitlines()
            if "assign-pane-colors.py" in line and not line.lstrip().startswith("#")
        ]
        assert len(hook_lines) == 4, f"expected 4 hook/run lines in tmux.conf, got {hook_lines}"
        conf_path = tmp_dir / "hooks.conf"
        conf_path.write_text("\n".join(hook_lines) + "\n", encoding="utf-8")

        p1 = tm("-f", str(conf_path), "new-session", "-d", "-s", "t1", "-P", "-F", "#{pane_id}", "/bin/sh")
        p2 = tm("split-window", "-h", "-t", p1, "-P", "-F", "#{pane_id}", "/bin/sh")
        p3 = tm("split-window", "-v", "-t", p2, "-P", "-F", "#{pane_id}", "/bin/sh")
        w2_p1 = tm("new-window", "-t", "t1", "-P", "-F", "#{pane_id}", "/bin/sh")

        # Wait up to 3s for async run-shell -b hooks to color all panes.
        deadline = time.monotonic() + 3.0
        colors = {}
        while time.monotonic() < deadline:
            colors = {
                pid: tm("show-options", "-p", "-qv", "-t", pid, "@pane_color")
                for pid in (p1, p2, p3, w2_p1)
            }
            if all(colors.values()):
                break
            time.sleep(0.05)

        assert all(colors.values()), f"some panes were not colored by hooks: {colors}"
        assert len({colors[p1], colors[p2], colors[p3]}) == 3, f"duplicate colors in window 1: {colors}"
        assert colors[w2_p1] == mod.PALETTE[0], f"new window should start with first palette color: {colors}"

        # Existing custom color must be preserved across re-runs & concurrency.
        tm("set-option", "-p", "-t", p1, "@pane_color", "#123456")
        p4 = tm("split-window", "-v", "-t", p1, "-P", "-F", "#{pane_id}", "/bin/sh")
        tm("set-option", "-pu", "-t", p4, "@pane_color")

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futs = [
                pool.submit(
                    subprocess.run,
                    [sys.executable, str(SCRIPT_PATH), "-S", sock],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                for _ in range(6)
            ]
            for fut in futs:
                r = fut.result()
                assert r.returncode == 0, f"concurrent run failed: {r.returncode} {r.stderr}"
                assert r.stderr == "", f"concurrent run stderr: {r.stderr}"

        assert tm("show-options", "-p", "-qv", "-t", p1, "@pane_color") == "#123456"
        p4_color = tm("show-options", "-p", "-qv", "-t", p4, "@pane_color")
        assert p4_color and p4_color not in {colors[p2], colors[p3], "#123456"}, f"bad p4 color: {p4_color}"
    finally:
        subprocess.run([tmux_bin, "-S", sock, "kill-server"], capture_output=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> int:
    mod = load_module()
    tests = [
        ("parse_pane_rows", lambda: test_parse_pane_rows(mod)),
        ("pick_color_and_fallback", lambda: test_pick_color_and_fallback(mod)),
        ("compute_assignments", lambda: test_compute_assignments_preserves_existing_and_scopes_per_window(mod)),
        ("lock_timeout", lambda: test_lock_timeout_does_not_hang(mod)),
        ("missing_server", test_missing_server_exits_cleanly),
        ("real_tmux_integration_and_hooks", lambda: test_real_tmux_integration_and_hooks(mod)),
    ]
    for name, fn in tests:
        fn()
        print(f"PASS: {name} ({sys.executable})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
