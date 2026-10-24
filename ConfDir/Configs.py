## ConfDir/Configs.py ху
from pathlib import Path
import os
import sys
import requests
import logging
from launcher_paths import resource_path


def set_window_icon(window):
    """Set icon for all windows"""
    try:
        icon_path = resource_path("icon.ico")

        # Дополнительная проверка для PyInstaller
        if not os.path.exists(icon_path):
            # Пробуем найти в домашней директории
            home_icon_path = Path.home() / "YamalPixelRes" / "icon.ico"
            if os.path.exists(home_icon_path):
                icon_path = home_icon_path
            else:
                print(f"Icon not found: {icon_path}")
                return

        window.iconbitmap(icon_path)
        print(f"Icon loaded from: {icon_path}")

    except Exception as e:
        print(f"Icon error: {e}")


# Конфигурация ресурсов
RESOURCE_DIR = Path.home() / "YamalPixelRes"

RESOURCES = {
    "logo.png": "https://disk.yandex.ru/i/XJ1rNloj-EcIGw",
    "logo1.png": "https://disk.yandex.ru/i/IazaA10AvflA2Q",
    "logo2.png": "https://disk.yandex.ru/i/X7VlJutjTuJI5g",
    "logo3.png": "https://disk.yandex.ru/i/aw_NY_pDSQ_yeg",
    "logo4.png": "https://disk.yandex.ru/i/qHwCeXH8SyMBqg",
    "logo5.png": "https://disk.yandex.ru/i/2ZbSia8Q4sPOmQ",
    "logo6.png": "https://disk.yandex.ru/i/9sk7fpOYULQe-w",
    "logo7.png": "https://disk.yandex.ru/i/Vks2YtorAoECdg",
    "logo8.png": "https://disk.yandex.ru/i/ztj5t0_y39yjcw",
    "menu_song.mp3": "https://disk.yandex.ru/d/Ahqnmj2T8YlNKg",
    "icon.ico": "https://disk.yandex.ru/i/nRwZp3AzRI16qQ"
}

# Secrets and proxy endpoints are deployment configuration, never source code.
API_KEY = os.getenv('YAMALPIXEL_PROXY_API_KEY', '')
CONFIG = {
    "version": "1.20.1",
    "fabric_loader": "0.17.2",
    "use_proxy_for_downloads": True,
    "minecraft_dir": os.path.expanduser("~/YamalPixel"),
    "mods_archive_url": "https://disk.yandex.ru/d/gyF-xpn4a0jfsQ",
    "mods": [],
}

# Конфигурация шейдеров
SHADERS_CONFIG = {
    "shaders": [
        {
            "name": "Aurora Shaders",
            "url": "https://disk.yandex.ru/d/AXeR74NrLMDpMw",
            "file": "Aurora-s-Shaders-1.20.2-1.20.zip",
        },
        {
            "name": "BSL Shaders",
            "url": "https://disk.yandex.ru/d/G7YX0Az5ZuUptA",
            "file": "BSL_v8.4.01.2.zip",
        },
        {
            "name": "Bliss Shaders",
            "url": "https://disk.yandex.ru/d/GjbXRVgDF9S55w",
            "file": "Bliss_v2.0.4_(Chocapic13_Shaders_edit).zip",
        },
        {
            "name": "Complementary Reimagined",
            "url": "https://disk.yandex.ru/d/1afdG-63Z4dxog",
            "file": "ComplementaryReimagined_r5.0.1.zip",
        },
        {
            "name": "Complementary Unbound",
            "url": "https://disk.yandex.ru/d/mPKPzpM5Rfw4Ag",
            "file": "ComplementaryUnbound_r5.1.1.zip",
        },
        {
            "name": "Hysteria Shaders",
            "url": "https://disk.yandex.ru/d/-sJWGfa1wzA77w",
            "file": "Hysteria-Shaders-Universal-v1.1.0.zip",
        },
        {
            "name": "Insanity Shader",
            "url": "https://disk.yandex.ru/d/fu3X8ZJ1FdyfWQ",
            "file": "Insanity-Shader-Universal-v1.500.zip",
        },
        {
            "name": "IterationT Shaders",
            "url": "https://disk.yandex.ru/d/U4ZsdD303pamBg",
            "file": "IterationT-Shaders-v2.0.0-All-Versions.zip",
        },
        {
            "name": "Kappa Shaders",
            "url": "https://disk.yandex.ru/d/salUSNvQg01C0A",
            "file": "Kappa_v5.2.zip",
        },
        {
            "name": "Lost Souls",
            "url": "https://disk.yandex.ru/d/XydaLzVyWPOeFg",
            "file": "Lost Souls version ComplementaryReimagined_r5.2.1.zip",
        },
        {
            "name": "MakeUp UltraFast",
            "url": "https://disk.yandex.ru/d/lXzHIs0K3Ico0Q",
            "file": "MakeUp-UltraFast-8.9d.zip",
        },
        {
            "name": "SEUS Renewed",
            "url": "https://disk.yandex.ru/d/yPiGbWFPYdfcqA",
            "file": "SEUS-Renewed-1.0.0.zip",
        },
        {
            "name": "Sildur Vibrant Shaders",
            "url": "https://disk.yandex.ru/d/258c6NIYVdugWw",
            "file": "Sildur's Vibrant Shaders v1.32 Extreme.zip",
        },
        {
            "name": "Solas Shader",
            "url": "https://disk.yandex.ru/d/z-tQHGTsiwQAhg",
            "file": "Solas Shader V2.0 [BETA 0.6b].zip",
        },
        {
            "name": "Spooklementary",
            "url": "https://disk.yandex.ru/d/AjAhhGl1ueGdsQ",
            "file": "Spooklementary_1.1.zip",
        },
        {
            "name": "VanillAA",
            "url": "https://disk.yandex.ru/d/NErUzx0Q6ZCgew",
            "file": "VanillAA.zip",
        },
        {
            "name": "Ymir Shader",
            "url": "https://disk.yandex.ru/d/IOv8qwrvYktaJQ",
            "file": "Ymir_beta3.0.zip",
        },
        {
            "name": "Miniature Shader",
            "url": "https://disk.yandex.ru/d/dNcMKdHzP1cFRQ",
            "file": "miniature-shader-2.14.1.zip",
        },
        {
            "name": "Nostalgia Shader",
            "url": "https://disk.yandex.ru/d/QwLrr-DRx2k8tw",
            "file": "nostalgia_v5.0.zip",
        },
        {
            "name": "Photon Shader",
            "url": "https://disk.yandex.ru/d/JNOA4ITKiqA04g",
            "file": "photon-iris-stable.zip",
        },
        {
            "name": "Rethinking Voxels",
            "url": "https://disk.yandex.ru/d/3SUoopowIUI8pA",
            "file": "rethinking-voxels_beta18c.zip",
        },
        {
            "name": "Super Duper Vanilla",
            "url": "https://disk.yandex.ru/d/aEiGZvEBXRe67Q",
            "file": "superDuperVanilla.zip",
        },
    ]
}

essential_mods = []  # Compatibility for the retired Tk entry point.


def get_minecraft_version(version_name):
    from ConfDir.Versions import get_minecraft_version as resolve
    return resolve(version_name)


# Canonical version_configs lives in ConfDir.Versions.
from ConfDir.Versions import version_configs


QUILT_CONFIG = {
    "supported_versions": ["1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2", "1.19.2", "1.20.1", "1.20.2", "1.20.3",
                           "1.20.4", "1.20.5", "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"]
}

import json
import os
from datetime import datetime

USER_COLLECTIONS_DIR = os.path.join(CONFIG["minecraft_dir"], "custom_collections")
os.makedirs(USER_COLLECTIONS_DIR, exist_ok=True)


def load_user_collections():
    """Загружает все пользовательские сборки"""
    collections = []

    if not os.path.exists(USER_COLLECTIONS_DIR):
        return collections

    for filename in os.listdir(USER_COLLECTIONS_DIR):
        if filename.endswith('.json'):
            try:
                filepath = os.path.join(USER_COLLECTIONS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if all(key in data for key in ['name', 'minecraft_version', 'loader']):
                    collections.append({
                        'name': data['name'],
                        'filename': filename,
                        'minecraft_version': data['minecraft_version'],
                        'loader': data['loader'],
                        'loader_version': data.get('loader_version'),
                        'mods': data.get('mods', []),
                        'mod_count': len(data.get('mods', [])),
                        'created_at': data.get('created_at', datetime.now().isoformat()),
                        'description': data.get('description', '')
                    })
            except Exception as e:
                print(f"⚠️ Ошибка загрузки сборки {filename}: {e}")

    return collections


def save_user_collection(collection_data):
    """Сохраняет пользовательскую сборку"""
    try:
        safe_name = "".join(c for c in collection_data['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name[:50]

        filename = f"{safe_name}.json"
        filepath = os.path.join(USER_COLLECTIONS_DIR, filename)

        collection_data['created_at'] = datetime.now().isoformat()
        collection_data['updated_at'] = datetime.now().isoformat()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, indent=2, ensure_ascii=False)

        return True, filename
    except Exception as e:
        return False, str(e)


def delete_user_collection(collection_name):
    """Удаляет пользовательскую сборку"""
    try:
        for filename in os.listdir(USER_COLLECTIONS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(USER_COLLECTIONS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if data.get('name') == collection_name:
                    os.remove(filepath)
                    return True

        return False
    except Exception as e:
        print(f"❌ Ошибка удаления сборки: {e}")
        return False


# Конфигурация коллекций
if hasattr(sys, '_MEIPASS'):
    collections_base = os.path.join(sys._MEIPASS, "collections")
else:
    collections_base = os.path.join(CONFIG["minecraft_dir"], "collections")

COLLECTIONS_CONFIG = {
    "collections_dir": os.path.join(CONFIG["minecraft_dir"], "collections"),  # ← Теперь всегда в папке игры
    "max_mods_per_collection": 200,
    "supported_sources": ["modrinth", "curseforge", "local"],
    "curseforge_proxy_url": "http://90.151.59.120:8000"
}

messages = [
    "Удачи! (она тебе понадобится)",
    "Не удивляйся если всё сломается!",
    "Твой компьютер уже ненавидит тебя...",
    "Помни: это твой выбор!",
    "RIP твоему FPS.",
    "Скажи привет майнеру.",
    "Спасибо за удаленный доступ.",
    "Ого сколько у тебя денег...Мало...",
    "Потрогай траву...",
    "А ты знаешь как выглядит небо?",
    "Выпил пива уже?",
    "Добро пожаловать!",
    "Люби аксолотлей.",
    "Может быть всё напрасно?",
    "У Артёмов нет детей.",
    "У меня есть дискорд сервер:)",
    "Sludge life тоже круто!",
    "Купи мне словарь Русского и Могучего!",
    "Твой FPS: да.",
    "Гречка дорожает, а ты в майнкрафт играешь...",
    "Пахнет жареным... (твой видеокартой)",
    "Системные требования: иметь систему (необязательно)",
    "Твой ПК: 🔥🔥🔥",
    "Запускаю криптоферму... шучу... наверное...",
    "Твоя мамка гордится тобой! (нет)",
    "Поздравляю! Ты 1000-й пользователь! (приз: вирус)",
    "Оптимизация? Не, не слышал.",
    "Добро пожаловать в ад, выбери свой котел!",
    "Твой скин такой же кринжовый, как и твой вкус",
    "Сервер просит не тыкать в него палкой",
    "Загрузка успешна! (это ложь)",
    "Ты знал что трава зеленая? Вот и я нет",
    "Рекомендуется: выключить монитор для лучшего FPS",
    "Твои моды конфликтуют сильнее, чем родители в разводе",
    "Чиним неисправность... шучу, идем пить чай",
    "Это не баг, это фича (ха-ха)",
    "Твой процессор плачет кровавыми слезами",
    "Памяти: мало. Проблем: много. Настроение: ахуенно",
    "Запускаю NASA... ой, это же майнкрафт",
    "Твоя видеокарта: 💀 RIP 💀",
    "Совет: не дыши на компьютер, он пугается",
    "Готовься к слайд-шоу вместо игры!",
    "Твои настройки графики: УЛЬТРА КРИНЖ",
    "Модпак загружен! (и твоя душа продана)",
    "Добро пожаловать в цифровой дурдом!",
    "Твой логин: анон. Пароль: ******** (все равно '12345')",
    "Система: работает. Разум: на перезагрузке",
    "Запускаю... стоп, а что это за кнопка?",
    "Все сломалось! Шучу... пока что...",
    "Твоя ОС: Windows (мне жаль)",
    "Рекомендуемое время игры: никогда",
    "Чекни свой FPS: ㋡ ㋡ ㋡ (это смайлики, не цифры)",
    "Твоя сборка модов: шедевр (психбольницы)",
    "Готово! Теперь можешь идти плакать в угол",
    "Установка завершена! (шутка, это только начало)",
    "Добро пожаловать в симулятор слабого ПК!",
    "Твоя мышь: жирная. Клавиатура: липкая. Настроение: gaming",
    "Запускаю... ой, подожди, нужно перекреститься",
    "Системные требования: терпение и алкоголь",
    "Твой ПК издает звуки? Это нормально! (нет)",
    "Готово! Теперь ты официально NEET",
    "Оптимизация проведена! (на самом деле нет)",
    "Добро пожаловать в адскую вечеринку FPS-дропов!",
    "Твоя сборка: 'ахуенная' (с) твоя мамка",
    "Все работает! (это временно)",
    "Загрузка... пока можешь сходить в душ",
    "Твой RAM: 💀 УБИТ 💀",
    "Привет от разработчика: иди нахуй <3",
    "Готово! Время играть... или нет?",
    "Система: загружена. Санity: не найдена",
    "Твоя игра теперь с DLC: 'баги и кринж'",
    "Добро пожаловать в симулятор ожидания!",
    "Все сломалось! Ахаха, расслабился? Шучу... наверное...",
    "Твой ПК теперь обогреватель! (бесплатно!)",
    "Готово! Наслаждайся слайд-шоу!",
    "Рекомендация: не смотри на FPS-счетчик",
    "Твоя видеокарта: 🔥 ГОРИТ 🔥 (в переносном смысле)",
    "Запуск успешен! (если успех = боль)",
    "Добро пожаловать в клуб 'У меня все тормозит!'",
    "Твои настройки: УЛЬТРА НИЗКИЕ (как твоя самооценка)",
    "Система: работает. Мозг: нет.",
    "Все готово! Теперь можешь идти за пивом",
    "Твой ПК издает странные звуки? Это фича!",
    "Готово! Время играть... или переустанавливать Windows?",
    "Добро пожаловать в ад! Выбери свой грех:",
    "- Кринжовые моды",
    "- Убитый FPS",
    "- Выжженная видеокарта",
    "Твоя сборка: 'я сам это собирал' (ошибка)",
    "Все работает! (пока не тронешь)",
    "Загрузка завершена! Теперь можно грузить моды...",
    "Твой CPU: 💯% (это плохо)",
    "Готово! Наслаждайся пикселями!",
    "Добро пожаловать в симулятор слабоумия!",
    "Твоя ОС: кринж. Железо: боль. Настроение: gaming",
    "Все сломалось! (шучу, все сломалось потом)",
    "Система: загружена. Проблемы: загружены тоже",
    "Твоя игра теперь с RTX! (шучу, у тебя GT 210)",
    "Готово! Время для... ой, все зависло",
    "Добро пожаловать в клуб 'Я 5 часов настраивал лаунчер'",
    "Твой ПК: 💸 ДЕНЬГИ НА ВЕТЕР 💸",
    "Все работает! (на старом ПК в музее)",
    "Запуск: успешен! FPS: провален! Настроение: ахуенно!",
    "Добро пожаловать в дикий запад багов и глитчей!",
    "Твоя сборка: 'оно как-то само'",
    "Готово! Теперь можешь идти гуглить 'почему все тормозит'",
    "Система: работает. Нервы: нет.",
    "Твой FPS: ❤️ ЛЮБОВЬ ❤️ (к слайд-шоу)",
    "Все сломалось! Ахаха... стоп, это не шутка...",
    "Добро пожаловать в адскую вечеринку глитчей!",
    "Твоя видеокарта: 💀 ОТДЫХАЕТ 💀 (навсегда)",
    "Готово! Наслаждайся... ой, синий экран...",
    "Сервак запущен, а ты - опущен",
]

# CurseForge Proxy Configuration
CURSEFORGE_CONFIG = {
    "proxy_url": os.getenv('YAMALPIXEL_PROXY_URL', 'http://127.0.0.1:8000'),
    "enabled": True,
    "api_version": "v1",
    "timeout": 10,
    "max_retries": 3
}


def setup_environment():
    """Настройка окружения и загрузка ресурсов"""
    try:
        RESOURCE_DIR.mkdir(parents=True, exist_ok=True)

        for filename, url in RESOURCES.items():
            file_path = RESOURCE_DIR / filename
            if not file_path.exists():
                download_url = get_yandex_direct_link(url)
                if not download_url:
                    continue

                response = requests.get(download_url, stream=True)
                response.raise_for_status()

                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logging.info(f"Файл {filename} успешно загружен")

    except Exception as e:
        logging.error(f"Ошибка инициализации: {str(e)}")
        raise


def get_yandex_direct_link(public_key):
    """Получаем прямую ссылку для скачивания через API Яндекс.Диска"""
    from Network.Downloader import get_yandex_direct_link_sync
    return get_yandex_direct_link_sync(public_key)
