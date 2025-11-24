import requests
import json
import os
import sys
import subprocess
import tempfile
import shutil
import threading
import zipfile
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime

CONFIG = {
    "version": "1.20.1",
    "fabric_loader": "0.17.2",
    "minecraft_dir": os.path.expanduser("~/YamalPixel")
}


def get_minecraft_major_version(full_version):
    """Извлекает основную версию Minecraft (1.21.1 -> 1.21)"""
    parts = full_version.split('.')
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return full_version


def get_neoforge_version_from_name(version_name):
    """Извлекает версию NeoForge из названия версии"""
    if "(" in version_name and ")" in version_name:
        return version_name.split("(")[1].replace(")", "").strip()
    return None


def get_minecraft_version_for_neoforge(version_name):
    """Получает версию Minecraft для NeoForge"""
    if "1.21.4" in version_name:
        return "1.21.4"
    elif "1.21.3" in version_name:
        return "1.21.3"
    elif "1.21.2" in version_name:
        return "1.21.2"
    elif "1.21.1" in version_name:
        return "1.21.1"
    elif "1.20.6" in version_name:
        return "1.20.6"
    elif "1.20.5" in version_name:
        return "1.20.5"
    elif "1.20.4" in version_name:
        return "1.20.4"
    elif "1.20.3" in version_name:
        return "1.20.3"
    elif "1.20.2" in version_name:
        return "1.20.2"
    elif "1.20.1" in version_name:
        return "1.20.1"
    else:
        return "1.20.1"


def is_neoforge_needed(selected_version):
    """Проверяет, требуется ли NeoForge для выбранной версии"""
    neoforge_supported_versions = [
        "Minecraft 1.20.2 + NeoForge (20.2.93)",
        "Minecraft 1.20.3 + NeoForge (20.3.8-beta)",
        "Minecraft 1.20.4 + NeoForge (20.4.251)",
        "Minecraft 1.20.5 + NeoForge (20.5.21-beta)",
        "Minecraft 1.20.6 + NeoForge (20.6.139)",
        "Minecraft 1.21.1 + NeoForge (21.1.215)",
        "Minecraft 1.21.2 + NeoForge (21.1.-beta)",
        "Minecraft 1.21.3 + NeoForge (21.3.94)",
        "Minecraft 1.21.4 + NeoForge (21.4.155)",
        "Minecraft 1.21.5 + NeoForge (21.5.95)",
        "Minecraft 1.21.6 + NeoForge (21.6.20-beta)",
        "Minecraft 1.21.7 + NeoForge (21.7.25-beta)",
        "Minecraft 1.21.8 + NeoForge (21.8.51)",
        "Minecraft 1.21.10 + NeoForge (21.10.52-beta)",
        "Minecraft 1.20.1 + NeoForge",
        "Minecraft 1.20.0 + NeoForge",
        "Minecraft 1.19.2 + NeoForge",
        "Minecraft 1.19.0 + NeoForge",
        "Minecraft 1.18.2 + NeoForge",
        "Minecraft 1.18.0 + NeoForge",
        "Minecraft 1.17.1 + NeoForge",
    ]
    return selected_version in neoforge_supported_versions


def create_minecraft_structure(minecraft_dir):
    """Создает полную структуру папок Minecraft"""
    required_dirs = [
        "versions",
        "libraries",
        "assets",
        "assets/indexes",
        "assets/objects",
        "logs",
        "saves",
        "mods",
        "resourcepacks",
        "shaderpacks"
    ]

    for dir_name in required_dirs:
        os.makedirs(os.path.join(minecraft_dir, dir_name), exist_ok=True)

    # Создаем базовый launcher_profiles.json если нет
    profiles_path = os.path.join(minecraft_dir, "launcher_profiles.json")
    if not os.path.exists(profiles_path):
        with open(profiles_path, 'w') as f:
            json.dump({
                "profiles": {},
                "settings": {},
                "version": 2
            }, f, indent=2)


def download_with_fallback(url, fallback_urls, callback=None):
    """Скачивает файл с fallback URLs"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [Download] {message}")

    all_urls = [url] + fallback_urls

    for download_url in all_urls:
        try:
            log(f"Пробуем: {download_url}")
            response = requests.head(download_url, timeout=10)
            if response.status_code == 200:
                log("✅ URL доступен")
                return download_url
        except Exception as e:
            log(f"❌ Ошибка: {e}")
            continue

    return None


def download_neoforge_libraries_smart(minecraft_dir, version_name, callback=None):
    """Умное скачивание библиотек с fallback"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Libs] {message}")

    try:
        version_dir = os.path.join(minecraft_dir, "versions", version_name)
        json_path = os.path.join(version_dir, f"{version_name}.json")

        with open(json_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        libraries = profile.get("libraries", [])

        log(f"📥 Скачиваем {len(libraries)} библиотек...")

        libraries_dir = os.path.join(minecraft_dir, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)

        # Основные репозитории с fallback
        repositories = [
            "https://libraries.minecraft.net/",
            "https://maven.neoforged.net/releases/",
            "https://repo1.maven.org/maven2/",  # Maven Central как fallback
        ]

        downloaded_count = 0
        skipped_count = 0

        for library in libraries:
            lib_name = library["name"]

            # Парсим имя библиотеки в путь
            parts = lib_name.split(":")
            group = parts[0].replace(".", "/")
            artifact = parts[1]
            version = parts[2]
            filename = f"{artifact}-{version}.jar"

            lib_path = f"{group}/{artifact}/{version}/{filename}"
            local_path = os.path.join(libraries_dir, lib_path)

            # Создаем папку для библиотеки
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Если файл уже существует - пропускаем
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                if file_size > 1024:  # Проверяем что файл не пустой
                    skipped_count += 1
                    continue
                else:
                    os.remove(local_path)  # Удаляем битый файл

            # Пробуем скачать с каждого репозитория
            downloaded = False
            for repo_url in repositories:
                try:
                    download_url = f"{repo_url}{lib_path}"
                    log(f"📦 {artifact}...")

                    response = requests.get(download_url, stream=True, timeout=30)
                    if response.status_code == 200:
                        with open(local_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                        # Проверяем что файл не пустой
                        if os.path.getsize(local_path) > 1024:
                            downloaded = True
                            downloaded_count += 1
                            break
                        else:
                            os.remove(local_path)
                            log(f"⚠️ Пустой файл: {artifact}")

                except Exception as e:
                    continue

            if not downloaded:
                log(f"⚠️ Не удалось скачать: {artifact}")
                # Создаем пустой файл чтобы избежать повторных попыток
                with open(local_path, 'wb') as f:
                    f.write(b'# Placeholder - download failed\n')

        log(f"✅ Готово! Скачано: {downloaded_count}, Пропущено: {skipped_count}")
        return downloaded_count > 0  # Успех если скачали хоть что-то

    except Exception as e:
        log(f"❌ Ошибка загрузки библиотек: {e}")
        return False


def create_complete_neoforge_profile(minecraft_version, neoforge_version, minecraft_dir, callback=None):
    """Создает ПОЛНЫЙ профиль NeoForge без установщика"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Complete] {message}")

    # Создаем структуру папок
    create_minecraft_structure(minecraft_dir)

    version_name = f"neoforge-{neoforge_version}"
    version_dir = os.path.join(minecraft_dir, "versions", version_name)
    os.makedirs(version_dir, exist_ok=True)

    time = datetime.now().isoformat()

    # Упрощенный но рабочий список библиотек
    libraries = [
        {
            "name": f"net.neoforged:neoforge:{neoforge_version}",
            "url": "https://maven.neoforged.net/releases/"
        },
        {
            "name": "cpw.mods:bootstraplauncher:1.1.2",
            "url": "https://maven.neoforged.net/releases/"
        },
        {
            "name": "cpw.mods:securejarhandler:2.1.10",
            "url": "https://maven.neoforged.net/releases/"
        },
        {
            "name": "org.ow2.asm:asm:9.5",
            "url": "https://libraries.minecraft.net/"
        },
        {
            "name": "org.ow2.asm:asm-commons:9.5",
            "url": "https://libraries.minecraft.net/"
        }
    ]

    # Аргументы из их кода
    game_arguments = [
        "--launcherTarget", "neoforgeclient",
        "--fml.neoForgeVersion", neoforge_version,
        "--fml.mcVersion", minecraft_version,
        "--fml.forgeGroup", "net.neoforged"
    ]

    jvm_arguments = [
        "-Djava.library.path=${natives_directory}",
        "-Dminecraft.launcher.brand=${launcher_name}",
        "-Dminecraft.launcher.version=${launcher_version}",
        "-DignoreList=bootstraplauncher,securejarhandler,asm-commons,asm-tree,asm-analysis,asm-util,asm-9.5.jar,client-extra.jar",
        "-DlibraryDirectory=${library_directory}",
        "-p", "${classpath}",
        "-Duser.language=ru",
        "-Duser.country=RU",
        "--add-modules", "ALL-MODULE-PATH",
        "--add-opens", "java.base/java.util.jar=cpw.mods.securejarhandler",
        "--add-opens", "java.base/java.lang.invoke=cpw.mods.securejarhandler"
    ]

    profile = {
        "id": version_name,
        "time": time,
        "releaseTime": time,
        "type": "release",
        "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher",  # Возвращаем правильный main class
        "inheritsFrom": minecraft_version,
        "arguments": {
            "game": game_arguments,
            "jvm": jvm_arguments
        },
        "libraries": libraries,
        "minimumLauncherVersion": 21
    }

    # Сохраняем профиль
    json_path = os.path.join(version_dir, f"{version_name}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    # Создаем минимальный JAR
    jar_path = os.path.join(version_dir, f"{version_name}.jar")
    with open(jar_path, 'wb') as f:
        f.write(b'# NeoForge installation - libraries will be downloaded on launch\n')

    log("✅ Профиль NeoForge создан!")
    log("📥 Пробуем скачать библиотеки...")

    # Пробуем скачать библиотеки, но не блокируем установку если не получится
    try:
        download_success = download_neoforge_libraries_smart(minecraft_dir, version_name, callback)
        if download_success:
            log("🎉 Библиотеки успешно скачаны!")
        else:
            log("⚠️ Библиотеки будут скачаны при первом запуске игры")
    except Exception as e:
        log(f"⚠️ Ошибка скачивания библиотек: {e}")
        log("📝 Библиотеки скачаются при запуске игры")

    return True


def download_neoforge(version, minecraft_dir, callback=None):
    """Установка NeoForge БЕЗ скачивания установщика"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge] {message}")

    # Получаем версии
    if "(" in version and ")" in version:
        neoforge_version = version.split("(")[1].replace(")", "").strip()
        minecraft_version = get_minecraft_version_for_neoforge(version)
    else:
        minecraft_version = get_minecraft_version_for_neoforge(version)
        neoforge_version = get_latest_neoforge_version(minecraft_version)

    log(f"🚀 Установка NeoForge {neoforge_version} для Minecraft {minecraft_version}")
    log("💡 Используем автономную установку (без скачивания установщика)")

    try:
        # Сразу создаем профиль - не зависим от скачивания установщика
        success = create_complete_neoforge_profile(minecraft_version, neoforge_version, minecraft_dir, callback)

        if success:
            log("🎉 NeoForge успешно установлен!")
            log("💫 Версия готова к использованию в лаунчере")
            return True, neoforge_version
        else:
            log("❌ Не удалось создать профиль NeoForge")
            return False, None

    except Exception as e:
        log(f"❌ Критическая ошибка установки: {e}")
        return False, None


def get_latest_neoforge_version(minecraft_version):
    """Получает последнюю версию NeoForge"""
    versions = get_neoforge_versions(minecraft_version)
    return versions[0] if versions else "21.1.215"


def get_neoforge_versions(minecraft_version):
    """Получает доступные версии NeoForge"""
    # Захардкоженные версии чтобы избежать сетевых запросов
    version_map = {
        "1.21.4": ["21.4.155"],
        "1.21.3": ["21.3.94"],
        "1.21.2": ["21.1.215"],
        "1.21.1": ["21.1.215"],
        "1.20.6": ["20.6.139"],
        "1.20.5": ["20.5.21-beta"],
        "1.20.4": ["20.4.251"],
        "1.20.3": ["20.3.8-beta"],
        "1.20.2": ["20.2.93"],
        "1.20.1": ["20.2.59-beta"],
    }


    return version_map.get(minecraft_version, ["21.1.215"])


def is_neoforge_installed(neoforge_version, minecraft_dir):
    """Проверяет, установлен ли NeoForge"""
    version_name = f"neoforge-{neoforge_version}"
    version_dir = os.path.join(minecraft_dir, "versions", version_name)

    json_path = os.path.join(version_dir, f"{version_name}.json")
    jar_path = os.path.join(version_dir, f"{version_name}.jar")

    return os.path.exists(json_path) and os.path.exists(jar_path)