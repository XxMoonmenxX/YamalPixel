# modrinth_api.py
import requests
import re # noqa
import os
from typing import List, Dict, Optional
import urllib.parse


class ModrinthAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://api.modrinth.com/v2"
        self.session.headers.update(
            {"User-Agent": "YamalPixel-Launcher/1.0 (moonmen@example.com)"}
        )

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
            print(f"Ошибка поиска модов: {e}")
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
            print(f"Ошибка получения версий мода {mod_id}: {e}")
            return None

    def download_mod(self, project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        """Скачивание мода с правильным экранированием имени файла"""
        try:
            # Экранируем имя файла — особенно важно для +, пробелов, % и т.д.
            encoded_filename = urllib.parse.quote(filename)

            # Правильный URL
            file_url = f"https://cdn.modrinth.com/data/{project_slug}/versions/{version_id}/{encoded_filename}"

            print(f"📥 Скачиваем: {file_url}")

            response = self.session.get(file_url, stream=True, timeout=30)
            response.raise_for_status()

            filepath = os.path.join(mods_dir, filename)
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"✅ Успешно скачан: {filename}")
            return True

        except Exception as e:
            print(f"❌ Ошибка скачивания мода {filename}: {e}")
            return self.download_mod_alternative(project_slug, version_id, filename, mods_dir)

    def download_mod_alternative(self, _project_slug: str, version_id: str, filename: str, mods_dir: str) -> bool:
        """Альтернативный метод скачивания через получение информации о версии"""
        try:
            # Получаем информацию о версии
            version_url = f"{self.base_url}/version/{version_id}"
            response = self.session.get(version_url, timeout=30)
            response.raise_for_status()
            version_data = response.json()

            print(f"🔍 Ищем файл в информации о версии: {filename}")

            if "files" in version_data and version_data["files"]:
                # Ищем нужный файл по имени
                target_file = None
                for file_info in version_data["files"]:
                    if file_info["filename"] == filename:
                        target_file = file_info
                        break

                if target_file and "url" in target_file:
                    download_url = target_file["url"]
                    print(f"📥 Альтернативное скачивание: {download_url}")

                    response = self.session.get(download_url, stream=True, timeout=30)
                    response.raise_for_status()

                    filepath = os.path.join(mods_dir, filename)
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    print(f"✅ Успешно скачан альтернативным методом: {filename}")
                    return True

            print(f"❌ Файл {filename} не найден в информации о версии")
            return False

        except Exception as e:
            print(f"❌ Альтернативный метод скачивания также не удался: {e}")
            return False

    def get_project_info(self, project_slug: str) -> Optional[Dict]:
        """Получить информацию о проекте по slug"""
        try:
            url = f"{self.base_url}/project/{project_slug}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения информации о проекте {project_slug}: {e}")
            return None
