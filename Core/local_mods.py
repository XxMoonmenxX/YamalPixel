"""Import local JARs into a persistent, content-addressed collection store."""
import hashlib
import os
import shutil
import tempfile
import zipfile
import re
from pathlib import Path, PurePosixPath

from Core.mod_transaction import safe_filename, MAX_ARCHIVE_ENTRIES

MAX_MOD_BYTES = 2 * 1024 * 1024 * 1024
MAX_IMPORT_BYTES = 16 * 1024 * 1024 * 1024
MAX_ENTRIES = 10000


def validate_jar(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if (len(entries) > MAX_ARCHIVE_ENTRIES or
                sum(entry.file_size for entry in entries) > MAX_MOD_BYTES or
                any(entry.file_size > MAX_MOD_BYTES for entry in entries)):
            raise ValueError(f'Слишком большой JAR: {Path(path).name}')
        if not entries or archive.testzip() is not None:
            raise ValueError(f'Повреждённый JAR: {Path(path).name}')


def import_local_mods(paths, collections_dir):
    """Accept JAR files, a mods/pack folder, or a ZIP containing actual JARs."""
    root = Path(collections_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    result = []
    names = {}
    with tempfile.TemporaryDirectory(prefix='.local-import-', dir=root) as temporary:
        staging = Path(temporary)
        total = 0

        def add(name, stream):
            nonlocal total
            if len(result) >= MAX_ENTRIES:
                raise ValueError('Слишком много локальных модов')
            name = safe_filename(name)
            candidate = staging / str(len(result))
            with candidate.open('wb') as target:
                size = 0
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    total += len(chunk)
                    if size > MAX_MOD_BYTES or total > MAX_IMPORT_BYTES:
                        raise ValueError('Слишком большой размер локальных модов')
                    target.write(chunk)
            validate_jar(candidate)
            with candidate.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            key = name.casefold()
            if key in names:
                if names[key] == digest:
                    return
                raise ValueError(f'Разные моды имеют одинаковое имя: {name}')
            names[key] = digest
            result.append({'source': 'local', 'name': Path(name).stem,
                           'filename': name, 'sha256': digest,
                           'local_file': f'local_mods/{digest}.jar', '_prepared': candidate})

        for selected in paths:
            path = Path(selected)
            if path.is_dir():
                folder = path / 'mods' if (path / 'mods').is_dir() else path
                for candidate in sorted(folder.glob('*')):
                    if candidate.is_file() and candidate.suffix.lower() == '.jar':
                        with candidate.open('rb') as stream:
                            add(candidate.name, stream)
            elif path.suffix.lower() == '.jar':
                with path.open('rb') as stream:
                    add(path.name, stream)
            elif path.suffix.lower() == '.zip':
                with zipfile.ZipFile(path) as archive:
                    jars = [entry for entry in archive.infolist()
                            if not entry.is_dir() and entry.filename.lower().endswith('.jar')]
                    in_mods = [entry for entry in jars
                               if 'mods' in PurePosixPath(entry.filename.replace('\\', '/')).parts[:-1]]
                    for entry in in_mods or jars:
                        # Read members directly; archive paths are never extracted.
                        with archive.open(entry) as stream:
                            add(PurePosixPath(entry.filename.replace('\\', '/')).name, stream)
            else:
                raise ValueError(f'Выберите JAR, ZIP или папку с модами: {path.name}')
        if not result:
            raise ValueError('JAR-моды не найдены. Выберите папку mods или архив с файлами модов.')
        store = root / 'local_mods'
        if store.is_symlink():
            raise ValueError('Недопустимая папка локальных модов')
        store.mkdir(exist_ok=True)
        for mod in result:
            target = store / (mod['sha256'] + '.jar')
            if target.is_symlink():
                raise ValueError('Недопустимый путь локального мода')
            mod.pop('_prepared').replace(target)
    return result


def _download_community_mod(mod, root, collection_id):
    from urllib.parse import quote
    import requests
    from ConfDir.Configs import CURSEFORGE_CONFIG
    from Network.proxy_auth import generate_auth_header
    digest = mod.get('sha256', '')
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Неверная контрольная сумма локального мода')
    store = root / 'local_mods'
    if store.is_symlink():
        raise ValueError('Недопустимая папка локальных модов')
    store.mkdir(parents=True, exist_ok=True)
    target = store / (digest + '.jar')
    if target.is_symlink():
        raise ValueError('Недопустимый путь локального мода')
    url = (CURSEFORGE_CONFIG['proxy_url'].rstrip('/') + '/api/v1/community/mod/'
           + quote(str(collection_id), safe='') + '/' + digest)
    fd, temporary = tempfile.mkstemp(prefix='.community-', dir=store)
    os.close(fd)
    try:
        with requests.get(url, headers=generate_auth_header(), stream=True,
                          timeout=(10, 120), allow_redirects=False) as response:
            if response.status_code != 200:
                raise ValueError(f'Прокси не выдал локальный мод {mod.get("filename", "")}: '
                                 f'HTTP {response.status_code}. Владельцу сборки нужно импортировать JAR на прокси.')
            size = 0
            actual = hashlib.sha256()
            with open(temporary, 'wb') as output:
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_MOD_BYTES:
                        raise ValueError('Слишком большой локальный мод')
                    actual.update(chunk)
                    output.write(chunk)
        if actual.hexdigest() != digest:
            raise ValueError('Скачанный мод не соответствует контрольной сумме сборки')
        validate_jar(temporary)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def copy_local_mod(mod, collections_dir, destination, community_id=None):
    root = Path(collections_dir).resolve()
    relative = PurePosixPath(mod.get('local_file', ''))
    if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != 'local_mods':
        raise ValueError('Неверный путь локального мода')
    source = (root / 'local_mods' / safe_filename(relative.name)).resolve()
    if not source.is_relative_to(root / 'local_mods'):
        raise ValueError('Неверный путь локального мода')
    if community_id and not source.is_file():
        _download_community_mod(mod, root, community_id)
    if not source.is_relative_to(root / 'local_mods') or not source.is_file():
        raise ValueError(f'Локальный мод отсутствует: {mod.get("filename", "")}')
    with source.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if community_id and digest != mod.get('sha256'):
        _download_community_mod(mod, root, community_id)
        with source.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != mod.get('sha256'):
        raise ValueError(f'Локальный мод изменён или повреждён: {mod.get("filename", "")}')
    validate_jar(source)
    # A hard link would let in-game or external edits corrupt the shared cache.
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.local-copy-', dir=destination.parent)
    os.close(fd)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
