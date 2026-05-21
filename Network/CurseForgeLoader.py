## Network/CurseForgeLoader.py
import requests
import json
import os
import threading
import urllib.parse
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class CurseForgeAPI:
    """Клиент для работы с CurseForge с улучшенным поиском по ID"""

    # Единый API ключ для доступа к прокси
    API_KEY = "F9bK7pL2sR5wX8zQ3vN6yT1mC4eB7gH0jU"

    def __init__(self, proxy_url: str = "http://90.151.59.120:8000"):
        self.proxy_url = proxy_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YamalPixelLauncher/1.0',
            'Accept': 'application/json',
            'X-API-Key': self.API_KEY
        })
        self.timeout = 30
        self.direct_timeout = 30
        self.proxy_timeout = 60

        # Кэш для информации о модах
        self.mod_info_cache = {}

        logger.info(f"Инициализирован CurseForge API с прокси: {self.proxy_url}")

    def _make_proxy_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Универсальный метод для запросов к прокси"""
        url = f"{self.proxy_url}{endpoint}"

        try:
            headers = kwargs.get('headers', {})
            headers['X-API-Key'] = self.API_KEY
            kwargs['headers'] = headers

            response = self.session.request(method, url, timeout=self.timeout, **kwargs)

            if response.status_code == 200:
                return response
            else:
                logger.debug(f"Прокси вернул {response.status_code} для {endpoint}")
                return None

        except requests.exceptions.ConnectionError:
            logger.debug(f"🔌 Не удалось подключиться к прокси: {self.proxy_url}")
            return None
        except Exception as e:
            logger.debug(f"❌ Ошибка запроса к {endpoint}: {e}")
            return None

    def test_connection(self) -> bool:
        """Проверка соединения с прокси-сервером"""
        try:
            health_response = self._make_proxy_request('GET', '/api/v1/health')
            if not health_response:
                return False

            ping_response = self._make_proxy_request('GET', '/api/v1/curseforge/ping')
            if ping_response and ping_response.status_code == 200:
                data = ping_response.json()
                return data.get("success", False)
            return False

        except Exception as e:
            logger.error(f"Ошибка проверки соединения: {e}")
            return False

    def search_mods(self, query: str, minecraft_version: str, loader: str, limit: int = 30) -> Optional[Dict]:
        """Поиск модов на CurseForge"""
        try:
            response = self._make_proxy_request(
                'GET',
                '/api/v1/curseforge/search',
                params={
                    'query': query,
                    'minecraft_version': minecraft_version,
                    'loader': loader.lower(),
                    'limit': limit
                }
            )

            if response:
                return response.json()
            return None

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return None

    def get_mod_info(self, mod_id: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Получение информации о моде с улучшенной обработкой ошибок.
        Использует кэш, пробует альтернативные методы если прокси не работает.
        """
        # Проверяем кэш
        if not force_refresh and mod_id in self.mod_info_cache:
            return self.mod_info_cache[mod_id]

        # 1. Пробуем через прокси
        response = self._make_proxy_request('GET', f'/api/v1/curseforge/mod/{mod_id}')
        if response:
            try:
                data = response.json()
                if data.get("success") and data.get("data"):
                    self.mod_info_cache[mod_id] = data["data"]
                    logger.info(f"✅ Получена информация о моде {mod_id} через прокси")
                    return data["data"]
            except:
                pass

        # 2. Пробуем получить через поиск (если прокси не вернул)
        logger.info(f"🔄 Пробуем найти мод {mod_id} через поиск...")
        search_result = self._get_mod_by_search(mod_id)
        if search_result:
            self.mod_info_cache[mod_id] = search_result
            return search_result

        # 3. Создаём базовую заглушку с минимальной информацией
        logger.warning(f"⚠️ Используем заглушку для мода {mod_id}")
        fallback_info = self._create_fallback_mod_info(mod_id)
        self.mod_info_cache[mod_id] = fallback_info
        return fallback_info

    def _get_mod_by_search(self, query: str) -> Optional[Dict]:
        """Пытается найти мод через поиск по имени или ID"""
        try:
            # Если query - это число, пробуем искать по ID
            if query.isdigit():
                # Делаем поиск по пустому запросу и фильтруем? Не работает.
                # Лучше пробуем прямой запрос к старому API
                old_api_url = f"https://www.curseforge.com/api/v1/mods/{query}"
                try:
                    response = self.session.get(old_api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('id'):
                            return {
                                'id': data['id'],
                                'name': data.get('name', f'Mod {query}'),
                                'slug': data.get('slug', str(query)),
                                'summary': data.get('summary', ''),
                                'downloads': data.get('downloadCount', 0),
                                'date_created': data.get('dateCreated'),
                                'date_modified': data.get('dateModified'),
                            }
                except:
                    pass

            # Пробуем поиск по имени
            search_response = self._make_proxy_request(
                'GET', '/api/v1/curseforge/search',
                params={'query': query, 'limit': 5}
            )
            if search_response:
                data = search_response.json()
                if data.get("success") and data.get("data"):
                    # Берём первый результат
                    first_result = data["data"][0]
                    logger.info(f"🔍 Найден мод через поиск: {first_result.get('title')}")
                    return {
                        'id': first_result.get('project_id'),
                        'name': first_result.get('title'),
                        'slug': first_result.get('slug'),
                        'summary': first_result.get('summary', ''),
                        'downloads': first_result.get('downloads', 0),
                    }

            return None

        except Exception as e:
            logger.debug(f"Ошибка поиска мода {query}: {e}")
            return None

    def _create_fallback_mod_info(self, mod_id: str) -> Dict:
        """Создаёт базовую информацию о моде для fallback"""
        return {
            'id': mod_id,
            'name': f'Mod {mod_id}',
            'slug': str(mod_id),
            'summary': f'CurseForge mod with ID {mod_id}',
            'downloads': 0,
            'is_fallback': True
        }

    def get_mod_versions(self, mod_id: str, minecraft_version: str, loader: str) -> Optional[List[Dict]]:
        """Получение версий мода с зависимостями"""
        try:
            # Убеждаемся, что запрашиваем зависимости
            response = self._make_proxy_request(
                'GET',
                f'/api/v1/curseforge/mod/{mod_id}/versions',
                params={
                    'minecraft_version': minecraft_version,
                    'loader': loader.lower(),
                    'include_dependencies': 'true'  # ← ЭТОТ ПАРАМЕТР КЛЮЧЕВОЙ!
                }
            )

            if response:
                data = response.json()
                if data.get("success"):
                    versions = data.get("data", [])

                    # Логируем найденные зависимости для отладки
                    for v in versions[:1]:  # Только последнюю версию
                        deps = v.get('dependencies', [])
                        if deps:
                            logger.info(f"📦 Найдено {len(deps)} зависимостей для версии {v.get('id')}")
                            for dep in deps:
                                logger.debug(f"  → {dep}")

                    return versions
            return None

        except Exception as e:
            logger.error(f"Ошибка получения версий: {e}")
            return None

    def _get_versions_alternative(self, mod_id: str, minecraft_version: str, loader: str) -> List[Dict]:
        """Альтернативный метод получения версий через прямой парсинг"""
        try:
            # Пробуем получить страницу мода на CurseForge
            url = f"https://www.curseforge.com/minecraft/mc-mods/{mod_id}/files"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            }
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                # Ищем ссылки на файлы в HTML
                # Простой парсинг: ищем паттерны file-{id}
                file_pattern = r'/files/(\d+)/download'
                file_ids = re.findall(file_pattern, response.text)

                versions = []
                for file_id in file_ids[:10]:  # Берем первые 10
                    versions.append({
                        'id': file_id,
                        'name': f'Version {file_id}',
                        'version_number': file_id,
                        'files': [{
                            'filename': f'mod-{mod_id}-{file_id}.jar',
                            'url': f'https://www.curseforge.com/minecraft/mc-mods/{mod_id}/files/{file_id}/download'
                        }],
                        'dependencies': [],
                        'game_versions': [minecraft_version],
                        'loaders': [loader]
                    })

                return versions

        except Exception as e:
            logger.debug(f"Альтернативный метод получения версий не сработал: {e}")

        return []

    def download_mod(self, mod_id: str, version_id: str, filename: str, destination_dir: str) -> bool:
        """Скачивание мода с приоритетом прямого источника"""
        logger.info(f"📥 Начинаем скачивание мода: {filename}")

        # 1. ПРЯМОЙ ИСТОЧНИК: Пробуем скачать с CurseForge CDN напрямую
        direct_url = self._build_direct_cdn_url(version_id, filename)

        if self._download_direct(direct_url, filename, destination_dir):
            logger.info(f"✅ Файл {filename} скачан напрямую с CDN")
            self._notify_proxy_to_cache(mod_id, version_id, filename, direct_url)
            return True

        # 2. ПРОКСИ (Fallback)
        logger.warning(f"⚠️ Прямой источник недоступен, пробуем через прокси...")
        return self._download_via_proxy(mod_id, version_id, filename, destination_dir)

    def _build_direct_cdn_url(self, file_id: str, filename: str) -> str:
        """Формирование прямой ссылки на CurseForge CDN"""
        if len(file_id) >= 7:
            folder1 = file_id[:4]
            folder2 = file_id[4:7]
            return f"https://edge.forgecdn.net/files/{folder1}/{folder2}/{filename}"
        return f"https://media.forgecdn.net/files/{file_id}/{filename}"

    def _download_direct(self, url: str, filename: str, destination_dir: str) -> bool:
        """Прямое скачивание с источника"""
        try:
            direct_session = requests.Session()
            direct_session.headers.update({'User-Agent': 'YamalPixelLauncher/1.0'})

            response = direct_session.get(url, stream=True, timeout=self.direct_timeout)

            if response.status_code == 200:
                os.makedirs(destination_dir, exist_ok=True)
                filepath = os.path.join(destination_dir, filename)

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    return True

                if os.path.exists(filepath):
                    os.remove(filepath)

            return False

        except Exception as e:
            logger.debug(f"Ошибка прямого скачивания: {e}")
            return False

    def _notify_proxy_to_cache(self, mod_id: str, file_id: str, filename: str, source_url: str):
        """Уведомление прокси о необходимости кэширования"""
        def _send_notification():
            try:
                cache_url = f"{self.proxy_url}/api/v1/cache/request"
                payload = {
                    "mod_id": mod_id,
                    "file_id": file_id,
                    "filename": filename,
                    "source_url": source_url,
                    "source": "curseforge",
                    "timestamp": datetime.now().isoformat()
                }
                headers = {'X-API-Key': self.API_KEY}
                requests.post(cache_url, json=payload, headers=headers, timeout=5)
            except:
                pass

        threading.Thread(target=_send_notification, daemon=True).start()

    def _download_via_proxy(self, mod_id: str, version_id: str, filename: str, destination_dir: str) -> bool:
        """Скачивание через прокси"""
        try:
            response = self._make_proxy_request(
                'GET',
                f'/api/v1/curseforge/download/{version_id}',
                params={'filename': filename, 'mod_id': mod_id}
            )

            if not response:
                return False

            data = response.json()
            if not data.get("success"):
                return False

            download_url = data.get("download_url")
            if not download_url:
                return False

            os.makedirs(destination_dir, exist_ok=True)
            file_response = self.session.get(download_url, stream=True, timeout=60)
            file_response.raise_for_status()

            destination_path = os.path.join(destination_dir, filename)
            with open(destination_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return os.path.exists(destination_path) and os.path.getsize(destination_path) > 1000

        except Exception as e:
            logger.error(f"Ошибка скачивания с прокси: {e}")
            return False

    def get_supported_loaders(self, minecraft_version: str) -> List[str]:
        """Получение списка поддерживаемых загрузчиков"""
        return ["fabric", "forge", "quilt", "neoforge"]

    def test_auth(self) -> Optional[Dict]:
        """Тестирование авторизации"""
        try:
            response = self._make_proxy_request('GET', '/api/v1/auth/test')
            if response:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Ошибка теста авторизации: {e}")
            return None