from pathlib import Path
import hashlib,zipfile,json
from .repair_models import *
from .repair_quarantine import Quarantine
from .repair_verifier import SilentVerifier
from .repair_registry import record
import json, datetime
def snapshot(instance_dir):
    mods=Path(instance_dir)/'mods'; out=[]
    for p in sorted(mods.glob('*.jar')) if mods.is_dir() else []:
        try: out.append({'filename':p.name,'size':p.stat().st_size,'sha256':Quarantine.sha256(p)})
        except OSError as e: out.append({'filename':p.name,'error':str(e)})
    return {'mods':out}
def scan(instance_dir,snap=None):
    root=Path(instance_dir); issues=[]
    for item in (snap or snapshot(root))['mods']:
        p=root/'mods'/item['filename']; reason=None
        try:
            if item.get('size',0)==0: reason='empty file'
            else:
                with zipfile.ZipFile(p) as z:
                    if z.testzip() is not None: reason='corrupt archive member'
                    elif not any(x in z.namelist() for x in ('fabric.mod.json','META-INF/mods.toml','META-INF/neoforge.mods.toml')): reason='missing mod metadata'
        except (OSError,zipfile.BadZipFile) as e: reason=str(e)
        if reason:
            iid=hashlib.sha256((item['filename']+'|'+reason).encode()).hexdigest()[:16]
            issues.append(Issue(iid,IssueSeverity.BLOCKER,'integrity','Повреждён JAR: '+item['filename'],reason,[p],Fix(FixKind.QUARANTINE_MOD,iid,'Убрать в карантин',{'path':str(p),'reason':reason}),{'reason':reason}))
    return issues
def plan(issues): return [i.suggested_fix for i in sorted(issues,key=lambda i:(i.severity.value,i.category,i.id)) if i.suggested_fix]
def apply(fix,instance_dir):
    try:
        if fix.kind is FixKind.QUARANTINE_MOD: return RepairResult(True,Quarantine(instance_dir).move(fix.payload['path'],fix.payload.get('reason','repair')))
        if fix.kind is FixKind.RENAME_CONFIG:
            src=Path(fix.payload['path']); dst=src.with_name(src.name+'.broken')
            src.replace(dst); return RepairResult(True,{'from':str(src),'to':str(dst)})
        return RepairResult(False,error='unsupported fix')
    except Exception as e: return RepairResult(False,error=str(e))

def _metadata(path):
    try:
        with zipfile.ZipFile(path) as z:
            if 'fabric.mod.json' in z.namelist():
                d=json.loads(z.read('fabric.mod.json')); return d.get('id'), d.get('name',d.get('id','')), d.get('depends',{})
            return None
    except Exception: return None

def scan_extended(instance_dir, snap=None):
    issues=scan(instance_dir,snap); root=Path(instance_dir); registry={}
    try:
        from Core.java_manager import required_java_major, discover_java
        version=(snap or {}).get('minecraft_version') or '1.20.1'
        required=required_java_major(version, root)
        selected=discover_java(root)
        if not any(x.get('major',0) >= required for x in selected):
            iid=hashlib.sha256(('java|'+str(required)).encode()).hexdigest()[:16]
            issues.append(Issue(iid,IssueSeverity.BLOCKER,'java',f'Требуется Java {required}', 'Подходящая Java не найдена; исправление вручную через менеджер Java.'))
    except Exception as e:
        issues.append(Issue('java-check',IssueSeverity.MEDIUM,'java','Проверка Java не выполнена',str(e)))
    for p in (root/'mods').glob('*.jar') if (root/'mods').is_dir() else []:
        meta=_metadata(p)
        if not meta: continue
        mod_id,name,deps=meta
        if mod_id in registry:
            iid=hashlib.sha256(('duplicate|'+mod_id).encode()).hexdigest()[:16]
            issues.append(Issue(iid,IssueSeverity.BLOCKER,'duplicate_id',f'Дубликат мода: {mod_id}',f'{registry[mod_id].name} и {p.name}',[registry[mod_id],p]))
        else: registry[mod_id]=p
    for p in (root/'mods').glob('*.jar') if (root/'mods').is_dir() else []:
        meta=_metadata(p)
        if not meta: continue
        for dep in meta[2]:
            if dep not in {'minecraft','java','fabricloader','forge','neoforge'} and dep not in registry:
                iid=hashlib.sha256(('missing|'+dep+'|'+p.name).encode()).hexdigest()[:16]
                issues.append(Issue(iid,IssueSeverity.BLOCKER,'missing_dep',f'Отсутствует зависимость: {dep}',f'Требуется для {p.name}',[p]))
    config=root/'config'
    if config.is_dir():
        for p in config.glob('*.json'):
            try: json.loads(p.read_text(encoding='utf-8'))
            except json.JSONDecodeError as e:
                iid=hashlib.sha256(('config|'+str(p)).encode()).hexdigest()[:16]
                fix=Fix(FixKind.RENAME_CONFIG,iid,'Переименовать повреждённый конфиг',{'path':str(p)})
                issues.append(Issue(iid,IssueSeverity.MEDIUM,'config',f'Битый JSON: {p.name}',f'строка {e.lineno}',[p],fix))
    return issues

class RepairSession:
    def __init__(self, instance_dir, progress=None, verifier=None, command=None, report_dir=None): self.instance_dir=Path(instance_dir); self.progress=progress; self.applied=[]; self.verifier=verifier; self.command=command; self.report_dir=Path(report_dir) if report_dir else self.instance_dir/'_repair'/'sessions'
    def run(self, plan_only=False):
        if not self.instance_dir.is_dir(): return {'outcome':'needs_user','issues':[],'plan':[]}
        snap=snapshot(self.instance_dir); issues=scan_extended(self.instance_dir,snap); fixes=plan(issues)
        if plan_only: return {'outcome':'issues' if issues else 'no_issues','snapshot':snap,'issues':issues,'plan':fixes}
        for fix in fixes:
            result=apply(fix,self.instance_dir)
            self.applied.append(result)
            if self.progress: self.progress(fix.description, result)
        if not issues: outcome='no_issues'
        elif not fixes: outcome='needs_user'
        elif all(r.applied for r in self.applied): outcome='fixed'
        else: outcome='partial'
        result={'outcome':outcome,'snapshot':snap,'issues':issues,'plan':fixes,'applied':self.applied}
        if self.verifier and self.command and outcome=='fixed':
            result['verification']=self.verifier.verify(self.instance_dir,self.command)
            if result['verification']['crashed']:
                result['outcome']='partial'; record(self.instance_dir,result['verification'].get('fingerprint'),result['verification'].get('suspects'))
        self.report_dir.mkdir(parents=True,exist_ok=True); report=self.report_dir/('repair-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
        report.write_text(json.dumps(_json(result),ensure_ascii=False,indent=2),encoding='utf8'); result['report_path']=str(report)
        text=report.with_name('report.txt')
        lines=['YamalPixel Repair Report',f'Outcome: {result["outcome"]}',f'Issues: {len(issues)}','']
        lines += [f'[{i.severity.value}] {i.title}: {i.detail}' for i in issues]
        if result.get('verification'): lines += ['', 'Verification: '+str(result['verification'])]
        text.write_text('\n'.join(lines),encoding='utf8'); result['text_report_path']=str(text)
        return result

def _json(value):
    if isinstance(value,(str,int,float,bool)) or value is None:return value
    if isinstance(value,Path):return str(value)
    if isinstance(value,IssueSeverity):return value.value
    if isinstance(value,FixKind):return value.value
    if isinstance(value,dict):return {k:_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_json(v) for v in value]
    if hasattr(value,'__dict__'):return _json(value.__dict__)
    return str(value)

def rollback(result):
    data=getattr(result,'rollback_data',{}) or {}
    try:
        if 'quarantined' in data: Path(data['quarantined']).replace(data['original']); return True
        if 'to' in data: Path(data['to']).replace(data['from']); return True
    except OSError: return False
    return False
