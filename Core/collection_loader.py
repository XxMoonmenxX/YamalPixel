# Core/collection_loader.py
import os
import json
import logging
import traceback
from datetime import datetime
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
                        'created_at': created_date,
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

        filepath = os.path.join(collections_dir, filename)

        collection_data['updated_at'] = datetime.now().isoformat()
        if 'created_at' not in collection_data:
            collection_data['created_at'] = datetime.now().isoformat()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, indent=2, ensure_ascii=False)

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


def install_collection(collection_data: Dict, progress_callback=None, create_backup=True) -> bool:
    """
    Устанавливает сборку с бэкапом и проверкой совместимости
    """
    from Core.run import set_current_collection
    from Core.backup import ModsBackupManager

    logger.info("=" * 60)
    logger.info("🚀 START install_collection")
    logger.info(f"   collection_data keys: {list(collection_data.keys())}")
    logger.info(f"   mods count: {len(collection_data.get('mods', []))}")
    logger.info(f"   create_backup: {create_backup}")
    logger.info("=" * 60)

    try:
        mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
        os.makedirs(mods_dir, exist_ok=True)
        logger.info(f"✅ mods_dir: {mods_dir}")

        backup_manager = ModsBackupManager(CONFIG["minecraft_dir"])
        logger.info("✅ backup_manager created")

        # 1. Создаём бэкап
        backup_path = None
        if create_backup:
            logger.info("📦 Creating backup...")
            backup_path = backup_manager.create_backup()
            if backup_path:
                logger.info(f"✅ Backup created: {backup_path}")
            else:
                logger.warning("⚠️ Backup not created")
        else:
            logger.info("⏭️ Backup skipped")

        # 2. Очищаем папку модов
        logger.info("🗑️ Clearing mods directory...")
        removed_count = backup_manager.clear_mods()
        logger.info(f"✅ Cleared {removed_count} mods")

        total_mods = len(collection_data.get('mods', []))
        success_count = 0
        skipped_count = 0

        minecraft_version = collection_data.get('minecraft_version', '1.20.1')
        loader = collection_data.get('loader', 'fabric')

        logger.info(f"📋 Collection info: MC={minecraft_version}, loader={loader}, total_mods={total_mods}")

        for i, mod in enumerate(collection_data.get('mods', [])):
            mod_name = mod.get('name', 'Unknown')
            logger.info(f"🔍 Processing mod {i+1}/{total_mods}: {mod_name}")

            if progress_callback:
                try:
                    progress_callback(i, total_mods, mod_name)
                except Exception as e:
                    logger.error(f"   ❌ progress_callback error: {e}")

            # Проверка совместимости
            is_compatible, reason = check_mod_compatibility(mod, minecraft_version, loader)

            if not is_compatible:
                logger.warning(f"   ⚠️ Skipped {mod_name}: {reason}")
                skipped_count += 1
                if progress_callback:
                    try:
                        progress_callback(i, total_mods, mod_name, status="skipped", reason=reason)
                    except Exception as e:
                        logger.error(f"   ❌ progress_callback error: {e}")
                continue

            source = mod.get('source', 'modrinth')

            try:
                mod_info = {
                    "file": mod.get('filename', f"{mod.get('modrinth_slug', mod_name)}.jar"),
                    "name": mod_name,
                    "source": source,
                    "minecraft_version": minecraft_version,
                    "loader": loader
                }

                if source == 'modrinth':
                    mod_info["modrinth_id"] = mod.get('modrinth_id')
                    mod_info["project_id"] = mod.get('modrinth_id')
                    mod_info["version_id"] = mod.get('version_id')
                elif source == 'curseforge':
                    mod_info["curseforge_id"] = str(mod.get('curseforge_id'))
                    mod_info["project_id"] = str(mod.get('curseforge_id'))
                elif source == 'yandex' or source == 'local':
                    mod_info["url"] = mod.get('url', '')

                logger.info(f"   📥 Downloading {mod_name}...")
                success = download_single_mod_turbo_sync(
                    mod_info=mod_info,
                    minecraft_dir=CONFIG["minecraft_dir"],
                    source=source,
                    minecraft_version=minecraft_version,
                    loader=loader
                )

                if success:
                    success_count += 1
                    logger.info(f"   ✅ {mod_name} installed")
                else:
                    logger.warning(f"   ❌ {mod_name} failed to download")

            except Exception as e:
                logger.error(f"   💥 Error installing {mod_name}: {e}")
                traceback.print_exc()

        # Итог
        logger.info(f"📊 Result: {success_count}/{total_mods} installed, {skipped_count} skipped")

        if success_count >= total_mods // 2:
            set_current_collection(collection_data.get('name'))
            logger.info(f"✅ Collection '{collection_data.get('name')}' installed")
            return True
        else:
            logger.warning(f"⚠️ Collection '{collection_data.get('name')}' partially installed")
            return False

    except Exception as e:
        logger.error(f"❌ Fatal error in install_collection: {e}")
        traceback.print_exc()
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