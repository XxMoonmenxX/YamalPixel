## ConfDir/collection_schema.py гы
"""
Схема JSON файла сборки с поддержкой зависимостей
"""

from typing import Dict
import re
from Core.mod_transaction import safe_filename

COLLECTION_SCHEMA = {
    "name": "Название сборки",
    "minecraft_version": "1.20.1",
    "loader": "fabric",  # или "forge", "neoforge", "quilt"
    "created_at": "2024-01-01T12:00:00",
    "mods": [
        {
            "source": "modrinth",  # или "curseforge", "local"
            "modrinth_id": "P7dR8mSH",  # для Modrinth
            "curseforge_id": "238222",  # для CurseForge
            "modrinth_slug": "sodium",  # для удобства
            "curseforge_slug": "jei",  # для удобства
            "name": "Название мода",
            "filename": "sodium-fabric-mc1.20.1-0.4.10.jar",
            "resolved_dependencies": [
                {
                    "source": "modrinth",
                    "modrinth_id": "P7dR8mSH",
                    "name": "Fabric API",
                    "dependency_type": "required",  # или "optional"
                    "version_range": ">=0.83.0"
                }
            ],
            "dependencies_resolved": True,  # Флаг, что зависимости проанализированы
            "last_dependency_check": "2024-01-01T12:00:00"
        }
    ],
    "mod_count": 10,
    "dependencies_analyzed": True,
    "dependency_info": {
        "total_dependencies": 5,
        "required_dependencies": 3,
        "optional_dependencies": 2,
        "conflicts": [],  # Список конфликтов
        "compatibility_issues": []  # Проблемы совместимости
    }
}


def validate_collection_schema(data:  Dict) -> bool:
    """Проверяет валидность схемы сборки"""
    required_fields = ["name", "minecraft_version", "loader", "mods"]

    if not isinstance(data, dict):
        return False
    for field in required_fields:
        if field not in data:
            return False

    if data.get('loader') not in {'fabric','forge','quilt','neoforge'}:
        return False
    if not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', str(data.get('minecraft_version',''))):
        return False
    # Проверяем моды
    if not isinstance(data["mods"], list):
        return False

    for mod in data["mods"]:
        if not isinstance(mod, dict) or not all(k in mod for k in ("source","name","filename")):
            return False
        if mod['source'] not in {'modrinth','curseforge','local','yandex','shader'}:
            return False
        if not isinstance(mod['filename'], str) or not mod['filename'].lower().endswith(('.jar','.zip')):
            return False
        try: safe_filename(mod['filename'])
        except ValueError: return False

    return True
