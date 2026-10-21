from pathlib import Path
import json, datetime
def _path(instance): return Path(instance)/'_crash_fingerprints.json'
def record(instance, fingerprint, suspects=None):
    if not fingerprint: return
    p=_path(instance)
    try: data=json.loads(p.read_text(encoding='utf8'))
    except (OSError,ValueError): data=[]
    data=[x for x in data if x.get('fingerprint')!=fingerprint]
    data.append({'fingerprint':fingerprint,'seen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'suspects':list(suspects or [])})
    p.write_text(json.dumps(data[-100:],ensure_ascii=False,indent=2),encoding='utf8')
def load(instance):
    try: return json.loads(_path(instance).read_text(encoding='utf8'))
    except (OSError,ValueError): return []
