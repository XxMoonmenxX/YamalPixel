# Network/Downloader.py
import os
from Network.proxy_status import proxy_available, mark_proxy_unavailable
import time
import hashlib
import requests
import asyncio
import logging
import zipfile
from urllib.parse import urljoin, urlparse
from Core.mod_transaction import safe_target, validate_jar_or_zip
from pathlib import Path
from Network.proxy_auth import generate_auth_header, ProxyAuthError
from Network.file_transfer import save_response

from ConfDir.Configs import CURSEFORGE_CONFIG

logger = logging.getLogger(__name__)


def _is_trusted_modpack_url(url, source):
    """Allow direct URLs only from the marketplace CDN domains."""
    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urlparse(url.strip())
    host = (parsed.hostname or '').lower().rstrip('.')
    if parsed.scheme.lower() != 'https' or not host or parsed.username or parsed.password:
        return False
    if source == 'modrinth':
        return host == 'modrinth.com' or host.endswith('.modrinth.com')
    return (host == 'curseforge.com' or host.endswith('.curseforge.com')
            or host == 'forgecdn.net' or host.endswith('.forgecdn.net'))

def _safe_print(message):
    """Keep diagnostic output from crashing on legacy Windows consoles."""
    try:
        print(message)
    except UnicodeEncodeError:
        try:
            print(str(message).encode("ascii", "backslashreplace").decode("ascii"))
        except Exception:
            logger.info("%s", message)


class LauncherCache:
    def __init__(self):
        self.cache_dir = Path.home() / ".yamalpixel_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def is_cache_fresh(self, cache_file, max_age_hours=24):
        if not cache_file.exists():
            return False
        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < (max_age_hours * 3600)

    def get_file_hash(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def download_and_cache(self, url, cache_file):
        if not download_file_sync(url, str(cache_file)):
            raise RuntimeError(f'Не удалось скачать файл в кэш: {cache_file.name}')

    def get_cached_file(self, url, force_refresh=False):
        file_hash = self.get_file_hash(url)
        cache_file = self.cache_dir / file_hash

        if cache_file.exists() and not force_refresh:
            if self.is_cache_fresh(cache_file):
                return cache_file

        self.download_and_cache(url, cache_file)
        return cache_file


class TurboDownloader:
    def __init__(self):
        self.cache = {}
        self._session = None

    async def cleanup(self):
        # Async compatibility API; downloads now use the same synchronous transport.
        pass

    async def get_turbo_link(self, public_key):
        cached = self.cache.get(public_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        link = await asyncio.to_thread(get_yandex_direct_link_sync, public_key)
        if link:
            self.cache[public_key] = (time.monotonic() + 60, link)
        return link

    async def download_file_async(self, url, file_path, progress_callback=None):
        return await asyncio.to_thread(download_file_sync, url, str(file_path), progress_callback)

    def download_file_sync(self, url, file_path, progress_callback=None):
        return download_file_sync(url, str(file_path), progress_callback)


def get_yandex_direct_link_sync(public_key):
    """Синхронное получение прямой ссылки с Яндекс.Диска"""
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    try:
        response = requests.get(api_url, params={"public_key": public_key}, timeout=30)
        response.raise_for_status()
        link = response.json().get("href")
        if not isinstance(link, str) or not link.startswith(('https://', 'http://')):
            raise ValueError('API Яндекс Диска не вернул ссылку на файл')
        return link
    except Exception as e:
        logger.error(f"Ошибка получения ссылки: {e}")
        return None


def download_file_sync(url, filepath, progress_callback=None, url_validator=None, max_bytes=None):
    try:
        request_url = url
        if url_validator is None:
            response = requests.get(request_url, stream=True, timeout=60,
                                    headers={'Accept-Encoding': 'identity'})
        else:
            for _ in range(6):
                if not url_validator(request_url):
                    raise ValueError('Небезопасная ссылка загрузки')
                response = requests.get(request_url, stream=True, timeout=60,
                                        headers={'Accept-Encoding': 'identity'}, allow_redirects=False)
                if response.status_code not in (301, 302, 303, 307, 308):
                    break
                location = response.headers.get('Location')
                response.close()
                if not location:
                    raise ValueError('Перенаправление без адреса')
                request_url = urljoin(request_url, location)
            else:
                raise ValueError('Слишком много перенаправлений')
        return save_response(response, filepath, progress_callback, max_bytes)
    except Exception as exc:
        logger.error('Ошибка скачивания %s: %s', url, exc)
        return False


def download_yandex_file_sync(public_url, filepath, source='yandex', progress_callback=None):
    if proxy_available() and download_through_proxy(public_url, filepath, source, progress_callback):
        return True
    public_url = public_url.strip()
    for attempt in range(2):
        direct_link = get_yandex_direct_link_sync(public_url)
        success = (download_file_sync(direct_link, filepath, progress_callback) if progress_callback
                   else download_file_sync(direct_link, filepath)) if direct_link else False
        if success:
            return True
        if attempt == 0:
            logger.info('Повторная попытка Яндекс Диска со свежей ссылкой: %s', public_url)
            time.sleep(0.3)
    logger.error('Не удалось скачать файл Яндекс Диска: %s', public_url)
    return False


def download_single_mod_turbo_sync(mod_info, minecraft_dir, source="yandex", minecraft_version=None, loader=None):
    """
    Синхронная загрузка одного мода
    source: "yandex", "modrinth", "curseforge", "shader", "local"
    """
    logger.info(f"🚀 download_single_mod_turbo_sync: {mod_info.get('name', 'unknown')}")
    try:
        # Определяем имя файла - пробуем разные ключи
        filename = mod_info.get('file') or mod_info.get('filename') or mod_info.get('file_name')
        if not filename:
            # Если нет имени файла, генерируем из названия
            name = mod_info.get('name', 'mod')
            filename = f"{name}.jar"

        _safe_print(f"🔍 Начинаем загрузку мода: {filename} (источник: {source})")

        mods_dir = os.path.join(minecraft_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        file_path = safe_target(mods_dir, filename)

        # 1. Проверяем локальный кэш
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
            _safe_print(f"✅ Мод уже есть: {filename}")
            if not file_path.lower().endswith(('.jar', '.zip')) or validate_jar_or_zip(file_path):
                return True

        # 2. Пробуем через прокси
        use_proxy = proxy_available()

        if use_proxy and source == "local":
            url = mod_info.get('url') or mod_info.get('download_url') or mod_info.get('direct_link')

            if url:
                _safe_print(f"🌐 Прокси: пробуем {filename}")
                if download_through_proxy(url, file_path, source):
                    _safe_print(f"✅ Загружено через прокси: {filename}")
                    return True
                _safe_print(f"⚠️ Прокси не сработал, пробуем прямой метод")

        # 3. Прямая загрузка в зависимости от источника
        if source == "yandex":
            return _download_from_yandex(mod_info, file_path, mods_dir)
        elif source == "modrinth":
            # Передаём minecraft_version и loader дальше
            return _download_from_modrinth(mod_info, file_path, mods_dir, minecraft_version, loader)
        elif source == "curseforge":
            return _download_from_curseforge(mod_info, file_path, mods_dir)
        elif source == "shader":
            return _download_shader(mod_info, file_path)
        else:
            _safe_print(f"❌ Неизвестный источник: {source}")
            return False

    except Exception as e:
        _safe_print(f"❌ Ошибка загрузки мода: {e}")
        return False


def _download_from_yandex(mod_info, file_path, mods_dir):
    """Прямая загрузка с Яндекс.Диска"""
    try:
        url = mod_info.get('url')
        if not url:
            _safe_print(f"❌ Нет URL для Яндекс.Диска")
            return False

        success = download_yandex_file_sync(url, file_path, 'yandex')
        if success and file_path.lower().endswith(('.jar', '.zip')) and not validate_jar_or_zip(file_path):
            try: os.remove(file_path)
            except OSError: pass
            return False

        if success and file_path.endswith(".zip"):
            try:
                import zipfile
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    root = Path(mods_dir).resolve()
                    for member in zip_ref.infolist():
                        if member.is_dir():
                            continue
                        target = (root / member.filename).resolve()
                        if target.parent != root and root not in target.parents:
                            raise ValueError(f"Небезопасный путь в архиве: {member.filename}")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(member) as source, target.open("wb") as output:
                            import shutil
                            shutil.copyfileobj(source, output)
                _safe_print(f"📦 Распакован: {os.path.basename(file_path)}")
            except Exception as e:
                _safe_print(f"⚠️ Ошибка распаковки: {e}")

        return success

    except Exception as e:
        _safe_print(f"❌ Ошибка прямой загрузки Яндекс: {e}")
        return False


def _download_from_modrinth(mod_info, file_path, mods_dir, minecraft_version=None, loader=None):
    """Загрузка с Modrinth"""
    _safe_print(f"🔄 Загрузка Modrinth")
    try:
        # Modrinth modpacks provide a pinned direct URL for every file.  Keep
        # it when present instead of inferring a project/version pair that the
        # pack manifest does not contain.
        direct_url = (mod_info.get('url') or mod_info.get('download_url') or
                      mod_info.get('direct_link'))
        if direct_url:
            if not _is_trusted_modpack_url(direct_url, 'modrinth'):
                _safe_print('❌ Небезопасный прямой URL Modrinth')
                return False
            return bool(download_file_sync(direct_url, file_path,
                                           url_validator=lambda url: _is_trusted_modpack_url(url, 'modrinth')))

        from Network.ModrinthLoader import ModrinthAPI

        api = ModrinthAPI()
        mod_id = mod_info.get('modrinth_id') or mod_info.get('project_id')

        if not mod_id:
            _safe_print(f"❌ Нет ID мода для Modrinth")
            return False

        filename = mod_info.get('file') or mod_info.get('filename') or f"{mod_id}.jar"

        # Если minecraft_version и loader не переданы, берём из mod_info
        mc_version = minecraft_version or mod_info.get('minecraft_version', '1.20.1')
        loader_type = loader or mod_info.get('loader', 'fabric')

        _safe_print(f"🔄 Загрузка Modrinth: {mod_id} для {mc_version}/{loader_type}")

        # Передаём minecraft_version и loader в download_mod
        success = api.download_mod(
            project_slug=mod_id,
            version_id=mod_info.get('version_id'),  # может быть None
            filename=filename,
            mods_dir=mods_dir,
            minecraft_version=mc_version,
            loader=loader_type
        )

        if success:
            _safe_print(f"✅ Загрузка Modrinth успешна: {filename}")
            return True

        if mod_info.get("version_id"):
            return False
        # Пробуем альтернативный метод
        _safe_print(f"🔄 Пробуем альтернативную загрузку...")
        cdn_url = f"https://cdn.modrinth.com/data/{mod_id}/versions/latest/{filename}"
        return download_file_sync(cdn_url, file_path)

    except Exception as e:
        _safe_print(f"❌ Ошибка прямой загрузки Modrinth: {e}")
        return False


def _download_from_curseforge(mod_info, file_path, mods_dir):
    """Загрузка с CurseForge"""
    try:
        direct_url = (mod_info.get('url') or mod_info.get('download_url') or
                      mod_info.get('direct_link'))
        if direct_url:
            if not _is_trusted_modpack_url(direct_url, 'curseforge'):
                _safe_print('❌ Небезопасный прямой URL CurseForge')
                return False
            return bool(download_file_sync(direct_url, file_path,
                                           url_validator=lambda url: _is_trusted_modpack_url(url, 'curseforge')))

        from Network.CurseForgeLoader import CurseForgeAPI
        from ConfDir.Configs import CURSEFORGE_CONFIG

        proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://90.151.59.120:8000")
        api = CurseForgeAPI(proxy_url)

        mod_id = mod_info.get('curseforge_id') or mod_info.get('project_id')
        if not mod_id:
            _safe_print(f"❌ Нет ID мода для CurseForge")
            return False

        filename = mod_info.get('file') or mod_info.get('filename') or f"mod-{mod_id}.jar"
        minecraft_version = mod_info.get('minecraft_version', '1.20.1')
        loader = mod_info.get('loader', 'fabric')

        _safe_print(f"🔄 Загрузка CurseForge: {mod_id} для {minecraft_version}/{loader}")

        pinned = mod_info.get('version_id') or mod_info.get('file_id')
        if pinned:
            # The stored ID and filename are enough to use CurseForge's public CDN.
            version_id = pinned
        else:
            versions = api.get_mod_versions(str(mod_id), minecraft_version, loader)
            if not versions:
                return False
            version_id = versions[0]['id']

        # Скачиваем через метод CurseForgeAPI
        success = api.download_mod(str(mod_id), version_id, filename, mods_dir)

        if success:
            _safe_print(f"✅ Загрузка CurseForge успешна: {filename}")
            return True

        return False

    except Exception as e:
        _safe_print(f"❌ Ошибка прямой загрузки CurseForge: {e}")
        return False


def _download_shader(mod_info, file_path):
    url = mod_info.get('url')
    return bool(url and download_yandex_file_sync(url, file_path, 'shader'))


def download_single_mod_turbo(mod_info, minecraft_dir):
    """Compatibility entry point using the same route as the UI downloader."""
    return download_single_mod_turbo_sync(mod_info, minecraft_dir, source=mod_info.get('source', 'yandex'),
                                          minecraft_version=mod_info.get('minecraft_version'),
                                          loader=mod_info.get('loader'))


def download_mods_turbo_ui(mods_list, parent=None):
    if mods_list:
        from Ui.DownloadDialog import DownloadProgressDialog
        DownloadProgressDialog(parent, mods_list).exec()


def download_shaders_turbo_ui(shaders_list, parent=None):
    if shaders_list:
        from Ui.DownloadDialog import DownloadProgressDialog
        DownloadProgressDialog(parent, shaders_list, kind='shaders').exec()


def download_through_proxy(url: str, filepath: str, source: str = "unknown", progress_callback=None) -> bool:
    """
    Универсальная загрузка файла через прокси-сервер
    source: "yandex", "curseforge", "modrinth", "shader", "unknown"
    """
    if not proxy_available():
        return False
    try:
        proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://90.151.59.120:8000")
        proxy_endpoint = f"{proxy_url}/api/v1/mirror/download"

        payload = {
            "url": url,
            "filename": os.path.basename(filepath),
            "source": source,
            "file_type": "shader" if source == "shader" else "mod"
        }

        _safe_print(f"🌐 Прокси: загрузка {os.path.basename(filepath)} через {source}")

        response = requests.post(
            proxy_endpoint,
            json=payload,
            timeout=60,
            stream=True,
            headers={"Content-Type": "application/json", **generate_auth_header()},
            allow_redirects=False,
        )

        if response.status_code == 200:
            return save_response(response, filepath, progress_callback)

        response.close()
        if response.status_code >= 500:
            mark_proxy_unavailable()
        return False

    except ProxyAuthError:
        raise
    except requests.RequestException as exc:
        mark_proxy_unavailable()
        logger.debug('Proxy unavailable: %s', exc)
        return False
    except (ValueError, zipfile.BadZipFile) as e:
        mark_proxy_unavailable()
        _safe_print(f"❌ Прокси: ошибка - {e}")
        return False
    except Exception as e:
        _safe_print(f"❌ Прокси: ошибка - {e}")
        return False


def __getattr__(name):
    if name == 'ModDownloadWorker':
        from Ui.DownloadDialog import ModDownloadWorker
        return ModDownloadWorker
    raise AttributeError(name)
