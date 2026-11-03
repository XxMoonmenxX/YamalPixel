## modrinh_api
import requests
from Network.proxy_status import proxy_available, mark_proxy_unavailable
import json
import os
from Core.mod_transaction import safe_target
from Network.file_transfer import save_response
import threading
import urllib.parse
from typing import List, Dict, Optional
import logging
from ConfDir.Configs import CURSEFORGE_CONFIG
from Network.proxy_auth import generate_auth_header, ProxyAuthError
from datetime import datetime

logger = logging.getLogger(__name__)


class ModrinthAPI:
    """API для работы с Modrinth с поддержкой API ключа"""

    def __init__(self, proxy_url: str = None):
        self.proxy_url = (proxy_url or CURSEFORGE_CONFIG.get('proxy_url', '')).rstrip('/')
        self.session = requests.Session()
        self.base_url = "https://api.modrinth.com/v2"
        self.session.headers.update({"User-Agent": "YamalPixel-Launcher/1.0"})

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

    def search_modpacks(self, query: str = "", sort: str = "relevance", limit: int = 50) -> List[Dict]:
        """Search only Modrinth modpacks, including empty-query top lists."""
        if sort not in ("relevance", "downloads", "updated"):
            sort = "relevance"
        try:
            params = {
                "limit": limit,
                "index": sort,
                "facets": json.dumps([["project_type:modpack"]]),
            }
            if query:
                params["query"] = query
            response = self.session.get(
                f"{self.base_url}/search",
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            return response.json().get("hits", [])
        except Exception as e:
            logger.error(f"Ошибка поиска модпаков Modrinth: {e}")
            raise

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
        """Use the shared health result; never substitute a pinned version."""
        pinned = version_id and version_id != 'latest'
        if not pinned:
            if not minecraft_version or not loader:
                return False
            latest = self._get_latest_version_id(project_slug, minecraft_version, loader)
            if not latest:
                return False
            version_id, filename = latest
        if proxy_available(self.proxy_url):
            if self._download_via_proxy(project_slug, version_id, filename, mods_dir):
                return True
        direct_url = self._build_direct_cdn_url(project_slug, version_id, filename)
        if self._download_direct(direct_url, filename, mods_dir):
            self._notify_proxy_to_cache(project_slug, version_id, filename, direct_url)
            return True
        return self.download_mod_alternative(project_slug, version_id, filename, mods_dir)

    def _build_direct_cdn_url(self, project_slug: str, version_id: str, filename: str) -> str:
        encoded_filename = urllib.parse.quote(filename)
        return f"https://cdn.modrinth.com/data/{project_slug}/versions/{version_id}/{encoded_filename}"

    def _download_direct(self, url: str, filename: str, mods_dir: str) -> bool:
        try:
            filepath = safe_target(mods_dir, filename)
            with requests.Session() as direct_session:
                direct_session.headers.update({'User-Agent': 'YamalPixelLauncher'})
                response = direct_session.get(url, stream=True, timeout=self.direct_timeout)
                return save_response(response, filepath)
        except Exception as exc:
            logger.debug('Direct download failed for %s: %s', filename, exc)
            return False

    def download_mod_alternative(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        try:
            response = self.session.get(f'{self.base_url}/version/{version_id}', timeout=30)
            try:
                response.raise_for_status()
                version_data = response.json()
            finally:
                response.close()
            for file_info in version_data.get('files', []):
                if file_info.get('filename') == filename and file_info.get('url'):
                    return self._download_direct(file_info['url'], filename, mods_dir)
            return False
        except Exception as exc:
            logger.debug('Alternative download failed for %s: %s', filename, exc)
            return False

    def _notify_proxy_to_cache(self, mod_id: str, file_id: str, filename: str, source_url: str):
        if not proxy_available(self.proxy_url):
            return
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
                headers = generate_auth_header()
                requests.post(cache_url, json=payload, headers=headers, timeout=5, allow_redirects=False)
            except Exception as exc:
                logger.warning('Не удалось уведомить прокси: %s', exc)

        threading.Thread(target=_send_notification, daemon=True).start()

    def _download_via_proxy(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        if not proxy_available(self.proxy_url):
            return False
        try:
            logger.info(f"🔄 Загрузка через прокси: {filename}")

            proxy_url = f"{self.proxy_url}/api/v1/cache/file/{project_slug}/{version_id}"
            response = self.session.get(proxy_url, stream=True, timeout=60,
                                        headers=generate_auth_header(), allow_redirects=False)

            if response.status_code == 200:
                return save_response(response, safe_target(mods_dir, filename))

            elif response.status_code == 404:
                logger.warning(f"⚠️ Файл {filename} не найден на прокси (404)")
            else:
                if response.status_code >= 500:
                    mark_proxy_unavailable(self.proxy_url)
                logger.debug('Proxy returned %s', response.status_code)

            response.close()
            return False

        except ProxyAuthError:
            raise
        except requests.RequestException as exc:
            mark_proxy_unavailable(self.proxy_url)
            logger.debug('Proxy download failed: %s', exc)
            return False
        except Exception as exc:
            logger.debug('Proxy file could not be saved: %s', exc)
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
            headers = dict(kwargs.get('headers', {}))
            headers.update(generate_auth_header())
            kwargs['headers'] = headers
            kwargs['allow_redirects'] = False
            response = self.session.request(method, url, timeout=30, **kwargs)

            if response.status_code in [401, 403]:
                logger.error(f"❌ Ошибка авторизации: {response.status_code}")
                return None
            elif response.status_code == 200:
                return response
            else:
                logger.error(f"❌ Ошибка {response.status_code} для {endpoint}")
                return None

        except ProxyAuthError:
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к {endpoint}: {e}")
            return None
