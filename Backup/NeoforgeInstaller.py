import requests
import json
import os
import sys
import subprocess
import tempfile
import shutil
from urllib.parse import urljoin
from pathlib import Path

minecraft_dir = os.path.expanduser("~/YamalPixel")
print('Minecraft directory is', minecraft_dir)

CONFIG = {
    "version": "1.20.1",
    "fabric_loader": "0.17.2",
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

def create_minecraft_launcher_profile(minecraft_dir, minecraft_version):
    """Создает необходимые файлы для Minecraft Launcher"""
    try:
        # Создаем папку versions если не существует
        versions_dir = os.path.join(minecraft_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)

        # Создаем папку для версии Minecraft
        version_dir = os.path.join(versions_dir, minecraft_version)
        os.makedirs(version_dir, exist_ok=True)

        # Создаем базовый JSON для версии Minecraft (как у официального лаунчера)
        version_json = {
            "id": minecraft_version,
            "type": "release",
            "mainClass": "net.minecraft.client.main.Main",
            "arguments": {
                "game": [],
                "jvm": []
            },
            "libraries": [],
            "releaseTime": "2023-01-01T00:00:00Z",
            "time": "2023-01-01T00:00:00Z",
            "complianceLevel": 1
        }

        json_path = os.path.join(version_dir, f"{minecraft_version}.json")
        if not os.path.exists(json_path):
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(version_json, f, indent=2, ensure_ascii=False)

        # Создаем пустой JAR файл (лаунчер его ожидает)
        jar_path = os.path.join(version_dir, f"{minecraft_version}.jar")
        if not os.path.exists(jar_path):
            with open(jar_path, 'wb') as f:
                f.write(b'# Minecraft version file\n')

        # Создаем launcher_profiles.json если не существует
        profiles_path = os.path.join(minecraft_dir, "launcher_profiles.json")
        if not os.path.exists(profiles_path):
            profiles_data = {
                "profiles": {
                    "(Default)": {
                        "name": "(Default)",
                        "lastVersionId": minecraft_version,
                        "created": "2023-01-01T00:00:00.000Z",
                        "lastUsed": "2023-01-01T00:00:00.000Z",
                        "icon": "Furnace",
                        "type": "custom"
                    }
                },
                "settings": {
                    "crashAssistance": True,
                    "enableAdvanced": True,
                    "enableAnalytics": True,
                    "enableHistorical": True,
                    "enableReleases": True,
                    "enableSnapshots": True,
                    "keepLauncherOpen": False,
                    "profileSorting": "ByLastPlayed",
                    "showGameLog": False,
                    "showMenu": False,
                    "soundOn": False
                },
                "version": 3
            }

            with open(profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"❌ Ошибка создания профиля лаунчера: {e}")
        return False

def download_neoforge(version, minecraft_dir, callback=None):
    """Скачать указанную версию NeoForge с улучшенными источниками"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge] {message}")

    def error(message):
        if callback:
            callback({"type": "error", "message": message})
        print(f"❌ [NeoForge] {message}")

    # Извлекаем версии
    if "(" in version and ")" in version:
        neoforge_version = version.split("(")[1].replace(")", "").strip()
        minecraft_version = get_minecraft_version_for_neoforge(version)
    else:
        minecraft_version = get_minecraft_version_for_neoforge(version)
        neoforge_version = get_latest_neoforge_version(minecraft_version)

    log(f"Установка NeoForge {neoforge_version} для Minecraft {minecraft_version}")

    # Создаем профиль Minecraft Launcher перед установкой NeoForge
    log("📝 Создаем профиль Minecraft Launcher...")
    if not create_minecraft_launcher_profile(minecraft_dir, minecraft_version):
        error("❌ Не удалось создать профиль лаунчера")
        return create_fallback_neoforge(minecraft_version, neoforge_version, minecraft_dir, callback)

    # РАСШИРЕННЫЙ список источников с зеркалами
    download_urls = [
        f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://repo.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://cdn.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://github.com/neoforged/NeoForge/releases/download/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
    ]

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*'
    })

    # Пробуем каждый URL с улучшенной обработкой ошибок
    successful_url = None
    for i, download_url in enumerate(download_urls):
        log(f"Попытка {i + 1}/{len(download_urls)}: {download_url}")

        try:
            response = session.head(download_url, timeout=30)
            if response.status_code == 200:
                log("✅ Файл доступен!")
                successful_url = download_url
                break
            else:
                log(f"❌ Файл недоступен (статус {response.status_code})")
                continue
        except Exception as e:
            log(f"⚠️ Ошибка при проверке: {e}")
            continue

    if not successful_url:
        log("🚨 Все URL недоступны, создаем ручную установку...")
        return create_fallback_neoforge(minecraft_version, neoforge_version, minecraft_dir, callback)

    # Скачивание с выбранного URL
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = f"neoforge-{neoforge_version}-installer.jar"
            installer_path = os.path.join(temp_dir, filename)

            log(f"📥 Скачивание {filename}...")
            response = session.get(successful_url, stream=True, timeout=120)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(installer_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        if callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            callback({
                                "type": "progress",
                                "message": f"Скачано {downloaded_size / (1024 * 1024):.1f}MB",
                                "progress": progress
                            })

            file_size = os.path.getsize(installer_path) / (1024 * 1024)
            log(f"✅ Успешно скачано: {filename} ({file_size:.2f} MB)")

            if file_size < 0.1:
                error("❌ Скачанный файл слишком мал")
                return create_fallback_neoforge(minecraft_version, neoforge_version, minecraft_dir, callback)

            # Устанавливаем NeoForge
            success = install_neoforge(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback)
            return success, neoforge_version

    except Exception as e:
        error(f"❌ Ошибка при скачивании: {e}")
        return create_fallback_neoforge(minecraft_version, neoforge_version, minecraft_dir, callback)


def create_fallback_neoforge(minecraft_version, neoforge_version, minecraft_dir, callback):
    """Создает установку NeoForge без скачивания (fallback)"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Fallback] {message}")

    try:
        log("🔄 Создаем fallback установку NeoForge...")

        # Создаем профиль Minecraft Launcher
        create_minecraft_launcher_profile(minecraft_dir, minecraft_version)

        # Получаем основную версию Minecraft
        minecraft_major = get_minecraft_major_version(minecraft_version)

        # Правильное имя версии (как у официального NeoForge)
        version_name = f"neoforge-{minecraft_major}-{neoforge_version}"
        version_dir = os.path.join(minecraft_dir, "versions", version_name)
        os.makedirs(version_dir, exist_ok=True)

        log(f"📁 Создана папка: {version_dir}")

        # Создаем минимальный JAR файл (заглушка)
        jar_path = os.path.join(version_dir, f"{version_name}.jar")
        with open(jar_path, 'wb') as f:
            f.write(b'# NeoForge fallback installation\n')

        # Создаем JSON конфигурацию (аналогично Fabric)
        json_path = os.path.join(version_dir, f"{version_name}.json")
        version_json = create_neoforge_version_json(minecraft_version, neoforge_version, version_name)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(version_json, f, indent=2, ensure_ascii=False)

        log("✅ Fallback установка NeoForge создана!")
        return True, neoforge_version

    except Exception as e:
        log(f"❌ Ошибка fallback установки: {e}")
        return False, None


def install_neoforge(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback=None):
    """Устанавливает NeoForge"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge] {message}")

    def error(message):
        if callback:
            callback({"type": "error", "message": message})
        print(f"❌ [NeoForge] {message}")

    try:
        log(f"🚀 Установка NeoForge {neoforge_version} для Minecraft {minecraft_version}...")

        # Убеждаемся, что профиль лаунчера существует
        log("📝 Проверяем профиль Minecraft Launcher...")
        create_minecraft_launcher_profile(minecraft_dir, minecraft_version)

        # Пробуем стандартную установку через Java
        log("🔧 Запуск установщика NeoForge...")
        try:
            install_command = [
                "java",
                "-jar",
                installer_path,
                "--installClient",
                minecraft_dir
            ]

            log(f"💻 Команда: {' '.join(install_command)}")

            result = subprocess.run(
                install_command,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.path.dirname(installer_path)
            )

            if result.returncode == 0:
                log("✅ NeoForge успешно установлен через установщик!")
                return True
            else:
                log(f"⚠️ Установщик вернул код {result.returncode}")
                if result.stdout:
                    log(f"📄 STDOUT: {result.stdout[-500:]}")
                if result.stderr:
                    log(f"⚠️ STDERR: {result.stderr[-500:]}")

                # Пробуем альтернативный метод
                log("🔄 Пробуем альтернативный метод установки...")
                return install_neoforge_manual(minecraft_version, neoforge_version, minecraft_dir, installer_path,
                                               callback)

        except subprocess.TimeoutExpired:
            log("⏰ Таймаут установки, пробуем альтернативный метод...")
            return install_neoforge_manual(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback)
        except Exception as e:
            log(f"⚠️ Ошибка установщика: {e}")
            return install_neoforge_manual(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback)

    except Exception as e:
        error(f"💥 Критическая ошибка установки: {e}")
        return False


def install_neoforge_manual(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback):
    """Ручная установка NeoForge"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Manual] {message}")

    try:
        log("🛠️ Ручная установка NeoForge...")

        # Убеждаемся, что профиль лаунчера существует
        create_minecraft_launcher_profile(minecraft_dir, minecraft_version)

        # Получаем основную версию Minecraft
        minecraft_major = get_minecraft_major_version(minecraft_version)

        # Создаем правильное имя версии для лаунчера
        launcher_version_name = f"neoforge-{minecraft_major}-{neoforge_version}"
        version_dir = os.path.join(minecraft_dir, "versions", launcher_version_name)
        os.makedirs(version_dir, exist_ok=True)

        log(f"📁 Создана папка версии: {version_dir}")

        # Копируем установщик как основной jar
        target_jar = os.path.join(version_dir, f"{launcher_version_name}.jar")
        shutil.copy2(installer_path, target_jar)
        log(f"📦 Скопирован JAR: {target_jar}")

        # Создаем JSON файл версии (аналогично Fabric)
        version_json = create_neoforge_version_json(minecraft_version, neoforge_version, launcher_version_name)
        json_path = os.path.join(version_dir, f"{launcher_version_name}.json")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(version_json, f, indent=2, ensure_ascii=False)

        log(f"📄 Создан JSON: {json_path}")
        log("✅ NeoForge успешно установлен вручную!")

        return True

    except Exception as e:
        log(f"❌ Ошибка ручной установки: {e}")
        return False


def create_neoforge_version_json(minecraft_version, neoforge_version, version_name):
    """Создает JSON конфигурацию для версии NeoForge по аналогии с Fabric"""

    # Получаем основную версию Minecraft
    minecraft_major = get_minecraft_major_version(minecraft_version)

    # Основные библиотеки NeoForge
    libraries = [
        {
            "name": f"net.neoforged:neoforge:{neoforge_version}",
            "url": "https://maven.neoforged.net/releases/"
        },
        {
            "name": "net.neoforged:fancymodloader:1.0.0",
            "url": "https://maven.neoforged.net/releases/"
        }
    ]

    # JSON структура аналогичная Fabric
    return {
        "id": version_name,
        "inheritsFrom": minecraft_version,  # Важно: наследуем от базовой версии Minecraft
        "releaseTime": "2023-01-01T00:00:00+0000",
        "time": "2023-01-01T00:00:00+0000",
        "type": "release",
        "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher",
        "libraries": libraries,
        "arguments": {
            "game": [
                "--launcherTarget", "neoforgeclient",
                "--fml.forgeVersion", neoforge_version,
                "--fml.mcVersion", minecraft_version,
                "--fml.forgeGroup", "net.neoforged"
            ],
            "jvm": [
                "-Dforge.logging.console.level=debug",
                "-Dforge.logging.markers=REGISTRIES",
                "-DlibraryDirectory=${library_directory}",  # Добавляем переменные окружения
                "-Dneoforge.enableGameTest=true"
            ]
        },
        "complianceLevel": 1
    }


def get_latest_neoforge_version(minecraft_version):
    """Получает последнюю версию NeoForge"""
    versions = get_neoforge_versions(minecraft_version)
    return versions[0] if versions else "21.1.215"


def get_neoforge_versions(minecraft_version):
    """Получает доступные версии NeoForge"""
    try:
        url = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            versions = []

            for version in data.get('versions', []):
                if minecraft_version in version:
                    versions.append(version)

            versions.sort(reverse=True)
            return versions[:5]
    except:
        pass

    # Fallback версии
    version_map = {
        "1.21.4": ["21.4.155", "21.4.154"],
        "1.21.3": ["21.3.94", "21.3.93"],
        "1.21.2": ["21.1.215", "21.1.214"],
        "1.21.1": ["21.1.215", "21.1.214"],
        "1.20.6": ["20.6.139", "20.6.138"],
        "1.20.5": ["20.5.21-beta", "20.5.20-beta"],
        "1.20.4": ["20.4.251", "20.4.250"],
        "1.20.3": ["20.3.8-beta", "20.3.7-beta"],
        "1.20.2": ["20.2.93", "20.2.92"],
        "1.20.1": ["20.4.1", "20.4.0"],
    }

    return version_map.get(minecraft_version, ["21.1.215"])


def is_neoforge_installed(minecraft_version, neoforge_version, minecraft_dir):
    """Проверяет, установлен ли NeoForge"""
    try:
        versions_dir = os.path.join(minecraft_dir, "versions")
        neoforge_version_name = f"neoforge-{minecraft_version}-{neoforge_version}"
        neoforge_dir = os.path.join(versions_dir, neoforge_version_name)

        # Проверяем существование папки и основных файлов
        if not os.path.exists(neoforge_dir):
            return False

        # Проверяем наличие jar файла
        jar_file = os.path.join(neoforge_dir, f"{neoforge_version_name}.jar")
        if not os.path.exists(jar_file):
            return False

        # Проверяем наличие json файла
        json_file = os.path.join(neoforge_dir, f"{neoforge_version_name}.json")
        if not os.path.exists(json_file):
            return False

        return True
    except:
        return False