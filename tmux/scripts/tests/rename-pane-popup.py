import os,pty,subprocess,tempfile,time,fcntl,termios,struct,select
from pathlib import Path
root=Path(tempfile.mkdtemp(prefix='tmux-popup-check-'));sock=str(root/'socket');env=dict(os.environ,TMUX=sock+',0,0',TERM='xterm-256color')
def client_setup():
 os.setsid();fcntl.ioctl(slave,termios.TIOCSCTTY,0)
def tm(*a):return subprocess.check_output(['tmux','-S',sock,*a],env=env,text=True).strip()
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',30,100,0,0))
script=str(Path.home()/'.config/tmux/scripts/rename-pane.zsh')
def running():
 rows=subprocess.check_output(['ps','-axo','args='],text=True).splitlines()
 return any(row.startswith('/bin/zsh -f '+script+' '+pane) for row in rows)
def wait_for(predicate,what):
 deadline=time.monotonic()+3
 while time.monotonic()<deadline:
  drain()
  if predicate():return
  time.sleep(.05)
 raise AssertionError(what+' OUTPUT='+repr(bytes(OUTPUT[-2500:])))
OUTPUT=bytearray()
def drain():
 data=b''
 while select.select([master],[],[],0)[0]:
  try:data+=os.read(master,65536)
  except OSError:break
 OUTPUT.extend(data)
 return data
try:
 first=tm('-f','/dev/null','new','-d','-s','verify','-P','-F','#{pane_id}','/bin/zsh -f')
 pane=tm('split','-h','-P','-F','#{pane_id}','/bin/zsh -f')
 tm('set','-as','terminal-features','xterm-256color:RGB')
 for k,v in [('prefix','C-q'),('@thm_bg','#1e1e2e'),('@thm_fg','#cdd6f4')]:tm('set','-g',k,v)
 tm('set','-p','-t',pane,'@pane_name','OLD_ALIAS_SHOULD_NOT_BE_PREFILLED')
 tm('set','-p','-t',first,'@pane_color','#89dceb');tm('set','-p','-t',pane,'@pane_color','#a6e3a1')
 binding=subprocess.check_output(['tmux','-L','vibe','list-keys','-T','prefix','t'],text=True)
 config=root/'bind.conf';config.write_text(binding);tm('source',str(config))
 client=subprocess.Popen(['tmux','-S',sock,'attach','-t','verify'],stdin=slave,stdout=slave,stderr=slave,env={k:v for k,v in env.items() if k!='TMUX'},preexec_fn=client_setup)
 time.sleep(.3);drain()
 os.write(master,b'\x11t')
 wait_for(running,'popup did not stay open from actual shortcut')
 deadline=time.monotonic()+1
 while time.monotonic()<deadline:
  drain();time.sleep(.01)
 assert running(),'popup flashed and exited'
 wait_for(lambda: '╭'.encode() in OUTPUT and '╯'.encode() in OUTPUT, 'missing rounded border')
 assert b'38;2;166;227;161' in OUTPUT,'pane green did not reach popup'
 assert b'OLD_ALIAS_SHOULD_NOT_BE_PREFILLED' not in OUTPUT,'old alias was prefilled'
 print('PASS: blank input, compact rounded frame and selected pane RGB colour',flush=True)
 print('PASS: Ctrl+q t opens a persistent popup in a real attached tmux client',flush=True)
 name='中文 API'
 os.write(master,b'\x15'+name.encode()+b'\r')
 wait_for(lambda:not running(),'save did not close popup')
 assert tm('show','-pqv','-t',pane,'@pane_name')==name
 assert tm('show','-pqv','-t',first,'@pane_name')==''
 print('PASS: Enter saves to the selected pane, neighbour unchanged',flush=True)
 os.write(master,b'\x11t');wait_for(running,'second popup did not open')
 os.write(master,b'\x15cancelled\x1b');wait_for(lambda:not running(),'Escape did not close popup')
 assert tm('show','-pqv','-t',pane,'@pane_name')==name
 print('PASS: Escape closes without changing the existing name',flush=True)
 os.write(master,b'\x11t');wait_for(running,'third popup did not open')
 os.write(master,b'\x15\r');wait_for(lambda:not running(),'clear did not close popup')
 assert tm('show','-pqv','-t',pane,'@pane_name')==''
 print('PASS: empty input clears the name',flush=True)
finally:
 subprocess.run(['tmux','-S',sock,'kill-server'],capture_output=True)
 os.close(master);os.close(slave)
