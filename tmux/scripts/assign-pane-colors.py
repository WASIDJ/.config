#!/usr/bin/env python3
"""Assign unused colors within each window; keep existing pane colors."""
import colorsys
import fcntl
import hashlib
import os
import subprocess
import tempfile

palette = ["#89dceb", "#a6e3a1", "#fab387", "#cba6f7", "#f38ba8", "#f9e2af", "#89b4fa", "#f5c2e7"]
server = os.environ.get("TMUX", "default").split(",")[0]
lock_name = hashlib.sha256(server.encode()).hexdigest()[:16]
with open(os.path.join(tempfile.gettempdir(), "tmux-pane-colors-" + lock_name + ".lock"), "w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    rows = subprocess.check_output(["tmux", "list-panes", "-a", "-F", "#{window_id}\t#{pane_id}\t#{@pane_color}"], text=True).splitlines()
    windows = {}
    for row in rows:
        window, pane, color = row.split("\t")
        windows.setdefault(window, []).append((pane, color))
    for panes in windows.values():
        used = {color.lower() for _, color in panes if color}
        for pane, color in panes:
            if color:
                continue
            candidates = iter(palette)
            n = 0
            while True:
                candidate = next(candidates, None)
                if candidate is None:
                    rgb = colorsys.hsv_to_rgb((n * 0.61803398875) % 1, 0.45, 0.95)
                    candidate = "#" + "".join(f"{round(c * 255):02x}" for c in rgb)
                    n += 1
                if candidate.lower() not in used:
                    break
            subprocess.run(["tmux", "set-option", "-p", "-t", pane, "@pane_color", candidate], check=True)
            used.add(candidate.lower())
