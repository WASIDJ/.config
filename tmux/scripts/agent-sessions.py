#!/usr/bin/env python3
"""Exact conversation recovery for tmux-resurrect; no newest-session guessing."""
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time

PREFIX = 'agent-session\t'
TOOLS = {'agy', 'codex', 'claude', 'pi', 'opencode', 'gemini', 'copilot', 'cursor-agent', 'agent', 'omp', 'grok'}
SELECTORS = {'agy': '--conversation', 'claude': '--resume', 'pi': '--session', 'opencode': '--session', 'gemini': '--resume', 'copilot': '--resume', 'cursor-agent': '--resume', 'agent': '--resume', 'omp': '--resume', 'grok': '--resume'}
VALUE_FLAGS = {'--model', '-m', '--provider', '--thinking', '--effort', '--agent', '--mode', '--project', '--profile', '-p', '--sandbox', '--ask-for-approval', '-a', '--session-dir', '--add-dir'}
BOOL_FLAGS = {'--dangerously-skip-permissions', '--dangerously-bypass-approvals-and-sandbox', '--yolo', '--no-daemon', '--no-alt-screen', '--search', '--auto', '--mini', '--pure', '--no-lens'}
UUID = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'


def tm(*args):
    return subprocess.check_output(['tmux', *args], text=True, stderr=subprocess.DEVNULL).rstrip('\n')


def processes():
    result = {}
    for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,args='], text=True).splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) == 3:
            try:
                result[int(fields[0])] = (int(fields[1]), shlex.split(fields[2]))
            except ValueError:
                pass
    return result


def detect(argv):
    for word in argv[:3]:
        name = Path(word).name
        if name in TOOLS:
            return name
        if 'pi-coding-agent/' in word and name in {'cli.js', 'index.js'}:
            return 'pi'
    return None


def agents(root, procs):
    found = []
    queue = [root]
    while queue:
        parent = queue.pop(0)
        for pid, (ppid, argv) in procs.items():
            if ppid != parent:
                continue
            tool = detect(argv)
            if tool:
                # An app-server/daemon is infrastructure, not a pane's interactive agent.
                if not any(x in argv for x in ['app-server', 'exec', '--print', '--help', '--version']):
                    found.append((pid, tool, argv))
            else:
                queue.append(pid)
    return found


def open_files(pid):
    p = subprocess.run(['lsof', '-n', '-p', str(pid), '-Fn'], text=True, capture_output=True)
    return [line[1:] for line in p.stdout.splitlines() if line.startswith('n/')]


def explicit_id(tool, argv):
    if tool == 'codex':
        if 'resume' in argv:
            tail = argv[argv.index('resume') + 1:]
            return next((x for x in tail if re.fullmatch(UUID, x)), None)
    flag = SELECTORS.get(tool)
    for i, word in enumerate(argv):
        if word == flag and i + 1 < len(argv) and not argv[i+1].startswith('-'):
            return argv[i+1]
        if flag and word.startswith(flag + '='):
            return word.split('=', 1)[1]
        if word == '--session-id' and i+1 < len(argv):
            return argv[i+1]
    if tool == 'opencode' and '-s' in argv:
        return argv[argv.index('-s')+1]
    return None


def flags(tool, argv):
    # Only replay known options. Initial prompts, credentials and commands are omitted.
    out = []
    i = 1
    while i < len(argv):
        word = argv[i]
        key = word.split('=', 1)[0]
        if key in BOOL_FLAGS:
            out.append(word)
        elif key in VALUE_FLAGS and not (key == '-p' and tool != 'codex'):
            if '=' in word:
                out.append(word)
            elif i+1 < len(argv):
                out.extend([word, argv[i+1]])
                i += 1
        i += 1
    return out


def tracked_id(pane, pid, tool):
    raw = tm('show', '-pqv', '-t', pane, '@agent_session')
    try:
        data = json.loads(raw)
        if data['pid'] == pid and data['tool'] == tool:
            return data['id']
    except (ValueError, KeyError, TypeError):
        pass
    return None


def codex_visible_id(pane):
    """Match persisted user text to THIS pane. Require exactly one matching thread."""
    screen = re.sub(r'\s+', '', tm('capture-pane', '-p', '-t', pane, '-S', '-2000'))
    home = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))
    candidates = set()
    # Read only live daemon rollout files, not the entire conversation archive.
    files = set()
    for pid, (_, argv) in processes().items():
        if detect(argv) == 'codex' and 'app-server' in argv:
            files.update(p for p in open_files(pid) if '/sessions/' in p and p.endswith('.jsonl'))
    # Native TUI footer shows the current thread name, including picker/switch changes.
    for database in home.glob('state_*.sqlite'):
        try:
            with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as db:
                for sid, name in db.execute('SELECT id, name FROM threads WHERE archived=0 AND name IS NOT NULL'):
                    label = re.sub(r'\s+', '', name)
                    if len(label) >= 8 and label in screen[-1600:]:
                        candidates.add(sid)
        except sqlite3.Error:
            pass
    if len(candidates) == 1:
        return next(iter(candidates))
    for name in files:
        try:
            p = Path(name)
            sid = re.search(UUID, p.name).group()
            # Native session ID printed in status or history also counts.
            if sid in screen:
                candidates.add(sid)
                continue
            with p.open() as f:
                for line in f:
                    data = json.loads(line)
                    payload = data.get('payload', {})
                    if data.get('type') == 'event_msg' and payload.get('type') == 'user_message':
                        text = re.sub(r'\s+', '', payload.get('message', ''))
                        # Skip shared setup instructions. Match a substantial full prompt suffix.
                        if len(text) >= 40 and not text.startswith(('<environment', '#AGENTS.md', '<INSTRUCTIONS>')) and text[-160:] in screen:
                            candidates.add(sid)
        except (OSError, ValueError, AttributeError):
            continue
    return next(iter(candidates)) if len(candidates) == 1 else None


def session_id(pane, pid, tool, argv):
    sid = tracked_id(pane, pid, tool)
    if sid:
        return sid, 'native-event'
    files = open_files(pid)
    if tool == 'agy':
        for name in files:
            if '/antigravity-cli/log/' not in name:
                continue
            text = Path(name).read_text(errors='replace')
            hits = re.findall(r'(?:Streaming conversation |Starting conversation update stream for )(' + UUID + ')', text)
            if hits:
                return hits[-1], 'pid-log'
    if tool == 'codex':
        sid = codex_visible_id(pane)
        if sid:
            return sid, 'unique-pane-transcript-match'
    for name in files:
        if tool == 'claude' and '/projects/' in name and name.endswith('.jsonl'):
            match = re.fullmatch(UUID, Path(name).stem)
            if match:
                return match.group(), 'pid-open-transcript'
        if tool in {'pi', 'omp'} and '/sessions/' in name and name.endswith('.jsonl'):
            return name, 'pid-open-transcript'
    sid = explicit_id(tool, argv)
    return (sid, 'argv') if sid else (None, 'unresolved')


def pane_rows():
    return [r.split('\t') for r in tm('list-panes', '-a', '-F', '#{session_name}\t#{window_index}\t#{pane_index}\t#{pane_id}\t#{pane_pid}').splitlines()]


def collect():
    procs = processes()
    records = []
    for session, window, index, pane, root in pane_rows():
        found = agents(int(root), procs)
        if len(found) != 1:
            continue
        pid, tool, argv = found[0]
        sid, evidence = session_id(pane, pid, tool, argv)
        executable = shutil.which(tool)
        records.append(dict(session=session, window=window, index=index, tool=tool, id=sid,
                            executable=executable, flags=flags(tool, argv), evidence=evidence))
    return records


def resume_argv(record):
    tool = record['tool']
    if tool not in TOOLS or not record.get('id'):
        return None
    binary = record.get('executable')
    if not binary or not Path(binary).is_file():
        return None
    # Revalidate saved flags rather than interpreting arbitrary snapshot commands.
    options = flags(tool, [tool] + record.get('flags', []))
    if tool == 'codex':
        if '--no-daemon' not in options:
            options.append('--no-daemon')
        return [binary, *options, 'resume', record['id']]
    return [binary, *options, SELECTORS[tool], record['id']]


def restore(snapshot):
    current = {(s,w,i): (p,int(root)) for s,w,i,p,root in pane_rows()}
    procs = processes()
    for line in Path(snapshot).read_text().splitlines():
        if not line.startswith(PREFIX):
            continue
        record = json.loads(line[len(PREFIX):])
        target = current.get((record['session'],record['window'],record['index']))
        if target is None:
            continue
        pane, root = target
        argv = resume_argv(record)
        if argv is None:
            continue
        # Existing/restored agents and busy foreground programs must never receive typed commands.
        if agents(root, procs) or tm('display', '-p', '-t', pane, '#{pane_current_command}') not in {'zsh','bash','fish','sh'}:
            continue
        token = json.dumps([record['tool'],record['id']])
        if tm('show', '-pqv', '-t', pane, '@agent_restored') == token:
            continue
        # Send one safely quoted line; never a prompt or a continuation instruction.
        tm('send-keys', '-t', pane, '-l', shlex.join(argv))
        tm('send-keys', '-t', pane, 'Enter')
        tm('set', '-p', '-t', pane, '@agent_restored', token)


def track(tool):
    data = json.load(sys.stdin)
    pane = os.environ.get('TMUX_PANE')
    sid = data.get('session_id')
    if not pane or not os.environ.get('TMUX') or not sid:
        return
    procs = processes()
    parent = os.getppid()
    owner = None
    while parent in procs:
        pp, argv = procs[parent]
        if '--managed-daemon' in argv:
            return  # A shared daemon inherits the first client's pane, so it is not authoritative.
        if detect(argv) == tool:
            owner = parent
            break
        parent = pp
    if owner is None:
        return
    tm('set','-p','-t',pane,'@agent_session',json.dumps(dict(tool=tool,id=sid,pid=owner)))


def main():
    mode = sys.argv[1]
    if mode == 'save':
        with open(sys.argv[2], 'a') as f:
            for record in collect():
                f.write(PREFIX + json.dumps(record,ensure_ascii=False) + '\n')
    elif mode == 'restore':
        restore(sys.argv[2])
    elif mode == 'track':
        track(sys.argv[2])
    elif mode == 'inspect':
        print(json.dumps(collect(),ensure_ascii=False,indent=2))
    else:
        raise SystemExit('save SNAPSHOT | restore SNAPSHOT | track TOOL | inspect')


if __name__ == '__main__':
    main()
