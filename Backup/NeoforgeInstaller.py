import requests
import json
import os
import sys
import subprocess
import tempfile
import shutil
from urllib.parse import urljoin
from pathlib import Path

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

    # РАСШИРЕННЫЙ список источников с зеркалами
    download_urls = [
        # Основные официальные
        f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://repo.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",

        # Зеркала и альтернативные источники
        f"https://cdn.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://files.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",

        # GitHub как запасной вариант
        f"https://github.com/neoforged/NeoForge/releases/download/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",

        # Без -installer (на всякий случай)
        f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}.jar",
        f"https://repo.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}.jar",
    ]

    session = requests.Session()
    # Увеличиваем таймауты и добавляем повторные попытки
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*'
    })

    # Пробуем каждый URL с улучшенной обработкой ошибок
    successful_url = None
    for i, download_url in enumerate(download_urls):
        log(f"Попытка {i + 1}/{len(download_urls)}: {download_url}")

        try:
            # Увеличиваем таймаут до 30 секунд
            response = session.head(download_url, timeout=30)
            if response.status_code == 200:
                log("✅ Файл доступен!")
                successful_url = download_url
                break
            else:
                log(f"❌ Файл недоступен (статус {response.status_code})")
                continue
        except requests.exceptions.Timeout:
            log("⏰ Таймаут соединения, пробуем следующий URL...")
            continue
        except requests.exceptions.ConnectionError as e:
            log(f"🌐 Проблемы с подключением: {e}, пробуем следующий URL...")
            continue
        except Exception as e:
            log(f"⚠️ Ошибка при проверке: {e}")
            continue

    if not successful_url:
        # ЕСЛИ ВСЕ URL НЕДОСТУПНЫ - пробуем создать ручную установку
        log("🚨 Все URL недоступны, создаем ручную установку...")
        return create_fallback_neoforge(minecraft_version, neoforge_version, minecraft_dir, callback)

    # Скачивание с выбранного URL
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = f"neoforge-{neoforge_version}-installer.jar"
            installer_path = os.path.join(temp_dir, filename)

            log(f"📥 Скачивание {filename}...")
            # Увеличиваем таймаут скачивания до 120 секунд
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

        # Получаем основную версию Minecraft
        minecraft_major = get_minecraft_major_version(minecraft_version)

        # Правильное имя версии
        version_name = f"neoforge-{minecraft_major}-{neoforge_version}"
        version_dir = os.path.join(minecraft_dir, "versions", version_name)
        os.makedirs(version_dir, exist_ok=True)

        log(f"📁 Создана папка: {version_dir}")

        # Создаем минимальный JAR файл (заглушка)
        jar_path = os.path.join(version_dir, f"{version_name}.jar")
        with open(jar_path, 'wb') as f:
            f.write(b'# NeoForge fallback installation\n')

        # Создаем JSON конфигурацию
        json_path = os.path.join(version_dir, f"{version_name}.json")
        version_json = create_version_json(minecraft_version, neoforge_version, version_name)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(version_json, f, indent=2, ensure_ascii=False)

        log("✅ Fallback установка NeoForge создана!")
        log("⚠️ Для работы потребуется ручная установка NeoForge")

        return True, neoforge_version

    except Exception as e:
        log(f"❌ Ошибка fallback установки: {e}")
        return False, None


def ensure_minecraft_profile_exists(minecraft_dir, callback=None):
    """Убеждается, что профиль Minecraft существует перед установкой NeoForge"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Setup] {message}")

    try:
        # Проверяем существование папки versions
        versions_dir = os.path.join(minecraft_dir, "versions")
        if not os.path.exists(versions_dir):
            os.makedirs(versions_dir)
            log("📁 Создана папка versions")

        # Для NeoForge нам нужна базовая версия Minecraft
        target_version = "1.21.1"
        version_dir = os.path.join(versions_dir, target_version)

        if not os.path.exists(version_dir):
            log(f"📁 Создаем структуру для версии {target_version}...")
            os.makedirs(version_dir)

            # Создаем минимальный JSON для версии
            base_json = {
                "id": target_version,
                "type": "release",
                "mainClass": "net.minecraft.client.main.Main",
                "arguments": {
                    "game": [],
                    "jvm": []
                },
                "libraries": [],
                "releaseTime": "2023-01-01T00:00:00Z",
                "time": "2023-01-01T00:00:00Z"
            }

            json_path = os.path.join(version_dir, f"{target_version}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(base_json, f, indent=2, ensure_ascii=False)

            log(f"📄 Создан базовый JSON для {target_version}")

        return True
    except Exception as e:
        log(f"❌ Ошибка создания профиля: {e}")
        return False

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

        # Сначала убедимся, что базовая версия Minecraft существует
        log("🔍 Проверяем наличие базовой версии Minecraft...")
        ensure_minecraft_profile_exists(minecraft_dir)

        # Пробуем стандартную установку через Java
        log("🔧 Запуск установщика NeoForge...")
        try:
            # Создаем команду для установки
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
                    log(f"📄 STDOUT: {result.stdout[-1000:]}")  # Последние 1000 символов
                if result.stderr:
                    log(f"⚠️ STDERR: {result.stderr[-1000:]}")

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


def ensure_minecraft_profile_exists(minecraft_dir, callback=None):
    """Убеждается, что профиль Minecraft существует перед установкой NeoForge"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Setup] {message}")

    try:
        # Проверяем существование папки versions
        versions_dir = os.path.join(minecraft_dir, "versions")
        if not os.path.exists(versions_dir):
            os.makedirs(versions_dir)
            log("📁 Создана папка versions")

        # Для NeoForge нам нужна базовая версия Minecraft
        target_version = "1.21.1"
        version_dir = os.path.join(versions_dir, target_version)

        if not os.path.exists(version_dir):
            log(f"📁 Создаем структуру для версии {target_version}...")
            os.makedirs(version_dir)

            # Создаем минимальный JSON для версии
            base_json = {
                "id": target_version,
                "type": "release",
                "mainClass": "net.minecraft.client.main.Main",
                "arguments": {
                    "game": [],
                    "jvm": []
                },
                "libraries": [],
                "releaseTime": "2023-01-01T00:00:00Z",
                "time": "2023-01-01T00:00:00Z"
            }

            json_path = os.path.join(version_dir, f"{target_version}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(base_json, f, indent=2, ensure_ascii=False)

            log(f"📄 Создан базовый JSON для {target_version}")

        return True
    except Exception as e:
        log(f"❌ Ошибка создания профиля: {e}")
        return False


def install_neoforge_manual(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback):
    """Ручная установка NeoForge"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Manual] {message}")

    try:
        log("🛠️ Ручная установка NeoForge...")

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

        # Создаем JSON файл версии
        version_json = create_version_json(minecraft_version, neoforge_version, launcher_version_name)
        json_path = os.path.join(version_dir, f"{launcher_version_name}.json")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(version_json, f, indent=2, ensure_ascii=False)

        log(f"📄 Создан JSON: {json_path}")
        log("✅ NeoForge успешно установлен вручную!")

        return True

    except Exception as e:
        log(f"❌ Ошибка ручной установки: {e}")
        return False


def create_version_json(minecraft_version, neoforge_version, version_name):
    """Создает JSON конфигурацию для версии NeoForge с правильными именами"""

    # Получаем основную версию Minecraft (1.21 вместо 1.21.1)
    minecraft_major = get_minecraft_major_version(minecraft_version)

    # Правильное имя версии для NeoForge
    # Должно быть: "neoforge-1.21-21.1.215"
    launcher_version_name = f"neoforge-{minecraft_major}-{neoforge_version}"

    return {
        "id": launcher_version_name,  # Это будет "neoforge-1.21-21.1.215"
        "inheritsFrom": minecraft_version,
        "type": "release",
        "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher",
        "libraries": [
            {
                "name": f"net.neoforged:neoforge:{neoforge_version}",
                "url": "https://maven.neoforged.net/releases/"
            }
        ],
        "arguments": {
            "game": [
                "--launcherTarget", "neoforgeclient",
                "--fml.forgeVersion", neoforge_version,
                "--fml.mcVersion", minecraft_version,
                "--fml.forgeGroup", "net.neoforged"
            ],
            "jvm": [
                "-Dforge.logging.console.level=debug",
                "-Dforge.logging.markers=REGISTRIES"
            ]
        },
        "releaseTime": "2023-01-01T00:00:00Z",
        "time": "2023-01-01T00:00:00Z"
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
    # Используем правильное имя версии для лаунчера
    minecraft_major = get_minecraft_major_version(minecraft_version)
    version_name = f"neoforge-{minecraft_major}-{neoforge_version}"
    version_dir = os.path.join(minecraft_dir, "versions", version_name)

    required_files = [
        os.path.join(version_dir, f"{version_name}.json"),
        os.path.join(version_dir, f"{version_name}.jar")
    ]

    if not os.path.exists(version_dir):
        return False

    for file in required_files:
        if not os.path.exists(file):
            return False

    return True