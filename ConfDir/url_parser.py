## ConfDir/url_parser.py
import re


def parse_mod_url(url):
    """
    Парсит URL мода и возвращает источник и идентификатор
    """
    if not url:
        return None, None

    url = url.strip()

    # Modrinth patterns
    modrinth_patterns = [
        r'modrinth\.com/mod/([^/?#]+)',  # modrinth.com/mod/sodium
        r'modrinth\.com/project/([^/?#]+)',  # modrinth.com/project/sodium
        r'^(?:https?://)?(?:www\.)?modrinth\.com/mod/([^/?#]+)',  # Полные URL
    ]

    # CurseForge patterns
    curseforge_patterns = [
        r'curseforge\.com/minecraft/mc-mods/([^/?#]+)',  # curseforge.com/minecraft/mc-mods/jei
        r'curseforge\.com/projects/(\d+)',  # curseforge.com/projects/238222 (ID)
        r'^(?:https?://)?(?:www\.)?curseforge\.com/minecraft/mc-mods/([^/?#]+)',
    ]

    # Проверяем Modrinth
    for pattern in modrinth_patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            identifier = match.group(1)
            # Если это ID в формате slug, очищаем
            if re.match(r'^[a-zA-Z0-9_-]+$', identifier):
                return 'modrinth', identifier

    # Проверяем CurseForge
    for pattern in curseforge_patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            identifier = match.group(1)
            # Если это числовой ID
            if identifier.isdigit():
                return 'curseforge', identifier
            # Если это slug
            else:
                return 'curseforge', identifier.lower()

    return None, None


def extract_mod_info_from_filename(filename):
    """
    Пытается извлечь информацию о моде из имени файла
    """
    if not filename or not filename.endswith('.jar'):
        return None, None

    # Удаляем .jar
    name = filename[:-4]

    # Пытаемся найти известные моды по паттернам
    known_mods = {
        'fabric-api': ('modrinth', 'fabric-api'),
        'sodium': ('modrinth', 'sodium'),
        'iris': ('modrinth', 'iris'),
        'indium': ('modrinth', 'indium'),
        'jei': ('curseforge', 'jei'),
        'appliedenergistics2': ('curseforge', 'applied-energistics-2'),
    }

    # Приводим к нижнему регистру и ищем совпадения
    name_lower = name.lower()
    for pattern, (source, mod_id) in known_mods.items():
        if pattern in name_lower:
            return source, mod_id

    return None, None