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

    # Единый API ключ для доступа к прокси
    API_KEY = "F9bK7pL2sR5wX8zQ3vN6yT1mC4eB7gH0jU"

    def __init__(self, proxy_url: str = "http://localhost:8000"):
        self.proxy_url = proxy_url.rstrip('/')
        self.session = requests.Session()
        self.base_url = "https://api.modrinth.com/v2"
        self.session.headers.update({
            "User-Agent": "YamalPixel-Launcher/1.0 (moonmen@example.com)",
            'X-API-Key': self.API_KEY  # Добавляем ключ для запросов к прокси
        })

        self.direct_timeout = 15
        self.proxy_timeout = 30

        # Поддерживаемые версии и загрузчики
        self.supported_versions = {
            "fabric": [
                "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
                "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
                "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ],
            "neoforge": [
                "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.6",
                "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ],
            "forge": [
                "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
                "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
                "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ],
            "quilt": [
                "1.18.2", "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
                "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ]
        }

        logger.info(f"Инициализирован Modrinth API с прокси: {self.proxy_url}")

    def _make_proxy_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Универсальный метод для запросов к прокси"""
        url = f"{self.proxy_url}{endpoint}"

        try:
            # Убеждаемся, что ключ есть в заголовках
            headers = kwargs.get('headers', {})
            headers['X-API-Key'] = self.API_KEY
            kwargs['headers'] = headers

            response = self.session.request(method, url, timeout=30, **kwargs)

            # Логируем статусы авторизации
            if response.status_code == 401:
                logger.error("❌ Ошибка авторизации: неверный или отсутствующий API ключ")
                return None
            elif response.status_code == 403:
                logger.error("❌ Доступ запрещен: неверный API ключ")
                return None
            elif response.status_code == 200:
                return response
            else:
                logger.error(f"❌ Ошибка {response.status_code} для {endpoint}")
                return None

        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Не удалось подключиться к прокси: {self.proxy_url}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к {endpoint}: {e}")
            return None

    def get_supported_loaders(self, minecraft_version: str) -> List[str]:
        """Получить доступные загрузчики для версии Minecraft"""
        available_loaders = []
        for loader, versions in self.supported_versions.items():
            if minecraft_version in versions:
                available_loaders.append(loader)
        return available_loaders

    def search_mods(self, query: str, limit: int = 30) -> Optional[Dict]:
        """Поиск модов на Modrinth"""
        try:
            url = f"{self.base_url}/search"
            params = {"query": query, "limit": limit, "index": "relevance"}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка поиска модов: {e}")
            return None

    def get_mod_versions(self, mod_id: str, minecraft_version: str, loader: str) -> Optional[List[Dict]]:
        """Получить версии мода для конкретной версии Minecraft и загрузчика"""
        try:
            url = f"{self.base_url}/project/{mod_id}/version"
            # Передаём как JSON-строки
            params = {
                "game_versions": f'["{minecraft_version}"]',
                "loaders": f'["{loader}"]',
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            versions = response.json()

            # Фильтруем версии, у которых есть JAR-файл
            return [
                v for v in versions
                if v.get("files") and any(f["filename"].endswith(".jar") for f in v["files"])
            ]

        except Exception as e:
            logger.error(f"Ошибка получения версий мода {mod_id}: {e}")
            return None

    def download_mod(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        """
        Скачивание мода с приоритетом прямого источника

        Стратегия:
        1. Пытаемся скачать напрямую с Modrinth CDN
        2. При успехе - уведомляем прокси о файле (фоновое кеширование)
        3. При неудаче - пробуем альтернативный метод
        4. Если всё неудачно - пробуем через прокси (fallback)
        """
        logger.info(f"📥 Начинаем скачивание мода Modrinth: {filename}")

        # 1. ПРЯМОЙ ИСТОЧНИК (Primary): Пробуем скачать с Modrinth CDN напрямую
        direct_url = self._build_direct_cdn_url(project_slug, version_id, filename)

        if self._download_direct(direct_url, filename, mods_dir):
            logger.info(f"✅ Файл {filename} скачан напрямю с Modrinth CDN")

            # 2. ФОНОВАЯ СИНХРОНИЗАЦИЯ: Уведомляем прокси о файле
            self._notify_proxy_to_cache(project_slug, version_id, filename, direct_url)
            return True

        # 3. АЛЬТЕРНАТИВНЫЙ МЕТОД: Пробуем через API информации о версии
        logger.warning("⚠️ Прямой CDN недоступен, пробуем альтернативный метод...")
        if self.download_mod_alternative(project_slug, version_id, filename, mods_dir):
            logger.info(f"✅ Файл {filename} скачан альтернативным методом")
            return True

        # 4. ПРОКСИ (Fallback): Если оба метода Modrinth недоступны
        logger.warning("⚠️ Оба метода Modrinth недоступны, пробуем через прокси...")
        return self._download_via_proxy(project_slug, version_id, filename, mods_dir)

    def _build_direct_cdn_url(self, project_slug: str, version_id: str, filename: str) -> str:
        """Формирование прямой ссылки на Modrinth CDN"""
        # Экранируем имя файла — особенно важно для +, пробелов, % и т.д.
        encoded_filename = urllib.parse.quote(filename)

        # Основной CDN URL для Modrinth
        return f"https://cdn.modrinth.com/data/{project_slug}/versions/{version_id}/{encoded_filename}"

    def _download_direct(self, url: str, filename: str, mods_dir: str) -> bool:
        """Прямое скачивание с Modrinth CDN без использования прокси"""
        try:
            logger.debug(f"🔄 Пробуем прямое скачивание Modrinth: {url}")

            # Используем отдельную сессию для прямого скачивания
            direct_session = requests.Session()
            direct_session.headers.update({
                'User-Agent': 'YamalPixel-Launcher/1.0',
            })

            response = direct_session.get(url, stream=True, timeout=self.direct_timeout)
            response.raise_for_status()

            os.makedirs(mods_dir, exist_ok=True)
            filepath = os.path.join(mods_dir, filename)

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            # Проверяем целостность файла
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                logger.debug(f"✅ Прямое скачивание Modrinth успешно: {filename} ({os.path.getsize(filepath)} байт)")
                return True
            else:
                logger.warning(f"❌ Файл Modrinth скачался с ошибкой (маленький размер): {filename}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return False

        except requests.exceptions.Timeout:
            logger.debug(f"⏰ Таймаут прямого скачивания Modrinth: {filename}")
            return False
        except requests.exceptions.ConnectionError:
            logger.debug(f"🔌 Ошибка подключения к Modrinth CDN: {filename}")
            return False
        except Exception as e:
            logger.debug(f"⚠️ Ошибка прямого скачивания Modrinth {filename}: {e}")
            return False

    def download_mod_alternative(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        """Альтернативный метод скачивания через получение информации о версии"""
        try:
            logger.debug(f"🔄 Пробуем альтернативный метод для: {filename}")

            # Получаем информацию о версии с Modrinth API
            version_url = f"{self.base_url}/version/{version_id}"
            response = self.session.get(version_url, timeout=30)
            response.raise_for_status()
            version_data = response.json()

            logger.debug(f"🔍 Ищем файл в информации о версии: {filename}")

            if "files" in version_data and version_data["files"]:
                # Ищем нужный файл по имени
                target_file = None
                for file_info in version_data["files"]:
                    if file_info["filename"] == filename:
                        target_file = file_info
                        break

                if target_file and "url" in target_file:
                    download_url = target_file["url"]
                    logger.debug(f"📥 Альтернативное скачивание: {download_url}")

                    # Скачиваем через альтернативный URL
                    response = self.session.get(download_url, stream=True, timeout=30)
                    response.raise_for_status()

                    os.makedirs(mods_dir, exist_ok=True)
                    filepath = os.path.join(mods_dir, filename)

                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    # Проверяем целостность
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                        logger.debug(f"✅ Альтернативный метод успешен: {filename}")
                        return True

            logger.debug(f"❌ Файл {filename} не найден в информации о версии")
            return False

        except Exception as e:
            logger.debug(f"❌ Альтернативный метод скачивания также не удался: {e}")
            return False

    def _notify_proxy_to_cache(self, mod_id: str, file_id: str, filename: str, source_url: str):
        """Уведомление прокси о необходимости кэширования файла (асинхронно)"""

        def _send_notification():
            try:
                cache_url = f"{self.proxy_url}/api/v1/cache/request"

                # Для Modrinth используем project_slug и version_id
                payload = {
                    "project_slug": mod_id,  # project_slug
                    "version_id": file_id,  # version_id
                    "filename": filename,
                    "source_url": source_url,
                    "source": "modrinth",
                    "timestamp": datetime.now().isoformat()
                }

                # Отправляем запрос с API ключом
                headers = {'X-API-Key': self.API_KEY}
                response = requests.post(cache_url, json=payload, headers=headers, timeout=5)

                if response.status_code == 200:
                    logger.debug(f"📤 Прокси уведомлен о Modrinth файле {filename}")
                elif response.status_code in [401, 403]:
                    logger.debug(f"🔒 Прокси отклонил уведомление: неверный ключ")
                else:
                    logger.debug(f"⚠️ Прокси не ответил на уведомление: {response.status_code}")

            except Exception as e:
                # Молча игнорируем ошибки уведомления - это не критично
                logger.debug(f"📴 Ошибка уведомления прокси: {e}")

        # Запускаем в отдельном потоке, чтобы не блокировать пользователя
        threading.Thread(target=_send_notification, daemon=True).start()

    def _download_via_proxy(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        """Резервное скачивание Modrinth мода через прокси"""
        try:
            logger.info(f"🔄 Пробуем скачать Modrinth мод через прокси: {filename}")

            # Используем универсальный эндпоинт кэша прокси
            proxy_url = f"{self.proxy_url}/api/v1/cache/file/{project_slug}/{version_id}"

            # Используем сессию с API ключом
            response = self.session.get(proxy_url, stream=True, timeout=60)

            if response.status_code == 200:
                os.makedirs(mods_dir, exist_ok=True)
                filepath = os.path.join(mods_dir, filename)

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Проверяем целостность
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    logger.info(f"✅ Успешно скачан через прокси: {filename}")
                    return True
                else:
                    logger.error(f"❌ Файл с прокси скачался с ошибкой: {filename}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return False
            else:
                logger.error(f"❌ Прокси Modrinth вернул ошибку: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка скачивания Modrinth мода с прокси: {e}")
            return False

    def get_project_info(self, project_slug: str) -> Optional[Dict]:
        """Получить информацию о проекте по slug"""
        try:
            url = f"{self.base_url}/project/{project_slug}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения информации о проекте {project_slug}: {e}")
            return None

    def get_project(self, project_id_or_slug: str) -> Optional[Dict]:
        """Получает информацию о проекте"""
        try:
            response = self.session.get(
                f"{self.base_url}/project/{project_id_or_slug}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения проекта {project_id_or_slug}: {e}")
            return None

    def get_version(self, version_id: str) -> Optional[Dict]:
        """Получает информацию о конкретной версии"""
        try:
            response = self.session.get(
                f"{self.base_url}/version/{version_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения версии {version_id}: {e}")
            return None

    def test_auth(self) -> Optional[Dict]:
        """Тестирование авторизации с прокси"""
        try:
            response = self._make_proxy_request('GET', '/api/v1/auth/test')
            if response:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Ошибка теста авторизации: {e}")
            return None

    def test_connection(self) -> bool:
        """Проверка соединения с прокси"""
        try:
            response = self._make_proxy_request('GET', '/api/v1/health')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка проверки соединения: {e}")
            return False