# utils/validation_utils.py
import re
import subprocess
import os

def validate_username(username):
    """Проверяет имя пользователя на допустимые символы."""
    if not username:
        return False
    # Простая проверка: только буквы, цифры, подчеркивания, тире, длина 3-16
    pattern = r'^[a-zA-Z0-9_-]{3,16}$'
    return bool(re.match(pattern, username))

def check_java_version(java_path="java"):
    """Проверяет версию Java."""
    try:
        result = subprocess.run([java_path, "-version"], capture_output=True, text=True, stderr=subprocess.STDOUT)
        version_str = result.stdout.split('\n')[0] # Берем первую строку вывода
        # Ищем версию, например "openjdk version "17.0.1"..." или "java version "1.8.0_..."
        match = re.search(r'version "([^"]+)"', version_str)
        if match:
            full_version = match.group(1)
            # Извлекаем мажорную версию (например, 1.8 -> 8, 17.0.1 -> 17)
            major_version = extract_major_version(full_version)
            return major_version, full_version
        else:
            print(f"⚠️ Не удалось распознать версию Java из: {version_str}")
            return None, None
    except FileNotFoundError:
        print(f"❌ Java не найдена по пути: {java_path}")
        return None, None
    except Exception as e:
        print(f"❌ Ошибка проверки Java: {e}")
        return None, None

def extract_major_version(version_str):
    """Извлекает мажорную версию из строки версии."""
    # Обрабатывает строки вроде "1.8.0_281", "17.0.1", "11.0.12"
    parts = version_str.split('.')
    if parts[0] == '1': # Для старых версий вида 1.8.x
        return int(parts[1]) if len(parts) > 1 else None
    else: # Для новых версий вида 17.x.x
        return int(parts[0]) if parts else None

def is_valid_path(path):
    """Проверяет, является ли путь допустимым."""
    try:
        # Проверяем, является ли путь абсолютным или относительным и корректным
        Path(path).resolve()
        return True
    except:
        return False
