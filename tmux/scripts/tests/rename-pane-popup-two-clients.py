import os,pty,subprocess,tempfile,time,fcntl,termios,struct,select
from pathlib import Path
root=Path(tempfile.mkdtemp(prefix='tmux-popup-two-client-'));sock=str(root/'socket')
env={k:v for k,v in os.environ.items() if k!='TMUX'};env['TERM']='xterm-256color'
def tm(*a):return subprocess.check_output(['tmux','-S',sock,*a],env=env,text=True).strip()
clients=[]
def attach():
 master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',30,100,0,0))
 def setup():os.setsid();fcntl.ioctl(slave,termios.TIOCSCTTY,0)
 proc=subprocess.Popen(['tmux','-S',sock,'attach','-t','verify'],stdin=slave,stdout=slave,stderr=slave,env=env,preexec_fn=setup)
 clients.append((master,slave,proc));time.sleep(.3)
 return master

def drain(fd):
 data=b''
 while select.select([fd],[],[],0)[0]:
  try:data+=os.read(fd,65536)
  except OSError:break
 return data
try:
 pane=tm('-f','/dev/null','new','-d','-s','verify','-P','-F','#{pane_id}','/bin/zsh -f')
 for k,v in [('prefix','C-q'),('@thm_bg','#1e1e2e'),('@thm_fg','#cdd6f4')]:tm('set','-g',k,v)
 tm('set','-p','-t',pane,'@pane_color','#a6e3a1')
 tm('set','-as','terminal-features',',*:RGB')
 binding=subprocess.check_output(['tmux','-L','vibe','list-keys','-T','prefix','t'],text=True)
 config=root/'bind.conf';config.write_text(binding);tm('source',str(config))
 a=attach();drain(a);b=attach();
 def collect(duration):
  buffers={fd:bytearray() for fd,_,_ in clients};deadline=time.monotonic()+duration
  while time.monotonic()<deadline:
   for fd in buffers:buffers[fd].extend(drain(fd))
   time.sleep(.01)
  return buffers
 collect(.5)
 for fd,other,label in [(a,b,'A'),(b,a,'B')]:
  collect(.2);os.write(fd,b'\x11t');buffers=collect(.8)
  opened=buffers[fd];unexpected=buffers[other]
  assert b'Pane ' in opened,repr(opened[-2000:])
  assert b'Pane ' not in unexpected,repr(unexpected[-2000:])
  rows=subprocess.check_output(['ps','-axo','args='],text=True).splitlines()
  rows=[r for r in rows if r.startswith('tmux display-popup -c ') and 'fg=#a6e3a1,bg=#1e1e2e' in r]
  assert rows,'expected direct style args absent'
  print('ARGV: '+rows[0],flush=True)
  print('FRAME/RGB: '+repr({c:c.encode() in opened for c in ['╭','╮','╰','╯']})+' '+repr([x for x in [b'38;2;166;227;161',b'48;2;30;30;46'] if x in opened]),flush=True)
  os.write(fd,b'\x15client-'+label.encode()+b'\r');collect(.3)
  assert tm('show','-pqv','-t',pane,'@pane_name')=='client-'+label
  print('PASS: client '+label+' alone receives its popup and Enter saves',flush=True)
finally:
 subprocess.run(['tmux','-S',sock,'kill-server'],capture_output=True)
 for master,slave,proc in clients:
  os.close(master);os.close(slave)
  try:proc.wait(timeout=2)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=2)
