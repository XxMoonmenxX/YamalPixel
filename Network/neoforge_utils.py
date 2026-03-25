# Network/neoforge_utils.py
import requests
import json
import os
import re
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger("NeoForgeUtils")


class NeoForgeVersionFetcher:
    """Автоматический загрузчик версий библиотек NeoForge"""

    MAVEN_BASE = "https://maven.neoforged.net/releases/net/neoforged/neoforge"

    @staticmethod
    def get_version_json(neoforge_version: str) -> Optional[Dict]:
        """Загружает официальный JSON для версии NeoForge"""
        urls = [
            f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}.json",
            f"https://maven.creeperhost.net/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}.json",
            f"https://repo.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}.json",
        ]

        for url in urls:
            try:
                logger.debug(f"Trying to fetch: {url}")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.debug(f"Failed to fetch {url}: {e}")

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

        return versions

    @staticmethod
    def get_loader_versions_from_maven(minecraft_version: str) -> list[str]:
        """Получает доступные версии NeoForge из Maven метаданных"""
        try:
            # Пробуем получить через API
            api_url = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                versions = []
                for version in data.get("versions", []):
                    # Проверяем, подходит ли под майнкрафт версию
                    if version.startswith(minecraft_version.replace("1.", "")):
                        versions.append(version)
                return sorted(versions, reverse=True)
        except Exception as e:
            logger.warning(f"Failed to fetch from Maven API: {e}")

        # Fallback к статическому маппингу
        return NeoForgeVersionFetcher._get_fallback_versions(minecraft_version)

    @staticmethod
    def _get_fallback_versions(minecraft_version: str) -> list[str]:
        """Fallback маппинг версий"""
        version_map = {
            "1.21.1": ["21.1.219", "21.1.215", "21.1.209", "21.1.199", "21.1.186", "21.1.174"],
            "1.21": ["21.1.219", "21.1.215", "21.1.209"],
            "1.20.6": ["20.6.139", "20.6.138", "20.6.137"],
            "1.20.4": ["20.4.251", "20.4.237", "20.4.223"],
            "1.20.2": ["20.2.93", "20.2.86", "20.2.83"],
        }

        for key, versions in version_map.items():
            if minecraft_version.startswith(key):
                return versions

        return [f"{minecraft_version.replace('1.', '')}.0"]  # Очень грубый fallback


class NeoForgeProfileGenerator:
    """Генератор профилей NeoForge с актуальными версиями"""

    def __init__(self):
        self.cache = {}

    def generate_profile(self, minecraft_version: str, neoforge_version: str, minecraft_dir: str) -> Dict:
        """Генерирует профиль с правильными версиями библиотек"""

        # Пробуем загрузить официальный JSON
        version_json = NeoForgeVersionFetcher.get_version_json(neoforge_version)

        if version_json:
            logger.info(f"✅ Found official JSON for NeoForge {neoforge_version}")
            versions = NeoForgeVersionFetcher.extract_library_versions(version_json)
        else:
            logger.warning(f"⚠️ No official JSON for NeoForge {neoforge_version}, using fallback")
            versions = self._get_fallback_versions(neoforge_version)

        # Получаем версии библиотек
        fml_version = versions.get("fml", self._guess_fml_version(neoforge_version))
        modlauncher_version = versions.get("modlauncher", self._guess_modlauncher_version(neoforge_version))
        bootstrap_version = versions.get("bootstraplauncher", self._guess_bootstrap_version(neoforge_version))
        securejarhandler_version = versions.get("securejarhandler",
                                                self._guess_securejarhandler_version(neoforge_version))

        logger.info(f"Using FML: {fml_version}")
        logger.info(f"Using ModLauncher: {modlauncher_version}")
        logger.info(f"Using Bootstrap: {bootstrap_version}")

        # Генерируем библиотеки
        libraries = self._generate_libraries(
            neoforge_version, fml_version, modlauncher_version,
            bootstrap_version, securejarhandler_version
        )

        # Генерируем аргументы
        game_args = self._generate_game_args(neoforge_version, fml_version, minecraft_version)
        jvm_args = self._generate_jvm_args(
            bootstrap_version, securejarhandler_version, modlauncher_version
        )

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

    def _generate_libraries(self, neoforge_version: str, fml_version: str,
                            modlauncher_version: str, bootstrap_version: str,
                            securejarhandler_version: str) -> list:
        """Генерирует список библиотек"""

        # Базовый набор библиотек (можно расширять)
        libraries = [
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
            {"name": "net.neoforged:mergetool:2.0.0:api", "url": "https://maven.neoforged.net/releases/"},
            {"name": "com.electronwill.night-config:toml:3.8.3", "url": "https://maven.neoforged.net/releases/"},
            {"name": "com.electronwill.night-config:core:3.8.3", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.neoforged:JarJarSelector:0.4.1", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.neoforged:JarJarMetadata:0.4.1", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.apache.maven:maven-artifact:3.8.5", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.jodah:typetools:0.6.3", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.minecrell:terminalconsoleappender:1.3.0", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.fabricmc:sponge-mixin:0.15.2+mixin.0.8.7", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.openjdk.nashorn:nashorn-core:15.4", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.apache.commons:commons-lang3:3.14.0", "url": "https://libraries.minecraft.net/"},
            {"name": f"cpw.mods:bootstraplauncher:{bootstrap_version}", "url": "https://maven.neoforged.net/releases/"},
            {"name": f"cpw.mods:securejarhandler:{securejarhandler_version}",
             "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.ow2.asm:asm-commons:9.8", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.ow2.asm:asm-util:9.8", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.ow2.asm:asm-analysis:9.8", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.ow2.asm:asm-tree:9.8", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.ow2.asm:asm:9.8", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.neoforged:JarJarFileSystems:0.4.1", "url": "https://maven.neoforged.net/releases/"},
            {"name": "net.sf.jopt-simple:jopt-simple:5.0.4", "url": "https://libraries.minecraft.net/"},
            {"name": "org.slf4j:slf4j-api:2.0.9", "url": "https://libraries.minecraft.net/"},
            {"name": "org.antlr:antlr4-runtime:4.13.1", "url": "https://maven.neoforged.net/releases/"},
            {"name": "com.mojang:logging:1.2.7", "url": "https://libraries.minecraft.net/"},
            {"name": "org.apache.logging.log4j:log4j-slf4j2-impl:2.22.1", "url": "https://libraries.minecraft.net/"},
            {"name": "org.apache.logging.log4j:log4j-core:2.22.1", "url": "https://libraries.minecraft.net/"},
            {"name": "org.apache.logging.log4j:log4j-api:2.22.1", "url": "https://libraries.minecraft.net/"},
            {"name": "org.jline:jline-reader:3.20.0", "url": "https://maven.neoforged.net/releases/"},
            {"name": "org.jline:jline-terminal:3.20.0", "url": "https://maven.neoforged.net/releases/"},
            {"name": "commons-io:commons-io:2.15.1", "url": "https://libraries.minecraft.net/"},
            {"name": "net.minecraftforge:srgutils:0.4.15", "url": "https://maven.neoforged.net/releases/"},
            {"name": "com.google.guava:guava:32.1.2-jre", "url": "https://libraries.minecraft.net/"},
            {"name": "com.google.guava:failureaccess:1.0.1", "url": "https://libraries.minecraft.net/"},
            {"name": "com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava",
             "url": "https://libraries.minecraft.net/"},
            {"name": "com.google.code.findbugs:jsr305:3.0.2", "url": "https://libraries.minecraft.net/"},
            {"name": "org.checkerframework:checker-qual:3.33.0", "url": "https://libraries.minecraft.net/"},
            {"name": "com.google.errorprone:error_prone_annotations:2.18.0", "url": "https://libraries.minecraft.net/"},
            {"name": "com.google.j2objc:j2objc-annotations:2.8", "url": "https://libraries.minecraft.net/"},
            {"name": "com.google.code.gson:gson:2.10.1", "url": "https://libraries.minecraft.net/"},
            {"name": "org.codehaus.plexus:plexus-utils:3.3.0", "url": "https://maven.neoforged.net/releases/"},
            {"name": "com.machinezoo.noexception:noexception:1.7.1", "url": "https://maven.neoforged.net/releases/"},
            {"name": f"net.neoforged:neoforge:{neoforge_version}", "url": "https://maven.creeperhost.net/"},
        ]

        return libraries

    def _generate_game_args(self, neoforge_version: str, fml_version: str, minecraft_version: str) -> list:
        """Генерирует game аргументы"""
        return [
            "--fml.neoForgeVersion", neoforge_version,
            "--fml.fmlVersion", fml_version,
            "--fml.mcVersion", minecraft_version,
            "--fml.neoFormVersion", "20240808.144430",
            "--launchTarget", "forgeclient"
        ]

    def _generate_jvm_args(self, bootstrap_version: str, securejarhandler_version: str,
                           modlauncher_version: str) -> list:
        """Генерирует JVM аргументы"""

        classpath_items = [
            f"cpw/mods/bootstraplauncher/{bootstrap_version}/bootstraplauncher-{bootstrap_version}.jar",
            f"cpw/mods/securejarhandler/{securejarhandler_version}/securejarhandler-{securejarhandler_version}.jar",
            "org/ow2/asm/asm-commons/9.8/asm-commons-9.8.jar",
            "org/ow2/asm/asm-util/9.8/asm-util-9.8.jar",
            "org/ow2/asm/asm-analysis/9.8/asm-analysis-9.8.jar",
            "org/ow2/asm/asm-tree/9.8/asm-tree-9.8.jar",
            "org/ow2/asm/asm/9.8/asm-9.8.jar",
            "net/neoforged/JarJarFileSystems/0.4.1/JarJarFileSystems-0.4.1.jar"
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

    def _guess_fml_version(self, neoforge_version: str) -> str:
        """Угадывает версию FML на основе версии NeoForge"""
        parts = neoforge_version.split('.')
        if len(parts) >= 3:
            try:
                build = int(parts[2])
                # Примерная формула: FML версия = 4.0.(build - 173)
                # Это приближение, для точности лучше использовать маппинг
                fml_build = max(1, build - 173)
                return f"4.0.{fml_build}"
            except ValueError:
                pass
        return "4.0.47"

    def _guess_modlauncher_version(self, neoforge_version: str) -> str:
        """Угадывает версию ModLauncher"""
        if "21.1." in neoforge_version:
            parts = neoforge_version.split('.')
            if len(parts) >= 3:
                try:
                    build = int(parts[2])
                    if build >= 215:
                        return "11.0.7"
                    elif build >= 200:
                        return "11.0.5"
                    elif build >= 174:
                        return "11.0.5"
                    elif build >= 158:
                        return "11.0.3"
                    elif build >= 142:
                        return "11.0.3"
                    elif build >= 125:
                        return "11.0.3"
                except ValueError:
                    pass
        return "11.0.5"

    def _guess_bootstrap_version(self, neoforge_version: str) -> str:
        """Угадывает версию BootstrapLauncher"""
        if "21.1." in neoforge_version:
            parts = neoforge_version.split('.')
            if len(parts) >= 3:
                try:
                    build = int(parts[2])
                    if build >= 215:
                        return "2.0.4"
                    elif build >= 209:
                        return "2.0.2"
                except ValueError:
                    pass
        return "2.0.2"

    def _guess_securejarhandler_version(self, neoforge_version: str) -> str:
        """Угадывает версию SecureJarHandler"""
        if "21.1." in neoforge_version:
            return "3.0.8"
        return "3.0.8"


# Кэш для скачанных JSON
_version_cache = {}


def get_neoforge_profile(minecraft_version: str, neoforge_version: str, minecraft_dir: str) -> Dict:
    """Основная функция для получения профиля NeoForge"""

    # Проверяем кэш
    cache_key = f"{minecraft_version}_{neoforge_version}"
    if cache_key in _version_cache:
        return _version_cache[cache_key]

    generator = NeoForgeProfileGenerator()
    profile = generator.generate_profile(minecraft_version, neoforge_version, minecraft_dir)

    # Сохраняем в кэш
    _version_cache[cache_key] = profile

    return profile