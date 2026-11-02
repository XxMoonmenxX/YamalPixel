"""Keep an atomic manifest and verified copies of the last working mods."""
import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .mod_transaction import safe_filename


def write(instance, version=None, mc_version=None, loader=None):
    root = Path(instance)
    objects = root / '_repair' / 'last-ok' / 'objects'
    objects.mkdir(parents=True, exist_ok=True)
    mods = []
    mods_dir = root / 'mods'
    for source in sorted(mods_dir.glob('*.jar')) if mods_dir.is_dir() else []:
        safe_filename(source.name)
        if source.is_symlink() or not source.is_file():
            raise ValueError(f'Недопустимый файл мода: {source.name}')
        descriptor, temporary = tempfile.mkstemp(prefix='.snapshot-', suffix='.tmp', dir=objects)
        try:
            digest = hashlib.sha256()
            size = 0
            with os.fdopen(descriptor, 'wb') as output, source.open('rb') as input_file:
                while chunk := input_file.read(1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                output.flush()
                os.fsync(output.fileno())
            checksum = digest.hexdigest()
            target = objects / f'{checksum}.jar'
            if target.is_symlink():
                raise ValueError('Недопустимый путь снимка мода')
            if target.exists():
                with target.open('rb') as stored:
                    if hashlib.file_digest(stored, 'sha256').hexdigest() != checksum:
                        raise ValueError(f'Повреждён снимок мода: {source.name}')
            else:
                os.replace(temporary, target)
            mods.append({'filename': source.name, 'sha256': checksum, 'size': size})
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    data = {'version': 2, 'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'instance_version': version, 'mc_version': mc_version, 'loader': loader, 'mods': mods}
    descriptor, temporary = tempfile.mkstemp(prefix='.last-ok-', suffix='.tmp', dir=root)
    path = root / '_last_ok_mods.json'
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def read(instance):
    try:
        return json.loads((Path(instance) / '_last_ok_mods.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
