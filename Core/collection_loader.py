## Core/collection_loader.py
import os
import json
import logging
import traceback
from datetime import datetime, timezone
import tempfile
import zipfile
import shutil
from pathlib import Path
from Core.mod_transaction import safe_filename, safe_target, replace_mods
from Core.local_mods import copy_local_mod
from typing import List, Dict, Optional

from ConfDir.Configs import COLLECTIONS_CONFIG, CONFIG
from Network.Downloader import download_single_mod_turbo_sync
from Core.backup import ModsBackupManager

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Добавляем обработчик для вывода в консоль, если его нет
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_collections_dir() -> str:
    """Возвращает путь к папке со сборками"""
    return COLLECTIONS_CONFIG["collections_dir"]


def load_collection_file(filename: str) -> Dict:
    with open(safe_target(get_collections_dir(), filename), encoding='utf-8') as stream:
        data = json.load(stream)
    if not isinstance(data, dict) or not all(key in data for key in ('name', 'minecraft_version', 'loader', 'mods')):
        raise ValueError('Неверный файл сборки')
    return data


def load_collection_data(collection_name: str) -> Optional[Dict]:
    """Загружает данные кастомной сборки"""
    try:
        collections_dir = get_collections_dir()

        if not os.path.exists(collections_dir):
            return None

        for filename in os.listdir(collections_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(collections_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if data.get('name') == collection_name or f"📦 {data.get('name')}" == collection_name:
                        data['filename'] = filename
                        return data
                except Exception as e:
                    logger.error(f"Ошибка чтения файла {filename}: {e}")

        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки сборки {collection_name}: {e}")
        return None


def load_all_collections() -> List[Dict]:
    """Загружает все сборки"""
    collections = []
    collections_dir = get_collections_dir()

    if not os.path.exists(collections_dir):
        return collections

    for filename in os.listdir(collections_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(collections_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if all(key in data for key in ['name', 'minecraft_version', 'loader']):
                    created_date = None
                    date_fields = ["created_at", "imported_date", "upload_date", "date_created"]

                    for date_field in date_fields:
                        if date_field in data:
                            try:
                                if "T" in data[date_field]:
                                    created_date = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
                                else:
                                    created_date = datetime.strptime(data[date_field], "%Y-%m-%d %H:%M:%S")
                                break
                            except:
                                continue

                    if created_date is None:
                        created_date = datetime.fromtimestamp(os.path.getctime(filepath))

                    collections.append({
                        'name': data['name'],
                        'display_name': f"📦 {data['name']}",
                        'filename': filename,
                        'minecraft_version': data['minecraft_version'],
                        'loader': data['loader'],
                        'loader_version': data.get('loader_version', ''),
                        'mods': data.get('mods', []),
                        'mod_count': len(data.get('mods', [])),
                        'created_at': created_date.astimezone(timezone.utc),
                        'created_str': created_date.strftime("%d.%m.%Y"),
                        'description': data.get('description', ''),
                        'source': data.get('source', 'local')
                    })
            except Exception as e:
                logger.error(f"Ошибка загрузки сборки {filename}: {e}")

    collections.sort(key=lambda x: x['created_at'], reverse=True)
    return collections


def save_collection(collection_data: Dict, filename: str = None) -> tuple:
    """Сохраняет сборку"""
    try:
        collections_dir = get_collections_dir()
        os.makedirs(collections_dir, exist_ok=True)

        if not filename:
            safe_name = "".join(c for c in collection_data['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name[:50]
            filename = f"{safe_name}.json"

        filepath = safe_target(collections_dir, filename)

        collection_data['updated_at'] = datetime.now().isoformat()
        if 'created_at' not in collection_data:
            collection_data['created_at'] = datetime.now().isoformat()

        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=collections_dir,
                                             prefix='.collection-', suffix='.tmp', delete=False) as stream:
                temporary = stream.name
                json.dump(collection_data, stream, indent=2, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, filepath)
        finally:
            if temporary and os.path.exists(temporary):
                os.remove(temporary)

        return True, filename
    except Exception as e:
        return False, str(e)


def delete_collection(filename: str) -> bool:
    """Удаляет сборку"""
    try:
        filepath = os.path.join(get_collections_dir(), filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка удаления сборки: {e}")
        return False


def check_mod_compatibility(mod: Dict, minecraft_version: str, loader: str) -> tuple:
    """
    Проверяет совместимость мода с версией Minecraft и загрузчиком
    Возвращает (is_compatible, reason)
    """
    filename = mod.get('filename', '')
    filename_lower = filename.lower()

    # Получаем название мода для отладки
    mod_name = mod.get('name', 'Unknown')

    # NeoForge совместим с Forge модами (обычно да)
    # Если выбран NeoForge, а мод для Forge - он должен работать
    if loader == 'neoforge' and 'forge' in filename_lower and 'neoforge' not in filename_lower:
        # NeoForge может запускать Forge моды, не пропускаем
        logger.info(f"   ℹ️ {mod_name}: Forge mod on NeoForge - should work")
        # Не возвращаем False, продолжаем

    # Проверка версии Minecraft
    if '1.20.1' in filename_lower and minecraft_version != '1.20.1':
        return False, f"Мод для 1.20.1, а игра на {minecraft_version}"
    if '1.21' in filename_lower and not minecraft_version.startswith('1.21'):
        return False, f"Мод для 1.21.x, а игра на {minecraft_version}"

    # Проверка загрузчика - только если это явно несовместимо
    # Fabric моды НЕ работают на NeoForge
    if 'fabric' in filename_lower and loader not in ['fabric', 'quilt']:
        return False, f"Мод для Fabric, а выбран {loader}"

    # Quilt моды обычно работают на Fabric
    if 'quilt' in filename_lower and loader not in ['fabric', 'quilt']:
        return False, f"Мод для Quilt, а выбран {loader}"

    # Forge моды работают на NeoForge (обратная совместимость)
    if 'forge' in filename_lower and loader not in ['forge', 'neoforge']:
        return False, f"Мод для Forge, а выбран {loader}"

    # NeoForge моды не работают на обычном Forge
    if 'neoforge' in filename_lower and loader not in ['neoforge']:
        return False, f"Мод для NeoForge, а выбран {loader}"

    return True, "OK"


def install_collection(collection_data: Dict, progress_callback=None, create_backup=True,
                       cancel_event=None, raise_on_error=False) -> bool:
    """Download a complete collection before replacing existing mods."""
    from Core.run import set_current_collection
    minecraft_dir = CONFIG["minecraft_dir"]
    os.makedirs(minecraft_dir, exist_ok=True)
    mods_dir = os.path.join(minecraft_dir, "mods")
    try:
        mods = collection_data.get('mods', [])
        if not isinstance(mods, list):
            raise ValueError("Неверный список модов")
        version = collection_data['minecraft_version']
        loader = collection_data['loader']
        filenames = set()
        for mod in mods:
            filename = safe_filename(mod.get('filename') or f"{mod.get('name', 'mod')}.jar")
            if filename.casefold() in filenames:
                raise ValueError(f"Повторяющееся имя файла: {filename}")
            filenames.add(filename.casefold())
            compatible, reason = ((True, 'OK') if mod.get('source') == 'local'
                                  else check_mod_compatibility(mod, version, loader))
            if not compatible:
                raise ValueError(f"{mod.get('name', filename)}: {reason}")
        with tempfile.TemporaryDirectory(prefix='.mods-install-', dir=minecraft_dir) as staging:
            prepared = os.path.join(staging, 'mods')
            os.makedirs(prepared)
            # Keep non-JAR user files, but never carry old mods into a new collection.
            if os.path.isdir(mods_dir):
                for entry in os.scandir(mods_dir):
                    if not entry.name.lower().endswith('.jar'):
                        target = os.path.join(prepared, entry.name)
                        if entry.is_dir():
                            shutil.copytree(entry.path, target)
                        else:
                            shutil.copy2(entry.path, target)
            if collection_data.get('archive_url'):
                from Core.archive_mods import prepare_archive_mods
                prepare_archive_mods(collection_data['archive_url'], prepared, progress_callback, cancel_event)
            for i, mod in enumerate(mods):
                if cancel_event and cancel_event.is_set():
                    raise InterruptedError("Установка отменена")
                name = mod.get('name') or mod.get('filename') or 'мод без имени'
                if progress_callback:
                    progress_callback(i, len(mods), name, status='loading')
                info = dict(mod)
                info['file'] = mod.get('filename') or f"{name}.jar"
                info['minecraft_version'] = version
                info['loader'] = loader
                source = mod.get('source', 'modrinth')
                if source == 'local':
                    copy_local_mod(mod, get_collections_dir(),
                                   os.path.join(prepared, safe_filename(info['file'])))
                elif not download_single_mod_turbo_sync(info, staging, source=source,
                                                        minecraft_version=version, loader=loader):
                    raise RuntimeError(f"Не удалось скачать {name}")
                if progress_callback:
                    progress_callback(i, len(mods), name, status='success')
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Установка отменена")
            # Validate once, after all downloads, before modifying the current installation.
            for candidate in Path(prepared).rglob('*.jar'):
                with zipfile.ZipFile(candidate) as archive:
                    if archive.testzip() is not None:
                        raise ValueError(f'Повреждённый мод: {candidate.name}')
            manager = ModsBackupManager(minecraft_dir)
            existing = [f for f in os.listdir(mods_dir) if f.lower().endswith('.jar')]
            if create_backup and existing and not manager.create_backup():
                raise RuntimeError("Не удалось создать бэкап: текущие моды сохранены")
            replace_mods(prepared, mods_dir, os.path.join(staging, 'previous'))
            if progress_callback and collection_data.get('archive_url'):
                progress_callback(1, 1, 'Моды установлены', status='archive_complete')
        set_current_collection(collection_data.get('name'))
        return True
    except Exception as exc:
        logger.exception("Установка сборки отменена без замены текущих модов: %s", exc)
        if raise_on_error:
            raise RuntimeError(f'{exc}. Текущие моды сохранены.') from exc
        return False


def get_collection_mods_info(collection_data: Dict) -> List[Dict]:
    """Получает информацию о модах в сборке"""
    mods_info = []

    for mod in collection_data.get('mods', []):
        mod_info = {
            'name': mod.get('name', 'Unknown'),
            'source': mod.get('source', 'unknown'),
            'filename': mod.get('filename', ''),
            'mod_id': mod.get('modrinth_id') or mod.get('curseforge_id', ''),
        }
        mods_info.append(mod_info)

    return mods_info
