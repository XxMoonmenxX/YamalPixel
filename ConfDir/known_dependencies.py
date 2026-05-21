## ConfDir/known_dependencies.py
"""
Предопределенные зависимости для популярных модов
"""

KNOWN_DEPENDENCIES = {
    # CurseForge IDs
    "techreborn": {
        "fabric": [
            {
                "name": "Fabric API",
                "source": "modrinth",
                "mod_id": "fabric-api",
                "modrinth_id": "P7dR8mSH",
                "version_range": ">=0.86.1",
                "type": "required"
            },
            {
                "name": "Reborn Core",
                "source": "curseforge",
                "curseforge_id": "237903",
                "version_range": "*",
                "type": "required"
            }
        ],
        "forge": [
            {
                "name": "Reborn Core",
                "source": "curseforge",
                "curseforge_id": "237903",
                "version_range": "*",
                "type": "required"
            }
        ]
    },

    "jei": {
        "fabric": [
            {
                "name": "Fabric API",
                "source": "modrinth",
                "mod_id": "fabric-api",
                "modrinth_id": "P7dR8mSH",
                "version_range": "*",
                "type": "required"
            }
        ],
        "forge": []  # Forge версия не требует зависимостей
    },

    # Fabric API для ВСЕХ Fabric модов
    "fabric": {
        "fabric": []  # Fabric API сам по себе
    }
}


def get_dependencies_for_mod(mod_name: str, mod_source: str, loader: str) -> list:
    """Получает предопределенные зависимости для мода"""
    mod_name_lower = mod_name.lower()

    # Ищем по части имени
    for key, deps_by_loader in KNOWN_DEPENDENCIES.items():
        if key in mod_name_lower:
            return deps_by_loader.get(loader.lower(), [])

    # Если не нашли, возвращаем Fabric API для Fabric модов
    if loader.lower() == "fabric":
        return [{
            "name": "Fabric API",
            "source": "modrinth",
            "mod_id": "fabric-api",
            "modrinth_id": "P7dR8mSH",
            "version_range": "*",
            "type": "required"
        }]

    return []