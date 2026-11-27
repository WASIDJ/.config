#!/usr/bin/env python3
"""Assign unused colors within each tmux window while keeping existing pane colors.

Designed to run safely from tmux asynchronous hooks (`run-shell -b`):
- Compatible with system Python 3.9+ (no third-party dependencies).
- Uses a bounded non-blocking per-server lock to prevent piling up processes.
- Applies subprocess timeouts and tolerates transient pane/server races cleanly.
"""
from __future__ import annotations

import argparse
import colorsys
from contextlib import contextmanager
import fcntl
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, Iterator, List, Mapping, Optional, Sequence, Set, Tuple

PALETTE: Tuple[str, ...] = (
    "#89dceb",
    "#a6e3a1",
    "#fab387",
    "#cba6f7",
    "#f38ba8",
    "#f9e2af",
    "#89b4fa",
    "#f5c2e7",
)
GOLDEN_RATIO_CONJUGATE = 0.6180339887498949
DEFAULT_TIMEOUT_SECONDS = 3.0
LOCK_WAIT_TIMEOUT_SECONDS = 3.0
LOCK_POLL_INTERVAL_SECONDS = 0.05
MAX_FALLBACK_ATTEMPTS = 4096
FALLBACK_TMUX_PATHS: Tuple[str, ...] = (
    "/opt/homebrew/bin/tmux",
    "/usr/local/bin/tmux",
    "/usr/bin/tmux",
)


def resolve_tmux_socket(env: Mapping[str, str]) -> Optional[str]:
    """Extract the tmux server socket path from the TMUX environment variable."""
    raw = env.get("TMUX", "").strip()
    if not raw:
        return None
    socket_path = raw.split(",", 1)[0].strip()
    return socket_path or None


def resolve_tmux_binary(env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """Locate the tmux executable even when invoked with a minimal PATH."""
    path_env = (env or os.environ).get("PATH")
    found = shutil.which("tmux", path=path_env)
    if found:
        return found
    for candidate in FALLBACK_TMUX_PATHS:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def parse_pane_rows(output: str) -> Dict[str, List[Tuple[str, str]]]:
    """Parse `tmux list-panes -a -F "#{window_id}\\t#{pane_id}\\t#{@pane_color}"` output."""
    windows: Dict[str, List[Tuple[str, str]]] = {}
    for raw_line in output.splitlines():
        if not raw_line:
            continue
        parts = raw_line.split("\t", 2)
        if len(parts) < 2:
            continue
        window_id = parts[0].strip()
        pane_id = parts[1].strip()
        color = parts[2].strip() if len(parts) == 3 else ""
        if not window_id or not pane_id.startswith("%"):
            continue
        windows.setdefault(window_id, []).append((pane_id, color))
    return windows


def pick_color(used: Set[str], palette: Sequence[str] = PALETTE) -> str:
    """Pick the first unused palette color, falling back to golden-ratio HSV."""
    for candidate in palette:
        if candidate.lower() not in used:
            return candidate

    for step in range(MAX_FALLBACK_ATTEMPTS):
        rgb = colorsys.hsv_to_rgb((step * GOLDEN_RATIO_CONJUGATE) % 1.0, 0.45, 0.95)
        candidate = "#" + "".join(f"{round(channel * 255):02x}" for channel in rgb)
        if candidate.lower() not in used:
            return candidate

    return palette[0] if palette else "#89dceb"


def compute_assignments(
    windows: Mapping[str, Sequence[Tuple[str, str]]],
    palette: Sequence[str] = PALETTE,
) -> List[Tuple[str, str]]:
    """Compute (pane_id, color) pairs for all uncolored panes without altering existing ones."""
    assignments: List[Tuple[str, str]] = []
    for panes in windows.values():
        used: Set[str] = {color.lower() for _, color in panes if color}
        for pane_id, color in panes:
            if color:
                continue
            chosen = pick_color(used, palette=palette)
            assignments.append((pane_id, chosen))
            used.add(chosen.lower())
    return assignments


def _select_lock_dir(env: Mapping[str, str]) -> str:
    uid = os.getuid()
    candidates: List[str] = []
    xdg_runtime = env.get("XDG_RUNTIME_DIR", "").strip()
    if xdg_runtime:
        candidates.append(xdg_runtime)
    candidates.append(f"/tmp/tmux-{uid}")
    candidates.append(tempfile.gettempdir())

    for directory in candidates:
        try:
            st = os.stat(directory)
        except OSError:
            continue
        if not os.path.isdir(directory):
            continue
        if directory != tempfile.gettempdir() and st.st_uid != uid:
            continue
        if os.access(directory, os.W_OK | os.X_OK):
            return directory
    return tempfile.gettempdir()


@contextmanager
def acquire_server_lock(
    server_key: str,
    timeout: float = LOCK_WAIT_TIMEOUT_SECONDS,
    env: Optional[Mapping[str, str]] = None,
) -> Iterator[bool]:
    """Acquire an exclusive per-server advisory lock with a bounded wait timeout.

    Yields True if the lock was acquired (or if locking is unavailable and we proceed),
    and False if another holder kept the lock beyond `timeout`.
    """
    uid = os.getuid()
    digest = hashlib.sha256(server_key.encode("utf-8", errors="replace")).hexdigest()[:16]
    lock_dir = _select_lock_dir(env or os.environ)
    lock_path = os.path.join(lock_dir, f"tmux-pane-colors-{uid}-{digest}.lock")

    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(lock_path, flags, 0o600)
    except OSError:
        # Locking failure (e.g. read-only tmpdir) should not crash pane coloring.
        yield True
        return

    acquired = False
    try:
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    break
                time.sleep(LOCK_POLL_INTERVAL_SECONDS)
            except OSError:
                # Filesystem does not support flock; proceed safely.
                acquired = True
                break
        yield acquired
    finally:
        if acquired:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        try:
            os.close(fd)
        except OSError:
            pass


def run_tmux(
    tmux_bin: str,
    args: Sequence[str],
    socket: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Optional[subprocess.CompletedProcess[str]]:
    """Run a tmux subcommand safely with a bounded timeout."""
    cmd: List[str] = [tmux_bin]
    if socket:
        cmd.extend(["-S", socket])
    cmd.extend(args)
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def assign_pane_colors(
    socket: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    lock_timeout: float = LOCK_WAIT_TIMEOUT_SECONDS,
    verbose: bool = False,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    """Assign colors to all uncolored panes on the target tmux server."""
    active_env = env if env is not None else os.environ
    tmux_bin = resolve_tmux_binary(active_env)
    if not tmux_bin:
        if verbose:
            print("assign-pane-colors: tmux binary not found", file=sys.stderr)
        return 0

    resolved_socket = socket if socket is not None else resolve_tmux_socket(active_env)
    server_key = resolved_socket or "default"

    with acquire_server_lock(server_key, timeout=lock_timeout, env=active_env) as locked:
        if not locked:
            if verbose:
                print("assign-pane-colors: skipped due to active lock", file=sys.stderr)
            return 0

        listed = run_tmux(
            tmux_bin,
            ["list-panes", "-a", "-F", "#{window_id}\t#{pane_id}\t#{@pane_color}"],
            socket=resolved_socket,
            timeout=timeout,
        )
        if listed is None or listed.returncode != 0:
            if verbose and listed is not None and listed.stderr:
                print(f"assign-pane-colors: list-panes failed: {listed.stderr.strip()}", file=sys.stderr)
            return 0

        windows = parse_pane_rows(listed.stdout)
        assignments = compute_assignments(windows)
        for pane_id, color in assignments:
            result = run_tmux(
                tmux_bin,
                ["set-option", "-p", "-t", pane_id, "@pane_color", color],
                socket=resolved_socket,
                timeout=timeout,
            )
            if verbose and (result is None or result.returncode != 0):
                detail = result.stderr.strip() if result and result.stderr else "timeout/oserror"
                print(f"assign-pane-colors: skipped pane {pane_id}: {detail}", file=sys.stderr)

    return 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign distinct colors to uncolored tmux panes.")
    parser.add_argument("-S", "--socket", default=None, help="Explicit tmux server socket path.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Per-command timeout in seconds.")
    parser.add_argument("--lock-timeout", type=float, default=LOCK_WAIT_TIMEOUT_SECONDS, help="Lock wait timeout in seconds.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print diagnostic messages to stderr.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parse_args(argv)
        return assign_pane_colors(
            socket=args.socket,
            timeout=args.timeout,
            lock_timeout=args.lock_timeout,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        return 0
    except Exception as exc:  # pragma: no cover - defensive top-level guard for tmux hooks
        if argv and ("-v" in argv or "--verbose" in argv):
            print(f"assign-pane-colors: unexpected error: {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
