# Network/DependencyManager.py
import sqlite3
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging

from Network.ModrinthLoader import ModrinthAPI
from Network.CurseForgeLoader import CurseForgeAPI
from ConfDir.Configs import CONFIG, CURSEFORGE_CONFIG
from ConfDir.known_dependencies import get_dependencies_for_mod

logger = logging.getLogger("YamalPixel.DependencyManager")


class ModDependency:
    """Класс для представления зависимости мода"""

    def __init__(self, data: Dict):
        self.source = data.get('source')  # 'modrinth' или 'curseforge'
        self.project_id = data.get('project_id')
        self.mod_id = data.get('mod_id')  # Slug или ID
        self.name = data.get('name', 'Unknown')
        self.version_range = data.get('version_range', '*')
        self.dependency_type = data.get('type', 'required')  # required/optional/incompatible
        self.loader = data.get('loader')  # fabric/forge/neoforge
        self.minecraft_version = data.get('minecraft_version')

    def __str__(self):
        return f"{self.name} ({self.source}:{self.mod_id or self.project_id}) [{self.dependency_type}]"

    def to_dict(self):
        """Преобразует в словарь для JSON"""
        return {
            'source': self.source,
            'project_id': self.project_id,
            'mod_id': self.mod_id,
            'name': self.name,
            'version_range': self.version_range,
            'type': self.dependency_type,
            'loader': self.loader,
            'minecraft_version': self.minecraft_version
        }


class DependencyCache:
    """Кеш зависимостей на основе SQLite"""

    def __init__(self):
        self.db_path = Path(CONFIG["minecraft_dir"]) / "dependency_cache.db"
        self.init_db()

    def init_db(self):
        """Инициализирует базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица для кеша зависимостей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mod_dependencies (
                mod_key TEXT PRIMARY KEY,
                source TEXT,
                mod_info_json TEXT,
                dependencies_json TEXT,
                last_updated TIMESTAMP
            )
        ''')

        # Таблица для результатов поиска
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                search_key TEXT PRIMARY KEY,
                results_json TEXT,
                last_updated TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def get_mod_dependencies(self, mod_key: str, max_age_hours: int = 24) -> Optional[Dict]:
        """Получает зависимости мода из кеша"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT dependencies_json, last_updated FROM mod_dependencies WHERE mod_key = ?',
            (mod_key,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        deps_json, last_updated = result
        last_updated = datetime.fromisoformat(last_updated)

        # Проверяем свежесть кеша
        if datetime.now() - last_updated > timedelta(hours=max_age_hours):
            return None

        return json.loads(deps_json)

    def save_mod_dependencies(self, mod_key: str, source: str, mod_info: Dict, dependencies: List[Dict]):
        """Сохраняет зависимости мода в кеш"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT OR REPLACE INTO mod_dependencies 
               (mod_key, source, mod_info_json, dependencies_json, last_updated)
               VALUES (?, ?, ?, ?, ?)''',
            (
                mod_key,
                source,
                json.dumps(mod_info),
                json.dumps(dependencies),
                datetime.now().isoformat()
            )
        )

        conn.commit()
        conn.close()

    def get_search_results(self, search_key: str) -> Optional[List[Dict]]:
        """Получает результаты поиска из кеша"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT results_json FROM search_cache WHERE search_key = ?',
            (search_key,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        return json.loads(result[0])

    def save_search_results(self, search_key: str, results: List[Dict]):
        """Сохраняет результаты поиска в кеш"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT OR REPLACE INTO search_cache 
               (search_key, results_json, last_updated)
               VALUES (?, ?, ?)''',
            (search_key, json.dumps(results), datetime.now().isoformat())
        )

        conn.commit()
        conn.close()


class DependencyManager:
    """Основной менеджер зависимостей"""

    def __init__(self):
        self.modrinth_api = ModrinthAPI()
        self.curseforge_api = None
        self.cache = DependencyCache()

        # Инициализируем CurseForge API если доступен
        if CURSEFORGE_CONFIG.get("enabled", False):
            try:
                proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://localhost:8000")
                self.curseforge_api = CurseForgeAPI(proxy_url)

                if not self.curseforge_api.test_connection():
                    logger.warning("CurseForge API недоступен")
                    self.curseforge_api = None
            except Exception as e:
                logger.error(f"Ошибка инициализации CurseForge API: {e}")
                self.curseforge_api = None

        # Очередь для обработки
        self.processing_queue = []
        self.is_processing = False

    def resolve_dependencies_for_mod(self, mod_info: Dict, minecraft_version: str, loader: str) -> List[ModDependency]:
        """
        Рекурсивно разрешает зависимости для одного мода
        """
        source = mod_info.get('source')
        mod_id = mod_info.get('mod_id') or mod_info.get('project_id')

        if not source or not mod_id:
            return []

        mod_key = f"{source}:{mod_id}:{minecraft_version}:{loader}"

        # Проверяем кеш
        cached = self.cache.get_mod_dependencies(mod_key)
        if cached:
            logger.debug(f"Используем кеш для {mod_key}")
            return [ModDependency(dep) for dep in cached]

        # Получаем зависимости из API
        dependencies = self._fetch_dependencies_from_api(source, mod_id, minecraft_version, loader)

        # Сохраняем в кеш
        if dependencies:
            self.cache.save_mod_dependencies(
                mod_key,
                source,
                mod_info,
                [dep.to_dict() for dep in dependencies]
            )

        # Рекурсивно обрабатываем обязательные зависимости
        all_deps = []
        visited = set([mod_key])  # Для предотвращения циклов

        for dep in dependencies:
            if dep.dependency_type == 'required':
                all_deps.extend(self._resolve_dependency_tree(
                    dep, minecraft_version, loader, visited, depth=0
                ))

        return all_deps

    def _resolve_dependency_tree(self, dependency: ModDependency, minecraft_version: str,
                                 loader: str, visited: Set[str], depth: int, max_depth: int = 5) -> List[ModDependency]:
        """Рекурсивно строит дерево зависимостей"""
        if depth >= max_depth:
            logger.warning(f"Достигнута максимальная глубина рекурсии: {max_depth}")
            return []

        mod_key = f"{dependency.source}:{dependency.mod_id or dependency.project_id}:{minecraft_version}:{loader}"

        if mod_key in visited:
            logger.debug(f"Обнаружен цикл: {mod_key}")
            return []

        visited.add(mod_key)

        # Получаем зависимости для этой зависимости
        sub_deps = self.resolve_dependencies_for_mod(
            {
                'source': dependency.source,
                'mod_id': dependency.mod_id,
                'project_id': dependency.project_id,
                'name': dependency.name
            },
            minecraft_version,
            loader
        )

        # Собираем все зависимости
        all_deps = [dependency]
        for sub_dep in sub_deps:
            if sub_dep.dependency_type == 'required':
                all_deps.extend(self._resolve_dependency_tree(
                    sub_dep, minecraft_version, loader, visited, depth + 1, max_depth
                ))

        return all_deps

    def _fetch_dependencies_from_api(self, source: str, mod_id: str,
                                     minecraft_version: str, loader: str) -> List[ModDependency]:
        """Получает зависимости из API"""
        try:
            if source == 'modrinth':
                return self._get_modrinth_dependencies(mod_id, minecraft_version, loader)
            elif source == 'curseforge' and self.curseforge_api:
                return self._get_curseforge_dependencies(mod_id, minecraft_version, loader)
        except Exception as e:
            logger.error(f"Ошибка получения зависимостей для {source}:{mod_id}: {e}")

        return []

    def _get_modrinth_dependencies(self, project_id: str, minecraft_version: str, loader: str) -> List[ModDependency]:
        """Получает зависимости из Modrinth API"""
        try:
            # Получаем информацию о проекте
            project_data = self.modrinth_api.get_project(project_id)
            if not project_data:
                return []

            # Получаем версии для указанной версии Minecraft и загрузчика
            versions = self.modrinth_api.get_mod_versions(project_id, minecraft_version, loader)
            if not versions:
                return []

            # Берем последнюю версию
            latest_version = versions[0]

            # Извлекаем зависимости
            dependencies = []
            for dep in latest_version.get('dependencies', []):
                dep_type = dep.get('dependency_type')
                dep_project_id = dep.get('project_id')

                if dep_type in ['required', 'optional'] and dep_project_id:
                    # Получаем информацию о зависимости
                    dep_project = self.modrinth_api.get_project(dep_project_id)
                    if dep_project:
                        dependencies.append(ModDependency({
                            'source': 'modrinth',
                            'project_id': dep_project_id,
                            'mod_id': dep_project.get('slug'),
                            'name': dep_project.get('title', 'Unknown'),
                            'version_range': dep.get('version_range', '*'),
                            'type': dep_type,
                            'loader': loader,
                            'minecraft_version': minecraft_version
                        }))

            return dependencies

        except Exception as e:
            logger.error(f"Ошибка получения зависимостей Modrinth: {e}")
            return []

    def _get_curseforge_dependencies(self, mod_id: str, minecraft_version: str, loader: str) -> List[ModDependency]:
        """Получает зависимости из CurseForge - используем предопределенные"""
        if not self.curseforge_api:
            return []

        try:
            # Пробуем получить информацию о моде (если метод есть)
            mod_info = {}
            if hasattr(self.curseforge_api, 'get_mod_info'):
                mod_info = self.curseforge_api.get_mod_info(str(mod_id)) or {}

            mod_name = mod_info.get("name", f"Mod {mod_id}")

            # Получаем предопределенные зависимости
            predefined_deps = get_dependencies_for_mod(mod_name, "curseforge", loader)

            dependencies = []
            for dep in predefined_deps:
                if dep["source"] == "modrinth":
                    dependencies.append(ModDependency({
                        'source': 'modrinth',
                        'project_id': dep.get("modrinth_id"),
                        'mod_id': dep.get("mod_id"),
                        'name': dep["name"],
                        'version_range': dep.get("version_range", "*"),
                        'type': dep.get("type", "required"),
                        'loader': loader,
                        'minecraft_version': minecraft_version
                    }))
                elif dep["source"] == "curseforge":
                    dependencies.append(ModDependency({
                        'source': 'curseforge',
                        'project_id': str(dep.get("curseforge_id")),
                        'mod_id': dep.get("mod_id", ""),
                        'name': dep["name"],
                        'version_range': dep.get("version_range", "*"),
                        'type': dep.get("type", "required"),
                        'loader': loader,
                        'minecraft_version': minecraft_version
                    }))

            logger.info(f"Найдено {len(dependencies)} зависимостей для {mod_name}")
            return dependencies

        except Exception as e:
            logger.error(f"Ошибка получения зависимостей CurseForge: {e}")
            return []

    def _get_techreborn_dependencies(self, minecraft_version: str, loader: str) -> List[ModDependency]:
        """Возвращает зависимости для TechReborn (хардкод для примера)"""
        dependencies = []

        if loader.lower() == "fabric":
            # TechReborn на Fabric требует эти моды
            fabric_deps = [
                {
                    'name': 'Fabric API',
                    'modrinth_id': 'P7dR8mSH',
                    'version': '>=0.86.1'
                },
                {
                    'name': 'Fabric Biome API',
                    'modrinth_id': 'nZ9dJp6t',  # Это пример, нужен реальный ID
                    'version': '>=3.0.0'
                },
                {
                    'name': 'Fabric Transfer API',
                    'modrinth_id': 'B3qOj5VU',  # Пример
                    'version': '>=3.0.1'
                },
                {
                    'name': 'Reborn Core',
                    'curseforge_id': '237903',  # TechReborn всегда идет с Reborn Core
                    'version': '*'
                }
            ]

            for dep in fabric_deps:
                if 'modrinth_id' in dep:
                    dependencies.append(ModDependency({
                        'source': 'modrinth',
                        'project_id': dep['modrinth_id'],
                        'mod_id': dep['name'].lower().replace(' ', '-'),
                        'name': dep['name'],
                        'version_range': dep.get('version', '*'),
                        'type': 'required',
                        'loader': 'fabric',
                        'minecraft_version': minecraft_version
                    }))
                elif 'curseforge_id' in dep:
                    dependencies.append(ModDependency({
                        'source': 'curseforge',
                        'project_id': str(dep['curseforge_id']),
                        'mod_id': dep['name'].lower().replace(' ', '-'),
                        'name': dep['name'],
                        'version_range': dep.get('version', '*'),
                        'type': 'required',
                        'loader': 'fabric',
                        'minecraft_version': minecraft_version
                    }))

        return dependencies

    def analyze_collection_dependencies(self, collection_mods: List[Dict],
                                        minecraft_version: str, loader: str) -> Dict:
        """
        Анализирует зависимости для всей сборки
        Возвращает структурированный результат
        """
        logger.info(f"Анализируем зависимости для {len(collection_mods)} модов")

        all_mods = {}
        required_deps = []
        optional_deps = []

        for mod in collection_mods:
            mod_source = mod.get('source')
            mod_id = mod.get('mod_id') or mod.get('project_id')

            if not mod_source or not mod_id:
                continue

            mod_key = f"{mod_source}:{mod_id}"

            # Получаем зависимости для мода
            dependencies = self.resolve_dependencies_for_mod(
                mod, minecraft_version, loader
            )

            # Группируем зависимости
            for dep in dependencies:
                dep_key = f"{dep.source}:{dep.mod_id or dep.project_id}"

                if dep_key not in all_mods:
                    all_mods[dep_key] = dep

                    if dep.dependency_type == 'required':
                        required_deps.append(dep)
                    elif dep.dependency_type == 'optional':
                        optional_deps.append(dep)

        return {
            'total_mods': len(all_mods),
            'required_dependencies': required_deps,
            'optional_dependencies': optional_deps,
            'all_dependencies': list(all_mods.values()),
            'dependency_tree': self._build_dependency_tree(collection_mods, minecraft_version, loader)
        }

    def _build_dependency_tree(self, mods: List[Dict], minecraft_version: str, loader: str) -> Dict:
        """Строит дерево зависимостей для визуализации"""
        tree = {}

        for mod in mods:
            mod_key = f"{mod.get('source')}:{mod.get('mod_id') or mod.get('project_id')}"
            dependencies = self.resolve_dependencies_for_mod(mod, minecraft_version, loader)

            tree[mod_key] = {
                'mod': mod,
                'dependencies': [dep.to_dict() for dep in dependencies],
                'children': []
            }

            # Рекурсивно строим дерево
            for dep in dependencies:
                if dep.dependency_type == 'required':
                    dep_key = f"{dep.source}:{dep.mod_id or dep.project_id}"
                    if dep_key not in tree:
                        tree[dep_key] = {
                            'mod': dep.to_dict(),
                            'dependencies': [],
                            'children': []
                        }

                    tree[mod_key]['children'].append(dep_key)

        return tree

    def deduplicate_mods(self, mods: List[ModDependency]) -> List[ModDependency]:
        """Удаляет дубликаты модов из списка"""
        seen = set()
        unique_mods = []

        for mod in mods:
            mod_key = f"{mod.source}:{mod.mod_id or mod.project_id}"
            if mod_key not in seen:
                seen.add(mod_key)
                unique_mods.append(mod)

        return unique_mods