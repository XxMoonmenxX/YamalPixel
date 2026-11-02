"""Run a bounded verification launch without blocking on a silent process."""
from collections import deque
from pathlib import Path
import queue
import subprocess
import threading
import time

from .repair_fingerprint import compute_fingerprint


class SilentVerifier:
    def __init__(self, timeout=600, launcher=None):
        self.timeout = timeout
        self.launcher = launcher

    def verify(self, instance_dir, command):
        instance_dir = Path(instance_dir)
        started = time.monotonic()
        log = instance_dir / '_repair' / 'silent-launch.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        try:
            crashed = False
            timed_out = False
            intentional_stop = False
            if self.launcher:
                with log.open('w', encoding='utf8') as out:
                    proc = self.launcher(command, instance_dir, out)
                    try:
                        code = proc.wait(timeout=self.timeout)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        code = None
                        timed_out = True
                raw = log.read_text(encoding='utf8', errors='replace')
            else:
                proc = subprocess.Popen(command, cwd=instance_dir, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                        errors='replace', bufsize=1)
                output = queue.Queue()

                def read_output():
                    try:
                        for line in proc.stdout:
                            output.put(line)
                    finally:
                        output.put(None)

                reader = threading.Thread(target=read_output, daemon=True)
                reader.start()
                lines = deque(maxlen=100_000)
                deadline = time.monotonic() + self.timeout
                reached = False
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        timed_out = True
                        break
                    try:
                        line = output.get(timeout=min(remaining, 0.1))
                    except queue.Empty:
                        continue
                    if line is None:
                        break
                    lines.append(line)
                    if any(marker in line for marker in ('Sound engine started', 'Main menu', 'OpenAL initialized')):
                        reached = True
                        intentional_stop = proc.poll() is None
                        break
                    if any(marker in line for marker in ('Exception', 'FATAL', 'Minecraft Crash Report')):
                        crashed = True
                        break
                if proc.poll() is None and (timed_out or reached or crashed):
                    proc.kill()
                try:
                    code = proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    code = None
                    timed_out = True
                reader.join(timeout=1)
                raw = ''.join(lines)
                log.write_text(raw, encoding='utf8')
            reached = any(marker in raw for marker in ('Sound engine started', 'Main menu', 'OpenAL initialized'))
            crashed = (timed_out or crashed or
                       (not intentional_stop and code not in (0, None)) or
                       'Exception' in raw or 'FATAL' in raw)
            return {'crashed': crashed, 'timed_out': timed_out, 'exit_code': code,
                    'fingerprint': compute_fingerprint(raw_log=raw) if crashed else None,
                    'reached_main_menu': reached, 'suspects': [], 'log_path': str(log),
                    'duration_seconds': round(time.monotonic() - started, 3)}
        except Exception as exc:
            return {'crashed': True, 'timed_out': False, 'exit_code': None, 'fingerprint': '',
                    'reached_main_menu': False, 'error': str(exc), 'log_path': str(log),
                    'duration_seconds': round(time.monotonic() - started, 3)}
