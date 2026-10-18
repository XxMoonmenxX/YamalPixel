"""Complete, local diagnostic export; never uploads anything."""
import gzip
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
import threading
import zipfile
from datetime import datetime
from pathlib import Path

_lock = threading.Lock()
_secret = re.compile(
    r'''(?i)((?:["']?(?:access[_-]?token|refresh[_-]?token|api[_-]?key|authorization|password|client[_-]?secret)["']?)\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;}]+)''')


def redact(text):
    text = _secret.sub(r'\1"[REDACTED]"', text)
    text = re.sub(r'(?i)(--(?:accessToken|clientId|xuid)\s+)[^\s]+', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)(Bearer\s+)[\w.\-]+', r'\1[REDACTED]', text)
    # Temporary Yandex download URLs contain credentials in the query string.
    return re.sub(r'(https?://[^\s"<>]*disk\.yandex\.[^\s"<>?]+)\?[^\s"<>]+',
                  r'\1?[REDACTED]', text)


def create_bugreport(minecraft_dir=None, output=None, context=None):
    """Export full logs (including gzip), crashes, configs and mod identities."""
    from ConfDir.Configs import CONFIG
    from ConfDir.Versions import CURRENT_VERSION
    game = Path(minecraft_dir or CONFIG['minecraft_dir']).resolve()
    target = Path(output or game / 'Bugreport.txt').resolve()
    project = Path(__file__).resolve().parents[1]
    shared = Path((context or {}).get('shared_dir', CONFIG['minecraft_dir']))
    with _lock:
        target.parent.mkdir(parents=True, exist_ok=True)
        for handler in logging.getLogger().handlers:
            handler.flush()
        for stream in (sys.stdout, sys.stderr):
            if stream:
                try:
                    stream.flush()
                except (OSError, ValueError):
                    pass
        fd, temporary = tempfile.mkstemp(prefix='bugreport-', suffix='.tmp', dir=target.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as report:
                def write(text):
                    report.write(redact(str(text)) + '\n')

                def section(title):
                    write('\n' + '=' * 90 + '\n' + title + '\n' + '=' * 90)

                def include(path):
                    section(f'FILE: {path} ({path.stat().st_size} bytes)')
                    try:
                        opener = gzip.open if path.suffix == '.gz' else open
                        with opener(path, 'rt', encoding='utf-8-sig', errors='replace') as source:
                            for line in source:
                                report.write(redact(line))
                        write('\n[END FILE]')
                    except Exception as exc:
                        write(f'[READ ERROR] {exc}')

                section('YamalPixel — Bugreport')
                write(f'Time: {datetime.now().astimezone().isoformat()}\nLauncher: {CURRENT_VERSION}')
                write(f'Game directory: {game}\nReport: {target}\nPython: {sys.version}\nExecutable: {sys.executable}')
                write(f'OS: {platform.platform()}\nMachine: {platform.machine()}\nCPU: {platform.processor()}')
                write('Logs are complete, not just tails. Secrets are redacted; player names, chat and server addresses remain.')
                write('Reproduction: launch YamalPixel, connect to Minecraft server 90.151.59.120:25565 (Minecraft protocol, not HTTP).')
                write(json.dumps(context or {}, ensure_ascii=False, indent=2))
                section('Launcher settings (diagnostic allowlist)')
                write(json.dumps({k: CONFIG.get(k) for k in (
                    'version', 'fabric_loader', 'minecraft_dir', 'jvm_memory', 'show_beta_versions', 'mods_archive_url')},
                    ensure_ascii=False, indent=2))
                section('System and installed Python packages')
                try:
                    import psutil
                    write(f'RAM: {psutil.virtual_memory()}\nDisk: {psutil.disk_usage(str(game))}')
                except Exception as exc:
                    write(exc)
                for dist in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata.get('Name', '')):
                    write(f'{dist.metadata.get("Name", "?")}=={dist.version}')
                section('Java runtimes')
                java_paths = set(game.glob('runtime/**/bin/java.exe'))
                java_paths.update(game.glob('java-runtimes/**/bin/java.exe'))
                if shared != game:
                    java_paths.update(shared.glob('runtime/**/bin/java.exe'))
                    java_paths.update(shared.glob('java-runtimes/**/bin/java.exe'))
                from Core.java_manager import load_java_selection
                selection = load_java_selection(game)
                if selection != 'auto':
                    java_paths.add(Path(selection))
                import shutil
                system_java = shutil.which('java')
                if system_java:
                    java_paths.add(Path(system_java))
                for java in sorted(java_paths):
                    write(java)
                    try:
                        result = subprocess.run([str(java), '-version'], capture_output=True, text=True,
                                                errors='replace', timeout=10,
                                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        write(result.stdout + result.stderr)
                    except Exception as exc:
                        write(exc)
                section('Mods: filenames, SHA256 and fabric.mod.json (including nested mods)')
                def metadata(archive, label, depth=0):
                    if 'fabric.mod.json' in archive.namelist():
                        data = json.loads(archive.read('fabric.mod.json'))
                        write(f'{label}: ' + json.dumps(data, ensure_ascii=False))
                        if depth < 5:
                            import io
                            for nested in data.get('jars', []):
                                name = nested['file']
                                with zipfile.ZipFile(io.BytesIO(archive.read(name))) as child:
                                    metadata(child, label + '!' + name, depth + 1)
                    elif 'META-INF/mods.toml' in archive.namelist():
                        write(archive.read('META-INF/mods.toml').decode('utf-8', 'replace'))
                for mod in sorted((game / 'mods').glob('*')):
                    if not mod.is_file():
                        continue
                    try:
                        with mod.open('rb') as source:
                            digest = hashlib.file_digest(source, 'sha256').hexdigest()
                        write(f'{mod.name} size={mod.stat().st_size} sha256={digest}')
                        if mod.suffix.lower() == '.jar':
                            with zipfile.ZipFile(mod) as archive:
                                metadata(archive, mod.name)
                    except Exception as exc:
                        write(f'{mod.name}: {exc}')
                section('Resource packs and shader packs')
                for folder in ('resourcepacks', 'shaderpacks'):
                    for path in sorted((game / folder).glob('*')):
                        write(f'{path} size={path.stat().st_size}')
                seen = set()
                section('ALL available logs, crashes, JVM failures, game profiles and text configs')
                roots = [game / 'logs', game / 'crash-reports',
                         Path.home() / 'YamalPixel' / 'logs', project / 'logs',
                         game / 'config', game / 'defaultconfigs', game / 'versions',
                         game / 'custom_collections']
                if shared != game:
                    roots.append(shared / 'versions')
                allowed = {'.log', '.txt', '.gz', '.json', '.toml', '.properties', '.cfg', '.ini', '.yaml', '.yml'}
                files = set()
                for root in roots:
                    if root.exists():
                        files.update(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in allowed)
                for root in (game, project):
                    files.update(root.glob('hs_err_pid*.log'))
                    files.update(root.glob('replay_pid*.log'))
                for name in ('options.txt', 'optionsof.txt', 'optionsshaders.txt', 'last_session.json',
                             'launcher-java.json', 'CrashAnalysis.txt'):
                    if (game / name).exists():
                        files.add(game / name)
                # Most recent evidence first; old logs remain in the report in full.
                for path in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True):
                    resolved = path.resolve()
                    if resolved == target or resolved in seen:
                        continue
                    seen.add(resolved)
                    include(path)
                section('END OF REPORT')
                write(f'Included text files: {len(seen)}')
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return str(target)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Export a complete local Bugreport.txt')
    parser.add_argument('--output')
    parser.add_argument('--minecraft-dir')
    args = parser.parse_args()
    print(create_bugreport(args.minecraft_dir, args.output))
