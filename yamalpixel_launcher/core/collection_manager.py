# core/collection_manager.py
import json
import os
from pathlib import Path
from models.collection import Collection

COLLECTIONS_DIR_NAME = "collections"
COLLECTIONS_CONFIG_KEY = "collections_dir" # Ключ в CONFIG для пути к папке

class CollectionManager:
    def __init__(self, config_instance):
        self.config = config_instance
        # Определяем путь к папке коллекций, создаем если нет
        self.collections_dir = Path(self.config.get(COLLECTIONS_CONFIG_KEY, Path.home() / "YamalPixel" / COLLECTIONS_DIR_NAME))
        self.collections_dir.mkdir(parents=True, exist_ok=True)
        self.config.set(COLLECTIONS_CONFIG_KEY, str(self.collections_dir)) # Обновляем путь в конфиге, если был по умолчанию

    def load_collections(self):
        """Загружает список объектов Collection из JSON файлов в папке."""
        collections = []
        json_files = self.collections_dir.glob("*.json")
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Предполагаем, что формат файла соответствует Collection.to_dict()
                collection = Collection.from_dict(data)
                collections.append(collection)
            except Exception as e:
                print(f"❌ Ошибка загрузки коллекции {file_path.name}: {e}")
        return collections

    def save_collection(self, collection: Collection):
        """Сохраняет объект Collection в JSON файл."""
        try:
            # Очищаем имя от недопустимых символов для имени файла
            safe_name = "".join(c for c in collection.name if c not in '/\\:*?"<>|')
            filename = f"{safe_name}.json"
            filepath = self.collections_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(collection.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Сохранена коллекция: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения коллекции {collection.name}: {e}")
            return False

    def delete_collection(self, collection_name):
        """Удаляет JSON файл коллекции по имени."""
        try:
            safe_name = "".join(c for c in collection_name if c not in '/\\:*?"<>|')
            filename = f"{safe_name}.json"
            filepath = self.collections_dir / filename
            if filepath.exists():
                filepath.unlink() # Удаляет файл
                print(f"✅ Удалена коллекция: {filepath}")
                return True
            else:
                print(f"⚠️ Файл коллекции не найден: {filepath}")
                return False
        except Exception as e:
            print(f"❌ Ошибка удаления коллекции {collection_name}: {e}")
            return False

    def find_collection_by_name(self, name):
        """Находит коллекцию по имени."""
        collections = self.load_collections()
        for coll in collections:
            if coll.name == name:
                return coll
        return None

    def add_mod_to_collection(self, collection_name, mod_object):
        """Добавляет мод в существующую коллекцию."""
        collection = self.find_collection_by_name(collection_name)
        if collection:
            if mod_object not in collection.mods:
                collection.mods.append(mod_object)
                return self.save_collection(collection)
            else:
                print(f"Мод {mod_object.name} уже в коллекции {collection_name}")
                return False
        else:
            print(f"Коллекция {collection_name} не найдена")
            return False

    def remove_mod_from_collection(self, collection_name, mod_name):
        """Удаляет мод из коллекции по имени мода."""
        collection = self.find_collection_by_name(collection_name)
        if collection:
            collection.mods = [m for m in collection.mods if m.name != mod_name]
            return self.save_collection(collection)
        else:
            print(f"Коллекция {collection_name} не найдена")
            return False

    def get_collections_dir(self):
        """Возвращает путь к папке коллекций."""
        return self.collections_dir
