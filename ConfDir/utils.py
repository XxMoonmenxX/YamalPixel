## mod_utils.py
import re
import os

# Ручные сопоставления для сложных названий модов
MANUAL_MOD_MAPPINGS = {
    "appliedenergistics2 fabric 15.4.9": "ae2",
    "xaeros minimap 25.2.10 fabric 1.20": "xaeros-minimap",
    "xaerosworldmap 1.39.12 fabric 1.20": "xaeros-world-map",
    "travelersbackpack fabric 1.20.1 9.1.41": "travelers-backpack",
    "ironchests 5.0.2 fabric": "iron-chests",
    "fallingleaves 1.15.6+1.20.1": "falling-leaves",
    "lambdynamiclights 4.4.0+1.20.1": "lambdynamiclights",
    "techreborn 5.8.3": "techreborn",
    "reborncore 5.8.3": "reborn-core",
    "inventoryprofilesnext fabric 1.20 1.10.19": "inventory-profiles-next",
    "noindium 1.1.0+1.20": "no-indium",
    "mavapi 1.1.4 mc1.20.1": "more-axolotl-variants-api",
    "mavm 1.2.6 mc1.20.1": "more-axolotl-variants-mod",
}

def aggressive_clean_name(mod_name: str) -> str:
    """Более агрессивная очистка названия мода"""
    patterns_to_remove = [
        r"[\d\.\-_]+(?:fabric|forge|quilt|neoforge|mc|minecraft)",
        r"\b(?:fabric|forge|quilt|neoforge|mc|minecraft|mod|jar)\b",
        r"[\(\\)\[\]\{\}]",
        r"\s+",
    ]

    cleaned = mod_name.lower()
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Удаляем лишние пробелы и возвращаем
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Если после очистки ничего не осталось, используем оригинал
    return cleaned if cleaned else mod_name.lower()

def calculate_similarity(str1: str, str2: str) -> float:
    """Вычисляет схожесть между двумя строками"""
    str1, str2 = str1.lower(), str2.lower()

    # Если одна строка содержится в другой
    if str1 in str2 or str2 in str1:
        return 0.8

    # Считаем совпадающие слова
    words1 = set(str1.split())
    words2 = set(str2.split())

    if not words1 or not words2:
        return 0.0

    common_words = words1.intersection(words2)
    similarity = len(common_words) / max(len(words1), len(words2))

    return similarity

def extract_core_name(mod_name: str) -> str:
    """Извлекает ядро названия мода"""
    core = re.sub(r"[\d.\-_]+.*$", "", mod_name)
    return core.strip()

COLLECTIONS_CONFIG = {
    "collections_dir": os.path.join(
        os.path.expanduser("~"), "YamalPixel", "collections"
    )
}

