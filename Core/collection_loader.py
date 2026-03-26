# Core/collection_loader.py
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from ConfDir.Configs import COLLECTIONS_CONFIG, CONFIG
from Network.Downloader import download_single_mod_turbo_sync
from Core.backup import ModsBackupManager
import logging

logger = logging.getLogger(__name__)


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

                    # Проверяем имя сборки (с учетом эмодзи и без)
                    if data.get('name') == collection_name or f"📦 {data.get('name')}" == collection_name:
                        data['filename'] = filename
                        return data
                except Exception as e:
                    print(f"⚠️ Ошибка чтения файла {filename}: {e}")

        return None
    except Exception as e:
        print(f"❌ Ошибка загрузки сборки {collection_name}: {e}")
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

                # Проверяем обязательные поля
                if all(key in data for key in ['name', 'minecraft_version', 'loader']):
                    # Получаем дату создания
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
                print(f"⚠️ Ошибка загрузки сборки {filename}: {e}")

    # Сортируем по дате создания (новые сверху)
    collections.sort(key=lambda x: x['created_at'], reverse=True)
    return collections


def save_collection(collection_data: Dict, filename: str = None) -> tuple:
    """Сохраняет сборку"""
    try:
        collections_dir = get_collections_dir()
        os.makedirs(collections_dir, exist_ok=True)

        # Генерируем имя файла если не указано
        if not filename:
            safe_name = "".join(c for c in collection_data['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name[:50]
            filename = f"{safe_name}.json"

        filepath = os.path.join(collections_dir, filename)

        # Добавляем метаданные
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
        print(f"❌ Ошибка удаления сборки: {e}")
        return False


def install_collection(collection_data: Dict, progress_callback=None, create_backup=True) -> bool:
    """
    Устанавливает сборку с бэкапом и проверкой совместимости
    """
    from Core.run import set_current_collection
    from Core.backup import ModsBackupManager

    mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
    os.makedirs(mods_dir, exist_ok=True)

    backup_manager = ModsBackupManager(CONFIG["minecraft_dir"])

    # 1. Создаём бэкап
    if create_backup:
        backup_path = backup_manager.create_backup()
        if backup_path:
            logger.info(f"📦 Создан бэкап: {os.path.basename(backup_path)}")
        else:
            logger.warning("⚠️ Бэкап не создан, продолжаем...")
    else:
        logger.info("⏭️ Создание бэкапа пропущено")

    # 2. Очищаем папку модов
    removed_count = backup_manager.clear_mods()
    logger.info(f"🗑️ Очищено {removed_count} модов")

    total_mods = len(collection_data.get('mods', []))
    success_count = 0
    skipped_count = 0

    minecraft_version = collection_data.get('minecraft_version', '1.20.1')
    loader = collection_data.get('loader', 'fabric')

    for i, mod in enumerate(collection_data.get('mods', [])):
        mod_name = mod.get('name', 'Unknown')

        if progress_callback:
            progress_callback(i, total_mods, mod_name)

        # 3. Проверка совместимости
        is_compatible, reason = check_mod_compatibility(mod, minecraft_version, loader)

        if not is_compatible:
            logger.warning(f"⚠️ Пропущен {mod_name}: {reason}")
            skipped_count += 1
            if progress_callback:
                progress_callback(i, total_mods, mod_name, status="skipped", reason=reason)
            continue

        source = mod.get('source', 'modrinth')

        logger.debug(f"   [{i + 1}/{total_mods}] Загрузка: {mod_name} (источник: {source})")

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

            success = download_single_mod_turbo_sync(
                mod_info=mod_info,
                minecraft_dir=CONFIG["minecraft_dir"],
                source=source,
                minecraft_version=minecraft_version,
                loader=loader
            )

            if success:
                success_count += 1
                logger.info(f"   ✅ {mod_name} - установлен")
            else:
                logger.warning(f"   ❌ {mod_name} - не удалось загрузить")

        except Exception as e:
            logger.error(f"   💥 Ошибка установки мода {mod_name}: {e}")

    # 4. Итог
    logger.info(f"📊 Итог: установлено {success_count}/{total_mods} модов (пропущено {skipped_count})")

    if success_count >= total_mods // 2:
        set_current_collection(collection_data.get('name'))
        logger.info(f"✅ Сборка '{collection_data.get('name')}' установлена")
        return True
    else:
        logger.warning(f"⚠️ Сборка '{collection_data.get('name')}' установлена частично")

        # Предлагаем восстановить бэкап при неудаче
        if create_backup and backup_path:
            logger.info("💡 Для восстановления используйте кнопку 'Восстановить бэкап'")

        return False


def check_mod_compatibility(mod, minecraft_version: str, loader: str) -> tuple:
    """
    Проверяет совместимость мода с версией Minecraft и загрузчиком
    Возвращает (is_compatible, reason)
    """
    # Проверка версии Minecraft из названия файла
    filename = mod.get('filename', '')
    filename_lower = filename.lower()

    # Ищем версию в имени файла
    if '1.20.1' in filename_lower and minecraft_version != '1.20.1':
        return False, f"Мод для 1.20.1, а игра на {minecraft_version}"
    if '1.21' in filename_lower and not minecraft_version.startswith('1.21'):
        return False, f"Мод для 1.21.x, а игра на {minecraft_version}"

    # Проверка загрузчика
    if 'forge' in filename_lower and loader != 'forge':
        return False, f"Мод для Forge, а выбран {loader}"
    if 'fabric' in filename_lower and loader != 'fabric':
        return False, f"Мод для Fabric, а выбран {loader}"
    if 'neoforge' in filename_lower and loader != 'neoforge':
        return False, f"Мод для NeoForge, а выбран {loader}"
    if 'quilt' in filename_lower and loader != 'quilt':
        return False, f"Мод для Quilt, а выбран {loader}"

    return True, "OK"

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