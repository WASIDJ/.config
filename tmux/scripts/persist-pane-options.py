#!/usr/bin/env python3
"""Persist pane user options as JSON records in tmux-resurrect snapshots."""
import json
import os
from pathlib import Path
import subprocess
import sys

OPTIONS = ('@pane_name', '@pane_color')
PREFIX = 'pane-options\t'


def tmux(*args):
    return subprocess.check_output(['tmux', *args], text=True).rstrip('\n')


def panes():
    rows = tmux('list-panes', '-a', '-F', '#{session_name}\t#{window_index}\t#{pane_index}\t#{pane_id}')
    return [row.split('\t') for row in rows.splitlines()]


def main():
    if sys.argv[1] == 'save':
        with open(sys.argv[2], 'a') as snapshot:
            for session, window, index, pane in panes():
                values = {key: tmux('show-options', '-p', '-qv', '-t', pane, key) for key in OPTIONS}
                snapshot.write(PREFIX + json.dumps([session, window, index, values], ensure_ascii=False) + '\n')
    elif sys.argv[1] == 'restore':
        configured = tmux('show-options', '-gqv', '@resurrect-dir')
        default = Path.home() / '.tmux/resurrect'
        if not default.is_dir():
            default = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'tmux/resurrect'
        directory = Path(os.path.expandvars(os.path.expanduser(configured))) if configured else default
        snapshot = directory / 'last'
        if not snapshot.exists():
            return
        current = {(s, w, i): p for s, w, i, p in panes()}
        for line in snapshot.read_text().splitlines():
            if not line.startswith(PREFIX):
                continue
            session, window, index, values = json.loads(line[len(PREFIX):])
            pane = current.get((session, window, index))
            if pane is None:
                continue
            for key in OPTIONS:
                value = values.get(key, '')
                if value:
                    tmux('set-option', '-p', '-t', pane, key, value)
                else:
                    tmux('set-option', '-pu', '-t', pane, key)
    else:
        raise SystemExit('usage: persist-pane-options.py save SNAPSHOT | restore')


if __name__ == '__main__':
    main()
