from pathlib import Path
import subprocess, time, shutil
from .repair_fingerprint import compute_fingerprint

class SilentVerifier:
    def __init__(self, timeout=120, launcher=None): self.timeout=timeout; self.launcher=launcher
    def verify(self, instance_dir, command):
        instance_dir=Path(instance_dir); started=time.monotonic(); log=instance_dir/'_repair'/'silent-launch.log'; log.parent.mkdir(parents=True,exist_ok=True)
        try:
            with log.open('w',encoding='utf8') as out:
                proc=(self.launcher(command,instance_dir,out) if self.launcher else subprocess.Popen(command,cwd=instance_dir,stdout=out,stderr=subprocess.STDOUT))
                try: code=proc.wait(timeout=self.timeout); timed_out=False
                except subprocess.TimeoutExpired: proc.kill(); code=None; timed_out=True
            raw=log.read_text(encoding='utf8',errors='replace')
            crashed=timed_out or code not in (0,None) or 'Exception' in raw or 'ERROR' in raw or 'FATAL' in raw
            reached='Sound engine started' in raw or 'Main menu' in raw
            return {'crashed':crashed,'timed_out':timed_out,'exit_code':code,'fingerprint':compute_fingerprint(raw_log=raw) if crashed else None,'reached_main_menu':reached,'suspects':[],'log_path':str(log),'duration_seconds':round(time.monotonic()-started,3)}
        except Exception as e:
            return {'crashed':True,'timed_out':False,'exit_code':None,'fingerprint':'','reached_main_menu':False,'error':str(e),'log_path':str(log),'duration_seconds':round(time.monotonic()-started,3)}
