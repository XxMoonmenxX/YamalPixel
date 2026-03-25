# Core/collection_loader.py
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from ConfDir.Configs import COLLECTIONS_CONFIG, CONFIG
from Network.ModrinthLoader import ModrinthAPI
from Network.CurseForgeLoader import CurseForgeAPI


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
    """Устанавливает сборку (скачивает моды) - для PyQt6"""
    try:
        from Core.run import set_current_collection
        mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
        os.makedirs(mods_dir, exist_ok=True)

        modrinth_api = ModrinthAPI()
        curseforge_api = None

        # Инициализируем CurseForge API если доступен
        from ConfDir.Configs import CURSEFORGE_CONFIG
        if CURSEFORGE_CONFIG.get("enabled", False):
            try:
                proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://localhost:8000")
                curseforge_api = CurseForgeAPI(proxy_url)
            except:
                pass

        if success_count == total_mods:
            # Сохраняем текущую сборку
            set_current_collection(collection_data['name'])

        total_mods = len(collection_data.get('mods', []))
        success_count = 0

        for i, mod in enumerate(collection_data.get('mods', [])):
            if progress_callback:
                progress_callback(i, total_mods, mod.get('name', 'Unknown'))

            source = mod.get('source', 'modrinth')

            try:
                if source == 'modrinth':
                    mod_id = mod.get('modrinth_id')
                    if not mod_id:
                        continue

                    versions = modrinth_api.get_mod_versions(
                        mod_id=mod_id,
                        minecraft_version=collection_data['minecraft_version'],
                        loader=collection_data['loader'].lower()
                    )

                    if versions:
                        latest_version = versions[0]
                        if latest_version.get('files'):
                            file_info = latest_version['files'][0]
                            filename = file_info['filename']
                            project_slug = mod.get('modrinth_slug', mod_id)

                            # Используем метод download_mod из ModrinthAPI
                            if modrinth_api.download_mod(project_slug, latest_version['id'], filename, mods_dir):
                                success_count += 1
                            else:
                                # Пробуем альтернативный метод
                                from Network.Downloader import download_single_mod_turbo
                                temp_mod = {"file": filename, "url": f"https://modrinth.com/mod/{project_slug}"}
                                if download_single_mod_turbo(temp_mod, CONFIG["minecraft_dir"]):
                                    success_count += 1

                elif source == 'curseforge' and curseforge_api:
                    mod_id = mod.get('curseforge_id')
                    if not mod_id:
                        continue

                    versions = curseforge_api.get_mod_versions(
                        mod_id=str(mod_id),
                        minecraft_version=collection_data['minecraft_version'],
                        loader=collection_data['loader'].lower()
                    )

                    if versions:
                        version_info = versions[0]
                        filename = version_info.get('filename', f'mod-{mod_id}.jar')

                        if curseforge_api.download_mod(str(mod_id), version_info['id'], filename, mods_dir):
                            success_count += 1

                elif source == 'local':
                    # Локальные моды копируем из папки сборки
                    local_path = os.path.join(get_collections_dir(), 'mods', mod.get('filename', ''))
                    if os.path.exists(local_path):
                        shutil.copy2(local_path, os.path.join(mods_dir, mod['filename']))
                        success_count += 1

            except Exception as e:
                print(f"Ошибка установки мода {mod.get('name')}: {e}")

        return success_count == total_mods
    except Exception as e:
        print(f"❌ Ошибка установки сборки: {e}")
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