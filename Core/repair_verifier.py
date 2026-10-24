from pathlib import Path
import subprocess, time, shutil
from .repair_fingerprint import compute_fingerprint

class SilentVerifier:
    def __init__(self, timeout=600, launcher=None): self.timeout=timeout; self.launcher=launcher
    def verify(self, instance_dir, command):
        instance_dir=Path(instance_dir); started=time.monotonic(); log=instance_dir/'_repair'/'silent-launch.log'; log.parent.mkdir(parents=True,exist_ok=True)
        try:
            crashed=False
            if self.launcher:
                with log.open('w',encoding='utf8') as out:
                    proc=self.launcher(command,instance_dir,out)
                    try: code=proc.wait(timeout=self.timeout); timed_out=False
                    except subprocess.TimeoutExpired: proc.kill(); code=None; timed_out=True
                raw=log.read_text(encoding='utf8',errors='replace')
            else:
                proc=subprocess.Popen(command,cwd=instance_dir,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1)
                lines=[]; code=None; timed_out=False; success=False; crashed=False
                deadline=time.monotonic()+self.timeout
                try:
                    while proc.stdout and time.monotonic()<deadline:
                        line=proc.stdout.readline()
                        if line:
                            lines.append(line); marker=line
                            if any(x in marker for x in ('Sound engine started','Main menu','OpenAL initialized')):
                                success=True; proc.kill(); break
                            if any(x in marker for x in ('Exception','FATAL','Minecraft Crash Report')):
                                crashed=True; proc.kill(); break
                        elif proc.poll() is not None: break
                    if proc.poll() is None: timed_out=True; proc.kill()
                    code=proc.wait(timeout=5)
                except subprocess.TimeoutExpired: timed_out=True; proc.kill(); code=None
                raw=''.join(lines); log.write_text(raw,encoding='utf8')
                if not success and not crashed and code not in (0,None): crashed=True
            crashed=timed_out or crashed or code not in (0,None) or 'Exception' in raw or 'FATAL' in raw
            reached='Sound engine started' in raw or 'Main menu' in raw or 'OpenAL initialized' in raw
            return {'crashed':crashed,'timed_out':timed_out,'exit_code':code,'fingerprint':compute_fingerprint(raw_log=raw) if crashed else None,'reached_main_menu':reached,'suspects':[],'log_path':str(log),'duration_seconds':round(time.monotonic()-started,3)}
        except Exception as e:
            return {'crashed':True,'timed_out':False,'exit_code':None,'fingerprint':'','reached_main_menu':False,'error':str(e),'log_path':str(log),'duration_seconds':round(time.monotonic()-started,3)}
