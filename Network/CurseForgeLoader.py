import requests
import json
import os
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CurseForgeAPI:
    """Клиент для работы с CurseForge через прокси-сервер"""

    def __init__(self, proxy_url: str = "http://localhost:8000"):
        self.proxy_url = proxy_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YamalPixelLauncher/1.0',
            'Accept': 'application/json'
        })
        self.timeout = 10
        logger.info(f"Инициализирован CurseForge API с прокси: {self.proxy_url}")

    def test_connection(self) -> bool:
        """Проверка соединения с прокси-сервером"""
        try:
            # Сначала проверяем доступность прокси-сервера
            health_response = self.session.get(
                f"{self.proxy_url}/api/v1/health",
                timeout=3
            )

            if health_response.status_code != 200:
                logger.error(f"Прокси-сервер недоступен (health): {health_response.status_code}")
                return False

            # Затем проверяем CurseForge API (упрощенная версия)
            ping_response = self.session.get(
                f"{self.proxy_url}/api/v1/curseforge/ping",
                timeout=5
            )

            if ping_response.status_code == 200:
                data = ping_response.json()
                success = data.get("success", False)

                if success:
                    logger.info("✅ CurseForge прокси доступен")
                else:
                    error_msg = data.get("error", "Неизвестная ошибка")
                    logger.warning(f"⚠️ CurseForge API проблема: {error_msg}")

                return success
            else:
                logger.error(f"Ошибка ping: {ping_response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            logger.error(f"Не удалось подключиться к прокси: {self.proxy_url}")
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
            response = self.session.get(
                f"{self.proxy_url}/api/v1/curseforge/search",
                params={
                    'query': query,
                    'minecraft_version': minecraft_version,
                    'loader': loader.lower(),
                    'limit': limit
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка поиска: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            logger.error("Таймаут при поиске модов")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка подключения к прокси-серверу")
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return None

    def get_mod_versions(self, mod_id: str, minecraft_version: str, loader: str) -> Optional[List[Dict]]:
        """Получение версий мода"""
        try:
            response = self.session.get(
                f"{self.proxy_url}/api/v1/curseforge/mod/{mod_id}/versions",
                params={
                    'minecraft_version': minecraft_version,
                    'loader': loader.lower()
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("data", [])
            return None

        except Exception as e:
            logger.error(f"Ошибка получения версий: {e}")
            return None

    def download_mod(self, mod_id: str, version_id: str, filename: str, destination_dir: str) -> bool:
        """Скачивание мода через прокси"""
        try:
            # Используем version_id напрямую для скачивания
            response = self.session.get(
                f"{self.proxy_url}/api/v1/curseforge/download/{version_id}",
                params={
                    'filename': filename
                },
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"Ошибка получения ссылки: {response.status_code}")
                return False

            data = response.json()
            if not data.get("success"):
                logger.error(f"Ошибка в ответе: {data.get('error')}")
                return False

            download_url = data.get("download_url")
            if not download_url:
                logger.error("Нет ссылки для скачивания")
                return False

            # Создаем директорию если её нет
            os.makedirs(destination_dir, exist_ok=True)

            # Скачиваем файл
            file_response = self.session.get(download_url, stream=True, timeout=60)
            file_response.raise_for_status()

            destination_path = os.path.join(destination_dir, filename)

            # Скачиваем файл
            with open(destination_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Проверяем что файл скачался
            if os.path.exists(destination_path) and os.path.getsize(destination_path) > 1000:
                logger.info(f"✅ Успешно скачан: {filename}")
                return True
            else:
                logger.error(f"Файл скачался с ошибкой: {filename}")
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                return False

        except Exception as e:
            logger.error(f"Ошибка скачивания мода: {e}")
            return False

    def get_supported_loaders(self, minecraft_version: str) -> List[str]:
        """Получение списка поддерживаемых загрузчиков"""
        # Для CurseForge всегда доступны основные загрузчики
        return ["fabric", "forge", "quilt", "neoforge"]

    def get_mod_info(self, mod_id: str) -> Optional[Dict]:
        """Упрощенное получение информации о моде"""
        try:
            # Используем поиск для получения информации о моде
            response = self.session.get(
                f"{self.proxy_url}/api/v1/curseforge/mod/{mod_id}",
                timeout=self.timeout
            )

            if response.status_code == 200:
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