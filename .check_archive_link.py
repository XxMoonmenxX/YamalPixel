import json
from pathlib import Path
import requests

url = 'https://disk.yandex.ru/d/aQIzo1UvI2M_Kw'
for endpoint in ('resources', 'resources/download'):
    response = requests.get('https://cloud-api.yandex.net/v1/disk/public/' + endpoint,
                            params={'public_key': url}, timeout=(8, 20))
    try:
        data = response.json()
    except ValueError:
        data = {'description': response.text[:250]}
    print(endpoint, response.status_code,
          json.dumps({k: data.get(k) for k in ('name', 'type', 'size', 'error', 'message', 'description') if k in data}, ensure_ascii=False))
    if data.get('href'):
        with requests.get(data['href'], stream=True, timeout=(8, 20)) as download:
            first = next(download.iter_content(32), b'')
            print('download', download.status_code, download.headers.get('Content-Type'), first[:16].hex())
for path in (Path.home() / 'YamalPixel/logs/launcher.log', Path.home() / 'YamalPixel/logs/launcher-console.log'):
    if path.exists():
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        from Core.bugreport import redact
        print(path.name)
        print('\n'.join(redact(line)[:500] for line in lines[-80:] if 'скачив' in line or 'ссылк' in line or 'ERROR' in line or 'Error' in line))
