"""Isolated game data; downloaded Minecraft components remain shared."""
import hashlib
import json
import os
import re
import shutil
import tempfile
import threading
from pathlib import Path

_lock = threading.RLock()
_selected_version = 'YamalPixel'
LEGACY_ENTRIES = ('mods', 'config', 'defaultconfigs', 'saves', 'shaderpacks', 'resourcepacks',
                  'schematics', 'xaero', 'XaeroWaypoints', 'Distant_Horizons_server_data',
                  'patchouli_books', 'options.txt', 'optionsof.txt', 'optionsshaders.txt',
                  'servers.dat', 'servers.dat_old', 'usercache.json', 'emi.json', 'patchouli_data.json')


def launcher_root():
    from ConfDir.Configs import CONFIG
    return Path(CONFIG['minecraft_dir']).resolve()


def select_instance(version):
    global _selected_version
    _selected_version = version or 'YamalPixel'


def collection_identity(data):
    if data.get('instance_id'):
        return 'collection:' + str(data['instance_id'])
    return 'collection-file:' + str(data.get('filename') or data.get('name'))


def _directory(identity, label, root=None):
    root = Path(root).resolve() if root is not None else launcher_root()
    slug = re.sub(r'[^a-zA-Z0-9_-]+', '-', str(label)).strip('-')[:32] or 'collection'
    digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]
    # Identity alone controls the directory: display-name edits must not lose worlds.
    name = 'yamalpixel' if identity == 'builtin:YamalPixel' else 'instance-' + digest
    return root / 'instances' / name


def collection_directory(data, root=None):
    return _directory(collection_identity(data), data.get('name', 'collection'), root)


def game_directory(version=None, root=None):
    version = version or _selected_version
    if version == 'YamalPixel':
        return _directory('builtin:YamalPixel', version, root)
    if version.startswith('📦 '):
        from Core.collection_loader import load_collection_data
        data = load_collection_data(version[2:])
        if data is None:
            raise ValueError(f'Не найдена сборка: {version}')
        return collection_directory(data, root)
    return _directory('version:' + version, version, root)


def ensure_directory(directory, migrate_legacy=False, root=None):
    root = Path(root).resolve() if root is not None else launcher_root()
    directory = Path(directory).resolve()
    base = root / 'instances'
    if base.is_symlink():
        raise ValueError('Папка instances не должна быть символической ссылкой')
    if directory.parent != base.resolve():
        raise ValueError('Игровая папка должна находиться внутри instances')
    with _lock:
        if directory.exists():
            if directory.is_symlink() or not directory.is_dir():
                raise ValueError('Неверная папка сборки')
            return str(directory)
        base.mkdir(parents=True, exist_ok=True)
        if not migrate_legacy:
            directory.mkdir()
            return str(directory)
        # Copy once into a staging folder; never move/delete the old installation.
        with tempfile.TemporaryDirectory(prefix='.migration-', dir=base) as temporary:
            staging = Path(temporary) / 'game'
            staging.mkdir()
            for entry in LEGACY_ENTRIES:
                source = root / entry
                if source.is_symlink():
                    continue
                if source.is_dir():
                    shutil.copytree(source, staging / entry, symlinks=False,
                                    ignore=lambda folder, names: [n for n in names if (Path(folder) / n).is_symlink()])
                elif source.is_file():
                    shutil.copy2(source, staging / entry)
            (staging / '.legacy-import.json').write_text(
                json.dumps({'copied_from': str(root), 'originals_preserved': True}), encoding='utf-8')
            os.replace(staging, directory)
        return str(directory)


def ensure_game_directory(version=None):
    version = version or _selected_version
    return ensure_directory(game_directory(version), migrate_legacy=version == 'YamalPixel')
