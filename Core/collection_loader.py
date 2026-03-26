# Core/collection_loader.py
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from ConfDir.Configs import COLLECTIONS_CONFIG, CONFIG
from Network.Downloader import download_single_mod_turbo_sync
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


def install_collection(collection_data: Dict, progress_callback=None) -> bool:
    """
    Устанавливает сборку (скачивает моды)
    Использует универсальную функцию загрузки с поддержкой прокси
    """
    try:
        from Core.run import set_current_collection

        mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
        os.makedirs(mods_dir, exist_ok=True)

        total_mods = len(collection_data.get('mods', []))
        success_count = 0

        # Сохраняем информацию о сборке для callback
        collection_name = collection_data.get('name', 'Unknown')
        minecraft_version = collection_data.get('minecraft_version', '1.20.1')
        loader = collection_data.get('loader', 'fabric')

        logger.info(f"📦 Установка сборки: {collection_name}")
        logger.info(f"   Версия: {minecraft_version}, Загрузчик: {loader}")
        logger.info(f"   Модов: {total_mods}")

        for i, mod in enumerate(collection_data.get('mods', [])):
            if progress_callback:
                progress_callback(i, total_mods, mod.get('name', 'Unknown'))

            source = mod.get('source', 'modrinth')
            mod_name = mod.get('name', 'Unknown')

            logger.debug(f"   [{i + 1}/{total_mods}] Загрузка: {mod_name} (источник: {source})")

            try:
                # Подготавливаем информацию о моде для загрузчика
                mod_info = {
                    "file": mod.get('filename', f"{mod.get('modrinth_slug', mod_name)}.jar"),
                    "name": mod_name,
                    "source": source,
                }

                # Добавляем URL в зависимости от источника
                if source == 'modrinth':
                    mod_info["modrinth_id"] = mod.get('modrinth_id')
                    mod_info["project_id"] = mod.get('modrinth_id')
                    mod_info["version_id"] = mod.get('version_id')  # может быть None
                elif source == 'curseforge':
                    mod_info["curseforge_id"] = str(mod.get('curseforge_id'))
                    mod_info["project_id"] = str(mod.get('curseforge_id'))
                elif source == 'yandex' or source == 'local':
                    mod_info["url"] = mod.get('url', '')

                # Используем универсальную функцию загрузки с передачей версии и загрузчика
                success = download_single_mod_turbo_sync(
                    mod_info=mod_info,
                    minecraft_dir=CONFIG["minecraft_dir"],
                    source=source,
                    minecraft_version=minecraft_version,  # ← передаём версию Minecraft
                    loader=loader  # ← передаём тип загрузчика
                )

                if success:
                    success_count += 1
                    logger.info(f"   ✅ {mod_name} - установлен")
                else:
                    logger.warning(f"   ❌ {mod_name} - не удалось загрузить")

            except Exception as e:
                logger.error(f"   💥 Ошибка установки мода {mod_name}: {e}")

        # Сохраняем текущую сборку если успешно загружено больше половины
        if success_count >= total_mods // 2:
            set_current_collection(collection_name)
            logger.info(f"✅ Сборка '{collection_name}' установлена ({success_count}/{total_mods})")
        else:
            logger.warning(f"⚠️ Сборка '{collection_name}' установлена частично ({success_count}/{total_mods})")

        return success_count == total_mods

    except Exception as e:
        logger.error(f"❌ Ошибка установки сборки: {e}")
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