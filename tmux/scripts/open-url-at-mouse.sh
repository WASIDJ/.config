#!/usr/bin/env bash
# open-url-at-mouse.sh: Open OSC 8 hyperlink or plain text URL at mouse cursor in tmux

hyperlink="$1"
line="$2"
col="$3"

# 1. Direct OSC 8 hyperlink (fastest path: ~0ms, used by pi, modern CLI tools)
if [ -n "$hyperlink" ]; then
    open "$hyperlink" 2>/dev/null &
    exit 0
fi

# 2. Plain text URL fallback from the line under cursor
if [ -n "$line" ]; then
    url=$(python3 -c '
import sys, re

line = sys.argv[1] if len(sys.argv) > 1 else ""
col = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0

pattern = re.compile(r"https?://[^\s\"`\x27<>\[\]{}|\\^]+")
matches = list(pattern.finditer(line))

target = None
for m in matches:
    if m.start() - 2 <= col <= m.end() + 2:
        target = m.group(0)
        break

if not target and len(matches) == 1:
    target = matches[0].group(0)

if target:
    target = re.sub(r"[.,;:?!)]+$", "", target)
    print(target)
' "$line" "$col" 2>/dev/null)

    if [ -n "$url" ]; then
        open "$url" 2>/dev/null &
        exit 0
    fi
fi
