CURRENT_VERSION = "0.9.1"

version_configs = {
    "YamalPixel": ("1.20.1", "fabric", "0.17.2"),
    "Minecraft 1.12.2": ("1.12.2", None, None),
    "Minecraft 1.12.2 + Fabric": ("1.12.2", "fabric", "0.17.2"),
    "Minecraft 1.12.2 + Forge": ("1.12.2", "forge", "latest"),
    "Minecraft 1.12.2 + Quilt": ("1.12.2", "quilt", None),

    "Minecraft 1.14.4": ("1.14.4", None, None),
    "Minecraft 1.14.4 + Fabric": ("1.14.4", "fabric", "0.17.2"),
    "Minecraft 1.14.4 + Forge": ("1.14.4", "forge", "latest"),
    "Minecraft 1.14.4 + Quilt": ("1.14.4", "quilt", None),

    "Minecraft 1.15.2": ("1.15.2", None, None),
    "Minecraft 1.15.2 + Fabric": ("1.15.2", "fabric", "0.17.2"),
    "Minecraft 1.15.2 + Forge": ("1.15.2", "forge", "latest"),
    "Minecraft 1.15.2 + Quilt": ("1.15.2", "quilt", None),

    "Minecraft 1.16.5": ("1.16.5", None, None),
    "Minecraft 1.16.5 + Fabric": ("1.16.5", "fabric", "0.17.2"),
    "Minecraft 1.16.5 + Forge": ("1.16.5", "forge", "latest"),
    "Minecraft 1.16.5 + Quilt": ("1.16.5", "quilt", None),

    "Minecraft 1.17.1": ("1.17.1", None, None),
    "Minecraft 1.17.1 + Fabric": ("1.17.1", "fabric", "0.17.2"),
    "Minecraft 1.17.1 + Forge": ("1.17.1", "forge", "latest"),
    "Minecraft 1.17.1 + Quilt": ("1.17.1", "quilt", None),

    "Minecraft 1.18.2": ("1.18.2", None, None),
    "Minecraft 1.18.2 + Fabric": ("1.18.2", "fabric", "0.17.2"),
    "Minecraft 1.18.2 + Forge": ("1.18.2", "forge", "latest"),
    "Minecraft 1.18.2 + Quilt": ("1.18.2", "quilt", None),

    "Minecraft 1.19.2": ("1.19.2", None, None),
    "Minecraft 1.19.2 + Fabric": ("1.19.2", "fabric", "0.17.2"),
    "Minecraft 1.19.2 + Forge": ("1.19.2", "forge", "latest"),
    "Minecraft 1.19.2 + Quilt": ("1.19.2", "quilt", None),

    "Minecraft 1.20.1": ("1.20.1", None, None),
    "Minecraft 1.20.1 + Fabric": ("1.20.1", "fabric", "0.17.2"),
    "Minecraft 1.20.1 + Forge": ("1.20.1", "forge", "latest"),
    "Minecraft 1.20.1 + Quilt": ("1.20.1", "quilt", None),

    "Minecraft 1.20.2": ("1.20.2", None, None),
    "Minecraft 1.20.2 + Fabric": ("1.20.2", "fabric", "0.17.2"),
    "Minecraft 1.20.2 + Forge": ("1.20.2", "forge", "latest"),
    "Minecraft 1.20.2 + Quilt": ("1.20.2", "quilt", None),
    "Minecraft 1.20.2 + NeoForge": ("1.20.2", "neoforge", None),

    "Minecraft 1.20.3": ("1.20.3", None, None),
    "Minecraft 1.20.3 + Fabric": ("1.20.3", "fabric", "0.17.2"),
    "Minecraft 1.20.3 + Forge": ("1.20.3", "forge", "latest"),
    "Minecraft 1.20.3 + Quilt": ("1.20.3", "quilt", None),
    "Minecraft 1.20.3 + NeoForge": ("1.20.3", "neoforge", None),

    "Minecraft 1.20.4": ("1.20.4", None, None),
    "Minecraft 1.20.4 + Fabric": ("1.20.4", "fabric", "0.17.2"),
    "Minecraft 1.20.4 + Forge": ("1.20.4", "forge", "latest"),
    "Minecraft 1.20.4 + Quilt": ("1.20.4", "quilt", None),
    "Minecraft 1.20.4 + NeoForge": ("1.20.4", "neoforge", None),

    "Minecraft 1.20.5": ("1.20.5", None, None),
    "Minecraft 1.20.5 + Fabric": ("1.20.5", "fabric", "0.17.2"),
    "Minecraft 1.20.5 + Forge": ("1.20.5", "forge", "latest"),
    "Minecraft 1.20.5 + Quilt": ("1.20.5", "quilt", None),
    "Minecraft 1.20.5 + NeoForge": ("1.20.5", "neoforge", None),

    "Minecraft 1.20.6": ("1.20.6", None, None),
    "Minecraft 1.20.6 + Fabric": ("1.20.6", "fabric", "0.17.2"),
    "Minecraft 1.20.6 + Forge": ("1.20.6", "forge", "latest"),
    "Minecraft 1.20.6 + Quilt": ("1.20.6", "quilt", None),
    "Minecraft 1.20.6 + NeoForge": ("1.20.6", "neoforge", None),

    "Minecraft 1.21": ("1.21", None, None),
    "Minecraft 1.21 + Fabric": ("1.21", "fabric", "0.17.2"),
    "Minecraft 1.21 + Forge": ("1.21", "forge", "latest"),
    "Minecraft 1.21 + Quilt": ("1.21", "quilt", None),
    "Minecraft 1.21 + NeoForge": ("1.21", "neoforge", None),

    "Minecraft 1.21.1": ("1.21.1", None, None),
    "Minecraft 1.21.1 + Fabric": ("1.21.1", "fabric", "0.17.2"),
    "Minecraft 1.21.1 + Forge": ("1.21.1", "forge", "latest"),
    "Minecraft 1.21.1 + Quilt": ("1.21.1", "quilt", None),
    "Minecraft 1.21.1 + NeoForge": ("1.21.1", "neoforge", None),

    "Minecraft 1.21.2": ("1.21.2", None, None),
    "Minecraft 1.21.2 + Fabric": ("1.21.2", "fabric", "0.17.2"),
    "Minecraft 1.21.2 + Forge": ("1.21.2", "forge", "latest"),
    "Minecraft 1.21.2 + Quilt": ("1.21.2", "quilt", None),
    "Minecraft 1.21.2 + NeoForge": ("1.21.2", "neoforge", None),

    "Minecraft 1.21.3": ("1.21.3", None, None),
    "Minecraft 1.21.3 + Fabric": ("1.21.3", "fabric", "0.17.2"),
    "Minecraft 1.21.3 + Forge": ("1.21.3", "forge", "latest"),
    "Minecraft 1.21.3 + Quilt": ("1.21.3", "quilt", None),
    "Minecraft 1.21.3 + NeoForge": ("1.21.3", "neoforge", None),

    "Minecraft 1.21.4": ("1.21.4", None, None),
    "Minecraft 1.21.4 + Fabric": ("1.21.4", "fabric", "0.17.2"),
    "Minecraft 1.21.4 + Forge": ("1.21.4", "forge", "latest"),
    "Minecraft 1.21.4 + Quilt": ("1.21.4", "quilt", None),
    "Minecraft 1.21.4 + NeoForge": ("1.21.4", "neoforge", None),
}

fabric_supported_versions = [
    "YamalPixel",
    "Minecraft 1.14.4 + Fabric",
    "Minecraft 1.15.2 + Fabric",
    "Minecraft 1.16.5 + Fabric",
    "Minecraft 1.17.1 + Fabric",
    "Minecraft 1.18.2 + Fabric",
    "Minecraft 1.19.2 + Fabric",
    "Minecraft 1.20.1 + Fabric",
    "Minecraft 1.20.2 + Fabric",
    "Minecraft 1.20.3 + Fabric",
    "Minecraft 1.20.4 + Fabric",
    "Minecraft 1.20.5 + Fabric",
    "Minecraft 1.20.6 + Fabric",
    "Minecraft 1.21 + Fabric",
    "Minecraft 1.21.1 + Fabric",
    "Minecraft 1.21.2 + Fabric",
    "Minecraft 1.21.3 + Fabric",
    "Minecraft 1.21.4 + Fabric",
]

quilt_supported_versions = [
    "Minecraft 1.14.4 + Quilt",
    "Minecraft 1.15.2 + Quilt",
    "Minecraft 1.16.5 + Quilt",
    "Minecraft 1.17.1 + Quilt",
    "Minecraft 1.18.2 + Quilt",
    "Minecraft 1.19.2 + Quilt",
    "Minecraft 1.20.1 + Quilt",
    "Minecraft 1.20.2 + Quilt",
    "Minecraft 1.20.3 + Quilt",
    "Minecraft 1.20.4 + Quilt",
    "Minecraft 1.20.5 + Quilt",
    "Minecraft 1.20.6 + Quilt",
    "Minecraft 1.21 + Quilt",
    "Minecraft 1.21.1 + Quilt",
    "Minecraft 1.21.2 + Quilt",
    "Minecraft 1.21.3 + Quilt",
    "Minecraft 1.21.4 + Quilt",
]

neoforge_supported_versions = [
    "Minecraft 1.20.2 + NeoForge",
    "Minecraft 1.20.3 + NeoForge",
    "Minecraft 1.20.4 + NeoForge",
    "Minecraft 1.20.5 + NeoForge",
    "Minecraft 1.20.6 + NeoForge",
    "Minecraft 1.21 + NeoForge",
    "Minecraft 1.21.1 + NeoForge",
    "Minecraft 1.21.2 + NeoForge",
    "Minecraft 1.21.3 + NeoForge",
    "Minecraft 1.21.4 + NeoForge",
]

forge_supported_versions = [
    "Minecraft 1.12.2 + Forge",
    "Minecraft 1.14.4 + Forge",
    "Minecraft 1.15.2 + Forge",
    "Minecraft 1.16.5 + Forge",
    "Minecraft 1.17.1 + Forge",
    "Minecraft 1.18.2 + Forge",
    "Minecraft 1.19.2 + Forge",
    "Minecraft 1.20.1 + Forge",
    "Minecraft 1.20.2 + Forge",
    "Minecraft 1.20.3 + Forge",
    "Minecraft 1.20.4 + Forge",
    "Minecraft 1.20.5 + Forge",
    "Minecraft 1.20.6 + Forge",
    "Minecraft 1.21 + Forge",
    "Minecraft 1.21.1 + Forge",
    "Minecraft 1.21.2 + Forge",
    "Minecraft 1.21.3 + Forge",
    "Minecraft 1.21.4 + Forge",
]

all_versions = [
    "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
    "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.5",
    "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
]

# === НОВЫЕ ФУНКЦИИ ===

def load_user_collections_safely():
    """Безопасная загрузка пользовательских сборок"""
    try:
        from ConfDir.Configs import load_user_collections
        return load_user_collections()
    except (ImportError, AttributeError) as e:
        print(f"⚠️ Не удалось загрузить пользовательские сборки: {e}")
        return []  # Возвращаем пустой список при ошибке

def get_all_version_configs():
    """Возвращает все конфигурации версий: статические + пользовательские"""
    all_configs = version_configs.copy()
    user_collections = load_user_collections_safely()

    for collection in user_collections:
        collection_name = f"📦 {collection['name']}"
        all_configs[collection_name] = (
            collection['minecraft_version'],
            collection['loader'],
            collection.get('loader_version')
        )

        # Добавляем в списки поддержки
        loader = collection['loader']
        if loader == "fabric" and collection_name not in fabric_supported_versions:
            fabric_supported_versions.append(collection_name)
        elif loader == "quilt" and collection_name not in quilt_supported_versions:
            quilt_supported_versions.append(collection_name)
        elif loader == "forge" and collection_name not in forge_supported_versions:
            forge_supported_versions.append(collection_name)
        elif loader == "neoforge" and collection_name not in neoforge_supported_versions:
            neoforge_supported_versions.append(collection_name)

    return all_configs


def get_version_config(version_name):
    """Возвращает конфигурацию для указанной версии (включая кастомные сборки)"""
    # Проверяем статические версии
    if version_name in version_configs:
        return version_configs[version_name]

    # Проверяем кастомные сборки
    if version_name.startswith("📦 "):
        try:
            from ConfDir.Configs import COLLECTIONS_CONFIG
            import json
            import os

            collection_name = version_name[2:]  # Убираем эмодзи
            collections_dir = COLLECTIONS_CONFIG["collections_dir"]

            if os.path.exists(collections_dir):
                for filename in os.listdir(collections_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(collections_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if data['name'] == collection_name:
                            # Возвращаем конфигурацию сборки
                            return (
                                data['minecraft_version'],
                                data['loader'],
                                #data.get('loader_version')
                            )
        except Exception as e:
            print(f"❌ Ошибка получения конфигурации сборки: {e}")

    return None


def get_all_versions():
    """Возвращает ВСЕ версии (статические + пользовательские)"""
    # Статические версии
    all_versions = []

    # Добавляем YamalPixel первым
    if "YamalPixel" in version_configs:
        all_versions.append("YamalPixel")

    # Добавляем остальные статические версии
    for version_name in version_configs.keys():
        if version_name != "YamalPixel" and version_name not in all_versions:
            all_versions.append(version_name)

    print(f"📋 Статических версий: {len(all_versions)}")

    # Добавляем пользовательские сборки
    try:
        from ConfDir.Configs import COLLECTIONS_CONFIG
        import json
        import os

        collections_dir = COLLECTIONS_CONFIG.get("collections_dir", "collections")
        print(f"📁 Проверяем папку сборок: {collections_dir}")

        if os.path.exists(collections_dir):
            json_files = [f for f in os.listdir(collections_dir) if f.endswith('.json')]
            print(f"📄 Найдено JSON файлов: {len(json_files)}")

            for filename in json_files:
                try:
                    filepath = os.path.join(collections_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if 'name' in data:
                        collection_name = f"📦 {data['name']}"
                        if collection_name not in all_versions:
                            all_versions.append(collection_name)
                            print(f"   + Добавлена сборка: {collection_name}")
                        else:
                            print(f"   ⚠️ Сборка уже есть в списке: {collection_name}")

                except Exception as e:
                    print(f"⚠️ Ошибка загрузки сборки {filename}: {e}")

        else:
            print(f"📁 Папка сборок не существует: {collections_dir}")

    except Exception as e:
        print(f"❌ Не удалось загрузить пользовательские сборки: {e}")

    print(f"📊 Всего версий: {len(all_versions)}")

    return all_versions


def get_minecraft_version(version_name):
    """Получает версию Minecraft для выбранной версии"""
    config = get_version_config(version_name)
    if config:
        return config[0]  # Версия Minecraft

    # Запасной вариант для старых версий
    version_map = {
        "YamalPixel": "1.20.1",
        "Minecraft 1.12.2": "1.12.2",
        "Minecraft 1.12.2 + Fabric": "1.12.2",
        "Minecraft 1.12.2 + Forge": "1.12.2",
        "Minecraft 1.12.2 + Quilt": "1.12.2",

        "Minecraft 1.14.4": "1.14.4",
        "Minecraft 1.14.4 + Fabric": "1.14.4",
        "Minecraft 1.14.4 + Forge": "1.14.4",
        "Minecraft 1.14.4 + Quilt": "1.14.4",

        "Minecraft 1.15.2": "1.15.2",
        "Minecraft 1.15.2 + Fabric": "1.15.2",
        "Minecraft 1.15.2 + Forge": "1.15.2",
        "Minecraft 1.15.2 + Quilt": "1.15.2",

        "Minecraft 1.16.5": "1.16.5",
        "Minecraft 1.16.5 + Fabric": "1.16.5",
        "Minecraft 1.16.5 + Forge": "1.16.5",
        "Minecraft 1.16.5 + Quilt": "1.16.5",

        "Minecraft 1.17.1": "1.17.1",
        "Minecraft 1.17.1 + Fabric": "1.17.1",
        "Minecraft 1.17.1 + Forge": "1.17.1",
        "Minecraft 1.17.1 + Quilt": "1.17.1",

        "Minecraft 1.18.2": "1.18.2",
        "Minecraft 1.18.2 + Fabric": "1.18.2",
        "Minecraft 1.18.2 + Forge": "1.18.2",
        "Minecraft 1.18.2 + Quilt": "1.18.2",

        "Minecraft 1.19.2": "1.19.2",
        "Minecraft 1.19.2 + Fabric": "1.19.2",
        "Minecraft 1.19.2 + Forge": "1.19.2",
        "Minecraft 1.19.2 + Quilt": "1.19.2",

        "Minecraft 1.20.1": "1.20.1",
        "Minecraft 1.20.1 + Fabric": "1.20.1",
        "Minecraft 1.20.1 + Forge": "1.20.1",
        "Minecraft 1.20.1 + Quilt": "1.20.1",
        "Minecraft 1.20.1 + NeoForge": "1.20.1",

        "Minecraft 1.20.2": "1.20.2",
        "Minecraft 1.20.2 + Fabric": "1.20.2",
        "Minecraft 1.20.2 + Forge": "1.20.2",
        "Minecraft 1.20.2 + Quilt": "1.20.2",
        "Minecraft 1.20.2 + NeoForge": "1.20.2",

        "Minecraft 1.20.3": "1.20.3",
        "Minecraft 1.20.3 + Fabric": "1.20.3",
        "Minecraft 1.20.3 + Forge": "1.20.3",
        "Minecraft 1.20.3 + Quilt": "1.20.3",
        "Minecraft 1.20.3 + NeoForge": "1.20.3",

        "Minecraft 1.20.4": "1.20.4",
        "Minecraft 1.20.4 + Fabric": "1.20.4",
        "Minecraft 1.20.4 + Forge": "1.20.4",
        "Minecraft 1.20.4 + Quilt": "1.20.4",
        "Minecraft 1.20.4 + NeoForge": "1.20.4",

        "Minecraft 1.20.5": "1.20.5",
        "Minecraft 1.20.5 + Fabric": "1.20.5",
        "Minecraft 1.20.5 + Forge": "1.20.5",
        "Minecraft 1.20.5 + Quilt": "1.20.5",
        "Minecraft 1.20.5 + NeoForge": "1.20.5",

        "Minecraft 1.20.6": "1.20.6",
        "Minecraft 1.20.6 + Fabric": "1.20.6",
        "Minecraft 1.20.6 + Forge": "1.20.6",
        "Minecraft 1.20.6 + Quilt": "1.20.6",
        "Minecraft 1.20.6 + NeoForge": "1.20.6",

        "Minecraft 1.21": "1.21",
        "Minecraft 1.21 + Fabric": "1.21",
        "Minecraft 1.21 + Forge": "1.21",
        "Minecraft 1.21 + Quilt": "1.21",
        "Minecraft 1.21 + NeoForge": "1.21",

        "Minecraft 1.21.1": "1.21.1",
        "Minecraft 1.21.1 + Fabric": "1.21.1",
        "Minecraft 1.21.1 + Forge": "1.21.1",
        "Minecraft 1.21.1 + Quilt": "1.21.1",
        "Minecraft 1.21.1 + NeoForge": "1.21.1",

        "Minecraft 1.21.2": "1.21.2",
        "Minecraft 1.21.2 + Fabric": "1.21.2",
        "Minecraft 1.21.2 + Forge": "1.21.2",
        "Minecraft 1.21.2 + Quilt": "1.21.2",
        "Minecraft 1.21.2 + NeoForge": "1.21.2",

        "Minecraft 1.21.3": "1.21.3",
        "Minecraft 1.21.3 + Fabric": "1.21.3",
        "Minecraft 1.21.3 + Forge": "1.21.3",
        "Minecraft 1.21.3 + Quilt": "1.21.3",
        "Minecraft 1.21.3 + NeoForge": "1.21.3",

        "Minecraft 1.21.4": "1.21.4",
        "Minecraft 1.21.4 + Fabric": "1.21.4",
        "Minecraft 1.21.4 + Forge": "1.21.4",
        "Minecraft 1.21.4 + Quilt": "1.21.4",
        "Minecraft 1.21.4 + NeoForge": "1.21.4",
    }

    return version_map.get(version_name, "1.20.1")


def is_modloader_needed(selected_version):
    """Определяет, нужен ли модлоадер и какой (включая кастомные сборки)"""
    # Проверяем статические версии
    if selected_version in fabric_supported_versions:
        return "fabric"
    elif selected_version in quilt_supported_versions:
        return "quilt"
    elif selected_version in forge_supported_versions:
        return "forge"
    elif selected_version in neoforge_supported_versions:
        return "neoforge"

    # Проверяем кастомные сборки
    if selected_version.startswith("📦 "):
        try:
            from ConfDir.Configs import COLLECTIONS_CONFIG
            import json
            import os

            collection_name = selected_version[2:]
            collections_dir = COLLECTIONS_CONFIG["collections_dir"]

            if os.path.exists(collections_dir):
                for filename in os.listdir(collections_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(collections_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if data['name'] == collection_name:
                            return data['loader']  # Возвращаем тип загрузчика сборки
        except Exception as e:
            print(f"❌ Ошибка определения загрузчика сборки: {e}")

    return None

# === ИНИЦИАЛИЗАЦИЯ СПИСКОВ ПОСЛЕ ЗАГРУЗКИ ===
versions = get_all_versions()


# Versions.py - добавить в конец файла

def load_user_collections():
    """Загружает пользовательские сборки из папки collections"""
    try:
        from ConfDir.Configs import COLLECTIONS_CONFIG
        import json
        import os

        collections_dir = COLLECTIONS_CONFIG["collections_dir"]
        if not os.path.exists(collections_dir):
            return []

        collections = []
        for filename in os.listdir(collections_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(collections_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Добавляем сборку в список версий
                    collection_name = f"📦 {data['name']}"

                    # Добавляем в общий список
                    collections.append({
                        'name': collection_name,
                        'filename': filename,
                        'data': data
                    })

                except Exception as e:
                    print(f"⚠️ Ошибка загрузки сборки {filename}: {e}")

        return collections

    except Exception as e:
        print(f"❌ Ошибка загрузки пользовательских сборок: {e}")
        return []