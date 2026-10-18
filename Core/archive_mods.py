"""Download one mod bundle and unpack only safe JAR entries into staging."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import time
import zipfile
import requests
import rarfile

from Core.mod_transaction import safe_filename
from Network.Downloader import download_yandex_file_sync


def prepare_archive_mods(url, destination, progress=None, cancel_event=None):
    cache = Path.home() / '.yamalpixel_cache' / 'mod_archives'
    cache.mkdir(parents=True, exist_ok=True)
    archive_path = cache / (hashlib.sha256(url.encode()).hexdigest() + '.zip')
    metadata_path = archive_path.with_suffix('.json')
    remote = None
    try:
        response = requests.get('https://cloud-api.yandex.net/v1/disk/public/resources',
                                params={'public_key': url, 'fields': 'md5,size,modified'}, timeout=15)
        response.raise_for_status()
        remote = response.json()
    except (requests.RequestException, ValueError):
        pass
    if isinstance(remote, dict) and str(remote.get('name', '')).lower().endswith('.rar'):
        archive_path = cache / (hashlib.sha256(url.encode()).hexdigest() + '.rar')
        metadata_path = archive_path.with_suffix('.json')
    cached = False
    if archive_path.is_file() and metadata_path.is_file():
        try:
            saved = json.loads(metadata_path.read_text(encoding='utf-8'))
            with archive_path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'md5').hexdigest()
            cached = digest == saved.get('md5') and (remote is None or remote.get('md5') == digest)
        except (OSError, ValueError):
            pass
    if not cached:
        last = [0.0]
        def downloaded(done, total):
            if cancel_event and cancel_event.is_set():
                raise InterruptedError('Установка отменена')
            now = time.monotonic()
            if progress and (now - last[0] >= 0.1 or done == total):
                last[0] = now
                progress(done, total, 'Архив модов', status='archive_download')
        if not download_yandex_file_sync(url, str(archive_path), progress_callback=downloaded):
            raise RuntimeError('Не удалось скачать архив модов YamalPixel')
        with archive_path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'md5').hexdigest()
        if remote and remote.get('md5') and remote['md5'] != digest:
            raise ValueError('Контрольная сумма архива не совпала; повторите запуск')
        metadata_path.write_text(json.dumps({'md5': digest}), encoding='utf-8')
    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile:
        try:
            archive = rarfile.RarFile(archive_path)
        except rarfile.RarCannotExec as exc:
            raise RuntimeError('Для RAR нужен установленный 7-Zip или unrar. Установите 7-Zip и повторите запуск.') from exc
        except rarfile.Error as exc:
            raise ValueError('Архив модов повреждён или имеет неподдерживаемый формат') from exc
    with archive:
        jars = []
        names = set()
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename.replace('\\', '/'))
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Небезопасный путь в архиве: ' + entry.filename)
            if entry.is_dir() or path.suffix.lower() != '.jar':
                continue
            for part in path.parts:
                safe_filename(part)
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Символическая ссылка в архиве')
            name = safe_filename(path.name)
            if name.casefold() in names:
                raise ValueError('Повторяющийся мод в архиве: ' + name)
            names.add(name.casefold())
            jars.append((entry, name))
        if not jars:
            raise ValueError('Архив не содержит JAR-модов')
        for index, (entry, name) in enumerate(jars):
            if cancel_event and cancel_event.is_set():
                raise InterruptedError('Установка отменена')
            if progress:
                progress(index, len(jars), name, status='archive_extract')
            with archive.open(entry) as source, (Path(destination) / name).open('wb') as target:
                shutil.copyfileobj(source, target)
    if progress:
        progress(len(jars), len(jars), 'Архив распакован', status='archive_ready')
    return len(jars)
