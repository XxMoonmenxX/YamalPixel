## Network/neoforge_utils.py
import requests
import json
import os
import re
from typing import Dict, Optional, Tuple, List
import logging

logger = logging.getLogger("NeoForgeUtils")

# Кэш для загруженных JSON
_profile_cache = {}


class NeoForgeVersionFetcher:
    """Автоматический загрузчик версий библиотек NeoForge"""

    MAVEN_BASE = "https://maven.neoforged.net/releases/net/neoforged/neoforge"
    MAVEN_CREEPER = "https://maven.creeperhost.net/net/neoforged/neoforge"
    MAVEN_REPO = "https://repo.neoforged.net/releases/net/neoforged/neoforge"

    @staticmethod
    def get_version_json(neoforge_version: str) -> Optional[Dict]:
        """Загружает официальный JSON для версии NeoForge"""
        urls = [
            f"{NeoForgeVersionFetcher.MAVEN_BASE}/{neoforge_version}/neoforge-{neoforge_version}.json",
            f"{NeoForgeVersionFetcher.MAVEN_CREEPER}/{neoforge_version}/neoforge-{neoforge_version}.json",
            f"{NeoForgeVersionFetcher.MAVEN_REPO}/{neoforge_version}/neoforge-{neoforge_version}.json",
        ]

        for url in urls:
            try:
                logger.debug(f"Trying to fetch: {url}")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Loaded NeoForge profile for {neoforge_version}")
                    return data
            except Exception as e:
                logger.debug(f"Failed to fetch {url}: {e}")

        logger.warning(f"⚠️ Could not load profile for NeoForge {neoforge_version}")
        return None

    @staticmethod
    def extract_library_versions(version_json: Dict) -> Dict[str, str]:
        """Извлекает версии библиотек из JSON"""
        versions = {}

        if not version_json:
            return versions

        # Извлекаем из libraries секции
        for lib in version_json.get("libraries", []):
            name = lib.get("name", "")
            if ":" in name:
                parts = name.split(":")
                if len(parts) >= 3:
                    group = parts[0]
                    artifact = parts[1]
                    version = parts[2]

                    # Сохраняем важные библиотеки
                    if "fancymodloader" in name:
                        versions["fml"] = version
                    elif "modlauncher" in name and "cpw.mods" in name:
                        versions["modlauncher"] = version
                    elif "bootstraplauncher" in name:
                        versions["bootstraplauncher"] = version
                    elif "securejarhandler" in name:
                        versions["securejarhandler"] = version
                    elif "neoforge" in name and group == "net.neoforged" and artifact == "neoforge":
                        versions["neoforge"] = version

        # Извлекаем из versionJson если есть
        if "versionInfo" in version_json:
            vinfo = version_json["versionInfo"]
            if "javaVersion" in vinfo:
                versions["javaVersion"] = vinfo["javaVersion"].get("component", "")
            if "mainClass" in vinfo:
                versions["mainClass"] = vinfo["mainClass"]

        return versions

    @staticmethod
    def get_loader_versions_from_maven(minecraft_version: str) -> List[str]:
        """Получает доступные версии NeoForge из Maven метаданных"""
        try:
            # Пробуем получить через API
            api_url = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                versions = []
                mc_num = minecraft_version.replace("1.", "")
                for version in data.get("versions", []):
                    if version.startswith(mc_num) and not "beta" in version.lower() and not "alpha" in version.lower():
                        versions.append(version)
                return sorted(versions, reverse=True)
        except Exception as e:
            logger.warning(f"Failed to fetch from Maven API: {e}")

        # Fallback: парсим HTML страницу
        return NeoForgeVersionFetcher._scrape_maven_page(minecraft_version)

    @staticmethod
    def _scrape_maven_page(minecraft_version: str) -> List[str]:
        """Парсит страницу Maven для получения версий"""
        import re
        from bs4 import BeautifulSoup

        mc_num = minecraft_version.replace("1.", "")
        urls = [
            f"https://maven.neoforged.net/releases/net/neoforged/neoforge/",
            f"https://maven.creeperhost.net/net/neoforged/neoforge/",
        ]

        versions = []
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a'):
                        href = link.get('href', '')
                        if href.startswith(mc_num) and href.endswith('/'):
                            version = href.rstrip('/')
                            if version not in versions:
                                versions.append(version)
                if versions:
                    break
            except:
                continue

        return sorted(versions, reverse=True)


class NeoForgeProfileGenerator:
    """Генератор профилей NeoForge с динамической загрузкой"""

    def __init__(self):
        self.cache = {}

    def generate_profile(self, minecraft_version: str, neoforge_version: str, minecraft_dir: str) -> Dict:
        """Генерирует профиль с актуальными версиями библиотек"""
        cache_key = f"{minecraft_version}_{neoforge_version}"

        # Проверяем кэш
        if cache_key in _profile_cache:
            logger.info(f"Using cached profile for {neoforge_version}")
            return _profile_cache[cache_key]

        logger.info(f"Generating profile for NeoForge {neoforge_version} (MC {minecraft_version})")

        # Пробуем загрузить официальный JSON
        version_json = NeoForgeVersionFetcher.get_version_json(neoforge_version)

        if version_json:
            logger.info(f"✅ Found official JSON for NeoForge {neoforge_version}")
            # Если есть полный JSON, используем его
            profile = self._create_profile_from_json(version_json, minecraft_version, neoforge_version, minecraft_dir)
        else:
            logger.warning(f"⚠️ No official JSON, generating fallback profile")
            profile = self._generate_fallback_profile(minecraft_version, neoforge_version, minecraft_dir)

        # Сохраняем в кэш
        _profile_cache[cache_key] = profile
        return profile

    def _create_profile_from_json(self, version_json: Dict, minecraft_version: str, neoforge_version: str,
                                  minecraft_dir: str) -> Dict:
        """Создает профиль из официального JSON"""
        versions = NeoForgeVersionFetcher.extract_library_versions(version_json)

        # Получаем версии из JSON или используем то, что есть
        fml_version = versions.get("fml", self._get_fml_version(neoforge_version))
        modlauncher_version = versions.get("modlauncher", self._get_modlauncher_version(neoforge_version))
        bootstrap_version = versions.get("bootstraplauncher", self._get_bootstrap_version(neoforge_version))
        securejarhandler_version = versions.get("securejarhandler",
                                                self._get_securejarhandler_version(neoforge_version))
        main_class = versions.get("mainClass", "cpw.mods.bootstraplauncher.BootstrapLauncher")

        # Используем библиотеки из JSON
        libraries = version_json.get("libraries", [])

        # Если библиотек нет в JSON, генерируем
        if not libraries:
            libraries = self._generate_libraries(
                neoforge_version, fml_version, modlauncher_version,
                bootstrap_version, securejarhandler_version
            )

        # Получаем аргументы из JSON или генерируем
        game_args = self._get_game_args(version_json, neoforge_version, fml_version, minecraft_version)
        jvm_args = self._get_jvm_args(version_json, bootstrap_version, securejarhandler_version, modlauncher_version)

        return {
            "id": f"neoforge-{neoforge_version}",
            "type": "release",
            "mainClass": main_class,
            "inheritsFrom": minecraft_version,
            "arguments": {
                "game": game_args,
                "jvm": jvm_args
            },
            "libraries": libraries,
            "minimumLauncherVersion": 21
        }

    def _get_game_args(self, version_json: Dict, neoforge_version: str, fml_version: str, minecraft_version: str) -> \
    List[str]:
        """Получает game аргументы из JSON или генерирует"""
        # Пробуем взять из arguments
        if "arguments" in version_json and "game" in version_json["arguments"]:
            args = version_json["arguments"]["game"]
            # Преобразуем в плоский список
            result = []
            for arg in args:
                if isinstance(arg, str):
                    result.append(arg)
                elif isinstance(arg, dict) and "value" in arg:
                    if isinstance(arg["value"], list):
                        result.extend(arg["value"])
                    else:
                        result.append(arg["value"])
            if result:
                return result

        # Генерируем стандартные аргументы
        return [
            "--fml.neoForgeVersion", neoforge_version,
            "--fml.fmlVersion", fml_version,
            "--fml.mcVersion", minecraft_version,
            "--fml.neoFormVersion", self._get_neoform_version(neoforge_version),
            "--launchTarget", "forgeclient"
        ]

    def _get_jvm_args(self, version_json: Dict, bootstrap_version: str, securejarhandler_version: str,
                      modlauncher_version: str) -> List[str]:
        """Получает JVM аргументы из JSON или генерирует"""
        # Пробуем взять из arguments
        if "arguments" in version_json and "jvm" in version_json["arguments"]:
            args = version_json["arguments"]["jvm"]
            result = []
            for arg in args:
                if isinstance(arg, str):
                    result.append(arg)
                elif isinstance(arg, dict) and "value" in arg:
                    if isinstance(arg["value"], list):
                        result.extend(arg["value"])
                    else:
                        result.append(arg["value"])
            if result:
                return result

        # Генерируем стандартные аргументы
        classpath_items = [
            f"cpw/mods/bootstraplauncher/{bootstrap_version}/bootstraplauncher-{bootstrap_version}.jar",
            f"cpw/mods/securejarhandler/{securejarhandler_version}/securejarhandler-{securejarhandler_version}.jar",
            "org/ow2/asm/asm-commons/9.8/asm-commons-9.8.jar",
            "org/ow2/asm/asm-util/9.8/asm-util-9.8.jar",
            "org/ow2/asm/asm-analysis/9.8/asm-analysis-9.8.jar",
            "org/ow2/asm/asm-tree/9.8/asm-tree-9.8.jar",
            "org/ow2/asm/asm/9.8/asm-9.8.jar",
        ]

        classpath = "${library_directory}/" + "${classpath_separator}${library_directory}/".join(classpath_items)

        return [
            "-Djava.net.preferIPv6Addresses=system",
            "-DignoreList=client-extra,${version_name}.jar",
            "-DlibraryDirectory=${library_directory}",
            "-p", classpath,
            "--add-modules", "ALL-MODULE-PATH",
            "--add-opens", "java.base/java.util.jar=cpw.mods.securejarhandler",
            "--add-opens", "java.base/java.lang.invoke=cpw.mods.securejarhandler",
            "--add-exports", "java.base/sun.security.util=cpw.mods.securejarhandler",
            "--add-exports", "jdk.naming.dns/com.sun.jndi.dns=java.naming"
        ]

    def _generate_fallback_profile(self, minecraft_version: str, neoforge_version: str, minecraft_dir: str) -> Dict:
        """Генерирует fallback профиль на основе версии"""
        # Пробуем загрузить из кэша версий
        versions = self._get_cached_versions(neoforge_version)

        fml_version = versions.get("fml", self._get_fml_version(neoforge_version))
        modlauncher_version = versions.get("modlauncher", self._get_modlauncher_version(neoforge_version))
        bootstrap_version = versions.get("bootstraplauncher", self._get_bootstrap_version(neoforge_version))
        securejarhandler_version = versions.get("securejarhandler",
                                                self._get_securejarhandler_version(neoforge_version))

        libraries = self._generate_libraries(
            neoforge_version, fml_version, modlauncher_version,
            bootstrap_version, securejarhandler_version
        )

        game_args = [
            "--fml.neoForgeVersion", neoforge_version,
            "--fml.fmlVersion", fml_version,
            "--fml.mcVersion", minecraft_version,
            "--fml.neoFormVersion", self._get_neoform_version(neoforge_version),
            "--launchTarget", "forgeclient"
        ]

        jvm_args = self._generate_jvm_args(bootstrap_version, securejarhandler_version, modlauncher_version)

        return {
            "id": f"neoforge-{neoforge_version}",
            "type": "release",
            "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher",
            "inheritsFrom": minecraft_version,
            "arguments": {
                "game": game_args,
                "jvm": jvm_args
            },
            "libraries": libraries,
            "minimumLauncherVersion": 21
        }

    def _get_cached_versions(self, neoforge_version: str) -> Dict[str, str]:
        """Получает версии из локального кэша (можно расширять)"""
        # Здесь можно добавить локальный маппинг для известных версий
        version_cache = {
            "21.1.219": {
                "fml": "4.0.47",
                "modlauncher": "11.0.7",
                "bootstraplauncher": "2.0.4",
                "securejarhandler": "3.0.8"
            },
            "21.1.215": {
                "fml": "4.0.42",
                "modlauncher": "11.0.5",
                "bootstraplauncher": "2.0.2",
                "securejarhandler": "3.0.8"
            }
        }
        return version_cache.get(neoforge_version, {})

    def _get_fml_version(self, neoforge_version: str) -> str:
        """Определяет версию FML на основе версии NeoForge"""
        # Формула: FML версия = 4.0.(build - 173)
        try:
            parts = neoforge_version.split('.')
            if len(parts) >= 3:
                build = int(parts[2])
                fml_build = max(1, build - 173)
                return f"4.0.{fml_build}"
        except:
            pass
        return "4.0.47"

    def _get_modlauncher_version(self, neoforge_version: str) -> str:
        """Определяет версию ModLauncher"""
        try:
            parts = neoforge_version.split('.')
            if len(parts) >= 3:
                build = int(parts[2])
                if build >= 215:
                    return "11.0.7"
                elif build >= 209:
                    return "11.0.5"
        except:
            pass
        return "11.0.5"

    def _get_bootstrap_version(self, neoforge_version: str) -> str:
        """Определяет версию BootstrapLauncher"""
        try:
            parts = neoforge_version.split('.')
            if len(parts) >= 3:
                build = int(parts[2])
                if build >= 215:
                    return "2.0.4"
                elif build >= 209:
                    return "2.0.2"
        except:
            pass
        return "2.0.2"

    def _get_securejarhandler_version(self, neoforge_version: str) -> str:
        """Определяет версию SecureJarHandler"""
        return "3.0.8"

    def _get_neoform_version(self, neoforge_version: str) -> str:
        """Определяет версию NeoForm"""
        # Примерная формула
        try:
            parts = neoforge_version.split('.')
            if len(parts) >= 3:
                build = int(parts[2])
                return f"20240808.{build}"
        except:
            pass
        return "20240808.144430"

    def _generate_libraries(self, neoforge_version: str, fml_version: str,
                            modlauncher_version: str, bootstrap_version: str,
                            securejarhandler_version: str) -> List[Dict]:
        """Генерирует список библиотек"""
        return [
            {"name": f"net.neoforged.fancymodloader:earlydisplay:{fml_version}",
             "url": "https://maven.neoforged.net/releases/"},
            {"name": f"net.neoforged.fancymodloader:loader:{fml_version}",
             "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.neoforged.accesstransformers:at-modlauncher:10.0.1",
             "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.neoforged:accesstransformers:10.0.1", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.neoforged:bus:8.0.5", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.neoforged:coremods:7.0.3", "url": "https://maven.neoforged.net/releases/"},
            {"name": f"cpw.mods:modlauncher:{modlauncher_version}", "url": "https://maven.neoforged.net/releases/"},
            {"name": f"cpw.mods:bootstraplauncher:{bootstrap_version}", "url": "https://maven.neoforged.net/releases/"},
            {"name": f"cpw.mods:securejarhandler:{securejarhandler_version}",
             "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.fabricmc:sponge-mixin:0.15.2+mixin.0.8.7", "url": "https://maven.neoforged.net/releases/"},
            {"name": f"net.neoforged:neoforge:{neoforge_version}", "url": "https://maven.creeperhost.net/"},
        ]

    def _generate_jvm_args(self, bootstrap_version: str, securejarhandler_version: str, modlauncher_version: str) -> \
    List[str]:
        """Генерирует JVM аргументы"""
        classpath_items = [
            f"cpw/mods/bootstraplauncher/{bootstrap_version}/bootstraplauncher-{bootstrap_version}.jar",
            f"cpw/mods/securejarhandler/{securejarhandler_version}/securejarhandler-{securejarhandler_version}.jar",
            "org/ow2/asm/asm-commons/9.8/asm-commons-9.8.jar",
            "org/ow2/asm/asm-util/9.8/asm-util-9.8.jar",
            "org/ow2/asm/asm-analysis/9.8/asm-analysis-9.8.jar",
            "org/ow2/asm/asm-tree/9.8/asm-tree-9.8.jar",
            "org/ow2/asm/asm/9.8/asm-9.8.jar",
        ]

        classpath = "${library_directory}/" + "${classpath_separator}${library_directory}/".join(classpath_items)

        return [
            "-Djava.net.preferIPv6Addresses=system",
            "-DignoreList=client-extra,${version_name}.jar",
            "-DlibraryDirectory=${library_directory}",
            "-p", classpath,
            "--add-modules", "ALL-MODULE-PATH",
            "--add-opens", "java.base/java.util.jar=cpw.mods.securejarhandler",
            "--add-opens", "java.base/java.lang.invoke=cpw.mods.securejarhandler",
            "--add-exports", "java.base/sun.security.util=cpw.mods.securejarhandler",
            "--add-exports", "jdk.naming.dns/com.sun.jndi.dns=java.naming"
        ]


# Кэш для скачанных JSON
_version_cache = {}


def get_neoforge_profile(minecraft_version: str, neoforge_version: str, minecraft_dir: str) -> Dict:
    """Основная функция для получения профиля NeoForge"""
    cache_key = f"{minecraft_version}_{neoforge_version}"
    if cache_key in _version_cache:
        return _version_cache[cache_key]

    generator = NeoForgeProfileGenerator()
    profile = generator.generate_profile(minecraft_version, neoforge_version, minecraft_dir)

    _version_cache[cache_key] = profile
    return profile