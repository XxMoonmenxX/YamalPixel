import requests
import json
import os
import threading
import urllib.parse
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CurseForgeAPI:
    """Клиент для работы с CurseForge с приоритетом прямых скачиваний"""

    # Единый API ключ для доступа к прокси
    API_KEY = "F9bK7pL2sR5wX8zQ3vN6yT1mC4eB7gH0jU"

    def __init__(self, proxy_url: str = "http://90.151.59.120:8000"):
        self.proxy_url = proxy_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YamalPixelLauncher/1.0',
            'Accept': 'application/json',
            'X-API-Key': self.API_KEY  # Добавляем ключ по умолчанию
        })
        self.timeout = 30  # увеличиваем с 10 до 30
        self.direct_timeout = 30
        self.proxy_timeout = 60  # увеличиваем с 30 до 60

        logger.info(f"Инициализирован CurseForge API с прокси: {self.proxy_url}")

    def _make_proxy_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Универсальный метод для запросов к прокси с проверкой авторизации"""
        url = f"{self.proxy_url}{endpoint}"

        try:
            # Убеждаемся, что ключ есть в заголовках
            headers = kwargs.get('headers', {})
            headers['X-API-Key'] = self.API_KEY
            kwargs['headers'] = headers

            response = self.session.request(method, url, timeout=self.timeout, **kwargs)

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

    def test_connection(self) -> bool:
        """Проверка соединения с прокси-сервером"""
        try:
            # Проверяем доступность прокси-сервера
            health_response = self._make_proxy_request('GET', '/api/v1/health')

            if not health_response or health_response.status_code != 200:
                logger.error(f"Прокси-сервер недоступен (health)")
                return False

            # Проверяем CurseForge API через прокси
            ping_response = self._make_proxy_request('GET', '/api/v1/curseforge/ping')

            if ping_response and ping_response.status_code == 200:
                data = ping_response.json()
                success = data.get("success", False)

                if success:
                    logger.info("✅ CurseForge прокси доступен")
                else:
                    error_msg = data.get("error", "Неизвестная ошибка")
                    logger.warning(f"⚠️ CurseForge API проблема: {error_msg}")

                return success
            else:
                logger.error(f"Ошибка ping")
                return False

        except requests.exceptions.Timeout:
            logger.error("Таймаут при проверке прокси-сервера")
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

        except requests.exceptions.Timeout:
            logger.error("Таймаут при поиске модов")
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return None

    def get_mod_versions(self, mod_id: str, minecraft_version: str, loader: str) -> Optional[List[Dict]]:
        """Получение версий мода с зависимостями"""
        try:
            response = self._make_proxy_request(
                'GET',
                f'/api/v1/curseforge/mod/{mod_id}/versions',
                params={
                    'minecraft_version': minecraft_version,
                    'loader': loader.lower(),
                    'include_dependencies': 'true'  # <-- добавить этот параметр
                }
            )

            if response:
                data = response.json()
                if data.get("success"):
                    return data.get("data", [])
            return None

        except Exception as e:
            logger.error(f"Ошибка получения версий: {e}")
            return None

    def get_mod_info(self, mod_id: str) -> Optional[Dict]:
        """Получает информацию о моде по ID"""
        try:
            response = self._make_proxy_request(
                'GET',
                f'/api/v1/curseforge/mod/{mod_id}'
            )

            if response:
                data = response.json()
                if data.get("success"):
                    return data.get("data", {})

            logger.warning(f"Не удалось получить информацию о моде {mod_id}")
            return None

        except Exception as e:
            logger.error(f"Ошибка получения информации о моде {mod_id}: {e}")
            return None

    def download_mod(self, mod_id: str, version_id: str, filename: str, destination_dir: str) -> bool:
        """
        Скачивание мода с приоритетом прямого источника

        Стратегия:
        1. Пытаемся скачать напрямую с CurseForge CDN
        2. При успехе - уведомляем прокси о файле (фоновое кеширование)
        3. При неудаче - скачиваем через прокси как fallback
        """
        logger.info(f"📥 Начинаем скачивание мода: {filename}")

        # 1. ПРЯМОЙ ИСТОЧНИК (Primary): Пробуем скачать с CurseForge CDN напрямую
        direct_url = self._build_direct_cdn_url(version_id, filename)

        if self._download_direct(direct_url, filename, destination_dir):
            logger.info(f"✅ Файл {filename} скачан напрямую с CDN")

            # 2. ФОНОВАЯ СИНХРОНИЗАЦИЯ: Уведомляем прокси о файле (не блокируя пользователя)
            self._notify_proxy_to_cache(mod_id, version_id, filename, direct_url)
            return True

        # 3. ПРОКСИ (Fallback): Если прямой источник недоступен
        logger.warning(f"⚠️ Прямой источник недоступен, пробуем через прокси...")
        return self._download_via_proxy(mod_id, version_id, filename, destination_dir)

    def _build_direct_cdn_url(self, file_id: str, filename: str) -> str:
        """
        Формирование прямой ссылки на CurseForge CDN

        Структура ссылок CurseForge:
        https://edge.forgecdn.net/files/{folder1}/{folder2}/{filename}
        где folder1 = первые 4 символа file_id, folder2 = символы 5-7
        """
        if len(file_id) >= 7:
            folder1 = file_id[:4]
            folder2 = file_id[4:7]
            return f"https://edge.forgecdn.net/files/{folder1}/{folder2}/{filename}"

        # Fallback для коротких ID
        return f"https://media.forgecdn.net/files/{file_id}/{filename}"

    def _download_direct(self, url: str, filename: str, destination_dir: str) -> bool:
        """Прямое скачивание с источника без использования прокси"""
        try:
            logger.debug(f"🔄 Пробуем прямое скачивание: {url}")

            # Используем отдельную сессию без прокси
            direct_session = requests.Session()
            direct_session.headers.update({
                'User-Agent': 'YamalPixelLauncher/1.0',
            })

            response = direct_session.get(url, stream=True, timeout=self.direct_timeout)

            if response.status_code == 200:
                os.makedirs(destination_dir, exist_ok=True)
                filepath = os.path.join(destination_dir, filename)

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                # Проверяем целостность файла
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    logger.debug(f"✅ Прямое скачивание успешно: {filename} ({os.path.getsize(filepath)} байт)")
                    return True
                else:
                    logger.warning(f"❌ Файл скачался с ошибкой (маленький размер): {filename}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return False
            else:
                logger.debug(f"❌ Прямой источник недоступен: HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            logger.debug(f"⏰ Таймаут прямого скачивания: {filename}")
            return False
        except requests.exceptions.ConnectionError:
            logger.debug(f"🔌 Ошибка подключения к прямому источнику: {filename}")
            return False
        except Exception as e:
            logger.debug(f"⚠️ Ошибка прямого скачивания {filename}: {e}")
            return False

    def _notify_proxy_to_cache(self, mod_id: str, file_id: str, filename: str, source_url: str):
        """Уведомление прокси о необходимости кэширования файла (асинхронно)"""

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

                # Отправляем запрос с API ключом
                headers = {'X-API-Key': self.API_KEY}
                response = requests.post(cache_url, json=payload, headers=headers, timeout=5)

                if response.status_code == 200:
                    logger.debug(f"📤 Прокси уведомлен о файле {filename}")
                elif response.status_code in [401, 403]:
                    logger.debug(f"🔒 Прокси отклонил уведомление: неверный ключ")
                else:
                    logger.debug(f"⚠️ Прокси не ответил на уведомление: {response.status_code}")

            except Exception as e:
                # Молча игнорируем ошибки уведомления - это не критично
                logger.debug(f"📴 Ошибка уведомления прокси: {e}")

        # Запускаем в отдельном потоке, чтобы не блокировать пользователя
        threading.Thread(target=_send_notification, daemon=True).start()

    def _download_via_proxy(self, mod_id: str, version_id: str, filename: str, destination_dir: str) -> bool:
        """Резервное скачивание через прокси"""
        try:
            logger.info(f"🔄 Пробуем скачать через прокси: {filename}")

            # Получаем информацию о файле с прокси
            response = self._make_proxy_request(
                'GET',
                f'/api/v1/curseforge/download/{version_id}',
                params={
                    'filename': filename,
                    'mod_id': mod_id
                }
            )

            if not response:
                return False

            data = response.json()
            if not data.get("success"):
                logger.error(f"❌ Ошибка в ответе прокси: {data.get('error')}")
                return False

            download_url = data.get("download_url")
            if not download_url:
                logger.error("❌ Нет ссылки для скачивания с прокси")
                return False

            # Скачиваем файл с прокси
            os.makedirs(destination_dir, exist_ok=True)
            file_response = self.session.get(download_url, stream=True, timeout=60)
            file_response.raise_for_status()

            destination_path = os.path.join(destination_dir, filename)

            # Скачиваем файл
            total_size = int(file_response.headers.get('content-length', 0))
            downloaded = 0

            with open(destination_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            # Проверяем что файл скачался
            if os.path.exists(destination_path) and os.path.getsize(destination_path) > 1000:
                logger.info(f"✅ Успешно скачан через прокси: {filename}")
                return True
            else:
                logger.error(f"❌ Файл с прокси скачался с ошибкой: {filename}")
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                return False

        except requests.exceptions.Timeout:
            logger.error(f"⏰ Таймаут при скачивании с прокси: {filename}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Не удалось подключиться к прокси для скачивания: {filename}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания с прокси: {e}")
            return False

    def get_supported_loaders(self, minecraft_version: str) -> List[str]:
        """Получение списка поддерживаемых загрузчиков"""
        # Для CurseForge всегда доступны основные загрузчики
        return ["fabric", "forge", "quilt", "neoforge"]

    def get_mod_info(self, mod_id: str) -> Optional[Dict]:
        """Упрощенное получение информации о моде"""
        try:
            # Используем поиск для получения информации о моде
            response = self._make_proxy_request('GET', f'/api/v1/curseforge/mod/{mod_id}')

            if response:
                data = response.json()
                if data.get("success"):
                    return data.get("data", {})

            # Если не сработало, пробуем через поиск
            logger.warning(f"Не удалось получить информацию о моде {mod_id}, используем заглушку")

            # Заглушка с базовой информацией
            return {
                "id": mod_id,
                "name": f"Mod {mod_id}",
                "slug": mod_id,
                "dependencies": []  # Прокси не предоставляет зависимости
            }

        except Exception as e:
            logger.error(f"Ошибка получения информации о моде: {e}")
            return None

    def download_mod_with_fallback(self, mod_id: str, version_id: str, filename: str, destination_dir: str) -> bool:
        """
        Скачивание мода с приоритетом прямого источника и резервным прокси

        Стратегия:
        1. Пытаемся скачать напрямую с официального источника
        2. При успехе - уведомляем прокси о файле (фоновое кеширование)
        3. При неудаче - пытаемся скачать через прокси-кэш
        """
        logger.info(f"📥 Начинаем скачивание мода: {filename}")

        # Определяем тип источника по параметрам
        source_type = "curseforge"  # по умолчанию

        # 1. ПРЯМОЙ ИСТОЧНИК: Пробуем скачать напрямую
        direct_url = self._build_direct_url(mod_id, version_id, filename)

        if self._download_direct(direct_url, filename, destination_dir):
            logger.info(f"✅ Файл {filename} скачан напрямую")

            # 2. ФОНОВАЯ СИНХРОНИЗАЦИЯ: Уведомляем прокси о файле
            self._notify_proxy_to_cache(mod_id, version_id, filename, direct_url, source_type)
            return True

        # 3. ПРОКСИ КЭШ (Fallback): Если прямой источник недоступен
        logger.warning(f"⚠️ Прямой источник недоступен, пробуем через прокси-кэш...")
        return self._download_from_proxy_cache(mod_id, version_id, filename, destination_dir)

    def _build_direct_url(self, mod_id: str, version_id: str, filename: str) -> str:
        """
        Формирование прямой ссылки в зависимости от типа мода
        """
        # Здесь нужно определить, какой это источник
        # Можно по переданным параметрам или по контексту
        # Для примера - если mod_id похож на Modrinth ID (короткий)
        if len(mod_id) <= 10 and len(version_id) <= 10:
            # Вероятно Modrinth
            return f"https://cdn.modrinth.com/data/{mod_id}/versions/{version_id}/{filename}"
        else:
            # Вероятно CurseForge
            if len(version_id) >= 7:
                folder1 = version_id[:4]
                folder2 = version_id[4:7]
                return f"https://edge.forgecdn.net/files/{folder1}/{folder2}/{filename}"
            return f"https://media.forgecdn.net/files/{version_id}/{filename}"

    def _download_from_proxy_cache(self, mod_id: str, version_id: str, filename: str, destination_dir: str) -> bool:
        """
        Скачивание файла из кэша прокси (резервный метод)
        """
        try:
            logger.info(f"🔄 Пробуем скачать из прокси-кэша: {filename}")

            proxy_url = f"{self.proxy_url}/api/v1/cache/file/{mod_id}/{version_id}"

            # Используем сессию с API ключом
            response = self.session.get(proxy_url, stream=True, timeout=30)

            if response.status_code == 200:
                os.makedirs(destination_dir, exist_ok=True)
                filepath = os.path.join(destination_dir, filename)

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Проверяем целостность файла
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ Успешно скачан из прокси-кэша: {filename} ({file_size} байт)")
                    return True
                else:
                    logger.error(f"❌ Файл с прокси скачался с ошибкой: {filename}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return False
            else:
                logger.error(f"❌ Прокси вернул ошибку: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка скачивания из прокси-кэша: {e}")
            return False

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