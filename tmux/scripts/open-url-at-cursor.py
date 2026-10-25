#!/usr/bin/env python3
"""Open the web link at the tmux copy-mode cursor without using the clipboard."""

import os
import re
import subprocess
import sys
import unicodedata
from urllib.parse import urlsplit


URL = re.compile(r"https?://[^\s<>\"`{}|\\\x00-\x1f，。；、！？）】》」』]+", re.I)
TRAILING = ".,;:!'\"，。；、！？"
PAIRS = {')': '(', ']': '['}


def tmux(*args):
    result = subprocess.run(
        ['tmux', *args], check=True, capture_output=True, text=True
    )
    return result.stdout.removesuffix('\n')


def web_url(value):
    if not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme.lower() in ('http', 'https') and parsed.netloc else None
    except ValueError:
        return None


def character_offset(line, column):
    """Convert terminal cells to a Python string offset, including CJK padding."""
    cells = 0
    for index, char in enumerate(line):
        width = 0 if unicodedata.combining(char) or char in ('\u200d', '\ufe0f') else (
            2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1
        )
        if cells + width > column:
            return index
        cells += width
    return len(line)


def url_at(text, position):
    for match in URL.finditer(text):
        value = match.group().rstrip(TRAILING)
        while value and value[-1] in PAIRS and value.count(value[-1]) > value.count(PAIRS[value[-1]]):
            value = value[:-1]
        # tmux search leaves the cursor immediately after the search match.
        if match.start() <= position <= match.end():
            return web_url(value)
    return None


def only_url_on_line(text, position):
    start = text.rfind('\n', 0, position) + 1
    end = text.find('\n', position)
    if end < 0:
        end = len(text)
    line = text[start:end]
    matches = list(URL.finditer(line))
    return url_at(line, matches[0].start()) if len(matches) == 1 else None


def url_under_cursor(pane):
    fields = ('pane_mode', 'copy_cursor_hyperlink', 'copy_cursor_x', 'copy_cursor_y',
              'scroll_position', 'history_size', 'copy_cursor_line')
    values = tmux('display-message', '-p', '-t', pane,
                  '\x1f'.join('#{' + key + '}' for key in fields)).split('\x1f', 6)
    if len(values) != 7 or values[0] != 'copy-mode':
        return None
    _, hyperlink, x, y, scroll, history, line = values
    x, y = int(x), int(y)
    if web_url(hyperlink):
        return hyperlink

    # A search for an OSC 8 label ends one cell past it. Peek left and restore.
    if x > 0:
        tmux('send-keys', '-t', pane, '-X', 'cursor-left')
        try:
            hyperlink = tmux('display-message', '-p', '-t', pane, '#{copy_cursor_hyperlink}')
        finally:
            tmux('send-keys', '-t', pane, '-X', 'cursor-right')
        if web_url(hyperlink):
            return hyperlink

    # Capture the copy-mode snapshot, so new agent output cannot shift the target.
    # -J joins physical wraps back into one URL, while preserving real newlines.
    # capture-pane uses rows relative to the snapshot's bottom viewport, while
    # copy_cursor_y is relative to the user's scrolled viewport.
    row = y - int(scroll)
    start = max(-int(history), row - 128)
    screen = tmux('capture-pane', '-p', '-M', '-J', '-t', pane,
                  '-S', str(start), '-E', str(row + 128))
    prefix = '' if row == start else tmux(
        'capture-pane', '-p', '-M', '-J', '-t', pane, '-S', str(start), '-E', str(row - 1)
    ) + '\n'
    offset = len(os.path.commonprefix([prefix, screen]))
    position = offset + character_offset(line, x)
    return url_at(screen, position) or only_url_on_line(screen, position)


def main():
    if len(sys.argv) != 2:
        return 2
    pane = sys.argv[1]
    try:
        url = url_under_cursor(pane)
        if url is None:
            tmux('display-message', '-t', pane, '此处没有网址；按 f 查找网址，n/N 切换，Enter 打开')
            return 1
        subprocess.run(['/usr/bin/open', url], check=True, capture_output=True, text=True)
        return 0
    except (subprocess.SubprocessError, ValueError, OSError) as error:
        try:
            tmux('display-message', '-t', pane, '打开链接失败：' + str(error)[:160])
        except (subprocess.SubprocessError, OSError):
            pass
        return 1


if __name__ == '__main__':
    sys.exit(main())
