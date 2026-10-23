"""Validate paths and replace mods only after the replacement is ready."""
import os
import zipfile
from pathlib import Path


def safe_filename(name):
    if (not isinstance(name, str) or not name or name in (".", "..")
            or any(c in name for c in '/\\:\x00')
            or name.endswith((' ', '.'))
            or any(c in name for c in '<>"|?*')
            or name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
                *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}):
        raise ValueError(f"Недопустимое имя файла: {name!r}")
    return name


def safe_target(directory, filename):
    root = Path(directory).resolve()
    target = root / safe_filename(filename)
    if target.is_symlink() or target.resolve().parent != root:
        raise ValueError("Путь файла выходит за пределы папки")
    return str(target)


def replace_mods(prepared, destination, rollback):
    """All paths must be on the same filesystem; restore on commit failure."""
    moved = False
    if os.path.exists(destination):
        os.replace(destination, rollback)
        moved = True
    try:
        os.replace(prepared, destination)
    except BaseException:
        if moved:
            os.replace(rollback, destination)
        raise

def validate_jar_or_zip(path):
    """Validate a downloaded archive before it becomes visible to the game."""
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad is not None:
                return False
        return True
    except (OSError, zipfile.BadZipFile):
        return False
