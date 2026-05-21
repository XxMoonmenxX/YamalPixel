## Core/run.py
import os
import sys
import uuid
import time
import json
import shutil
import subprocess
import threading
import zipfile
import requests
import minecraft_launcher_lib
from datetime import datetime
from typing import Optional, Dict, Any
import atexit

from ConfDir.Configs import CONFIG, essential_mods
from ConfDir.Versions import (
    fabric_supported_versions, quilt_supported_versions,
    forge_supported_versions, neoforge_supported_versions,
    get_minecraft_version, version_configs
)
from Network.Downloader import download_single_mod_turbo_sync

# Глобальные переменные для состояния
LAUNCH_IN_PROGRESS = False
LAUNCH_START_TIME = None
GAME_PROCESS = None
discord_rpc = None


def set_discord_rpc(rpc_instance):
    """Устанавливает экземпляр RPC для использования в запуске"""
    global discord_rpc
    discord_rpc = rpc_instance


def update_discord_status(state, details):
    """Обновляет статус в Discord"""
    global discord_rpc
    if discord_rpc:
        try:
            discord_rpc.update(
                state=state,
                details=details,
                large_image="logo",
                start=int(time.time())
            )
        except:
            pass
def validate_username(username: str) -> tuple:
    """Проверяет корректность имени пользователя"""
    if not username or username == "Введите никнейм":
        return False, "Имя пользователя не может быть пустым"

    if len(username) < 3 or len(username) > 16:
        return False, "Длина имени должна быть от 3 до 16 символов"

    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Имя может содержать только буквы, цифры и _"

    return True, "OK"


def check_fabric_installed() -> bool:
    """Проверяет установлен ли Fabric"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        versions_dir = os.path.join(minecraft_dir, "versions")
        fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
        fabric_version_dir = os.path.join(versions_dir, fabric_version)
        return os.path.exists(fabric_version_dir)
    except:
        return False


def install_fabric_silent() -> bool:
    """Тихая установка Fabric"""
    try:
        print("🔧 Устанавливаем Fabric...")
        minecraft_launcher_lib.fabric.install_fabric(
            minecraft_version=CONFIG["version"],
            loader_version=CONFIG["fabric_loader"],
            minecraft_directory=CONFIG["minecraft_dir"],
        )
        print("✅ Fabric установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Fabric: {e}")
        return False


def check_quilt_installed() -> bool:
    """Проверяет установлен ли Quilt"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_dir)
        for version in installed_versions:
            if version["id"].startswith("quilt-loader-"):
                return True
        return False
    except:
        return False


def install_quilt_silent() -> bool:
    """Тихая установка Quilt"""
    try:
        print("🔧 Устанавливаем Quilt...")
        minecraft_launcher_lib.quilt.install_quilt(
            minecraft_version=CONFIG["version"],
            loader_version=None,
            minecraft_directory=CONFIG["minecraft_dir"],
        )
        print("✅ Quilt установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Quilt: {e}")
        return False


def check_forge_installed(minecraft_version: str, minecraft_directory: str) -> bool:
    """Проверяет установлен ли Forge"""
    try:
        versions_dir = os.path.join(minecraft_directory, "versions")
        for folder in os.listdir(versions_dir):
            folder_lower = folder.lower()
            if ("forge" in folder_lower) and minecraft_version in folder_lower:
                json_path = os.path.join(versions_dir, folder, f"{folder}.json")
                if os.path.exists(json_path):
                    return True
        return False
    except:
        return False


def install_forge_sync(minecraft_version: str, minecraft_directory: str) -> bool:
    """Установка Forge"""
    try:
        print(f"🔧 Устанавливаем Forge для {minecraft_version}...")
        from minecraft_launcher_lib.mod_loader import get_mod_loader
        forge_loader = get_mod_loader("forge")
        loader_versions = forge_loader.get_loader_versions(minecraft_version, stable_only=True)

        if not loader_versions:
            raise Exception(f"Не найдены версии Forge для {minecraft_version}")

        latest_loader_version = loader_versions[0]
        print(f"📦 Используем Forge {latest_loader_version}")

        forge_loader.install(
            minecraft_version=minecraft_version,
            minecraft_directory=minecraft_directory,
            loader_version=latest_loader_version,
            callback={
                "setStatus": lambda text: print(f"   {text}"),
                "setProgress": lambda value: None,
                "setMax": lambda value: None
            },
            java=None
        )
        print(f"✅ Forge успешно установлен!")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Forge: {e}")
        return False


def install_neoforge_sync(minecraft_version: str, minecraft_directory: str) -> bool:
    """Установка NeoForge"""
    try:
        print(f"🔧 Устанавливаем NeoForge для {minecraft_version}...")
        neoforge_versions = minecraft_launcher_lib.neoforge.get_versions(minecraft_version)

        if not neoforge_versions:
            raise Exception(f"Не найдены версии NeoForge для {minecraft_version}")

        latest_neoforge = neoforge_versions[0]
        print(f"📦 Используем NeoForge {latest_neoforge}")

        minecraft_launcher_lib.neoforge.install(
            minecraft_version=minecraft_version,
            loader_version=latest_neoforge,
            minecraft_directory=minecraft_directory
        )
        print(f"✅ NeoForge успешно установлен!")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки NeoForge: {e}")
        return False


def install_quilt_sync(minecraft_version: str, minecraft_directory: str) -> bool:
    """Синхронная установка Quilt"""
    try:
        print(f"🔧 Устанавливаем Quilt для {minecraft_version}...")
        quilt_loader = minecraft_launcher_lib.mod_loader.get_mod_loader("quilt")
        quilt_versions = quilt_loader.get_loader_versions(minecraft_version, stable_only=True)

        if not quilt_versions:
            raise Exception(f"Не найдены версии Quilt для {minecraft_version}")

        latest_quilt = quilt_versions[0]
        print(f"📦 Используем Quilt {latest_quilt}")

        quilt_loader.install(
            minecraft_version=minecraft_version,
            minecraft_directory=minecraft_directory,
            loader_version=latest_quilt
        )
        print(f"✅ Quilt успешно установлен!")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Quilt: {e}")
        return False


def get_latest_quilt_loader_version() -> str:
    """Получает последнюю версию Quilt loader"""
    try:
        quilt_loader = minecraft_launcher_lib.mod_loader.get_mod_loader("quilt")
        versions = quilt_loader.get_loader_versions()
        if versions:
            return versions[0]
        return "0.25.0"
    except:
        return "0.25.0"


def is_modloader_needed(selected_version: str) -> Optional[str]:
    """Проверяет нужен ли модлоадер"""
    if selected_version in fabric_supported_versions:
        return "fabric"
    elif selected_version in quilt_supported_versions:
        return "quilt"
    elif selected_version in forge_supported_versions:
        return "forge"
    elif selected_version in neoforge_supported_versions:
        return "neoforge"
    return None


def check_modloader_installed(minecraft_version: str, loader_type: str, loader_version: str = None) -> bool:
    """Проверяет установлен ли модлоадер"""
    try:
        versions_dir = os.path.join(CONFIG["minecraft_dir"], "versions")

        if loader_type == "fabric":
            fabric_loader = loader_version or "0.17.2"
            fabric_version = f"fabric-loader-{fabric_loader}-{minecraft_version}"
            return os.path.exists(os.path.join(versions_dir, fabric_version))

        elif loader_type == "quilt":
            for folder in os.listdir(versions_dir):
                if folder.startswith("quilt-loader-") and folder.endswith(f"-{minecraft_version}"):
                    return True
            return False

        elif loader_type == "forge":
            for folder in os.listdir(versions_dir):
                if "forge" in folder.lower() and minecraft_version in folder:
                    return True
            return False

        elif loader_type == "neoforge":
            for folder in os.listdir(versions_dir):
                if folder.startswith("neoforge-") and minecraft_version in folder:
                    return True
            try:
                installed_versions = minecraft_launcher_lib.utils.get_installed_versions(CONFIG["minecraft_dir"])
                for version in installed_versions:
                    if "neoforge" in version["id"].lower():
                        return True
            except:
                pass
            return False

        return False
    except Exception as e:
        print(f"⚠️ Ошибка проверки модлоадера: {e}")
        return False


def install_modloader_sync(minecraft_version: str, loader_type: str, loader_version: str = None) -> bool:
    """Устанавливает модлоадер"""
    try:
        if loader_type == "fabric":
            fabric_loader = loader_version or "0.17.2"
            minecraft_launcher_lib.fabric.install_fabric(
                minecraft_version=minecraft_version,
                loader_version=fabric_loader,
                minecraft_directory=CONFIG["minecraft_dir"]
            )
            print(f"✅ Fabric {fabric_loader} установлен для {minecraft_version}")
            return True

        elif loader_type == "quilt":
            return install_quilt_sync(minecraft_version, CONFIG["minecraft_dir"])

        elif loader_type == "neoforge":
            return install_neoforge_sync(minecraft_version, CONFIG["minecraft_dir"])

        elif loader_type == "forge":
            if not check_forge_installed(minecraft_version, CONFIG["minecraft_dir"]):
                return install_forge_sync(minecraft_version, CONFIG["minecraft_dir"])
            else:
                print(f"✅ Forge уже установлен для {minecraft_version}")
                return True

        return False
    except Exception as e:
        print(f"❌ Ошибка установки {loader_type}: {e}")
        return False


def cleanup_before_launch():
    """Очистка перед запуском"""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/f", "/im", "javaw.exe"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.run(["pkill", "-f", "minecraft"], capture_output=True)
        time.sleep(2)
    except Exception as e:
        print(f"Очистка перед запуском: {e}")


def clear_auth_cache():
    """Очищает кэш аутентификации"""
    minecraft_dir = CONFIG["minecraft_dir"]
    cache_files = [
        os.path.join(minecraft_dir, "usercache.json"),
        os.path.join(minecraft_dir, "launcher_profiles.json"),
        os.path.join(minecraft_dir, "launcher_accounts.json"),
    ]
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"Удален: {cache_file}")
            except Exception as e:
                print(f"Ошибка удаления {cache_file}: {e}")


def launch_minecraft_process(command):
    """Запускает процесс Minecraft"""
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска: {str(e)}")
        return None


def is_minecraft_process_running(process):
    """Проверяет, запущен ли процесс Minecraft"""
    try:
        if process and process.poll() is None:
            return True
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/fi", "imagename eq javaw.exe", "/fo", "csv"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return "javaw.exe" in result.stdout
        else:
            result = subprocess.run(
                ["pgrep", "-f", "minecraft"], capture_output=True, text=True
            )
            return result.returncode == 0
    except:
        return False


def monitor_game_process(process):
    """Мониторит процесс игры в фоне"""
    global GAME_PROCESS
    try:
        GAME_PROCESS = process
        process.wait()
        print("[LAUNCHER] Процесс Minecraft завершен")
        GAME_PROCESS = None
    except Exception as e:
        print(f"[LAUNCHER] Ошибка мониторинга: {e}")
        GAME_PROCESS = None


def is_game_running():
    """Проверяет, запущена ли игра"""
    global GAME_PROCESS
    if GAME_PROCESS and GAME_PROCESS.poll() is None:
        return True

    # Дополнительная проверка через tasklist
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["tasklist", "/fi", "imagename eq javaw.exe", "/fo", "csv"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return "javaw.exe" in result.stdout
        except:
            pass
    return False

def get_minecraft_version_for_fabric(version_name: str) -> str:
    """Получает версию Minecraft для Fabric"""
    return get_minecraft_version(version_name)


def install_required_components_sync(version_name: str) -> bool:
    """Синхронная установка компонентов"""
    try:
        print(f"🔍 Начинаем установку для: {version_name}")

        # Для кастомных сборок
        if version_name.startswith("📦 "):
            from Core.collection_loader import load_collection_data
            collection_name = version_name[2:]
            collection_data = load_collection_data(collection_name)

            if not collection_data:
                raise Exception(f"Не удалось загрузить данные сборки: {collection_name}")

            minecraft_version = collection_data['minecraft_version']
            loader_type = collection_data['loader']
            loader_version = collection_data.get('loader_version')
        else:
            # Статические версии
            if version_name not in version_configs:
                raise ValueError(f"Версия {version_name} не найдена в конфигурациях")

            config_data = version_configs[version_name]
            if isinstance(config_data, (list, tuple)):
                if len(config_data) == 2:
                    minecraft_version, loader_type = config_data
                    loader_version = None
                elif len(config_data) == 3:
                    minecraft_version, loader_type, loader_version = config_data
                else:
                    raise ValueError(f"Неверная конфигурация для {version_name}")
            else:
                minecraft_version = config_data
                loader_type = None
                loader_version = None

        # Установка Minecraft
        versions_dir = os.path.join(CONFIG["minecraft_dir"], "versions")
        version_dir = os.path.join(versions_dir, minecraft_version)

        if not os.path.exists(version_dir):
            print(f"🔄 Устанавливаем Minecraft {minecraft_version}...")
            minecraft_launcher_lib.install.install_minecraft_version(
                version=minecraft_version,
                minecraft_directory=CONFIG["minecraft_dir"]
            )
            print(f"✅ Minecraft {minecraft_version} успешно установлена")

        # Установка модлоадера
        if loader_type and loader_type != "none":
            print(f"🔧 Проверяем {loader_type.capitalize()}...")
            if not check_modloader_installed(minecraft_version, loader_type, loader_version):
                print(f"🔄 Устанавливаем {loader_type.capitalize()} для {minecraft_version}...")
                install_modloader_sync(minecraft_version, loader_type, loader_version)
            else:
                print(f"✅ {loader_type.capitalize()} уже установлен")

        return True

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False


def get_launch_version(selected_version: str, loader_type: str, minecraft_version: str) -> str:
    """Определяет версию для запуска"""
    if loader_type == "fabric":
        mc_ver = get_minecraft_version_for_fabric(selected_version)
        return f"fabric-loader-0.17.2-{mc_ver}"

    elif loader_type == "quilt":
        mc_ver = get_minecraft_version(selected_version)
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(CONFIG["minecraft_dir"])
        for version in installed_versions:
            if version["id"].startswith("quilt-loader-") and version["id"].endswith(f"-{mc_ver}"):
                return version["id"]
        return f"quilt-loader-{get_latest_quilt_loader_version()}-{mc_ver}"

    elif loader_type == "forge":
        mc_ver = get_minecraft_version(selected_version)
        if not check_forge_installed(mc_ver, CONFIG["minecraft_dir"]):
            install_forge_sync(mc_ver, CONFIG["minecraft_dir"])
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(CONFIG["minecraft_dir"])
        for version in installed_versions:
            if "forge" in version["id"].lower() and mc_ver in version["id"]:
                return version["id"]
        return f"{mc_ver}-forge"

    elif loader_type == "neoforge":
        mc_ver = get_minecraft_version(selected_version)
        try:
            neoforge_versions = minecraft_launcher_lib.neoforge.get_versions(mc_ver)
            if neoforge_versions:
                return f"neoforge-{neoforge_versions[0]}"
        except:
            pass
        return f"neoforge-{mc_ver}"

    else:
        return get_minecraft_version(selected_version)


def run_game_launch(selected_version: str, username: str, progress_callback=None) -> bool:
    """Основная функция запуска игры"""
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME, GAME_PROCESS

    try:
        # Обновляем статус Discord перед запуском
        if selected_version.startswith("📦 "):
            collection_name = selected_version[2:]
            update_discord_status("Играет со сборкой", collection_name)
        else:
            update_discord_status("Играет в YamalPixel", selected_version)
    except Exception as e:
        print(f"Error updating status:" + str(e))

    # Проверяем, не запущена ли уже игра
    if is_game_running():
        if progress_callback:
            progress_callback("error", "Игра уже запущена!")
        return False



    try:
        # Валидация имени
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            if progress_callback:
                progress_callback("error", error_msg)
            return False

        print(f"🚀 Запуск игры: версия={selected_version}, игрок={username}")

        if progress_callback:
            progress_callback("status", f"Запуск {selected_version}")

        # Установка компонентов (только если нужно)
        if selected_version != "YamalPixel":
            # Для Forge 1.12.2 нужна специальная обработка
            if selected_version == "Minecraft 1.12.2 + Forge":
                # Проверяем установлен ли Forge
                if not check_forge_installed("1.12.2", CONFIG["minecraft_dir"]):
                    if progress_callback:
                        progress_callback("status", "Установка Forge 1.12.2...")
                    install_forge_sync("1.12.2", CONFIG["minecraft_dir"])
            else:
                if not install_required_components_sync(selected_version):
                    raise Exception("Не удалось установить компоненты")

        # Подготовка
        cleanup_before_launch()
        clear_auth_cache()

        # Определение типа загрузчика
        loader_type = is_modloader_needed(selected_version)
        minecraft_version = get_minecraft_version(selected_version)

        # Для кастомных сборок
        if selected_version.startswith("📦 "):
            from Core.collection_loader import load_collection_data
            collection_name = selected_version[2:]
            collection_data = load_collection_data(collection_name)
            if collection_data:
                minecraft_version = collection_data['minecraft_version']
                loader_type = collection_data['loader']

        # Формирование команды запуска
        namespace = uuid.UUID('6ba7b811-9dad-11d1-80b4-00c04fd430c8')
        offline_uuid = str(uuid.uuid5(namespace, "OfflinePlayer:" + username))

        selected_memory = CONFIG.get("jvm_memory", "-Xmx4G")
        jvm_args = [
            selected_memory,
            f"-Xms{selected_memory.replace('-Xmx', '')}",
            "-XX:+UseG1GC",
            "-Duser.language=ru",
            "-Duser.country=RU",
        ]

        options = {
            "username": username,
            "uuid": offline_uuid,
            "token": "",
            "jvmArguments": jvm_args,
            "gameDirectory": CONFIG["minecraft_dir"],
            "gameLocale": "ru_RU"
        }

        launch_version = get_launch_version(selected_version, loader_type, minecraft_version)
        print(f"🎯 Версия запуска: {launch_version}")

        command = minecraft_launcher_lib.command.get_minecraft_command(
            version=launch_version,
            minecraft_directory=CONFIG["minecraft_dir"],
            options=options,
        )

        process = launch_minecraft_process(command)
        if not process:
            raise Exception("Не удалось создать процесс")

        GAME_PROCESS = process

        if progress_callback:
            progress_callback("success", f"Игра запущена для {username}")

        # Мониторинг в фоне
        threading.Thread(target=monitor_game_process, args=(process,), daemon=True).start()

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"[LAUNCH ERROR] {error_msg}")
        if progress_callback:
            progress_callback("error", error_msg)
        GAME_PROCESS = None
        return False

@atexit.register
def cleanup_on_exit():
    """Очистка при выходе из программы"""
    global GAME_PROCESS
    if GAME_PROCESS and GAME_PROCESS.poll() is None:
        try:
            GAME_PROCESS.terminate()
            GAME_PROCESS.wait(timeout=5)
        except:
            try:
                GAME_PROCESS.kill()
            except:
                pass

_current_collection = None

def set_current_collection(collection_name):
    """Устанавливает текущую активную сборку"""
    global _current_collection
    _current_collection = collection_name

def get_current_collection():
    """Возвращает текущую активную сборку"""
    return _current_collection