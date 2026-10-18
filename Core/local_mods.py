"""Import local JARs into a persistent, content-addressed collection store."""
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from Core.mod_transaction import safe_filename


def validate_jar(path):
    with zipfile.ZipFile(path) as archive:
        if not archive.namelist() or archive.testzip() is not None:
            raise ValueError(f'Повреждённый JAR: {Path(path).name}')


def import_local_mods(paths, collections_dir):
    """Accept JAR files, a mods/pack folder, or a ZIP containing actual JARs."""
    root = Path(collections_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    result = []
    names = {}
    with tempfile.TemporaryDirectory(prefix='.local-import-', dir=root) as temporary:
        staging = Path(temporary)

        def add(name, stream):
            name = safe_filename(name)
            candidate = staging / str(len(result))
            with candidate.open('wb') as target:
                shutil.copyfileobj(stream, target)
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


def copy_local_mod(mod, collections_dir, destination):
    root = Path(collections_dir).resolve()
    relative = PurePosixPath(mod.get('local_file', ''))
    if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != 'local_mods':
        raise ValueError('Неверный путь локального мода')
    source = (root / 'local_mods' / safe_filename(relative.name)).resolve()
    if not source.is_relative_to(root / 'local_mods') or not source.is_file():
        raise ValueError(f'Локальный мод отсутствует: {mod.get("filename", "")}')
    with source.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != mod.get('sha256'):
        raise ValueError(f'Локальный мод изменён или повреждён: {mod.get("filename", "")}')
    validate_jar(source)
    shutil.copy2(source, destination)
