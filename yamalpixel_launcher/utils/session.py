# utils/session.py
import json
import os
from pathlib import Path

# Путь к файлу last_session.json
LAST_SESSION_FILE = Path.home() / "YamalPixel" / "last_session.json"

def load_last_session():
    """Загружает последние настройки из файла JSON."""
    try:
        if LAST_SESSION_FILE.exists():
            with open(LAST_SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"📁 Загружена сессия: {len(data)} параметров")
            return data
        else:
            print(f"⚠️ Файл сессии не найден: {LAST_SESSION_FILE}")
            return None
    except Exception as e:
        print(f"❌ Ошибка загрузки сессии: {e}")
        return None

def save_last_session(session_data):
    """Сохраняет последние настройки в файл JSON."""
    try:
        # Создаем директорию, если её нет
        LAST_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(LAST_SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Настройки сохранены: {len(session_data)} параметров")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения сессии: {e}")
        return False
