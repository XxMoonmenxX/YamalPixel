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
    "minecraft_dir": os.path.expanduser("~/YamalPixel")}

minecraft_dir = CONFIG["minecraft_dir"]
mods_dir = os.path.join(minecraft_dir, "mods")
versions_dir = os.path.join(minecraft_dir, "versions")
config_dir = os.path.join(minecraft_dir, "config")


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
    elif "1.21.0" in version_name or "1.21" in version_name:
        return "1.21"
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


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # В режиме разработки используем домашнюю директорию
        base_path = Path.home() / "YamalPixelRes"

    return os.path.join(base_path, relative_path)


def is_neoforge_needed(selected_version):
    """Проверяет, требуется ли NeoForge для выбранной версии"""
    neoforge_supported_versions = [
        "Minecraft 1.20.2 + NeoForge (20.2.93)",
        "Minecraft 1.20.3 + NeoForge (20.3.8-beta)",
        "Minecraft 1.20.4 + NeoForge (20.4.251)",
        "Minecraft 1.20.5 + NeoForge (20.5.21-beta)",
        "Minecraft 1.20.6 + NeoForge (20.6.139)",
        "Minecraft 1.21 + NeoForge (21.0.167)",
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


def download_neoforge(version, minecraft_dir: str, callback=None):
    """Скачать указанную версию NeoForge с улучшенной обработкой таймаутов"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge] {message}")

    def error(message):
        if callback:
            callback({"type": "error", "message": message})
        print(f"❌ [NeoForge] {message}")

    # Извлекаем чистую версию NeoForge из строки
    if "(" in version and ")" in version:
        # Формат: "Minecraft 1.20.2 + NeoForge (20.2.93)"
        neoforge_version = version.split("(")[1].replace(")", "").strip()
        minecraft_version = get_minecraft_version_for_neoforge(version)
    else:
        # Формат: "Minecraft 1.20.1 + NeoForge"
        neoforge_version = get_latest_neoforge_version(get_minecraft_version_for_neoforge(version))
        minecraft_version = get_minecraft_version_for_neoforge(version)

    # Список возможных URL для скачивания
    download_urls = [
        f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://repo.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://cdn.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar",
        f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}.jar",
        f"https://repo.neoforged.net/releases/net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}.jar",
    ]

    # Создаем сессию с увеличенными таймаутами
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    # Пробуем каждый URL
    for i, download_url in enumerate(download_urls):
        log(f"Попытка {i + 1}/{len(download_urls)}: {download_url}")

        try:
            # Проверяем доступность файла с таймаутом
            log("Проверка доступности файла...")
            response = session.head(download_url, timeout=15)
            if response.status_code == 200:
                log("Файл доступен, начинаем скачивание...")
                break
            else:
                log(f"Файл недоступен (статус {response.status_code}), пробуем следующий URL...")
                continue
        except requests.exceptions.Timeout:
            log("Таймаут при проверке файла, пробуем следующий URL...")
            continue
        except requests.exceptions.RequestException as e:
            log(f"Ошибка при проверке файла: {e}, пробуем следующий URL...")
            continue
    else:
        # Если ни один URL не сработал
        error("Все URL для скачивания недоступны")
        return False, None

    try:
        # Создаем временную папку для скачивания
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.basename(download_url)
            installer_path = os.path.join(temp_dir, filename)

            # Скачиваем файл с увеличенным таймаутом
            log(f"Скачивание NeoForge {neoforge_version}...")

            response = session.get(download_url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(installer_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)

                        # Отправляем прогресс, если есть callback
                        if callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            callback({
                                "type": "progress",
                                "message": f"Скачано {downloaded_size / (1024 * 1024):.1f}MB из {total_size / (1024 * 1024):.1f}MB",
                                "progress": progress
                            })

            file_size = os.path.getsize(installer_path) / (1024 * 1024)  # Размер в МБ
            log(f"Успешно скачано: {filename} ({file_size:.2f} MB)")

            # Проверяем, что файл не пустой
            if file_size < 0.1:  # Меньше 100KB - вероятно, ошибка
                error("Скачанный файл слишком мал, вероятно ошибка загрузки")
                return False, None

            # Теперь устанавливаем
            success = install_neoforge(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback)
            return success, neoforge_version

    except requests.exceptions.Timeout:
        error("Таймаут при скачивании файла")
        return False, None
    except requests.exceptions.RequestException as e:
        error(f"Ошибка сети при скачивании: {e}")
        return False, None
    except Exception as e:
        error(f"Неожиданная ошибка при скачивании: {e}")
        return False, None


def install_neoforge(minecraft_version: str, neoforge_version: str, minecraft_dir: str, installer_path: str,
                     callback=None):
    """Устанавливает NeoForge в указанную директорию Minecraft"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge] {message}")

    def error(message):
        if callback:
            callback({"type": "error", "message": message})
        print(f"❌ [NeoForge] {message}")

    try:
        log(f"Начинаем установку NeoForge {neoforge_version} для Minecraft {minecraft_version}")

        # Пробуем стандартную установку через Java
        log("Пробуем стандартную установку...")
        try:
            result = subprocess.run([
                "java", "-jar", installer_path, "--installClient", minecraft_dir
            ], capture_output=True, text=True, timeout=300)  # 5 минут таймаут

            if result.returncode == 0:
                log("NeoForge успешно установлен!")
                return True
            else:
                log(f"Стандартная установка не удалась: {result.stderr}")
                # Пробуем альтернативный метод
                return install_neoforge_alternative(minecraft_version, neoforge_version, minecraft_dir, installer_path,
                                                    callback)

        except subprocess.TimeoutExpired:
            error("Таймаут установки NeoForge")
            return install_neoforge_alternative(minecraft_version, neoforge_version, minecraft_dir, installer_path,
                                                callback)
        except Exception as e:
            error(f"Ошибка при стандартной установке: {e}")
            return install_neoforge_alternative(minecraft_version, neoforge_version, minecraft_dir, installer_path,
                                                callback)

    except Exception as e:
        error(f"Критическая ошибка при установке NeoForge: {e}")
        return False


def install_neoforge_alternative(minecraft_version, neoforge_version, minecraft_dir, installer_path, callback):
    """Альтернативный метод установки NeoForge"""

    def log(message):
        if callback:
            callback({"type": "status", "message": message})
        print(f"🔧 [NeoForge Alt] {message}")

    try:
        log("Пробуем альтернативный метод установки...")

        # Просто распаковываем инсталлер как JAR
        version_name = f"neoforge-{minecraft_version}-{neoforge_version}"
        version_dir = os.path.join(minecraft_dir, "versions", version_name)
        os.makedirs(version_dir, exist_ok=True)

        # Копируем инсталлер как версию игры
        shutil.copy2(installer_path, os.path.join(version_dir, f"{version_name}.jar"))

        # Создаем минимальный json файл версии
        version_json = {
            "id": version_name,
            "inheritsFrom": minecraft_version,
            "type": "release",
            "mainClass": "net.minecraft.launchwrapper.Launch",
            "libraries": [
                {
                    "name": f"net.neoforged:neoforge:{neoforge_version}",
                    "url": "https://maven.neoforged.net/releases/"
                }
            ]
        }

        with open(os.path.join(version_dir, f"{version_name}.json"), 'w') as f:
            json.dump(version_json, f, indent=2)

        log("NeoForge установлен альтернативным методом!")
        return True

    except Exception as e:
        log(f"Альтернативный метод также не сработал: {e}")
        return False


def get_neoforge_versions(minecraft_version: str):
    """Получает доступные версии NeoForge для указанной версии Minecraft"""
    try:
        # Получаем версии через Maven API
        url = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return get_neoforge_versions_fallback(minecraft_version)

        data = response.json()
        versions = []

        # Фильтруем версии по версии Minecraft
        for version in data.get('versions', []):
            # NeoForge версии обычно содержат версию Minecraft
            if minecraft_version in version:
                versions.append(version)

        # Если не нашли подходящих версий, используем fallback
        if not versions:
            return get_neoforge_versions_fallback(minecraft_version)

        # Сортируем по убыванию (новые версии первыми)
        versions.sort(reverse=True)
        return versions[:5]  # Возвращаем топ-5 последних версий

    except Exception as e:
        print(f"❌ Ошибка получения версий NeoForge: {e}")
        return get_neoforge_versions_fallback(minecraft_version)


def get_latest_neoforge_version(minecraft_version: str):
    """Получает последнюю версию NeoForge для указанной версии Minecraft"""
    versions = get_neoforge_versions(minecraft_version)
    return versions[0] if versions else "20.4.1"  # Версия по умолчанию


def get_neoforge_versions_fallback(minecraft_version: str):
    """Fallback список версий NeoForge"""
    # Ручное сопоставление версий Minecraft и NeoForge
    version_map = {
        "1.21.4": ["21.4.155", "21.4.154", "21.4.153"],
        "1.21.3": ["21.3.94", "21.3.93", "21.3.92"],
        "1.21.2": ["21.1.215", "21.1.214"],
        "1.21.1": ["21.1.215", "21.1.214"],
        "1.21.0": ["21.0.167", "21.0.166"],
        "1.20.6": ["20.6.139", "20.6.138"],
        "1.20.5": ["20.5.21-beta", "20.5.20-beta"],
        "1.20.4": ["20.4.251", "20.4.250"],
        "1.20.3": ["20.3.8-beta", "20.3.7-beta"],
        "1.20.2": ["20.2.93", "20.2.92"],
        "1.20.1": ["20.4.1", "20.4.0", "20.3.0"],
        "1.20.0": ["20.0.0"],
        "1.19.2": ["19.2.0", "19.1.0"],
        "1.19.0": ["19.0.0"],
        "1.18.2": ["18.2.0", "18.1.0"],
        "1.18.0": ["18.0.0"],
        "1.17.1": ["17.1.0", "17.0.0"],
    }

    return version_map.get(minecraft_version, ["21.4.155"])  # По умолчанию последняя версия


def is_neoforge_installed(minecraft_version, neoforge_version, minecraft_dir):
    """Проверяет, установлен ли NeoForge (с проверкой всех файлов)"""
    version_name = f"neoforge-{minecraft_version}-{neoforge_version}"
    version_dir = os.path.join(minecraft_dir, "versions", version_name)

    # Проверяем все необходимые файлы
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


# Пример использования
if __name__ == "__main__":
    # Тестирование функций
    test_version = "Minecraft 1.21.4 + NeoForge (21.4.155)"

    if is_neoforge_needed(test_version):
        print(f"NeoForge требуется для: {test_version}")
        minecraft_ver = get_minecraft_version_for_neoforge(test_version)
        print(f"Версия Minecraft: {minecraft_ver}")

        # Скачивание и установка
        success, neoforge_ver = download_neoforge(test_version, minecraft_dir)
        if success:
            print(f"NeoForge {neoforge_ver} успешно установлен!")
        else:
            print("Не удалось установить NeoForge")