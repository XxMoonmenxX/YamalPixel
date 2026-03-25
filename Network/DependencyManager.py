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
        # Правильное получение ID мода - ищем в разных полях
        mod_id = (mod_info.get('mod_id') or
                  mod_info.get('project_id') or
                  mod_info.get('modrinth_id') or
                  mod_info.get('curseforge_id'))

        logger.info(f"🔍 Анализ зависимостей для: {mod_info.get('name', 'Unknown')} (source={source}, id={mod_id})")

        if not source or not mod_id:
            logger.warning(f"⚠️ Недостаточно данных: source={source}, mod_id={mod_id}")
            return []

        mod_key = f"{source}:{mod_id}:{minecraft_version}:{loader}"

        # Проверяем кеш
        cached = self.cache.get_mod_dependencies(mod_key)
        if cached:
            logger.debug(f"📦 Используем кеш для {mod_key}")
            return [ModDependency(dep) for dep in cached]

        # Получаем зависимости из API
        dependencies = self._fetch_dependencies_from_api(source, mod_id, minecraft_version, loader)

        logger.info(f"📊 Для {mod_info.get('name')} получено {len(dependencies)} зависимостей")

        # Сохраняем в кеш
        if dependencies:
            self.cache.save_mod_dependencies(
                mod_key,
                source,
                mod_info,
                [dep.to_dict() for dep in dependencies]
            )

        return dependencies

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
        """Получает зависимости из Modrinth API - как в старом коде"""
        try:
            logger.info(f"🔍 Получаем зависимости Modrinth для {project_id}")

            # Получаем версии для указанной версии Minecraft и загрузчика
            versions = self.modrinth_api.get_mod_versions(project_id, minecraft_version, loader)
            if not versions:
                logger.warning(f"❌ Нет версий для {project_id} под MC={minecraft_version}, loader={loader}")
                return []

            # Берем последнюю версию
            latest_version = versions[0]
            logger.info(f"📦 Версия {latest_version.get('version_number')}")
            logger.info(f"📋 Зависимости в версии: {latest_version.get('dependencies', [])}")

            # Извлекаем зависимости - прямо как в старом коде
            dependencies = []
            for dep in latest_version.get('dependencies', []):
                dep_type = dep.get('dependency_type')
                dep_project_id = dep.get('project_id')

                logger.info(f"   - Зависимость: {dep_project_id} (тип: {dep_type})")

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
                        logger.info(f"      ✅ Добавлена: {dep_project.get('title')}")
                    else:
                        logger.warning(f"      ❌ Не удалось получить информацию о {dep_project_id}")

            logger.info(f"✅ Найдено {len(dependencies)} зависимостей для {project_id}")
            return dependencies

        except Exception as e:
            logger.error(f"❌ Ошибка получения зависимостей Modrinth: {e}", exc_info=True)
            return []

    def _get_curseforge_dependencies(self, mod_id: str, minecraft_version: str, loader: str) -> List[ModDependency]:
        """Получает зависимости из CurseForge API через прокси - как в старом коде"""
        if not self.curseforge_api:
            logger.warning("❌ CurseForge API недоступен")
            return []

        try:
            logger.info(f"🔍 Получаем зависимости для CurseForge мода ID={mod_id}")

            # Получаем информацию о моде
            mod_info = self.curseforge_api.get_mod_info(str(mod_id))
            if not mod_info:
                logger.warning(f"❌ Не найдена информация о моде {mod_id}")
                return []

            logger.info(f"📦 Название мода: {mod_info.get('name')}")

            # Получаем версии мода
            versions = self.curseforge_api.get_mod_versions(
                mod_id=str(mod_id),
                minecraft_version=minecraft_version,
                loader=loader
            )

            if not versions:
                logger.warning(f"❌ Нет версий для мода {mod_id} под MC={minecraft_version}, loader={loader}")
                return []

            # Берем последнюю версию
            latest_version = versions[0]
            logger.info(f"📦 Версия {latest_version.get('id')} для {mod_info.get('name')}")
            logger.info(f"📋 Зависимости в версии: {latest_version.get('dependencies', [])}")

            # Получаем зависимости из API
            dependencies = []

            if 'dependencies' in latest_version:
                for dep in latest_version['dependencies']:
                    dep_type = dep.get('dependencyType')
                    dep_mod_id = dep.get('modId')

                    # dependencyType: 1=required, 2=optional, 3=incompatible, 4=embedded, 5=tool
                    is_required = dep_type == 1
                    is_optional = dep_type == 2

                    logger.info(f"   - Зависимость: modId={dep_mod_id} (тип: {dep_type}, required={is_required})")

                    if (is_required or is_optional) and dep_mod_id:
                        # Получаем информацию о зависимости
                        dep_info = self.curseforge_api.get_mod_info(str(dep_mod_id))
                        if dep_info:
                            dependencies.append(ModDependency({
                                'source': 'curseforge',
                                'project_id': str(dep_mod_id),
                                'mod_id': dep_info.get('slug', str(dep_mod_id)),
                                'name': dep_info.get('name', f'Mod {dep_mod_id}'),
                                'version_range': dep.get('versionRange', '*'),
                                'type': 'required' if is_required else 'optional',
                                'loader': loader,
                                'minecraft_version': minecraft_version
                            }))
                            logger.info(f"      ✅ Добавлена зависимость: {dep_info.get('name')}")
                        else:
                            logger.warning(f"      ❌ Не удалось получить информацию о моде {dep_mod_id}")

            logger.info(f"✅ Найдено {len(dependencies)} зависимостей для {mod_info.get('name')}")
            return dependencies

        except Exception as e:
            logger.error(f"❌ Ошибка получения зависимостей CurseForge: {e}", exc_info=True)
            return []

    def _get_dependencies_by_keywords(self, mod_name: str, minecraft_version: str, loader: str) -> List[ModDependency]:
        """
        Ищет зависимости по ключевым словам в названии мода
        Это как в старом коде - ищем по известным зависимостям
        """
        dependencies = []
        mod_name_lower = mod_name.lower()

        logger.info(f"🔍 Ищем зависимости по ключевым словам для: {mod_name}")

        # Словарь известных зависимостей
        known_deps = {
            # Fabric API - почти для всех Fabric модов
            'fabric': {
                'keywords': ['fabric', 'create', 'sodium', 'iris', 'jei', 'emi', 'ae2', 'applied', 'techreborn'],
                'deps': [{
                    'name': 'Fabric API',
                    'source': 'modrinth',
                    'modrinth_id': 'P7dR8mSH',
                    'mod_id': 'fabric-api',
                    'type': 'required'
                }]
            },

            # Для Create
            'create': {
                'keywords': ['create', 'steam', 'rail', 'crafts', 'addition', 'deco', 'slice', 'dice'],
                'deps': [
                    {
                        'name': 'Fabric API',
                        'source': 'modrinth',
                        'modrinth_id': 'P7dR8mSH',
                        'mod_id': 'fabric-api',
                        'type': 'required'
                    },
                    {
                        'name': 'Indium',
                        'source': 'modrinth',
                        'modrinth_id': 'Orvt0mRa',
                        'mod_id': 'indium',
                        'type': 'required'
                    }
                ]
            },

            # Sodium и оптимизация
            'sodium': {
                'keywords': ['sodium', 'iris', 'indium'],
                'deps': [
                    {
                        'name': 'Fabric API',
                        'source': 'modrinth',
                        'modrinth_id': 'P7dR8mSH',
                        'mod_id': 'fabric-api',
                        'type': 'required'
                    }
                ]
            },

            # JEI / EMI
            'jei': {
                'keywords': ['jei', 'emi', 'just enough', 'roughly enough'],
                'deps': [
                    {
                        'name': 'Fabric API',
                        'source': 'modrinth',
                        'modrinth_id': 'P7dR8mSH',
                        'mod_id': 'fabric-api',
                        'type': 'required'
                    }
                ]
            },

            # Applied Energistics 2
            'ae2': {
                'keywords': ['ae2', 'applied', 'energistics'],
                'deps': [
                    {
                        'name': 'Fabric API',
                        'source': 'modrinth',
                        'modrinth_id': 'P7dR8mSH',
                        'mod_id': 'fabric-api',
                        'type': 'required'
                    }
                ]
            },

            # Tech Reborn
            'techreborn': {
                'keywords': ['techreborn', 'tech reborn', 'reborn'],
                'deps': [
                    {
                        'name': 'Fabric API',
                        'source': 'modrinth',
                        'modrinth_id': 'P7dR8mSH',
                        'mod_id': 'fabric-api',
                        'type': 'required'
                    },
                    {
                        'name': 'Reborn Core',
                        'source': 'curseforge',
                        'curseforge_id': '237903',
                        'mod_id': 'reborncore',
                        'type': 'required'
                    }
                ]
            },

            # Traveler's Backpack
            'travelersbackpack': {
                'keywords': ['travelersbackpack', 'traveler', 'backpack'],
                'deps': [
                    {
                        'name': 'Fabric API',
                        'source': 'modrinth',
                        'modrinth_id': 'P7dR8mSH',
                        'mod_id': 'fabric-api',
                        'type': 'required'
                    },
                    {
                        'name': 'Cardinal Components API',
                        'source': 'modrinth',
                        'modrinth_id': 'KFTjWFTV',
                        'mod_id': 'cardinal-components',
                        'type': 'required'
                    }
                ]
            },

            # Iron Chests
            'ironchests': {
                'keywords': ['ironchests', 'iron chest'],
                'deps': [
                    {
                        'name': 'Fabric API',
                        'source': 'modrinth',
                        'modrinth_id': 'P7dR8mSH',
                        'mod_id': 'fabric-api',
                        'type': 'required'
                    }
                ]
            },

            # Xaero's Maps
            'xaero': {
                'keywords': ['xaero', 'minimap', 'worldmap'],
                'deps': []  # Xaero's maps не требуют зависимостей
            }
        }

        # Проверяем, подходит ли мод под какой-то из известных паттернов
        for key, data in known_deps.items():
            for keyword in data['keywords']:
                if keyword in mod_name_lower:
                    logger.info(f"  ✅ Найдено совпадение по ключевому слову: '{keyword}' для мода '{mod_name}'")

                    for dep_data in data['deps']:
                        # Проверяем, не добавляли ли уже эту зависимость
                        already_added = False
                        for existing in dependencies:
                            if existing.name == dep_data['name']:
                                already_added = True
                                break

                        if not already_added:
                            if dep_data['source'] == 'modrinth':
                                dependencies.append(ModDependency({
                                    'source': 'modrinth',
                                    'project_id': dep_data['modrinth_id'],
                                    'mod_id': dep_data['mod_id'],
                                    'name': dep_data['name'],
                                    'version_range': '*',
                                    'type': dep_data.get('type', 'required'),
                                    'loader': loader,
                                    'minecraft_version': minecraft_version
                                }))
                                logger.info(f"      🔧 Добавлена зависимость: {dep_data['name']} (Modrinth)")
                            else:
                                dependencies.append(ModDependency({
                                    'source': 'curseforge',
                                    'project_id': dep_data['curseforge_id'],
                                    'mod_id': dep_data['mod_id'],
                                    'name': dep_data['name'],
                                    'version_range': '*',
                                    'type': dep_data.get('type', 'required'),
                                    'loader': loader,
                                    'minecraft_version': minecraft_version
                                }))
                                logger.info(f"      🔧 Добавлена зависимость: {dep_data['name']} (CurseForge)")

                    break  # Нашли совпадение, выходим

        # Если это Fabric мод, но не нашли специфических зависимостей, добавляем Fabric API
        if loader == 'fabric' and not dependencies:
            # Проверяем, не является ли сам мод Fabric API
            if 'fabric api' not in mod_name_lower and 'fabric-api' not in mod_name_lower:
                dependencies.append(ModDependency({
                    'source': 'modrinth',
                    'project_id': 'P7dR8mSH',
                    'mod_id': 'fabric-api',
                    'name': 'Fabric API',
                    'version_range': '*',
                    'type': 'required',
                    'loader': loader,
                    'minecraft_version': minecraft_version
                }))
                logger.info(f"  🔧 Добавлена общая зависимость: Fabric API")

        return dependencies

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