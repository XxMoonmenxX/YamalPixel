# Network/DependencyManager.py
import re
import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

logger = logging.getLogger("YamalPixel.DependencyManager")


class ModDependency:
    """Класс для представления зависимости мода"""

    def __init__(self, data: Dict):
        self.source = data.get('source')
        self.project_id = data.get('project_id')
        self.mod_id = data.get('mod_id')
        self.name = data.get('name', 'Unknown')
        self.dependency_type = data.get('type', 'required')
        self.url = data.get('url')


class DependencyManager:
    def __init__(self):
        self.modrinth_api = None
        self.curseforge_api = None
        self._init_curseforge_api()

    def _get_modrinth_api(self):
        """Ленивая инициализация Modrinth API"""
        if self.modrinth_api is None:
            from Network.ModrinthLoader import ModrinthAPI
            self.modrinth_api = ModrinthAPI()
        return self.modrinth_api

    def _init_curseforge_api(self):
        """Инициализация CurseForge API через прокси"""
        try:
            from Network.CurseForgeLoader import CurseForgeAPI
            from ConfDir.Configs import CURSEFORGE_CONFIG

            proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://90.151.59.120:8000")
            self.curseforge_api = CurseForgeAPI(proxy_url)

            if not self.curseforge_api.test_connection():
                logger.warning("⚠️ CurseForge прокси недоступен")
                self.curseforge_api = None
            else:
                logger.info("✅ CurseForge API через прокси инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации CurseForge API: {e}")
            self.curseforge_api = None

    def resolve_dependencies_for_mod(self, mod_info: Dict, minecraft_version: str, loader: str) -> List[ModDependency]:
        """Основной метод для получения зависимостей"""
        source = mod_info.get('source')
        mod_id = mod_info.get('mod_id') or mod_info.get('project_id') or mod_info.get('curseforge_id')
        mod_name = mod_info.get('name', '')

        if not source or not mod_id:
            logger.warning(f"⚠️ Мод {mod_name} пропущен: нет source={source} или id={mod_id}")
            return []

        logger.info(f"🔍 Анализ зависимостей для: {mod_name} (ID: {mod_id}, источник: {source})")

        if source == 'modrinth':
            return self._get_modrinth_dependencies(mod_id, minecraft_version, loader)
        elif source == 'curseforge':
            return self._get_curseforge_dependencies(mod_id, minecraft_version, loader)

        return []

    def _get_modrinth_dependencies(self, project_id: str, minecraft_version: str, loader: str) -> List[ModDependency]:
        """Получение зависимостей из Modrinth API"""
        try:
            api = self._get_modrinth_api()
            logger.info(f"🔍 Modrinth: получаем версии для {project_id}")

            versions = api.get_mod_versions(project_id, minecraft_version, loader)

            if not versions:
                logger.warning(f"❌ Нет версий для {project_id} под MC={minecraft_version}, loader={loader}")
                return []

            latest_version = versions[0]
            logger.info(f"📦 Версия {latest_version.get('version_number')}")

            dependencies = []
            for dep in latest_version.get('dependencies', []):
                dep_type = dep.get('dependency_type')
                dep_project_id = dep.get('project_id')

                if not dep_project_id:
                    continue

                if dep_type in ['required', 'optional']:
                    logger.info(f"   → Найдена зависимость: {dep_project_id} ({dep_type})")

                    dep_project = api.get_project(dep_project_id)
                    dep_name = dep_project.get('title',
                                               f"Mod {dep_project_id}") if dep_project else f"Mod {dep_project_id}"

                    dependencies.append(ModDependency({
                        'source': 'modrinth',
                        'project_id': dep_project_id,
                        'mod_id': dep_project_id,
                        'name': dep_name,
                        'type': dep_type,
                        'url': f"https://modrinth.com/mod/{dep_project_id}"
                    }))
                    logger.info(f"      ✅ {dep_name}")

            return dependencies

        except Exception as e:
            logger.error(f"Ошибка получения зависимостей Modrinth: {e}")
            return []

    def _get_curseforge_dependencies(self, mod_slug: str, minecraft_version: str, loader: str) -> List[ModDependency]:
        """
        Получение зависимостей из CurseForge через прокси
        """
        try:
            if not self.curseforge_api:
                logger.warning("CurseForge API недоступен")
                return self._fallback_dependencies(mod_slug, loader)

            # 1. Пробуем получить зависимости через API
            logger.info(f"🔍 CurseForge API: получаем информацию о моде {mod_slug}")

            # Получаем версии мода через API
            versions = self.curseforge_api.get_mod_versions(
                mod_id=mod_slug,
                minecraft_version=minecraft_version,
                loader=loader
            )

            if versions:
                logger.info(f"📦 Найдено {len(versions)} версий для {mod_slug}")

                # Берем последнюю версию
                latest_version = versions[0]

                # Проверяем зависимости в версии
                if "dependencies" in latest_version and latest_version["dependencies"]:
                    logger.info(f"🔍 Найдены зависимости в API")
                    dependencies = []
                    for dep in latest_version["dependencies"]:
                        dep_type = dep.get("dependencyType")
                        dep_mod_id = dep.get("modId")

                        if dep_mod_id and (dep_type == 1 or dep_type == "required"):
                            logger.info(f"   → Найдена зависимость через API: {dep_mod_id}")
                            dependencies.append(ModDependency({
                                'source': 'curseforge',
                                'project_id': str(dep_mod_id),
                                'mod_id': str(dep_mod_id),
                                'name': f"Mod {dep_mod_id}",
                                'type': 'required',
                                'url': f"https://www.curseforge.com/minecraft/mc-mods/{dep_mod_id}"
                            }))
                    if dependencies:
                        return dependencies

            # 2. Пробуем получить через HTML парсинг (через прокси)
            logger.info(f"🌐 Пробуем парсинг через прокси для {mod_slug}")

            # Используем CurseForge API для получения HTML через прокси
            proxy_url = f"{self.curseforge_api.proxy_url}/api/v1/curseforge/mod/{mod_slug}"

            response = self.curseforge_api._make_proxy_request('GET', f'/api/v1/curseforge/mod/{mod_slug}')

            if response and response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    mod_data = data["data"]
                    description = mod_data.get("description", "")

                    # Ищем в описании секцию Requirements
                    dependencies = self._parse_requirements_from_text(description)
                    if dependencies:
                        return dependencies

                    # Ищем в категориях
                    categories = mod_data.get("categories", [])
                    for cat in categories:
                        if "create" in cat.get("name", "").lower():
                            logger.info(f"   → Мод относится к категории Create")
                            dependencies.append(ModDependency({
                                'source': 'curseforge',
                                'project_id': '328085',
                                'mod_id': 'create',
                                'name': 'Create',
                                'type': 'required',
                                'url': 'https://www.curseforge.com/minecraft/mc-mods/create'
                            }))

                    if dependencies:
                        return dependencies

            # 3. Fallback: для модов, связанных с Create
            return self._fallback_dependencies(mod_slug, loader)

        except Exception as e:
            logger.error(f"Ошибка получения зависимостей для {mod_slug}: {e}", exc_info=True)
            return self._fallback_dependencies(mod_slug, loader)

    def _parse_requirements_from_text(self, text: str) -> List[ModDependency]:
        """Парсит текст описания в поисках зависимостей"""
        if not text:
            return []

        dependencies = []

        # Ищем секцию "Requirements" в HTML или тексте
        req_patterns = [
            r'(?:Requirements|Requires|Dependencies?|Needs):\s*([^\n<]+)',
            r'<strong>Requirements?</strong>\s*<br/?>\s*([^<]+)',
            r'<h[23]>Requirements?</h[23]>\s*<ul>\s*<li>([^<]+)</li>',
            r'Requires\s+([A-Za-z\s]+?)\s+(?:mod|addon)',
        ]

        for pattern in req_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Разбиваем на отдельные моды
                items = re.split(r'[,;]', match)
                for item in items:
                    item = item.strip()
                    if not item or len(item) < 3:
                        continue

                    # Очищаем от версий
                    clean_name = re.sub(r'\d+\.\d+\.\d+.*$', '', item)
                    clean_name = re.sub(r'\d+\.\d+.*$', '', clean_name)
                    clean_name = re.sub(r'\([^)]+\)', '', clean_name)
                    clean_name = clean_name.strip()

                    if clean_name and len(clean_name) > 2:
                        # Проверяем, не является ли это "Minecraft" или "Java"
                        if clean_name.lower() in ['minecraft', 'java', 'and', 'or']:
                            continue

                        # Ищем известные моды
                        mod_info = self._find_known_mod(clean_name)
                        if mod_info:
                            logger.info(f"   → Найдена зависимость из описания: {clean_name} -> {mod_info['name']}")
                            dependencies.append(ModDependency({
                                'source': mod_info['source'],
                                'project_id': mod_info['id'],
                                'mod_id': mod_info['slug'],
                                'name': mod_info['name'],
                                'type': 'required',
                                'url': mod_info.get('url')
                            }))
                        else:
                            logger.info(f"   → Найдена возможная зависимость: {clean_name}")
                            dependencies.append(ModDependency({
                                'source': 'curseforge',
                                'project_id': None,
                                'mod_id': None,
                                'name': clean_name,
                                'type': 'required',
                                'url': None
                            }))

        return dependencies

    def _find_known_mod(self, name: str) -> Optional[Dict]:
        """Находит известный мод по названию (без базы данных)"""
        name_lower = name.lower()

        # Популярные моды
        popular_mods = {
            'create': ('curseforge', '328085', 'create', 'Create'),
            'jei': ('curseforge', '238222', 'jei', 'Just Enough Items'),
            'fabric api': ('modrinth', 'P7dR8mSH', 'fabric-api', 'Fabric API'),
            'forge': None,
            'minecraft': None,
        }

        for key, info in popular_mods.items():
            if key in name_lower:
                if info:
                    return {
                        'source': info[0],
                        'id': info[1],
                        'slug': info[2],
                        'name': info[3],
                        'url': f"https://www.curseforge.com/minecraft/mc-mods/{info[2]}" if info[
                                                                                                0] == 'curseforge' else f"https://modrinth.com/mod/{info[2]}"
                    }
                return None

        return None

    def _fallback_dependencies(self, mod_slug: str, loader: str) -> List[ModDependency]:
        """Fallback зависимости для случаев, когда не удалось найти через API"""
        dependencies = []

        # Для модов Create добавляем Create как зависимость
        if "create" in mod_slug.lower():
            logger.info(f"🔧 Добавляем Create как зависимость для {mod_slug}")
            dependencies.append(ModDependency({
                'source': 'curseforge',
                'project_id': '328085',
                'mod_id': 'create',
                'name': 'Create',
                'type': 'required',
                'url': 'https://www.curseforge.com/minecraft/mc-mods/create'
            }))

        # Для Fabric модов добавляем Fabric API
        if loader == "fabric":
            logger.info(f"🔧 Добавляем Fabric API как зависимость для {mod_slug}")
            dependencies.append(ModDependency({
                'source': 'modrinth',
                'project_id': 'P7dR8mSH',
                'mod_id': 'fabric-api',
                'name': 'Fabric API',
                'type': 'required',
                'url': 'https://modrinth.com/mod/fabric-api'
            }))

        return dependencies

    def analyze_collection_dependencies(self, collection_mods: List[Dict],
                                        minecraft_version: str, loader: str) -> Dict:
        """Анализирует зависимости всей сборки"""
        logger.info(f"🔍 Анализируем зависимости для {len(collection_mods)} модов")

        all_deps = []
        seen = set()

        for mod in collection_mods:
            mod_source = mod.get('source')
            mod_id = mod.get('mod_id') or mod.get('project_id') or mod.get('curseforge_id')

            if not mod_source or not mod_id:
                logger.warning(f"⚠️ Мод {mod.get('name')} пропущен: нет source или id")
                continue

            logger.info(f"📦 Анализ: {mod.get('name')} (ID: {mod_id}, источник: {mod_source})")

            dependencies = self.resolve_dependencies_for_mod(mod, minecraft_version, loader)

            for dep in dependencies:
                if dep.project_id:
                    dep_key = f"{dep.source}:{dep.project_id}"
                elif dep.name:
                    dep_key = f"name:{dep.name}"
                else:
                    dep_key = f"unknown:{dep.mod_id}"

                if dep_key not in seen:
                    seen.add(dep_key)
                    all_deps.append(dep)
                    logger.info(f"   + Добавлена зависимость: {dep.name} ({dep.source})")

        required = [d for d in all_deps if d.dependency_type == 'required']
        optional = [d for d in all_deps if d.dependency_type == 'optional']

        logger.info(f"📊 Результат: обязательных={len(required)}, опциональных={len(optional)}")

        return {
            'total_mods': len(
                [m for m in collection_mods if m.get('mod_id') or m.get('project_id') or m.get('curseforge_id')]),
            'required_dependencies': required,
            'optional_dependencies': optional,
            'all_dependencies': all_deps,
        }