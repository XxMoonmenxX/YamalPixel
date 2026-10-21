from pathlib import Path
import json,datetime
from .repair_quarantine import Quarantine
def write(instance, version=None, mc_version=None, loader=None):
    root=Path(instance); mods=[]
    for p in (root/'mods').glob('*.jar') if (root/'mods').is_dir() else []:
        try: mods.append({'filename':p.name,'sha256':Quarantine.sha256(p),'size':p.stat().st_size})
        except OSError: pass
    data={'version':1,'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'instance_version':version,'mc_version':mc_version,'loader':loader,'mods':mods}
    path=root/'_last_ok_mods.json'; path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8'); return path
def read(instance):
    try: return json.loads((Path(instance)/'_last_ok_mods.json').read_text(encoding='utf8'))
    except (OSError,ValueError): return None
