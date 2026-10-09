"""Install and launch Minecraft using the local MCLIB package."""
import json
import logging
import os
import re
import subprocess
import threading
import time
import uuid
from typing import Optional
import MCLIB
from ConfDir.Configs import CONFIG
from ConfDir.Versions import get_version_config, get_minecraft_version
from Core.backup import ModsBackupManager

LAUNCH_IN_PROGRESS = False
LAUNCH_START_TIME = None
GAME_PROCESS = None
discord_rpc = None
_current_collection = None
_launch_lock = threading.Lock()
_launch_versions = {}
logger = logging.getLogger(__name__)


def set_discord_rpc(instance):
    global discord_rpc
    discord_rpc = instance


def update_discord_status(state, details):
    if discord_rpc:
        try:
            discord_rpc.update(state=state, details=details, large_image='logo', start=int(time.time()))
        except Exception:
            pass


def validate_username(username):
    if not username or not re.fullmatch(r'[a-zA-Z0-9_]{3,16}', username):
        return False, 'Никнейм должен содержать от 3 до 16 букв, цифр или _'
    return True, 'OK'


def is_game_running():
    return GAME_PROCESS is not None and GAME_PROCESS.poll() is None


def is_minecraft_process_running(process):
    return process is not None and process.poll() is None


def monitor_game_process(process):
    global GAME_PROCESS
    exit_code = process.wait()
    logger.info('Minecraft завершён: PID=%s, exit_code=%s', process.pid, exit_code)
    try:
        from Core.bugreport import create_bugreport
        context = getattr(process, '_yamal_context', {}).copy()
        context.update(pid=process.pid, exit_code=exit_code)
        report = create_bugreport(context=context)
        logger.info('Полный отчёт Minecraft: %s', report)
    except Exception:
        logger.exception('Не удалось сохранить Bugreport.txt')
    if GAME_PROCESS is process:
        GAME_PROCESS = None
    update_discord_status('В меню', 'YamalPixel')


def is_modloader_needed(selected_version):
    config = get_version_config(selected_version)
    return config[1] if config else None


def _installed_loader(mc, loader, loader_version=None):
    directory = os.path.join(CONFIG['minecraft_dir'], 'versions')
    if not os.path.isdir(directory):
        return None
    api = MCLIB.mod_loader.get_mod_loader(loader)
    exact = api.get_installed_version(mc, loader_version) if loader_version else None
    matches = []
    for folder in os.listdir(directory):
        if exact and folder != exact:
            continue
        try:
            with open(os.path.join(directory, folder, folder + '.json'), encoding='utf-8') as source:
                profile = json.load(source)
            is_loader = (folder.startswith(loader + '-loader-') if loader in ('fabric', 'quilt')
                         else folder.startswith('neoforge-') if loader == 'neoforge'
                         else '-forge-' in folder or folder.endswith('-forge'))
            if is_loader and profile.get('inheritsFrom') == mc:
                libraries = [lib for lib in profile.get('libraries', [])
                             if not lib.get('rules') or MCLIB._helper.parse_rule_list(lib['rules'], {})]
                if not all(os.path.isfile(MCLIB._helper.get_library_path(lib['name'], CONFIG['minecraft_dir']))
                           for lib in libraries):
                    continue
                if loader == 'neoforge' and any(lib['name'].startswith('net.neoforged:neoforge:')
                                               and len(lib['name'].split(':')) == 3 for lib in libraries):
                    # Previous handmade profiles used an installer/ordinary JAR instead of processed client artifacts.
                    continue
                matches.append(folder)
        except (OSError, ValueError):
            continue
    if not matches:
        return None
    return max(matches, key=lambda name: os.path.getmtime(os.path.join(directory, name, name + '.json')))


def check_modloader_installed(minecraft_version, loader_type, loader_version=None):
    return _installed_loader(minecraft_version, loader_type, loader_version) is not None


def install_modloader_sync(minecraft_version, loader_type, loader_version=None, raise_on_error=False):
    try:
        api = MCLIB.mod_loader.get_mod_loader(loader_type)
        if loader_version in (None, '', 'latest'):
            available = api.get_loader_versions(minecraft_version, not CONFIG.get('show_beta_versions', False))
            if not available:
                raise RuntimeError(f'Нет доступной версии {loader_type} для {minecraft_version}')
            loader_version = available[0]
        installed = _installed_loader(minecraft_version, loader_type, loader_version)
        if installed is None:
            java = None
            try:
                with open(os.path.join(CONFIG['minecraft_dir'], 'versions', minecraft_version,
                                       minecraft_version + '.json'), encoding='utf-8') as source:
                    base = json.load(source)
                component = base.get('javaVersion', {}).get('component')
                if component:
                    java = MCLIB.runtime.get_executable_path(component, CONFIG['minecraft_dir'])
            except (OSError, ValueError):
                pass
            installed = api.install(minecraft_version, CONFIG['minecraft_dir'],
                                    loader_version=loader_version, java=java)
        _launch_versions[(minecraft_version, loader_type)] = installed
        return True
    except Exception as exc:
        logger.exception('Установка %s %s для Minecraft %s не выполнена', loader_type, loader_version, minecraft_version)
        if raise_on_error:
            raise RuntimeError(f'{loader_type} {loader_version} для Minecraft {minecraft_version}: {exc}') from exc
        return False


def switch_mods_for_version(version_name, progress_callback=None, raise_on_error=False):
    from Core.collection_loader import load_collection_data, install_collection
    config = get_version_config(version_name)
    if not config:
        if raise_on_error:
            raise ValueError(f'Неизвестная версия/сборка: {version_name}')
        return False
    if CONFIG.pop('launch_without_mods_next', False):
        return True
    if version_name.startswith('📦 '):
        data = load_collection_data(version_name[2:])
        if data is None:
            if raise_on_error:
                raise ValueError(f'Не найдена сборка: {version_name}')
            return False
    elif version_name == 'YamalPixel':
        data = {'name': 'YamalPixel', 'minecraft_version': config[0], 'loader': config[1],
                'mods': [], 'archive_url': CONFIG['mods_archive_url']}
    else:
        data = {'name': None, 'minecraft_version': config[0], 'loader': config[1], 'mods': []}

    def progress(i, total, name, **kwargs):
        if progress_callback:
            status = kwargs.get('status', '')
            if status == 'archive_download':
                percent = int(75 * i / total) if total else 0
                message = f'Скачивание архива: {i / 1048576:.1f}/{total / 1048576:.1f} МБ'
            elif status.startswith('archive_'):
                percent = 75 + int(20 * i / total) if total else 75
                if status == 'archive_complete':
                    percent = 100
                message = f'Распаковка/проверка модов: {name}'
            else:
                message = f'Моды: {i + 1}/{total} — {name}'
                percent = int(100 * (i + 1) / total) if total else 100
            progress_callback('progress', str(percent))
            progress_callback('status', message)
    return install_collection(data, progress, create_backup=True, raise_on_error=raise_on_error)


def install_required_components_sync(version_name, progress_callback=None, raise_on_error=False):
    config = get_version_config(version_name)
    if not config:
        if raise_on_error:
            raise ValueError(f'Неизвестная версия/сборка: {version_name}')
        return False
    mc, loader, loader_version = config
    stage = f'Установка/проверка Minecraft {mc}'
    try:
        if progress_callback:
            progress_callback('status', f'Проверка Minecraft {mc}')
        # The library validates and repairs an existing installation too.
        MCLIB.install.install_minecraft_version(mc, CONFIG['minecraft_dir'])
        if loader and loader != 'none':
            stage = f'Установка/проверка {loader}'
            if progress_callback:
                progress_callback('status', f'Установка {loader}')
            if not install_modloader_sync(mc, loader, loader_version, raise_on_error=True):
                raise RuntimeError('Установщик загрузчика вернул ошибку')
        # Never replace mods until base game and loader are successfully installed.
        stage = 'Установка модов'
        if not switch_mods_for_version(version_name, progress_callback, raise_on_error=True):
            raise RuntimeError('Установщик модов вернул ошибку')
        return True
    except Exception as exc:
        logger.exception('%s не выполнена', stage)
        if raise_on_error:
            raise RuntimeError(f'{stage}: {exc}') from exc
        return False


def get_launch_version(selected_version, loader_type, minecraft_version):
    if not loader_type or loader_type == 'none':
        return minecraft_version
    config = get_version_config(selected_version)
    loader_version = config[2] if config else None
    if loader_version in ('latest', ''):
        loader_version = None
    if loader_version:
        return MCLIB.mod_loader.get_mod_loader(loader_type).get_installed_version(minecraft_version, loader_version)
    version = _launch_versions.get((minecraft_version, loader_type)) or _installed_loader(minecraft_version, loader_type)
    if version is None:
        raise RuntimeError(f'{loader_type} для {minecraft_version} не установлен')
    return version


def launch_minecraft_process(command):
    from pathlib import Path
    from datetime import datetime
    from Core.bugreport import redact
    directory = Path(CONFIG['minecraft_dir']) / 'logs'
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / ('minecraft-console-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.log')
    # Let Java write directly to a file: no pipe deadlocks, and logging continues
    # even if the launcher is closed while the game is running.
    with log_path.open('wb') as console:
        process = subprocess.Popen(command, cwd=CONFIG['minecraft_dir'], stdout=console,
                                   stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    process._yamal_context = {'command': redact(subprocess.list2cmdline(command)),
                              'java_console': str(log_path), 'started': datetime.now().astimezone().isoformat()}
    logger.info('Minecraft PID=%s; console=%s', process.pid, log_path)
    return process


def run_game_launch(selected_version, username, progress_callback=None):
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME, GAME_PROCESS
    def notify(kind, message):
        if progress_callback:
            progress_callback(kind, message)
    if not _launch_lock.acquire(blocking=False):
        notify('error', 'Запуск уже выполняется')
        return False
    try:
        if is_game_running():
            raise RuntimeError('Игра уже запущена')
        valid, reason = validate_username(username)
        if not valid:
            raise ValueError(reason)
        LAUNCH_IN_PROGRESS = True
        LAUNCH_START_TIME = time.time()
        if not install_required_components_sync(selected_version, progress_callback, raise_on_error=True):
            raise RuntimeError('Не удалось установить компоненты. Текущие моды сохранены.')
        mc, loader, _ = get_version_config(selected_version)
        memory = CONFIG.get('jvm_memory', '-Xmx4G')
        options = {'username': username, 'uuid': str(uuid.UUID(bytes=__import__('hashlib').md5(
                       ('OfflinePlayer:' + username).encode('utf-8')).digest(), version=3)),
                   'token': '', 'jvmArguments': [memory, '-Xms' + memory.removeprefix('-Xmx'),
                       '-XX:+UseG1GC', '-Duser.language=ru', '-Duser.country=RU'],
                   'gameDirectory': CONFIG['minecraft_dir']}
        command = MCLIB.command.get_minecraft_command(get_launch_version(selected_version, loader, mc),
                                                     CONFIG['minecraft_dir'], options)
        process = launch_minecraft_process(command)
        if process is None:
            raise RuntimeError('Не удалось создать процесс игры')
        GAME_PROCESS = process
        process._yamal_context.update(selected_version=selected_version, minecraft=mc, loader=loader)
        from Core.bugreport import redact
        try:
            with open(os.path.join(CONFIG['minecraft_dir'], 'logs', 'launch-session.json'), 'w', encoding='utf-8') as session:
                session.write(redact(json.dumps(process._yamal_context, ensure_ascii=False, indent=2)))
        except OSError:
            logger.exception('Не удалось записать метаданные запуска')
        update_discord_status('В игре', selected_version)
        threading.Thread(target=monitor_game_process, args=(process,), daemon=True).start()
        notify('success', f'Игра запущена для {username}')
        return True
    except Exception as exc:
        logger.exception('Запуск %s не выполнен', selected_version)
        notify('error', str(exc))
        return False
    finally:
        LAUNCH_IN_PROGRESS = False
        _launch_lock.release()


def cleanup_before_launch():
    # Never terminate unrelated Java processes.
    pass


def clear_auth_cache():
    # Existing accounts and vanilla launcher profiles belong to the user.
    pass


def cleanup_on_exit():
    # Closing the launcher deliberately leaves Minecraft running.
    pass


def set_current_collection(name):
    global _current_collection
    _current_collection = name


def get_current_collection():
    return _current_collection


def get_minecraft_version_for_fabric(name):
    return get_minecraft_version(name)


def check_forge_installed(version, directory):
    return check_modloader_installed(version, 'forge')


def check_fabric_installed():
    return check_modloader_installed(CONFIG['version'], 'fabric', CONFIG['fabric_loader'])


def check_quilt_installed():
    return check_modloader_installed(CONFIG['version'], 'quilt')


def install_fabric_silent():
    return install_modloader_sync(CONFIG['version'], 'fabric', CONFIG['fabric_loader'])


def install_quilt_silent():
    return install_modloader_sync(CONFIG['version'], 'quilt')


def install_forge_sync(version, directory):
    return install_modloader_sync(version, 'forge')


def install_neoforge_sync(version, directory):
    return install_modloader_sync(version, 'neoforge')


def install_quilt_sync(version, directory):
    return install_modloader_sync(version, 'quilt')
