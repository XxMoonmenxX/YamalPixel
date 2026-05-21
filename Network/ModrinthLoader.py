# modrinh_api
import requests
import json
import os
import threading
import urllib.parse
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ModrinthAPI:
    """API для работы с Modrinth с поддержкой API ключа"""

    API_KEY = "F9bK7pL2sR5wX8zQ3vN6yT1mC4eB7gH0jU"

    def __init__(self, proxy_url: str = "http://90.151.59.120:8000"):
        self.proxy_url = proxy_url.rstrip('/')
        self.session = requests.Session()
        self.base_url = "https://api.modrinth.com/v2"
        self.session.headers.update({
            "User-Agent": "YamalPixel-Launcher/1.0 (moonmen@example.com)",
            'X-API-Key': self.API_KEY
        })

        self.direct_timeout = 15
        self.proxy_timeout = 30

        # Кэш для version_id
        self._version_cache = {}

        self.supported_versions = {
            "fabric": ["1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2", "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"],
            "neoforge": ["1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"],
            "forge": ["1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2", "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"],
            "quilt": ["1.18.2", "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"]
        }

        logger.info(f"Инициализирован Modrinth API с прокси: {self.proxy_url}")

    def search_mods(self, query: str, limit: int = 50) -> Optional[Dict]:
        """
        Поиск модов на Modrinth
        """
        try:
            # Используем v2 API для поиска
            url = f"{self.base_url}/search"
            params = {
                "query": query,
                "limit": limit,
                "facets": '[]'  # можно добавить фильтры
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка поиска модов: {e}")
            return None

    def _get_latest_version_id(self, project_slug: str, minecraft_version: str, loader: str) -> Optional[tuple]:
        """
        Получает ID последней версии мода для указанной версии Minecraft и загрузчика
        Возвращает (version_id, filename) или None
        """
        cache_key = f"{project_slug}_{minecraft_version}_{loader}"
        if cache_key in self._version_cache:
            return self._version_cache[cache_key]

        try:
            logger.info(f"🔍 Получаем актуальную версию для {project_slug} (MC={minecraft_version}, loader={loader})")

            url = f"{self.base_url}/project/{project_slug}/version"
            params = {
                "game_versions": f'["{minecraft_version}"]',
                "loaders": f'["{loader}"]',
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            versions = response.json()

            for version in versions:
                if version.get("files"):
                    jar_files = [f for f in version["files"] if f["filename"].endswith(".jar")]
                    if jar_files:
                        result = (version["id"], jar_files[0]["filename"])
                        self._version_cache[cache_key] = result
                        logger.info(f"✅ Найдена версия: {version['id']} -> {jar_files[0]['filename']}")
                        return result

            logger.warning(f"❌ Не найдено подходящих версий для {project_slug}")
            return None

        except Exception as e:
            logger.error(f"Ошибка получения версии для {project_slug}: {e}")
            return None

    def download_mod(self, project_slug: str, version_id: str, filename: str, mods_dir: str,
                     minecraft_version: str = None, loader: str = None) -> bool:
        """
        Скачивание мода с автоматическим обновлением версии если указанная не существует
        """
        # Если version_id указан, пробуем скачать с ним
        print("try1")
        if version_id and version_id != "latest":
            logger.info(f"📥 Пробуем скачать {filename} с указанной версией {version_id}")
            direct_url = self._build_direct_cdn_url(project_slug, version_id, filename)

            if self._download_direct(direct_url, filename, mods_dir):
                self._notify_proxy_to_cache(project_slug, version_id, filename, direct_url)
                return True

            logger.warning(f"⚠️ Версия {version_id} не существует, получаем актуальную...")

        # Если версия не указана или указанная не существует, получаем актуальную
        if minecraft_version and loader:
            latest = self._get_latest_version_id(project_slug, minecraft_version, loader)
            if latest:
                new_version_id, new_filename = latest
                logger.info(f"🔄 Используем актуальную версию: {new_version_id} -> {new_filename}")

                direct_url = self._build_direct_cdn_url(project_slug, new_version_id, new_filename)

                if self._download_direct(direct_url, new_filename, mods_dir):
                    self._notify_proxy_to_cache(project_slug, new_version_id, new_filename, direct_url)
                    return True

        # Пробуем через прокси как fallback
        logger.warning("⚠️ Прямой CDN недоступен, пробуем через прокси...")
        return self._download_via_proxy(project_slug, version_id, filename, mods_dir)

    def _build_direct_cdn_url(self, project_slug: str, version_id: str, filename: str) -> str:
        encoded_filename = urllib.parse.quote(filename)
        return f"https://cdn.modrinth.com/data/{project_slug}/versions/{version_id}/{encoded_filename}"

    def _download_direct(self, url: str, filename: str, mods_dir: str) -> bool:
        print('try2')
        try:
            logger.debug(f"🔄 Прямое скачивание: {url}")

            direct_session = requests.Session()
            direct_session.headers.update({'User-Agent': 'YamalPixel-Launcher/1.0'})

            response = direct_session.get(url, stream=True, timeout=self.direct_timeout)
            response.raise_for_status()

            os.makedirs(mods_dir, exist_ok=True)
            filepath = os.path.join(mods_dir, filename)

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                logger.info(f"✅ Скачан: {filename} ({os.path.getsize(filepath)} байт)")
                return True
            else:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return False

        except requests.exceptions.Timeout:
            logger.debug(f"⏰ Таймаут: {filename}")
            return False
        except requests.exceptions.ConnectionError:
            logger.debug(f"🔌 Ошибка подключения: {filename}")
            return False
        except Exception as e:
            logger.debug(f"⚠️ Ошибка: {e}")
            return False

    def download_mod_alternative(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        print ('try3')
        try:
            logger.debug(f"🔄 Альтернативный метод для: {filename}")

            version_url = f"{self.base_url}/version/{version_id}"
            response = self.session.get(version_url, timeout=30)
            response.raise_for_status()
            version_data = response.json()

            if "files" in version_data and version_data["files"]:
                for file_info in version_data["files"]:
                    if file_info["filename"] == filename and "url" in file_info:
                        download_url = file_info["url"]
                        response = self.session.get(download_url, stream=True, timeout=30)
                        response.raise_for_status()

                        os.makedirs(mods_dir, exist_ok=True)
                        filepath = os.path.join(mods_dir, filename)

                        with open(filepath, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                            logger.info(f"✅ Альтернативный метод: {filename}")
                            return True

            return False

        except Exception as e:
            logger.debug(f"❌ Альтернативный метод не удался: {e}")
            return False

    def _notify_proxy_to_cache(self, mod_id: str, file_id: str, filename: str, source_url: str):
        print ('try4')
        def _send_notification():
            try:
                cache_url = f"{self.proxy_url}/api/v1/cache/request"
                payload = {
                    "project_slug": mod_id,
                    "version_id": file_id,
                    "filename": filename,
                    "source_url": source_url,
                    "source": "modrinth",
                    "timestamp": datetime.now().isoformat()
                }
                headers = {'X-API-Key': self.API_KEY}
                requests.post(cache_url, json=payload, headers=headers, timeout=5)
            except:
                pass

        threading.Thread(target=_send_notification, daemon=True).start()

    def _download_via_proxy(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        try:
            logger.info(f"🔄 Загрузка через прокси: {filename}")

            proxy_url = f"{self.proxy_url}/api/v1/cache/file/{project_slug}/{version_id}"
            response = self.session.get(proxy_url, stream=True, timeout=60)

            if response.status_code == 200:
                os.makedirs(mods_dir, exist_ok=True)
                filepath = os.path.join(mods_dir, filename)

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    logger.info(f"✅ Скачан через прокси: {filename}")
                    return True

            elif response.status_code == 404:
                logger.warning(f"⚠️ Файл {filename} не найден на прокси (404)")
            else:
                logger.error(f"❌ Прокси вернул ошибку: {response.status_code}")

            return False

        except Exception as e:
            logger.error(f"❌ Ошибка скачивания через прокси: {e}")
            return False

    def get_mod_versions(self, mod_id: str, minecraft_version: str, loader: str) -> Optional[List[Dict]]:
        try:
            url = f"{self.base_url}/project/{mod_id}/version"
            params = {
                "game_versions": f'["{minecraft_version}"]',
                "loaders": f'["{loader}"]',
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            versions = response.json()
            return [v for v in versions if v.get("files") and any(f["filename"].endswith(".jar") for f in v["files"])]
        except Exception as e:
            logger.error(f"Ошибка получения версий мода {mod_id}: {e}")
            return None

    def get_project_info(self, project_slug: str) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/project/{project_slug}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения информации о проекте {project_slug}: {e}")
            return None

    def get_project(self, project_id_or_slug: str) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.base_url}/project/{project_id_or_slug}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения проекта {project_id_or_slug}: {e}")
            return None

    def get_version(self, version_id: str) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.base_url}/version/{version_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения версии {version_id}: {e}")
            return None

    def test_auth(self) -> Optional[Dict]:
        try:
            response = self._make_proxy_request('GET', '/api/v1/auth/test')
            if response:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Ошибка теста авторизации: {e}")
            return None

    def test_connection(self) -> bool:
        try:
            response = self._make_proxy_request('GET', '/api/v1/health')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка проверки соединения: {e}")
            return False

    def _make_proxy_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        url = f"{self.proxy_url}{endpoint}"
        try:
            headers = kwargs.get('headers', {})
            headers['X-API-Key'] = self.API_KEY
            kwargs['headers'] = headers
            response = self.session.request(method, url, timeout=30, **kwargs)

            if response.status_code in [401, 403]:
                logger.error(f"❌ Ошибка авторизации: {response.status_code}")
                return None
            elif response.status_code == 200:
                return response
            else:
                logger.error(f"❌ Ошибка {response.status_code} для {endpoint}")
                return None

        except Exception as e:
            logger.error(f"❌ Ошибка запроса к {endpoint}: {e}")
            return None