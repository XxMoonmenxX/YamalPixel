"""One atomic, validated file writer for direct downloads and proxy responses."""
import hashlib
import os
from pathlib import Path
import tempfile

from Core.mod_transaction import validate_jar_or_zip

MAX_DOWNLOAD_BYTES = 4 * 1024 * 1024 * 1024


def save_response(response, destination, progress_callback=None, max_bytes=None):
    """Publish only a complete response; preserve an existing file on failure."""
    destination = Path(destination)
    temporary = None
    limit = MAX_DOWNLOAD_BYTES if max_bytes is None else max_bytes
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='.download-', suffix='.part', dir=destination.parent)
        with os.fdopen(fd, 'wb') as output:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError(f'Источник не выдал файл: HTTP {response.status_code}')
            headers = response.headers
            total = int(headers.get('Content-Length', headers.get('content-length', 0)) or 0)
            if headers.get('Content-Encoding', 'identity').lower() != 'identity':
                total = 0  # requests yields decoded bytes, not encoded Content-Length.
            if total > limit:
                raise ValueError('Файл превышает допустимый размер')
            content_type = headers.get('Content-Type', '').lower()
            if content_type.startswith(('text/html', 'application/json')):
                raise ValueError('Источник вернул страницу ошибки вместо файла')
            digest = hashlib.sha256()
            downloaded = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > limit:
                    raise ValueError('Файл превышает допустимый размер')
                output.write(chunk)
                digest.update(chunk)
                if progress_callback:
                    progress_callback(downloaded, total)
            if not downloaded or (total and downloaded != total):
                raise ValueError('Неполная загрузка')
            expected = headers.get('X-Content-SHA256')
            if expected and digest.hexdigest() != expected.lower():
                raise ValueError('Контрольная сумма скачанного файла не совпала')
        if destination.suffix.lower() in ('.jar', '.zip') and not validate_jar_or_zip(temporary):
            raise ValueError('Повреждённый архив')
        os.replace(temporary, destination)
        return True
    finally:
        response.close()
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
