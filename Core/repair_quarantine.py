from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,shutil
class Quarantine:
    def __init__(self, instance_dir): self.instance_dir=Path(instance_dir); self.root=self.instance_dir/'mods'/'_quarantine'
    @staticmethod
    def sha256(path):
        h=hashlib.sha256()
        with Path(path).open('rb') as f:
            for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
        return h.hexdigest()
    def move(self, source, reason):
        source=Path(source).resolve(); mods=(self.instance_dir/'mods').resolve()
        if source.parent!=mods: raise ValueError('only direct mod files may be quarantined')
        folder=self.root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_'+reason[:40]); folder.mkdir(parents=True)
        target=folder/source.name; digest=self.sha256(source); os.replace(source,target)
        meta={'original':str(source),'quarantined':str(target),'sha256':digest,'reason':reason}
        try: (folder/(source.name+'.meta.json')).write_text(json.dumps(meta,indent=2),encoding='utf8')
        except Exception: os.replace(target,source); shutil.rmtree(folder,ignore_errors=True); raise
        return meta
    def restore(self, meta_path):
        p=Path(meta_path).resolve(); meta=json.loads(p.read_text(encoding='utf8')); src=Path(meta['quarantined']).resolve(); dst=Path(meta['original']).resolve()
        if src.parent!=p.parent or dst.parent!=(self.instance_dir/'mods').resolve() or dst.exists(): raise ValueError('invalid restore target')
        os.replace(src,dst); return dst
