import tkinter as tk
from tkinter import ttk, messagebox
import minecraft_launcher_lib
import subprocess
import threading
import os
import requests
import re
from ttkthemes import ThemedTk
from mcstatus import JavaServer
from pygame import mixer
import zipfile
import platform
import urllib.request
import sys
import shutil
import logging
from pypresence import Presence
from pathlib import Path
import datetime
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time
from datetime import datetime
from collections import deque
from pathlib import Path
import psutil
import math
import json


def old_repair_with_ui():
    """Полная версия починки с UI"""
    try:
        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        progress_window.title("🔧 Автопочинка файлов")
        progress_window.geometry("500x400")
        progress_window.resizable(False, False)
        progress_window.transient(win)
        progress_window.grab_set()

        # Центрируем окно
        progress_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (500 // 2)
        y = (win.winfo_screenheight() // 2) - (400 // 2)
        progress_window.geometry(f"500x400+{x}+{y}")

        main_frame = ttk.Frame(progress_window, padding=25)
        main_frame.pack(fill='both', expand=True)

        # Заголовок
        ttk.Label(main_frame, text="🔧 Автопочинка файлов игры",
                  font=('Comfortaa', 16, 'bold')).pack(pady=(0, 10))

        ttk.Label(main_frame, text="Проверяем и восстанавливаем игровые файлы",
                  font=('Comfortaa', 11), foreground='gray').pack(pady=(0, 20))

        # Прогресс-бар
        progress = ttk.Progressbar(main_frame, orient="horizontal",
                                   length=400, mode="determinate")
        progress.pack(pady=10)

        status_label = ttk.Label(main_frame, text="Начинаем проверку...",
                                 font=('Comfortaa', 10))
        status_label.pack()

        details_label = ttk.Label(main_frame, text="",
                                  font=('Comfortaa', 9), foreground='blue')
        details_label.pack()

        # Список найденных проблем и исправлений
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill='both', expand=True, pady=10)

        log_text = tk.Text(log_frame, height=8, width=60, wrap='word',
                           font=('Consolas', 8), state='disabled')
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)

        log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def add_log(message, color='black'):
            log_text.configure(state='normal')
            log_text.insert('end', f"• {message}\n", color)
            log_text.see('end')
            log_text.configure(state='disabled')
            progress_window.update()

        issues_found = []
        fixes_applied = []

        def repair_thread():
            nonlocal issues_found, fixes_applied

            try:
                minecraft_dir = CONFIG['minecraft_dir']
                mods_dir = os.path.join(minecraft_dir, 'mods')
                versions_dir = os.path.join(minecraft_dir, 'versions')
                config_dir = os.path.join(minecraft_dir, 'config')

                # Проверка папок
                win.after(0, lambda: status_label.config(text="Проверка папок..."))
                win.after(0, lambda: details_label.config(text="Проверяем структуру папок"))
                progress['value'] = 10

                for folder, path in [('mods', mods_dir), ('versions', versions_dir), ('config', config_dir)]:
                    if not os.path.exists(path):
                        issues_found.append(f"Папка {folder} отсутствует")
                        add_log(f"❌ Папка {folder} отсутствует", 'red')
                        os.makedirs(path, exist_ok=True)
                        fixes_applied.append(f"Создана папка {folder}")
                        add_log(f"✅ Создана папка {folder}", 'green')

                # Проверка модов
                progress['value'] = 50
                win.after(0, lambda: status_label.config(text="Проверка модов..."))

                missing_mods = []
                for mod in CONFIG['mods']:
                    mod_path = os.path.join(mods_dir, mod['file'])
                    if not os.path.exists(mod_path):
                        missing_mods.append(mod)

                if missing_mods:
                    issues_found.append(f"Отсутствуют {len(missing_mods)} модов")
                    add_log(f"❌ Отсутствует модов: {len(missing_mods)}", 'red')

                    # Загружаем моды
                    for i, mod in enumerate(missing_mods):
                        win.after(0, lambda: details_label.config(
                            text=f"Загружаем мод: {mod['file']} ({i + 1}/{len(missing_mods)})"
                        ))
                        if download_single_mod_turbo(mod):
                            fixes_applied.append(f"Загружен {mod['file']}")
                            add_log(f"✅ Загружен {mod['file']}", 'green')
                        else:
                            add_log(f"❌ Ошибка загрузки {mod['file']}", 'red')

                # Проверка Fabric
                progress['value'] = 80
                win.after(0, lambda: status_label.config(text="Проверка Fabric..."))

                if not check_fabric_installed():
                    issues_found.append("Fabric не установлен")
                    add_log("❌ Fabric не установлен", 'red')
                    if install_fabric_silent():
                        fixes_applied.append("Установлен Fabric")
                        add_log("✅ Установлен Fabric", 'green')

                progress['value'] = 100
                win.after(0, lambda: status_label.config(text="Проверка завершена!"))

                # Показываем результат
                win.after(1000, lambda: show_repair_result(issues_found, fixes_applied, progress_window))

            except Exception as e:
                win.after(0, progress_window.destroy)
                messagebox.showerror("Ошибка", f"❌ Ошибка автопочинки: {str(e)}")

        def show_repair_result(issues, fixes, window):
            window.destroy()

            report = "🔧 Автопочинка завершена!\n\n"

            if issues:
                report += "📋 Найдены проблемы:\n• " + "\n• ".join(issues) + "\n\n"

            if fixes:
                report += "✅ Исправления:\n• " + "\n• ".join(fixes) + "\n\n"

            if not issues and not fixes:
                report += "✅ Проблем не обнаружено! Все файлы в порядке.\n\n"

            messagebox.showinfo("Автопочинка", report)

        # Запускаем починку в отдельном потоке
        threading.Thread(target=repair_thread, daemon=True).start()
        return True

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить автопочинку: {e}")
        return False




#Пишется при помощи DeepSeek, каждый может сделать то же самое хоть немного зная python!!!
CURRENT_VERSION = "0.6.502" #обновление
logging.basicConfig(filename='launcher.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Конфигурация ресурсов
RESOURCE_DIR = Path.home() / "YamalPixelRes"
RESOURCES = {
    "logo.png": "https://disk.yandex.ru/i/ztKpQOZEjQDE_Q",
    "menu_song.mp3": "https://disk.yandex.ru/d/Ahqnmj2T8YlNKg"
}
# Конфигурация
CONFIG = {
    'version': '1.20.1',
    'fabric_loader': '0.16.10',
    'minecraft_dir': os.path.expanduser("~/YamalPixel"),
    'mods': [
        {'url': 'https://disk.yandex.ru/d/aJHjc2LrzS8ndA', 'file': 'XaerosWorldMap_1.39.12_Fabric_1.20.jar'},
        {'url': 'https://disk.yandex.ru/d/UzM5BWOXB9S7OA', 'file': 'AdvancedReborn-1.20.1-1.2.9.jar'},
        {'url': 'https://disk.yandex.ru/d/B48FGIIitm-olA', 'file': 'ae2-emi-crafting-1.3.1.jar'},
        {'url': 'https://disk.yandex.ru/d/YXPRt1scCMJ8kQ', 'file': 'antixray-fabric-1.4.6+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/ukmqzaHQaTP03g', 'file': 'appliedenergistics2-fabric-15.4.9.jar'},
        {'url': 'https://disk.yandex.ru/d/aH-BHO05_WeuLw', 'file': 'architectury-9.2.14-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/fo5V3PpaLtZ-gw', 'file': 'areas-1.20.1-6.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Tif04Xw7_kd8rQ', 'file': 'cardinal-components-api-5.2.3.jar'},
        {'url': 'https://disk.yandex.ru/d/k5xux5BX_T9-7g', 'file': 'choicetheorems-overhauled-village-friends-and-foes-add-on-1.1.jar'},
        {'url': 'https://disk.yandex.ru/d/378xaPNzlblGFA', 'file': 'cloth-config-11.1.136-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/5AivLjfk6Wgbog', 'file': 'collective-1.20.1-8.12.jar'},
        {'url': 'https://disk.yandex.ru/d/nSspzPB5G5ReWA', 'file': 'crafting_enchanted_golden_apple-1.0.0-fabric-1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Ox5-1T4a9qkXHg', 'file': 'ctov-beautify-compat-2.0.jar'},
        {'url': 'https://disk.yandex.ru/d/o2kPxeHul4byng', 'file': 'emi-1.1.22+1.20.1+fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/PNZi_54Tj4HP3Q', 'file': 'entityculling-fabric-1.9.1-mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/GNW5lwib5Xq9Eg', 'file': 'extra-mod-integrations-0.4.7+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/EHHAo7HSzH2mmg', 'file': 'fabric-api-0.92.6+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/IHBo3qyqAjR3fQ', 'file': 'fabric-language-kotlin-1.13.6+kotlin.2.2.20.jar'},
        {'url': 'https://disk.yandex.ru/d/r8gwsUQF7Wy9BQ', 'file': 'fallingleaves-1.15.6+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/pddZ2W8za1yiSQ', 'file': 'indium-1.0.36+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/PghcNlFWKcgSeg', 'file': 'InventoryProfilesNext-fabric-1.20-1.10.19.jar'},
        {'url': 'https://disk.yandex.ru/d/AZHbvFGGX_JAKQ', 'file': 'iris-1.7.6+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/wwCGHqSxly5pXg', 'file': 'ironchests-5.0.2-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/OrlYw3O3rnSN1A', 'file': 'lambdynamiclights-4.4.0+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Sr4rPWBdFjEZfA', 'file': 'libIPN-fabric-1.20-4.0.2.jar'},
        {'url': 'https://disk.yandex.ru/d/7G3BPLxK1Dul1g', 'file': 'lithium-fabric-mc1.20.1-0.11.3.jar'},
        {'url': 'https://disk.yandex.ru/d/yE26wprToTM9hg', 'file': 'mavapi-1.1.4-mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Po8eTPEwzDAOpg', 'file': 'mavm-1.2.6-mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/8luIo8Ygz83BEg', 'file': 'mcpitanlib-3.3.9-1.20.1-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/EsACr5Ex3R9Zdg', 'file': 'modmenu-badges-lib-2023.6.1.jar'},
        {'url': 'https://disk.yandex.ru/d/6CF52_F3QbnCzQ', 'file': 'noindium-1.1.0+1.20.jar'},
        {'url': 'https://disk.yandex.ru/d/B10LX8LVEZg0DQ', 'file': 'Patchouli-1.20.1-84.1-FABRIC.jar'},
        {'url': 'https://disk.yandex.ru/d/fCkZvVrEqlU3Rg', 'file': 'RebornCore-5.8.3.jar'},
        {'url': 'https://disk.yandex.ru/d/_CgYmn4OYeGnBQ', 'file': 'servercore-fabric-1.5.2+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/uI7zlr5Yg-7skQ', 'file': 'sodium-extra-0.5.9+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Mft3dmbdbHjhHA', 'file': 'sodium-fabric-0.5.13+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/dncEQy1PhTcgrw', 'file': 'TechReborn-5.8.3.jar'},
        {'url': 'https://disk.yandex.ru/d/_c-mQTKC4UB1cw', 'file': 'Terralith_1.20.x_v2.5.4.jar'},
        {'url': 'https://disk.yandex.ru/d/trH1NQ3Hw2QjXQ', 'file': 'Xaeros_Minimap_25.2.10_Fabric_1.20.jar'},
        {'url': 'https://disk.yandex.ru/d/H0dkq2G5XcrZFQ', 'file': 'moonlight-1.20-2.16.15-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/uXJYqfjy_aedHQ', 'file': 'immersive_weathering-1.20.1-2.0.5-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/7ebHrjGobc89Og', 'file': 'travelersbackpack-fabric-1.20.1-9.1.41.jar'}
    ]
}



LAUNCH_IN_PROGRESS = False
LAUNCH_START_TIME = None


class LauncherCache:
    def __init__(self):
        self.cache_dir = Path.home() / ".yamalpixel_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def is_cache_fresh(self, cache_file, max_age_hours=24):
        """Проверяет свежесть кэша"""
        if not cache_file.exists():
            return False

        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < (max_age_hours * 3600)

    def get_file_hash(self, url):
        """Создает хеш для имени файла кэша"""
        return hashlib.md5(url.encode()).hexdigest()

    def download_and_cache(self, url, cache_file):
        """Скачивает и кэширует файл"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            with open(cache_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192 * 4):
                    f.write(chunk)

            logging.info(f"Файл закэширован: {cache_file.name}")
        except Exception as e:
            logging.error(f"Ошибка кэширования {url}: {e}")
            raise

    def get_cached_file(self, url, force_refresh=False):
        """Возвращает кэшированный файл или качает новый"""
        file_hash = self.get_file_hash(url)
        cache_file = self.cache_dir / file_hash

        if cache_file.exists() and not force_refresh:
            if self.is_cache_fresh(cache_file):
                return cache_file

        # Качаем и кэшируем
        self.download_and_cache(url, cache_file)
        return cache_file


class TurboDownloader:
    def __init__(self):
        self.cache = {}
        self.cache_manager = LauncherCache()
        self._session = None  # Будем переиспользовать сессию

    @property
    def session(self):
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=300)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def cleanup(self):
        """Закрывает сессию при завершении"""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_turbo_link(self, public_key):
        """Быстрое получение ссылки через асинхронность"""
        if public_key in self.cache:
            return self.cache[public_key]

        api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
        try:
            async with self.session.get(api_url, params={"public_key": public_key}) as response:
                if response.status == 200:
                    data = await response.json()
                    direct_link = data.get('href')
                    self.cache[public_key] = direct_link
                    return direct_link
                else:
                    logging.error(f"Ошибка API Яндекс: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logging.error("Таймаут получения ссылки Яндекс")
            return None
        except Exception as e:
            logging.error(f"Ошибка получения ссылки: {e}")
            return None

    async def download_file_async(self, url, file_path, progress_callback=None):
        """Турбо-загрузка с прогрессом"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                total_size = int(response.headers.get('content-length', 0))

                with open(file_path, 'wb') as f:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(8192 * 8):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

                return True
        except Exception as e:
            logging.error(f"Ошибка загрузки {url}: {e}")
            return False

    def download_file_sync(self, url, file_path, progress_callback=None):
        """Синхронная версия для использования в потоках"""
        try:
            return asyncio.run(self.download_file_async(url, file_path, progress_callback))
        finally:
            # Закрываем сессию после завершения
            asyncio.run(self.cleanup())


def download_single_mod_turbo(mod_info):
    """Турбо-загрузка одного мода с правильным закрытием ресурсов"""
    try:
        print(f"🔍 Начинаем загрузку мода: {mod_info['file']}")

        # Создаем новый загрузчик для каждого мода
        downloader = TurboDownloader()

        # Получаем прямую ссылку
        direct_link = asyncio.run(downloader.get_turbo_link(mod_info['url']))
        print(f"🔗 Прямая ссылка получена: {direct_link is not None}")

        if not direct_link:
            logging.error(f"Не удалось получить ссылку для {mod_info['file']}")
            asyncio.run(downloader.cleanup())
            return False

        # Путь для сохранения
        mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
        os.makedirs(mods_dir, exist_ok=True)
        file_path = os.path.join(mods_dir, mod_info['file'])

        # Загружаем файл
        success = downloader.download_file_sync(direct_link, file_path)
        print(f"📥 Результат загрузки {mod_info['file']}: {'✅ Успех' if success else '❌ Ошибка'}")

        if success and mod_info['file'].endswith('.zip'):
            # Распаковываем ZIP
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(mods_dir)
                print(f"📦 Мод распакован: {mod_info['file']}")
            except Exception as e:
                logging.error(f"Ошибка распаковки {mod_info['file']}: {e}")

        # Явно закрываем загрузчик
        asyncio.run(downloader.cleanup())
        return success

    except Exception as e:
        logging.error(f"Ошибка загрузки мода {mod_info['file']}: {e}")
        # Пытаемся закрыть загрузчик даже при ошибке
        try:
            asyncio.run(downloader.cleanup())
        except:
            pass
        return False


def download_mods_turbo_ui(mods_list):
    """Версия с UI для использования в лаунчере - ИСПРАВЛЕННАЯ"""

    # Создаем окно прогресса
    progress_window = tk.Toplevel(win)
    progress_window.title("Загрузка модов")
    progress_window.geometry("400x150")

    progress_label = ttk.Label(progress_window, text="Подготовка к загрузке...")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=10)

    status_label = ttk.Label(progress_window, text=f"0/{len(mods_list)} модов")
    status_label.pack()

    def download_thread():
        total_mods = len(mods_list)
        success_count = 0

        def update_progress(current, total, mod_name=""):
            percent = (current * 100) // total
            progress['value'] = percent
            status_label.config(text=f"{current}/{total} модов - {mod_name}")
            progress_window.update()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []

            for i, mod in enumerate(mods_list):
                future = executor.submit(download_single_mod_turbo, mod)
                futures.append((future, mod['file']))

            # Обновляем прогресс
            for i, (future, mod_name) in enumerate(futures):
                try:
                    win.after(0, lambda: update_progress(i, total_mods, mod_name))
                    success = future.result(timeout=180)  # 3 минуты на мод
                    if success:
                        success_count += 1

                    win.after(0, lambda: update_progress(i + 1, total_mods, mod_name))

                except Exception as e:
                    logging.error(f"Ошибка в потоке загрузки {mod_name}: {e}")

        # Финальное сообщение
        win.after(0, lambda: show_download_result(success_count, total_mods, progress_window))

    def show_download_result(success, total, window):
        window.destroy()
        if success == total:
            messagebox.showinfo("Загрузка завершена", f"✅ Все {success} модов успешно загружены!")
        else:
            messagebox.showwarning(
                "Загрузка завершена",
                f"📊 Загружено {success} из {total} модов\n\n"
                f"Некоторые моды могли не загрузиться. Проверьте логи."
            )

    threading.Thread(target=download_thread, daemon=True).start()


# 🎯 ОБНОВЛЕННАЯ ФУНКЦИЯ ДЛЯ ШЕЙДЕРОВ:

def download_shaders_turbo(selected_shaders, progress_callback=None):
    """Турбо-загрузка шейдеров"""

    def download_shaders_thread():
        shaders_dir = os.path.join(CONFIG['minecraft_dir'], 'shaderpacks')
        os.makedirs(shaders_dir, exist_ok=True)

        downloader = TurboDownloader()
        total = len(selected_shaders)
        success_count = 0

        with ThreadPoolExecutor(max_workers=2) as executor:  # 2 потока для шейдеров
            futures = []

            for shader in selected_shaders:
                future = executor.submit(download_single_shader_turbo, downloader, shader, shaders_dir)
                futures.append(future)

            for i, future in enumerate(futures):
                try:
                    success = future.result(timeout=300)  # 5 минут на шейдер
                    if success:
                        success_count += 1

                    if progress_callback:
                        progress = (i + 1) * 100 // total
                        win.after(0, lambda: progress_callback(progress, f"Шейдер {i + 1}/{total}"))

                except Exception as e:
                    logging.error(f"Ошибка загрузки шейдера: {e}")

        return success_count, total

    threading.Thread(target=download_shaders_thread, daemon=True).start()


def download_single_shader_turbo(downloader, shader, shaders_dir):
    """Загрузка одного шейдера"""
    try:
        direct_link = asyncio.run(downloader.get_turbo_link(shader['url']))
        if not direct_link:
            return False

        shader_path = os.path.join(shaders_dir, shader['file'])
        return downloader.download_file_sync(direct_link, shader_path)

    except Exception as e:
        logging.error(f"Ошибка загрузки шейдера {shader['name']}: {e}")
        return False

def fig1():
    """Очистка игры с созданием бэкапов"""
    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')
    versions_dir = os.path.join(minecraft_dir, 'versions')

    # Создаем бэкапы перед удалением
    backups_created = []

    # Всегда создаем бэкапы, даже если папки не существуют
    backup_path_mods = create_backup(mods_dir, "mods")
    if backup_path_mods:
        backups_created.append(backup_path_mods)

    backup_path_versions = create_backup(versions_dir, "versions")
    if backup_path_versions:
        backups_created.append(backup_path_versions)

    # Удаляем папки если они существуют
    items_to_remove = [mods_dir, versions_dir]
    for item in items_to_remove:
        if os.path.exists(item):
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"Удалено: {item}")
                else:
                    os.remove(item)
                    print(f"Удалено: {item}")
            except Exception as e:
                print(f"Ошибка удаления {item}: {str(e)}")

    # Показываем информацию о созданных бэкапах
    if backups_created:
        backup_info = "Созданы бэкапы:\n" + "\n".join([f"• {os.path.basename(b)}" for b in backups_created])
        messagebox.showinfo("Бэкапы созданы", f"Игра очищена!\n\n{backup_info}")
    else:
        messagebox.showinfo("Очистка", "Папки mods и versions очищены")


# Конфигурация шейдеров
SHADERS_CONFIG = {
    'shaders': [
        {'name': 'Aurora Shaders', 'url': 'https://disk.yandex.ru/d/Ish63cvEZjqqMw',
         'file': 'Aurora-s-Shaders-1.20.2-1.20.zip'},
        {'name': 'BSL Shaders', 'url': 'https://disk.yandex.ru/d/G7YX0Az5ZuUptA', 'file': 'BSL_v8.4.01.2.zip'},
        {'name': 'Bliss Shaders', 'url': 'https://disk.yandex.ru/d/GjbXRVgDF9S55w',
         'file': 'Bliss_v2.0.4_(Chocapic13_Shaders_edit).zip'},
        {'name': 'Complementary Reimagined', 'url': 'https://disk.yandex.ru/d/1afdG-63Z4dxog',
         'file': 'ComplementaryReimagined_r5.0.1.zip'},
        {'name': 'Complementary Unbound', 'url': 'https://disk.yandex.ru/d/mPKPzpM5Rfw4Ag',
         'file': 'ComplementaryUnbound_r5.1.1.zip'},
        {'name': 'Hysteria Shaders', 'url': 'https://disk.yandex.ru/d/-sJWGfa1wzA77w',
         'file': 'Hysteria-Shaders-Universal-v1.1.0.zip'},
        {'name': 'Insanity Shader', 'url': 'https://disk.yandex.ru/d/fu3X8ZJ1FdyfWQ',
         'file': 'Insanity-Shader-Universal-v1.500.zip'},
        {'name': 'IterationT Shaders', 'url': 'https://disk.yandex.ru/d/U4ZsdD303pamBg',
         'file': 'IterationT-Shaders-v2.0.0-All-Versions.zip'},
        {'name': 'Kappa Shaders', 'url': 'https://disk.yandex.ru/d/salUSNvQg01C0A', 'file': 'Kappa_v5.2.zip'},
        {'name': 'Lost Souls', 'url': 'https://disk.yandex.ru/d/XydaLzVyWPOeFg',
         'file': 'Lost Souls version ComplementaryReimagined_r5.2.1.zip'},
        {'name': 'MakeUp UltraFast', 'url': 'https://disk.yandex.ru/d/lXzHIs0K3Ico0Q',
         'file': 'MakeUp-UltraFast-8.9d.zip'},
        {'name': 'SEUS Renewed', 'url': 'https://disk.yandex.ru/d/yPiGbWFPYdfcqA', 'file': 'SEUS-Renewed-1.0.0.zip'},
        {'name': 'Sildur Vibrant Shaders', 'url': 'https://disk.yandex.ru/d/258c6NIYVdugWw',
         'file': 'Sildur\'s Vibrant Shaders v1.32 Extreme.zip'},
        {'name': 'Solas Shader', 'url': 'https://disk.yandex.ru/d/z-tQHGTsiwQAhg',
         'file': 'Solas Shader V2.0 [BETA 0.6b].zip'},
        {'name': 'Spooklementary', 'url': 'https://disk.yandex.ru/d/AjAhhGl1ueGdsQ', 'file': 'Spooklementary_1.1.zip'},
        {'name': 'VanillAA', 'url': 'https://disk.yandex.ru/d/NErUzx0Q6ZCgew', 'file': 'VanillAA.zip'},
        {'name': 'Ymir Shader', 'url': 'https://disk.yandex.ru/d/IOv8qwrvYktaJQ', 'file': 'Ymir_beta3.0.zip'},
        {'name': 'Miniature Shader', 'url': 'https://disk.yandex.ru/d/dNcMKdHzP1cFRQ',
         'file': 'miniature-shader-2.14.1.zip'},
        {'name': 'Nostalgia Shader', 'url': 'https://disk.yandex.ru/d/QwLrr-DRx2k8tw', 'file': 'nostalgia_v5.0.zip'},
        {'name': 'Photon Shader', 'url': 'https://disk.yandex.ru/d/JNOA4ITKiqA04g', 'file': 'photon-iris-stable.zip'},
        {'name': 'Rethinking Voxels', 'url': 'https://disk.yandex.ru/d/3SUoopowIUI8pA',
         'file': 'rethinking-voxels_beta18c.zip'},
        {'name': 'Super Duper Vanilla', 'url': 'https://disk.yandex.ru/d/aEiGZvEBXRe67Q',
         'file': 'superDuperVanilla.zip'}
    ]
}


def speed_test():
    """НОРМАЛЬНЫЙ тест скорости с гарантированно работающими серверами"""
    try:
        # РЕАЛЬНО РАБОТАЮЩИЕ серверы для теста
        test_servers = [
            {
                'url': 'https://cdn.windows93.net/img/logo.png',  # Маленький файл - быстро
                'name': 'Тестовый файл 1',
                'size': 0.05  # ~50KB
            },
            {
                'url': 'https://httpbin.org/bytes/102400',  # Генерирует 100KB данных
                'name': 'Тестовые данные 100KB',
                'size': 0.1
            },
            {
                'url': 'https://httpbin.org/bytes/512000',  # Генерирует 500KB данных
                'name': 'Тестовые данные 500KB',
                'size': 0.5
            }
        ]

        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        progress_window.title("Тест скорости интернета")
        progress_window.geometry("450x250")
        progress_window.resizable(False, False)
        progress_window.transient(win)
        progress_window.grab_set()

        # Центрируем окно
        progress_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (450 // 2)
        y = (win.winfo_screenheight() // 2) - (250 // 2)
        progress_window.geometry(f"450x250+{x}+{y}")

        # Заголовок
        title_label = ttk.Label(progress_window,
                                text="🚀 Тест скорости интернета",
                                font=('Comfortaa', 14, 'bold'))
        title_label.pack(pady=10)

        # Статус
        status_label = ttk.Label(progress_window,
                                 text="Подготовка к тесту...",
                                 font=('Comfortaa', 10))
        status_label.pack(pady=5)

        # Прогресс-бар
        progress = ttk.Progressbar(progress_window,
                                   orient="horizontal",
                                   length=380,
                                   mode="determinate")
        progress.pack(pady=10)

        # Детали
        details_label = ttk.Label(progress_window,
                                  text="Инициализация...",
                                  font=('Comfortaa', 9),
                                  foreground='blue')
        details_label.pack()

        # Время
        time_label = ttk.Label(progress_window,
                               text="Время: 0 сек",
                               font=('Comfortaa', 8))
        time_label.pack()

        # Кнопка отмены
        cancel_flag = threading.Event()

        def cancel_test():
            cancel_flag.set()
            progress_window.destroy()
            messagebox.showinfo("Отменено", "Тест скорости отменен")

        cancel_btn = ttk.Button(progress_window,
                                text="❌ Отменить тест",
                                command=cancel_test)
        cancel_btn.pack(pady=10)

        def test_thread():
            try:
                best_speed_mbps = 0
                best_speed_mb_sec = 0
                test_results = []

                for i, server in enumerate(test_servers):
                    if cancel_flag.is_set():
                        return

                    win.after(0, lambda: status_label.config(
                        text=f"Тест {i + 1}/{len(test_servers)}: {server['name']}"
                    ))
                    win.after(0, lambda: details_label.config(
                        text=f"Размер: {server['size']} MB"
                    ))
                    win.after(0, lambda: progress.config(value=(i * 100 / len(test_servers))))

                    try:
                        # Тестируем скорость для этого сервера
                        speed_mbps, speed_mb_sec = test_single_server(
                            server['url'],
                            server['size'],
                            progress_window,
                            cancel_flag
                        )

                        if speed_mbps > best_speed_mbps:
                            best_speed_mbps = speed_mbps
                            best_speed_mb_sec = speed_mb_sec

                        test_results.append({
                            'server': server['name'],
                            'speed_mbps': speed_mbps,
                            'speed_mb_sec': speed_mb_sec
                        })

                        # Небольшая пауза между тестами
                        time.sleep(1)

                    except Exception as e:
                        print(f"Ошибка теста {server['name']}: {e}")
                        continue

                if cancel_flag.is_set():
                    return

                # Показываем лучший результат
                if best_speed_mbps > 0:
                    win.after(0, lambda: show_speed_result(
                        best_speed_mb_sec, best_speed_mbps, test_results, progress_window
                    ))
                else:
                    win.after(0, lambda: show_speed_error(
                        "Все тесты завершились ошибкой", progress_window
                    ))

            except Exception as e:
                if not cancel_flag.is_set():
                    win.after(0, lambda: show_speed_error(str(e), progress_window))

        def test_single_server(url, expected_size, window, cancel_flag):
            """Тестирует скорость для одного сервера"""
            start_time = time.time()
            downloaded = 0

            try:
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                chunk_size = 8192

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if cancel_flag.is_set():
                        raise Exception("Тест отменен")

                    if chunk:
                        downloaded += len(chunk)

                        # Обновляем прогресс в реальном времени
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            current_speed_mbps = (downloaded / elapsed) / 125000  # Mbit/s

                            win.after(0, lambda: details_label.config(
                                text=f"Скорость: {current_speed_mbps:.1f} Mbit/s"
                            ))
                            win.after(0, lambda: time_label.config(
                                text=f"Время: {elapsed:.1f} сек"
                            ))

                            # Если тест длится больше 10 секунд - прерываем
                            if elapsed > 10:
                                break

                end_time = time.time()
                total_time = end_time - start_time

                if total_time > 0 and downloaded > 0:
                    speed_mbps = (downloaded / total_time) / 125000  # Mbit/s
                    speed_mb_sec = (downloaded / total_time) / (1024 * 1024)  # MB/s
                    return speed_mbps, speed_mb_sec
                else:
                    return 0, 0

            except requests.exceptions.Timeout:
                raise Exception("Таймаут соединения")
            except requests.exceptions.ConnectionError:
                raise Exception("Ошибка подключения")
            except Exception as e:
                raise e

        def show_speed_result(mb_per_sec, mbit_per_sec, test_results, window):
            window.destroy()

            # Оценка скорости
            if mbit_per_sec < 2:
                rating = "🐢 ОЧЕНЬ МЕДЛЕННО"
                color = "red"
                issues = "• Проблемы с интернетом\n• Могут быть лаги в игре"
            elif mbit_per_sec < 5:
                rating = "🚶 МЕДЛЕННО"
                color = "orange"
                issues = "• Минимально для игры\n• Возможны лаги"
            elif mbit_per_sec < 15:
                rating = "👍 НОРМАЛЬНО"
                color = "green"
                issues = "• Хорошо для игры\n• Стабильное соединение"
            elif mbit_per_sec < 30:
                rating = "🚀 БЫСТРО"
                color = "blue"
                issues = "• Отлично для игры\n• Быстрая загрузка"
            else:
                rating = "⚡ ОЧЕНЬ БЫСТРО"
                color = "purple"
                issues = "• Идеально для игры\n• Максимальная скорость"

            # Создаем окно результатов
            result_window = tk.Toplevel(win)
            result_window.title("Результаты теста скорости")
            result_window.geometry("500x400")
            result_window.configure(bg='#2b2b2b')
            result_window.resizable(False, False)

            # Центрируем
            result_window.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (500 // 2)
            y = (win.winfo_screenheight() // 2) - (400 // 2)
            result_window.geometry(f"500x400+{x}+{y}")

            # Содержимое
            main_frame = ttk.Frame(result_window, padding=25)
            main_frame.pack(fill='both', expand=True)

            # Заголовок
            ttk.Label(main_frame,
                      text="🎯 РЕЗУЛЬТАТЫ ТЕСТА СКОРОСТИ",
                      font=('Comfortaa', 16, 'bold'),
                      foreground='white',
                      background='#2b2b2b').pack(pady=(0, 20))

            # Основные метрики
            metrics_frame = ttk.Frame(main_frame)
            metrics_frame.pack(fill='x', pady=10)

            ttk.Label(metrics_frame,
                      text=f"🚀 СКОРОСТЬ ЗАГРУЗКИ: {mb_per_sec:.2f} MB/сек",
                      font=('Comfortaa', 14, 'bold'),
                      foreground='#4ECDC4',
                      background='#2b2b2b').pack()

            ttk.Label(metrics_frame,
                      text=f"💨 ПРОПУСКНАЯ СПОСОБНОСТЬ: {mbit_per_sec:.2f} Mbit/сек",
                      font=('Comfortaa', 14, 'bold'),
                      foreground='#4ECDC4',
                      background='#2b2b2b').pack(pady=5)

            # Оценка
            ttk.Label(main_frame,
                      text=f"🏆 ОЦЕНКА: {rating}",
                      font=('Comfortaa', 16, 'bold'),
                      foreground=color,
                      background='#2b2b2b').pack(pady=15)

            # Детали тестов
            ttk.Label(main_frame,
                      text="Результаты по серверам:",
                      font=('Comfortaa', 10, 'bold'),
                      foreground='#cccccc',
                      background='#2b2b2b').pack()

            for result in test_results:
                ttk.Label(main_frame,
                          text=f"• {result['server']}: {result['speed_mbps']:.1f} Mbit/s",
                          font=('Comfortaa', 9),
                          foreground='#888888',
                          background='#2b2b2b').pack()

            # Рекомендации
            ttk.Label(main_frame,
                      text="💡 РЕКОМЕНДАЦИИ:",
                      font=('Comfortaa', 11, 'bold'),
                      foreground='#ffcc00',
                      background='#2b2b2b').pack(pady=(20, 5))

            ttk.Label(main_frame,
                      text=issues,
                      font=('Comfortaa', 9),
                      foreground='#cccccc',
                      background='#2b2b2b',
                      justify='left').pack()

            ttk.Label(main_frame,
                      text="Для комфортной игры рекомендуется 10+ Mbit/сек",
                      font=('Comfortaa', 9),
                      foreground='#666666',
                      background='#2b2b2b').pack(pady=10)

            ttk.Button(main_frame,
                       text="✅ Закрыть",
                       command=result_window.destroy,
                       width=20).pack(pady=10)

        def show_speed_error(error_msg, window):
            window.destroy()
            messagebox.showerror(
                "Ошибка теста скорости",
                f"❌ Не удалось измерить скорость!\n\n"
                f"Причина: {error_msg}\n\n"
                f"🔧 Проверьте:\n"
                f"• Подключение к интернету\n"
                f"• Антивирус/брандмауэр\n"
                f"• VPN соединение\n"
                f"• Прокси-настройки\n\n"
                f"📞 Если проблема повторяется - обратитесь к провайдеру"
            )

        # Запускаем тест в отдельном потоке
        threading.Thread(target=test_thread, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить тест скорости: {str(e)}")





# Функция для скачивания шейдеров
def download_shaders():
    global LAUNCH_IN_PROGRESS

    # Проверяем, не запущена ли игра
    if LAUNCH_IN_PROGRESS:
        messagebox.showwarning(
            "Запуск в процессе",
            "❌ Нельзя скачивать шейдеры во время запуска игры!\n\n"
            "Дождитесь завершения запуска игры, затем повторите попытку."
        )
        return

    # Проверяем наличие папки shaderpacks
    shaders_dir = os.path.join(CONFIG['minecraft_dir'], 'shaderpacks')
    if not os.path.exists(shaders_dir):
        os.makedirs(shaders_dir)

    # Создаем окно выбора шейдеров
    shaders_window = tk.Toplevel(win)
    shaders_window.title("📥 Менеджер шейдеров")
    shaders_window.geometry("1200x550")
    shaders_window.resizable(True, True)
    shaders_window.transient(win)
    shaders_window.grab_set()

    # Центрируем окно
    shaders_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (1200 // 2)
    y = (win.winfo_screenheight() // 2) - (550 // 2)
    shaders_window.geometry(f"1200x550+{x}+{y}")

    # Заголовок
    header_frame = ttk.Frame(shaders_window, padding=10)
    header_frame.pack(fill='x')

    ttk.Label(header_frame, text="🎨 Выберите шейдеры для установки",
              font=('Comfortaa', 14, 'bold')).pack(pady=(0, 5))

    ttk.Label(header_frame, text="Выберите один или несколько шейдеров для загрузки",
              font=('Comfortaa', 10), foreground='gray').pack()

    # Фрейм для списка шейдеров с прокруткой
    tree_frame = ttk.Frame(shaders_window)
    tree_frame.pack(fill='both', expand=True, padx=15, pady=10)

    # Создаем Treeview с чекбоксами
    columns = ('selected', 'name', 'size')
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)

    # Настраиваем колонки
    tree.heading('selected', text='✓')
    tree.heading('name', text='Название шейдера')
    tree.heading('size', text='Размер')

    tree.column('selected', width=50, anchor='center')
    tree.column('name', width=450, anchor='w')
    tree.column('size', width=100, anchor='center')

    # Добавляем данные
    for shader in SHADERS_CONFIG['shaders']:
        tree.insert('', 'end', values=('☐', shader['name'], '~10-50MB'),
                    tags=(shader['url'], shader['file']))

    # Скроллбар
    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Переменная для хранения выбранных шейдеров
    selected_shaders = []

    def toggle_selection(event):
        item = tree.selection()
        if item:
            item = item[0]
            current_values = tree.item(item, 'values')
            if current_values[0] == '☐':
                tree.set(item, 'selected', '☑')
                selected_shaders.append({
                    'name': current_values[1],
                    'url': tree.item(item, 'tags')[0],
                    'file': tree.item(item, 'tags')[1]
                })
            else:
                tree.set(item, 'selected', '☐')
                # Удаляем из выбранных
                for shader in selected_shaders[:]:
                    if shader['name'] == current_values[1]:
                        selected_shaders.remove(shader)

        # Обновляем счетчик выбранных
        update_selection_count()

    tree.bind('<Button-1>', toggle_selection)

    # Счетчик выбранных шейдеров
    counter_label = ttk.Label(shaders_window, text="Выбрано: 0 шейдеров",
                              font=('Comfortaa', 9))
    counter_label.pack()

    def update_selection_count():
        count = len(selected_shaders)
        counter_label.config(text=f"Выбрано: {count} шейдеров")

        # Предупреждение при большом количестве
        if count > 5:
            counter_label.config(foreground='orange')
        else:
            counter_label.config(foreground='black')

    # Фрейм для кнопок
    button_frame = ttk.Frame(shaders_window, padding=10)
    button_frame.pack(fill='x')

    def download_selected():
        if not selected_shaders:
            messagebox.showwarning("Выбор", "❌ Пожалуйста, выберите хотя бы один шейдер")
            return

        total_size = len(selected_shaders) * 50  # Примерный расчет размера
        confirm = messagebox.askyesno(
            "Подтверждение загрузки",
            f"📥 Начать загрузку {len(selected_shaders)} шейдеров?\n\n"
            f"Примерный размер: ~{total_size} MB\n"
            f"Время загрузки: 1-5 минут\n\n"
            f"Шейдеры будут сохранены в папку:\n{shaders_dir}"
        )

        if confirm:
            shaders_window.destroy()
            download_shaders_turbo_ui(selected_shaders)

    def select_all():
        selected_shaders.clear()
        for item in tree.get_children():
            tree.set(item, 'selected', '☑')
            values = tree.item(item, 'values')
            selected_shaders.append({
                'name': values[1],
                'url': tree.item(item, 'tags')[0],
                'file': tree.item(item, 'tags')[1]
            })
        update_selection_count()

    def deselect_all():
        selected_shaders.clear()
        for item in tree.get_children():
            tree.set(item, 'selected', '☐')
        update_selection_count()

    def open_shaders_folder():
        try:
            if not os.path.exists(shaders_dir):
                os.makedirs(shaders_dir)
            if os.name == 'nt':  # Windows
                os.startfile(shaders_dir)
            elif os.name == 'posix':  # Linux/MacOS
                subprocess.Popen(['xdg-open', shaders_dir])
            messagebox.showinfo("Папка открыта", f"📁 Открыта папка шейдеров:\n{shaders_dir}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")

    # Кнопки управления
    ttk.Button(button_frame, text="✅ Выбрать все",
               command=select_all, width=15).pack(side='left', padx=5)
    ttk.Button(button_frame, text="❌ Снять все",
               command=deselect_all, width=15).pack(side='left', padx=5)
    ttk.Button(button_frame, text="📥 Скачать выбранные",
               command=download_selected).pack(side='left', padx=5)
    ttk.Button(button_frame, text="📁 Открыть папку",
               command=open_shaders_folder, width=15).pack(side='left', padx=5)
    ttk.Button(button_frame, text="❌ Закрыть",
               command=shaders_window.destroy).pack(side='right', padx=5)


def download_shaders_turbo_ui(selected_shaders):
    """UI для загрузки шейдеров с прогрессом"""
    progress_window = tk.Toplevel(win)
    progress_window.title("Скачивание шейдеров")
    progress_window.geometry("400x150")

    progress_label = ttk.Label(progress_window, text="Подготовка к скачиванию...")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=10)

    status_label = ttk.Label(progress_window, text="")
    status_label.pack()

    def update_progress(percent, status):
        progress['value'] = percent
        status_label.config(text=status)
        progress_window.update()

    def completion_callback(success_count, total):
        progress_window.destroy()
        if success_count > 0:
            messagebox.showinfo(
                "Скачивание завершено",
                f"✅ Успешно скачано {success_count} из {total} шейдеров!\n\n"
                f"Шейдеры сохранены в папке shaderpacks"
            )
        else:
            messagebox.showerror("Ошибка", "❌ Не удалось скачать ни одного шейдера")

    # Запускаем загрузку в отдельном потоке
    def download_thread():
        shaders_dir = os.path.join(CONFIG['minecraft_dir'], 'shaderpacks')
        os.makedirs(shaders_dir, exist_ok=True)

        downloader = TurboDownloader()
        total = len(selected_shaders)
        success_count = 0

        for i, shader in enumerate(selected_shaders):
            try:
                win.after(0, lambda: update_progress(
                    (i * 100) // total,
                    f"Скачивание: {shader['name']}..."
                ))

                direct_link = asyncio.run(downloader.get_turbo_link(shader['url']))
                if direct_link:
                    shader_path = os.path.join(shaders_dir, shader['file'])
                    success = downloader.download_file_sync(direct_link, shader_path)

                    if success:
                        success_count += 1
                        logging.info(f"Успешно скачан шейдер: {shader['name']}")
                    else:
                        logging.error(f"Ошибка скачивания шейдера: {shader['name']}")
                else:
                    logging.error(f"Не удалось получить ссылку для шейдера: {shader['name']}")

            except Exception as e:
                logging.error(f"Ошибка при загрузке шейдера {shader['name']}: {e}")

        win.after(0, lambda: completion_callback(success_count, total))

    threading.Thread(target=download_thread, daemon=True).start()








def get_yandex_direct_link(public_key):
    """Получаем прямую ссылку для скачивания через API Яндекс.Диска"""
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    try:
        response = requests.get(api_url, params={"public_key": public_key})
        response.raise_for_status()
        return response.json().get('href')
    except Exception as e:
        logging.error(f"Ошибка получения ссылки: {str(e)}")
        return None


def setup_environment():
    """Настройка окружения и загрузка ресурсов"""
    try:
        # Создаем папку если не существует
        RESOURCE_DIR.mkdir(parents=True, exist_ok=True)

        # Скачиваем недостающие файлы
        for filename, url in RESOURCES.items():
            file_path = RESOURCE_DIR / filename
            if not file_path.exists():
                # Получаем прямую ссылку на файл
                download_url = get_yandex_direct_link(url)
                if not download_url:
                    continue

                # Скачиваем файл
                response = requests.get(download_url, stream=True)
                response.raise_for_status()

                # Сохраняем файл
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logging.info(f"Файл {filename} успешно загружен")

    except Exception as e:
        logging.error(f"Ошибка инициализации: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось загрузить ресурсы: {str(e)}")
        sys.exit(1)



def validate_backup_integrity(backup_path):
    """Проверяет целостность ZIP-архива"""
    try:
        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            return zip_ref.testzip() is None
    except Exception as e:
        print(f"Ошибка проверки целостности бэкапа: {str(e)}")
        return False


def download_missing_mods_silent():
    """Тихая загрузка отсутствующих модов без UI"""
    try:
        minecraft_dir = CONFIG['minecraft_dir']
        mods_dir = os.path.join(minecraft_dir, 'mods')
        os.makedirs(mods_dir, exist_ok=True)

        # Проверяем какие моды отсутствуют
        missing_mods = []
        for mod in CONFIG['mods']:
            mod_path = os.path.join(mods_dir, mod['file'])
            if not os.path.exists(mod_path):
                missing_mods.append(mod)

        if missing_mods:
            print(f"🔧 Скачиваем {len(missing_mods)} отсутствующих модов...")
            # Используем существующую функцию загрузки
            for mod in missing_mods:
                download_single_mod_turbo(mod)

        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки модов: {e}")
        return False


def check_fabric_installed():
    """Проверяет установлен ли Fabric"""
    try:
        minecraft_dir = CONFIG['minecraft_dir']
        versions_dir = os.path.join(minecraft_dir, 'versions')
        fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
        fabric_version_dir = os.path.join(versions_dir, fabric_version)
        return os.path.exists(fabric_version_dir)
    except:
        return False


def install_fabric_silent():
    """Тихая установка Fabric"""
    try:
        print("🔧 Устанавливаем Fabric...")
        minecraft_launcher_lib.fabric.install_fabric(
            minecraft_version=CONFIG['version'],
            loader_version=CONFIG['fabric_loader'],
            minecraft_directory=CONFIG['minecraft_dir']
        )
        print("✅ Fabric установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Fabric: {e}")
        return False
def download_missing_mods_silent():
    """Тихая загрузка отсутствующих модов без UI"""
    try:
        minecraft_dir = CONFIG['minecraft_dir']
        mods_dir = os.path.join(minecraft_dir, 'mods')
        os.makedirs(mods_dir, exist_ok=True)

        # Проверяем какие моды отсутствуют
        missing_mods = []
        for mod in CONFIG['mods']:
            mod_path = os.path.join(mods_dir, mod['file'])
            if not os.path.exists(mod_path):
                missing_mods.append(mod)

        if missing_mods:
            print(f"🔧 Скачиваем {len(missing_mods)} отсутствующих модов...")
            # Используем существующую функцию загрузки
            for mod in missing_mods:
                download_single_mod_turbo(mod)

        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки модов: {e}")
        return False

def check_fabric_installed():
    """Проверяет установлен ли Fabric"""
    try:
        minecraft_dir = CONFIG['minecraft_dir']
        versions_dir = os.path.join(minecraft_dir, 'versions')
        fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
        fabric_version_dir = os.path.join(versions_dir, fabric_version)
        return os.path.exists(fabric_version_dir)
    except:
        return False

def install_fabric_silent():
    """Тихая установка Fabric"""
    try:
        print("🔧 Устанавливаем Fabric...")
        minecraft_launcher_lib.fabric.install_fabric(
            minecraft_version=CONFIG['version'],
            loader_version=CONFIG['fabric_loader'],
            minecraft_directory=CONFIG['minecraft_dir']
        )
        print("✅ Fabric установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Fabric: {e}")
        return False


def is_discord_installed():
    # Проверяем, установлен ли Discord (пример для Windows)
    if os.name == 'nt':  # Windows
        discord_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Discord')
        return os.path.exists(discord_path)
    else:  # Linux/MacOS
        # Добавь проверки для других ОС, если нужно
        return False

def update_discord_status():
    if not is_discord_installed():
        print("Discord не установлен. Интеграция с Discord пропущена.")
        return

    try:
        RPC = Presence("1349070276327116890")
        RPC.connect()
        RPC.update(
            state="Играет",
            details="YamalPixel",
            large_image="logo",
            buttons=[{"label": "Скачать", "url": "https://disk.yandex.ru/d/WaJwp2ThduRrgQ"}]
        )
    except Exception as e:
        print(f"Ошибка при подключении к Discord: {str(e)}")





def check_for_updates():
    try:
        logging.info("Проверка обновлений...")

        # Проверяем права доступа
        if not can_update_launcher():
            logging.warning("Недостаточно прав для автоматического обновления")
            return
        response = requests.get("https://api.github.com/repos/XxMoonmenxX/YamalPixel/releases/latest")
        response.raise_for_status()

        release_data = response.json()
        changelog = release_data.get('body', 'Нет описания изменений')

        # Убираем Markdown-разметку и форматируем
        changelog = re.sub(r'\#{2,}', '', changelog)
        changelog = re.sub(r'\- ', '• ', changelog)
        changelog = re.sub(r'\*\*(.*?)\*\*', r'\1', changelog)
        changelog = re.sub(r'\*(.*?)\*', r'\1', changelog)
        changelog = changelog.strip()

        latest_version = release_data['tag_name'].lstrip('v')

        if latest_version != CURRENT_VERSION:
            logging.info(f"Найдена новая версия: {latest_version}")

            # Создаем окно обновления
            update_window = tk.Toplevel(win)
            update_window.title(f"YamalPixel - Обновление до v{latest_version}")
            update_window.geometry("550x450")
            update_window.resizable(True, True)
            update_window.transient(win)
            update_window.grab_set()

            # Устанавливаем минимальный размер окна
            update_window.minsize(500, 400)

            # Делаем светлую тему для лучшей читаемости
            update_window.configure(bg='white')

            # Центрируем окно
            update_window.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (550 // 2)
            y = (win.winfo_screenheight() // 2) - (450 // 2)
            update_window.geometry(f"550x450+{x}+{y}")

            # Используем grid для всего окна
            update_window.columnconfigure(0, weight=1)
            update_window.rowconfigure(2, weight=1)  # Текстовое поле будет расширяться

            # Заголовок
            header_frame = tk.Frame(update_window, bg='white')
            header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=15)
            header_frame.columnconfigure(0, weight=1)

            tk.Label(header_frame,
                     text=f"Доступно обновление!",
                     font=('Comfortaa', 14, 'bold'),
                     bg='white', fg='#2c3e50').grid(row=0, column=0)

            tk.Label(header_frame,
                     text=f"Версия {latest_version}",
                     font=('Comfortaa', 11),
                     bg='white', fg='#7f8c8d').grid(row=1, column=0, pady=(5, 0))

            # Разделитель
            separator = ttk.Separator(update_window, orient='horizontal')
            separator.grid(row=1, column=0, sticky='ew', padx=20, pady=10)

            # Метка "Что нового"
            label_frame = tk.Frame(update_window, bg='white')
            label_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=(0, 5))
            label_frame.columnconfigure(0, weight=1)

            tk.Label(label_frame,
                     text="Что нового в этой версии:",
                     font=('Comfortaa', 10, 'bold'),
                     bg='white', fg='#2c3e50').grid(row=0, column=0, sticky='w')

            # Фрейм для текста с прокруткой
            text_frame = tk.Frame(update_window, bg='white')
            text_frame.grid(row=3, column=0, sticky='nsew', padx=20, pady=(0, 10))
            text_frame.columnconfigure(0, weight=1)
            text_frame.rowconfigure(0, weight=1)

            # Текстовое поле
            text_widget = tk.Text(text_frame,
                                  wrap='word',
                                  width=60,
                                  height=15,
                                  font=('Comfortaa', 9),
                                  bg='#f8f9fa',
                                  fg='#2c3e50',
                                  relief='solid',
                                  borderwidth=1,
                                  padx=10,
                                  pady=10)

            scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            # Вставляем текст
            text_widget.insert('1.0', changelog)
            text_widget.configure(state='disabled')

            # Упаковываем с grid
            text_widget.grid(row=0, column=0, sticky='nsew')
            scrollbar.grid(row=0, column=1, sticky='ns')

            # Фрейм для кнопок
            button_frame = tk.Frame(update_window, bg='white')
            button_frame.grid(row=4, column=0, sticky='ew', padx=20, pady=15)
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)

            def install_update():
                update_window.destroy()

                # Ищем ЛЮБОЙ EXE-файл в ассетах
                update_asset = next(
                    (asset for asset in release_data['assets']
                     if asset['name'].lower().endswith('.exe')),
                    None
                )

                if update_asset:
                    download_and_install_update(update_asset['browser_download_url'])
                else:
                    # Если EXE не найден, показываем какие файлы есть
                    available_files = "\n".join([f"• {asset['name']}" for asset in release_data['assets']])
                    messagebox.showerror(
                        "Файл не найден",
                        f"EXE-файл не найден в релизе.\n\nДоступные файлы:\n{available_files}"
                    )

            def skip_update():
                update_window.destroy()
                logging.info("Пользователь отказался от обновления")

            # Кнопки - используем grid для фиксированного размера
            btn_install = tk.Button(button_frame,
                                    text="🔄 УСТАНОВИТЬ ОБНОВЛЕНИЕ",
                                    font=('Comfortaa', 10, 'bold'),
                                    bg='#27ae60',
                                    fg='white',
                                    relief='flat',
                                    padx=20,
                                    pady=10,
                                    command=install_update)
            btn_install.grid(row=0, column=0, padx=(0, 10), sticky='ew')

            btn_skip = tk.Button(button_frame,
                                 text="ПРОПУСТИТЬ",
                                 font=('Comfortaa', 10),
                                 bg='#95a5a6',
                                 fg='white',
                                 relief='flat',
                                 padx=20,
                                 pady=10,
                                 command=skip_update)
            btn_skip.grid(row=0, column=1, sticky='ew')

            # Фокус и прокрутка
            text_widget.focus_set()
            text_widget.see('1.0')

            # Добавляем ховер-эффекты для кнопок
            def on_enter_install(e):
                btn_install.configure(bg='#219653')

            def on_leave_install(e):
                btn_install.configure(bg='#27ae60')

            def on_enter_skip(e):
                btn_skip.configure(bg='#7f8c8d')

            def on_leave_skip(e):
                btn_skip.configure(bg='#95a5a6')

            btn_install.bind("<Enter>", on_enter_install)
            btn_install.bind("<Leave>", on_leave_install)
            btn_skip.bind("<Enter>", on_enter_skip)
            btn_skip.bind("<Leave>", on_leave_skip)

        else:
            logging.info("Лаунчер актуален")

    except Exception as e:
        logging.error(f"Ошибка проверки обновлений: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось проверить обновления: {str(e)}")


def can_update_launcher():
    """Проверяет, можно ли обновить лаунчер"""
    try:
        # Пробуем создать тестовый файл в той же директории
        test_file = os.path.join(os.path.dirname(sys.argv[0]), "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
    except:
        return False

def download_and_install_update(download_url):
    """Улучшенная функция обновления с обработкой прав доступа"""
    import tempfile
    import stat

    temp_dir = tempfile.gettempdir()
    temp_exe = os.path.join(temp_dir, "YamalPixelLauncher_New.exe")
    current_exe = os.path.abspath(sys.argv[0])  # Текущий исполняемый файл
    backup_exe = os.path.join(os.path.dirname(current_exe), "YamalPixelLauncher_Backup.exe")

    progress_window = None

    try:
        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        progress_window.title("Обновление")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)

        progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress.pack(pady=20)
        status_label = ttk.Label(progress_window, text="Скачивание обновления...")
        status_label.pack()

        # Скачиваем новую версию во временную папку
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))

            with open(temp_exe, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int((downloaded / total_size) * 100) if total_size > 0 else 0
                        progress['value'] = percent
                        status_label.config(text=f"Загружено {percent}%")
                        progress_window.update()

        # Делаем файл исполняемым (для Linux/MacOS)
        if os.name != 'nt':
            os.chmod(temp_exe, os.stat(temp_exe).st_mode | stat.S_IEXEC)

        progress['value'] = 100
        status_label.config(text="Подготовка к обновлению...")
        progress_window.update()

        # Создаем скрипт обновления
        if os.name == 'nt':  # Windows
            bat_path = os.path.join(temp_dir, "yamalpixel_update.bat")
            with open(bat_path, 'w') as bat_file:
                bat_file.write(f"""
@echo off
chcp 65001 >nul
echo YamalPixel - Обновление
timeout /t 2 /nobreak >nul

:: Закрываем лаунчер
taskkill /f /im "{os.path.basename(current_exe)}" >nul 2>&1
timeout /t 1 /nobreak >nul

:: Создаем бэкап старой версии
if exist "{current_exe}" (
    copy "{current_exe}" "{backup_exe}" >nul 2>&1
)

:: Заменяем файл
if exist "{temp_exe}" (
    del "{current_exe}" >nul 2>&1
    move "{temp_exe}" "{current_exe}" >nul 2>&1
)

:: Запускаем новую версию
if exist "{current_exe}" (
    start "" "{current_exe}"
)

:: Удаляем временные файлы
del "{backup_exe}" >nul 2>&1
del "%~f0" >nul 2>&1
""")

            # Запускаем батник
            subprocess.Popen([bat_path], shell=True,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        else:  # Linux/MacOS
            sh_path = os.path.join(temp_dir, "yamalpixel_update.sh")
            with open(sh_path, 'w') as sh_file:
                sh_file.write(f"""#!/bin/bash
echo "YamalPixel - Обновление"
sleep 2

# Закрываем лаунчер
pkill -f "{os.path.basename(current_exe)}" 2>/dev/null
sleep 1

# Создаем бэкап
if [ -f "{current_exe}" ]; then
    cp "{current_exe}" "{backup_exe}" 2>/dev/null
fi

# Заменяем файл
if [ -f "{temp_exe}" ]; then
    rm -f "{current_exe}" 2>/dev/null
    mv "{temp_exe}" "{current_exe}" 2>/dev/null
    chmod +x "{current_exe}" 2>/dev/null
fi

# Запускаем новую версию
if [ -f "{current_exe}" ]; then
    "{current_exe}" &
fi

# Очистка
rm -f "{backup_exe}" 2>/dev/null
rm -f "$0" 2>/dev/null
""")
            os.chmod(sh_path, 0o755)
            subprocess.Popen(['nohup', 'bash', sh_path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        # Закрываем текущий лаунчер
        if progress_window:
            progress_window.destroy()

        win.after(100, lambda: sys.exit(0))

    except Exception as e:
        logging.error(f"Ошибка обновления: {str(e)}")

        # Очистка при ошибке
        try:
            if os.path.exists(temp_exe):
                os.remove(temp_exe)
        except:
            pass

        if progress_window:
            progress_window.destroy()

        # Предлагаем альтернативный способ обновления
        show_manual_update_option(download_url)


def show_manual_update_option(download_url):
    """Показывает опцию ручного обновления при ошибке автоматического"""
    result = messagebox.askyesno(
        "Ошибка автоматического обновления",
        "Не удалось автоматически обновиться.\n\n"
        "Причины:\n"
        "• Недостаточно прав\n"
        "• Антивирус заблокировал обновление\n"
        "• Файл занят другим процессом\n\n"
        "Хотите скачать новую версию вручную?",
        icon='warning'
    )

    if result:
        import webbrowser
        webbrowser.open(download_url)
        messagebox.showinfo(
            "Ручное обновление",
            "Скачайте новую версию и замените текущий файл лаунчера.\n\n"
            "Текущий лаунчер будет закрыт."
        )
        sys.exit(0)



# Функция очистки перед запуском
def cleanup_before_launch():
    launcher_dir = os.getcwd()
    minecraft_dir = os.path.expanduser("~/YamalPixel/versions")
    old_Mods = os.path.expanduser("~/YamalPixel/mods")
    items_to_remove = [
        os.path.join(launcher_dir, 'config'),
        os.path.join(launcher_dir, 'patchouli_books'),
        os.path.join(launcher_dir, 'patchouli_data.json'),
        os.path.join(launcher_dir, 'logs'),
        os.path.join(launcher_dir, 'logo.png'),
        os.path.join(launcher_dir, 'Obuse - Menu song.mp3'),
        os.path.join(launcher_dir, 'YamalPixelLauncer_V_0.2.06.exe'),
        os.path.join(launcher_dir, 'YamalPixelLauncer_V_0.3.0.exe'),
        os.path.join(old_Mods, 'fabric-language-kotlin-1.13.6+kotlin.2.2.20.jarr'),

        # Старые моды 1.18.2 которые могут конфликтовать
        os.path.join(old_Mods, 'jei-1.18.2-fabric-10.2.1.283.jar'),
        os.path.join(old_Mods, 'Xaeros_Minimap_22.14.1_Fabric_1.18.2.jar'),
        os.path.join(old_Mods, 'fabric-language-kotlin-1.7.3+kotlin.1.6.20.jar'),
        os.path.join(old_Mods, 'JEI.zip'),

        # Старые версии Fabric
        os.path.join(minecraft_dir, 'fabric-loader-0.15.11-1.20.1'),
        os.path.join(minecraft_dir, 'fabric-loader-0.16.10-1.18.2'),

        # Все моды из твоего конфига 1.18.2
        os.path.join(old_Mods, 'fabric-api-0.77.0.jar'),
        os.path.join(old_Mods, 'sodium-fabric-mc1.18.2-0.4.1+build.15.jar'),
        os.path.join(old_Mods, 'indium-0.7.10+mc1.18.2.zip'),
        os.path.join(old_Mods, 'AdvancedReborn-1.18.2-1.0.6.jar'),
        os.path.join(old_Mods, 'RebornCore-5.2.0.jar'),
        os.path.join(old_Mods, 'TechReborn-5.2.0.jar'),
        os.path.join(old_Mods, 'Xaeros_Minimap_25.2.10_Fabric_1.18.2.jar'),
        os.path.join(old_Mods, 'architectury-4.9.83-fabric.jar'),
        os.path.join(old_Mods, 'betterdroppeditems-1.3.2-1.18.2.jar'),
        os.path.join(old_Mods, 'cloth-config-6.3.81-fabric.jar'),
        os.path.join(old_Mods, 'lithium-fabric-mc1.18.2-0.7.10.jar'),
        os.path.join(old_Mods, 'modmenu-3.2.5.jar'),
        os.path.join(old_Mods, 'autoconfig1u-3.4.0.jar'),
        os.path.join(old_Mods, 'NoIndium-1.0.2+1.18.2.jar'),
        os.path.join(old_Mods, 'omega-config-base-1.2.3-1.18.1.jar'),
        os.path.join(old_Mods, 'pal-1.5.0.jar'),
        os.path.join(old_Mods, 'Patchouli-1.18.2-66-FABRIC.jar'),
        os.path.join(old_Mods, 'cardinal-components-api-4.2.0.jar'),
        os.path.join(old_Mods, 'ctov-2.9.4.jar'),
        os.path.join(old_Mods, 'emi-0.7.3+1.18.2.jar'),
        os.path.join(old_Mods, 'lambdynamiclights-2.1.0+1.17.jar'),
        os.path.join(old_Mods, 'more-axolotls-1.1.0-1.18.jar'),
        os.path.join(old_Mods, 'enchanted-golden-apple-addition-2.0.jar'),
        os.path.join(old_Mods, 'mvs-2.2.6-1.18.2.jar'),
        os.path.join(old_Mods, 'ironchests-2.0.5-fabric.jar'),
        os.path.join(old_Mods, 'appliedenergistics2-fabric-11.7.6.jar'),
        os.path.join(old_Mods, 'lovely_snails-1.0.4+1.18.jar'),
        os.path.join(old_Mods, 'PresenceFootsteps-1.5.1.jar'),
        os.path.join(old_Mods, 'cloth-config-6.5.102-fabric.jar'),
        os.path.join(old_Mods, 'fallingleaves-1.11.1+1.18.2.jar'),
        os.path.join(old_Mods, 'InventoryProfilesNext-fabric-1.18.2-1.10.19.jar'),
        os.path.join(old_Mods, 'XaerosWorldMap_1.39.12_Fabric_1.18.2.jar'),
        os.path.join(old_Mods, 'libIPN-fabric-1.18.2-4.0.2.jar'),
        os.path.join(old_Mods, 'Frogmod.jar'),
        os.path.join(old_Mods, 'geckolib-fabric-1.18-3.0.80.jar'),
        os.path.join(old_Mods, 'extra-mod-integrations-0.0.31.18.2.jar'),
        os.path.join(old_Mods, 'travelersbackpack-fabric-1.18.2-7.1.43.jar')
    ]

    for item in items_to_remove:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
            print(f"Удалено: {item}")




# Функция проверки версии Java
def check_java_version():
    """
    Улучшенная проверка версии Java с несколькими методами
    """
    java_versions = []

    # Метод 1: Проверка через java -version (основной)
    try:
        result = subprocess.run(['java', '-version'],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                text=True,
                                timeout=10,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

        # Ищем версию в stderr (обычно там вывод)
        version_output = result.stderr or result.stdout

        # Несколько паттернов для поиска версии
        patterns = [
            r'version "([1-9]\d*\.\d+\.\d+[_\d]*)',  # OpenJDK/Oracle
            r'java version "([1-9]\d*\.\d+\.\d+[_\d]*)',  # Старые версии
            r'openjdk version "([1-9]\d*\.\d+\.\d+[_\d]*)',  # OpenJDK
            r'\"([1-9]\d*\.\d+\.\d+[_\d]*)'  # Общий паттерн
        ]

        for pattern in patterns:
            version_match = re.search(pattern, version_output)
            if version_match:
                version_str = version_match.group(1)
                major_version = extract_major_version(version_str)
                java_versions.append(major_version)
                print(f"Найдена Java версия: {version_str} (major: {major_version})")
                break

    except (subprocess.CalledProcessError, FileNotFoundError, IndexError, TimeoutError) as e:
        print(f"Метод 1 (java -version) не сработал: {str(e)}")

    # Метод 2: Проверка через where/java (поиск в PATH)
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['where', 'java'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    timeout=5,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        else:  # Linux/MacOS
            result = subprocess.run(['which', 'java'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    timeout=5)

        if result.returncode == 0:
            java_path = result.stdout.strip().split('\n')[0]
            print(f"Java найдена по пути: {java_path}")

            # Проверяем версию найденной Java
            version_result = subprocess.run([java_path, '-version'],
                                            stderr=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            text=True,
                                            timeout=5)

            version_output = version_result.stderr or version_result.stdout
            version_match = re.search(r'version "([1-9]\d*\.\d+\.\d+[_\d]*)', version_output)
            if version_match:
                version_str = version_match.group(1)
                major_version = extract_major_version(version_str)
                java_versions.append(major_version)
                print(f"Java из PATH: {version_str} (major: {major_version})")

    except Exception as e:
        print(f"Метод 2 (поиск в PATH) не сработал: {str(e)}")

    # Метод 3: Проверка переменных среды JAVA_HOME
    try:
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            java_exe = os.path.join(java_home, 'bin', 'java.exe' if os.name == 'nt' else 'java')
            if os.path.exists(java_exe):
                version_result = subprocess.run([java_exe, '-version'],
                                                stderr=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                text=True,
                                                timeout=5)

                version_output = version_result.stderr or version_result.stdout
                version_match = re.search(r'version "([1-9]\d*\.\d+\.\d+[_\d]*)', version_output)
                if version_match:
                    version_str = version_match.group(1)
                    major_version = extract_major_version(version_str)
                    java_versions.append(major_version)
                    print(f"Java из JAVA_HOME: {version_str} (major: {major_version})")

    except Exception as e:
        print(f"Метод 3 (JAVA_HOME) не сработал: {str(e)}")

    # Анализ результатов
    if java_versions:
        max_version = max(java_versions)
        print(f"Максимальная найденная версия Java: {max_version}")
        return max_version >= 17
    else:
        print("Java не найдена ни одним из методов")
        return False


def extract_major_version(version_str):
    """
    Извлекает мажорную версию из строки версии Java
    Обрабатывает разные форматы: 1.8.0, 9.0.1, 11.0.2, 17.0.1 и т.д.
    """
    try:
        # Убираем возможные префиксы и суффиксы
        clean_version = version_str.split('_')[0]  # Убираем update версии

        parts = clean_version.split('.')

        # Новый формат версий (9+): первое число - мажорная версия
        if len(parts) >= 1:
            major = int(parts[0])
            # Старый формат версий (1.8.x): второе число - мажорная версия
            if major == 1 and len(parts) >= 2:
                return int(parts[1])
            return major

    except (ValueError, IndexError) as e:
        print(f"Ошибка парсинга версии Java '{version_str}': {str(e)}")

    return 0


def get_java_installer_url():
    """
    Возвращает URL для установки Java 17 в зависимости от ОС
    """
    system = platform.system()
    architecture = platform.machine().lower()

    if system == "Windows":
        if '64' in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_windows_hotspot_17.0.11_9.msi"
        else:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x86-32_windows_hotspot_17.0.11_9.msi"

    elif system == "Linux":
        if 'x86_64' in architecture or 'amd64' in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_linux_hotspot_17.0.11_9.tar.gz"
        elif 'aarch64' in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_aarch64_linux_hotspot_17.0.11_9.tar.gz"

    elif system == "Darwin":  # macOS
        if 'arm' in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_aarch64_mac_hotspot_17.0.11_9.tar.gz"
        else:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_mac_hotspot_17.0.11_9.tar.gz"

    return None


def install_java_with_progress():
    """
    Улучшенная установка Java 17 с детектированием ОС и архитектуры
    """
    java_window = tk.Toplevel(win)
    java_window.title("Установка Java 17")
    java_window.geometry("450x200")
    java_window.resizable(False, False)

    # Центрируем окно
    java_window.transient(win)
    java_window.grab_set()

    progress_label = ttk.Label(java_window, text="Установка Java 17...", font=('Comfortaa', 10))
    progress_label.pack(pady=15)

    progress = ttk.Progressbar(java_window, orient="horizontal", length=350, mode="indeterminate")
    progress.pack(pady=10)
    progress.start()

    status_label = ttk.Label(java_window, text="Подготовка к установке...", font=('Comfortaa', 9))
    status_label.pack(pady=5)

    details_label = ttk.Label(java_window, text="", font=('Comfortaa', 8), foreground='gray')
    details_label.pack(pady=5)

    def install_thread():
        try:
            system = platform.system()
            status_label.config(text="Определение вашей системы...")
            details_label.config(text=f"ОС: {system}, Архитектура: {platform.machine()}")

            if system == "Windows":
                install_java_windows(status_label, details_label)
            elif system == "Linux":
                install_java_linux(status_label, details_label)
            elif system == "Darwin":
                install_java_macos(status_label, details_label)
            else:
                raise Exception(f"Неподдерживаемая ОС: {system}")

            # Проверяем успешность установки
            java_window.after(1000, lambda: verify_java_installation(java_window))

        except Exception as e:
            java_window.after(0, lambda: show_java_install_error(str(e)))

    def verify_java_installation(window):
        if check_java_version():
            window.destroy()
            messagebox.showinfo("Успех", "Java 17 успешно установлена! Теперь вы можете запустить игру.")
        else:
            messagebox.showwarning("Предупреждение",
                                   "Java может быть установлена, но не обнаружена.\n"
                                   "Попробуйте перезапустить лаунчер или перезагрузить компьютер.")

    threading.Thread(target=install_thread, daemon=True).start()


def install_java_windows(status_label, details_label):
    """Установка Java на Windows"""
    try:
        status_label.config(text="Скачивание установщика Java...")
        details_label.config(text="Это может занять несколько минут")

        url = get_java_installer_url()
        if not url:
            raise Exception("Не найден подходящий установщик для вашей системы")

        msi_path = os.path.join(os.environ['TEMP'], 'OpenJDK17.msi')

        def download_progress_hook(count, block_size, total_size):
            if total_size > 0:
                percent = min(int(count * block_size * 100 / total_size), 100)
                status_label.config(text=f"Скачивание: {percent}%")

        urllib.request.urlretrieve(url, msi_path, reporthook=download_progress_hook)

        status_label.config(text="Установка Java...")
        details_label.config(text="Не закрывайте это окно")

        # Запуск установки
        result = subprocess.run(
            f'msiexec /i "{msi_path}" /quiet /norestart',
            shell=True,
            timeout=300,  # 5 минут таймаут
            capture_output=True,
            text=True
        )

        # Очистка
        if os.path.exists(msi_path):
            os.remove(msi_path)

        if result.returncode != 0:
            raise Exception(f"Ошибка установки: {result.stderr}")

    except subprocess.TimeoutExpired:
        raise Exception("Установка заняла слишком много времени. Попробуйте установить Java вручную.")
    except Exception as e:
        raise Exception(f"Ошибка установки на Windows: {str(e)}")


def install_java_linux(status_label, details_label):
    """Установка Java на Linux"""
    try:
        status_label.config(text="Установка Java через пакетный менеджер...")

        # Проверяем какой пакетный менеджер доступен
        commands = [
            # Ubuntu/Debian
            ['sudo', 'apt-get', 'update', '-y'],
            ['sudo', 'apt-get', 'install', '-y', 'wget', 'apt-transport-https', 'gnupg'],
            ['wget', '-qO', '-', 'https://packages.adoptium.net/artifactory/api/gpg/key/public'],
            ['sudo', 'apt-key', 'add', '-'],
            ['echo', '"deb https://packages.adoptium.net/artifactory/deb $(lsb_release -cs) main"', '|', 'sudo', 'tee',
             '/etc/apt/sources.list.d/adoptium.list'],
            ['sudo', 'apt-get', 'update', '-y'],
            ['sudo', 'apt-get', 'install', '-y', 'temurin-17-jdk']
        ]

        for cmd in commands:
            status_label.config(text=f"Выполнение: {' '.join(cmd[:2])}...")
            result = subprocess.run(' '.join(cmd) if isinstance(cmd, list) else cmd,
                                    shell=True,
                                    capture_output=True,
                                    text=True,
                                    timeout=60)
            if result.returncode != 0:
                print(
                    f"Команда {' '.join(cmd) if isinstance(cmd, list) else cmd} завершилась с ошибкой: {result.stderr}")

    except Exception as e:
        raise Exception(f"Ошибка установки на Linux: {str(e)}")


def install_java_macos(status_label, details_label):
    """Установка Java на macOS"""
    try:
        status_label.config(text="Установка через Homebrew...")

        # Проверяем установлен ли Homebrew
        result = subprocess.run(['which', 'brew'], capture_output=True)
        if result.returncode != 0:
            status_label.config(text="Установка Homebrew...")
            subprocess.run(
                '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                shell=True,
                check=True,
                timeout=300
            )

        status_label.config(text="Установка Java...")
        subprocess.run(['brew', 'tap', 'adoptium/temurin'], check=True)
        subprocess.run(['brew', 'install', '--cask', 'temurin17'], check=True)

    except Exception as e:
        raise Exception(f"Ошибка установки на macOS: {str(e)}")


def show_java_install_error(error_msg):
    """Показывает детальную информацию об ошибке установки Java"""
    error_window = tk.Toplevel(win)
    error_window.title("Ошибка установки Java")
    error_window.geometry("500x300")

    tk.Label(error_window, text="❌ Ошибка установки Java 17",
             font=('Comfortaa', 12, 'bold'), foreground='red').pack(pady=10)

    tk.Label(error_window, text="Не удалось автоматически установить Java 17",
             font=('Comfortaa', 10)).pack(pady=5)

    # Детали ошибки
    details_text = tk.Text(error_window, height=8, width=60, font=('Consolas', 8))
    details_text.pack(pady=10, padx=10, fill='both', expand=True)
    details_text.insert('1.0', f"Детали ошибки:\n{error_msg}")
    details_text.config(state='disabled')

    # Рекомендации
    tk.Label(error_window, text="Рекомендации:", font=('Comfortaa', 9, 'bold')).pack()
    tk.Label(error_window, text="1. Установите Java 17 вручную с adoptium.net\n2. Перезапустите лаунчер",
             font=('Comfortaa', 8)).pack()

    tk.Button(error_window, text="Закрыть", command=error_window.destroy).pack(pady=10)





def debug_java_installation():
    """
    Функция для диагностики проблем с Java
    """
    print("=== ДИАГНОСТИКА JAVA ===")

    # Проверка PATH
    print("Переменная PATH:", os.environ.get('PATH', '').split(';'))

    # Проверка JAVA_HOME
    java_home = os.environ.get('JAVA_HOME')
    print(f"JAVA_HOME: {java_home}")

    if java_home:
        java_exe = os.path.join(java_home, 'bin', 'java.exe' if os.name == 'nt' else 'java')
        print(f"Java executable exists: {os.path.exists(java_exe)}")

    # Попытка запуска java -version с подробным выводом
    try:
        result = subprocess.run(['java', '-version'],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                text=True,
                                timeout=10)
        print(f"Java -version stderr: {result.stderr}")
        print(f"Java -version stdout: {result.stdout}")
        print(f"Return code: {result.returncode}")
    except Exception as e:
        print(f"Error running java -version: {e}")

    print("=== КОНЕЦ ДИАГНОСТИКИ ===")
debug_java_installation()

# Функция установки Java с прогрессом
def install_java_with_progress():
    java_window = tk.Toplevel(win)
    java_window.title("Установка Java 17")
    java_window.geometry("400x150")

    progress_label = ttk.Label(java_window, text="Прогресс установки Java 17:")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(java_window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=10)

    status_label = ttk.Label(java_window, text="")
    status_label.pack()

    def download_progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            progress['value'] = percent
            status_label.config(text=f"Скачано {percent}%")
            java_window.update_idletasks()

    def install_thread():
        try:
            system = platform.system()
            if system == "Windows":
                url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_windows_hotspot_17.0.11_9.msi"
                msi_path = os.path.join(os.environ['TEMP'], 'OpenJDK17.msi')
                urllib.request.urlretrieve(url, msi_path, reporthook=lambda c, b, t: download_progress_hook(c, b, t))
                subprocess.run(f'msiexec /i "{msi_path}" /quiet', shell=True, check=True)
                os.remove(msi_path)
            elif system == "Linux":
                subprocess.run('sudo apt-get install -y wget apt-transport-https', shell=True, check=True)
                subprocess.run(
                    'wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo apt-key add -',
                    shell=True, check=True)
                subprocess.run(
                    'echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= \'/^VERSION_CODENAME/{print $2}\' /etc/os-release) main" | sudo tee /etc/apt/sources.list.d/adoptium.list',
                    shell=True, check=True)
                subprocess.run('sudo apt-get update -y', shell=True, check=True)
                subprocess.run('sudo apt-get install -y temurin-17-jdk', shell=True, check=True)
            elif system == "Darwin":
                subprocess.run(
                    '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                    shell=True, check=True)
                subprocess.run('brew tap adoptium/temurin', shell=True, check=True)
                subprocess.run('brew install --cask temurin17', shell=True, check=True)
            java_window.destroy()
            messagebox.showinfo("Успех :D", "Java 17 успешно установлена! ЗАПУСКАЙ!!!")
        except Exception as e:
            messagebox.showerror("АШЫПКА :D", f"Java 17 установлена. ЗАПУСКАЙ!!!!")
            sys.exit(1)

    if not check_java_version():
        threading.Thread(target=install_thread, daemon=True).start()
    else:
        java_window.destroy()

# Инициализация проверки Java при запуске

def skip_java_check():
    """Пропустить проверку Java (для опытных пользователей)"""
    result = messagebox.askyesno(
        "Пропустить проверку Java",
        "Вы уверены, что хотите пропустить проверку Java?\n\n"
        "Игра может не запуститься если Java 17 не установлена.\n"
        "Продолжить на свой страх и риск?",
        icon='warning'
    )
    return result
# Инициализация звука
mixer.init()
mixer.music.set_volume(0.1)

# Создание главного окна
win = ThemedTk(theme="arc")
win.geometry("1920x1080")
win.title('YamPixel')

# === ПЕРЕМЕЩАЕМ СЮДА ВСЁ ОТНОСИТЕЛЬНО СЕССИИ ===
LAST_SESSION_FILE = os.path.expanduser("~/YamalPixel/last_session.json")


def load_last_session():
    """Загружает последние настройки"""
    try:
        if os.path.exists(LAST_SESSION_FILE):
            with open(LAST_SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📁 Загружена сессия: {len(data)} параметров")
                return data
    except Exception as e:
        print(f"❌ Ошибка загрузки сессии: {e}")
    return None


def save_last_session():
    """Сохраняет последние настройки"""
    try:
        session_data = {}

        # Сохраняем имя пользователя
        if 'username' in globals() and hasattr(username, 'text_value'):
            current_username = username.text_value.get()
            if current_username and current_username != "Введите никнейм":
                session_data['username'] = current_username

        # Сохраняем выбранную версию
        if 'version_selector' in globals() and hasattr(version_selector, 'current_value'):
            current_version = version_selector.current_value.get()
            if current_version:
                session_data['version'] = current_version

        # Сохраняем настройки памяти
        session_data['memory'] = CONFIG.get('jvm_memory', '4G')

        # Сохраняем настройки полноэкранного режима
        if 'enabled' in globals():
            session_data['fullscreen'] = bool(enabled.get())

        # Сохраняем настройки музыки
        if 'enabled1' in globals():
            session_data['music'] = bool(enabled1.get())

        # Добавляем временную метку
        session_data['launcher_version'] = CURRENT_VERSION

        # Сохраняем только если есть что сохранять
        if session_data:
            # Создаем папку если не существует
            os.makedirs(os.path.dirname(LAST_SESSION_FILE), exist_ok=True)

            with open(LAST_SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Настройки сохранены: {len(session_data)} параметров")
            return True
        else:
            print("⚠️ Нечего сохранять - сессия пустая")
            return False

    except Exception as e:
        print(f"❌ Ошибка сохранения настроек: {e}")
        return False


def apply_session_settings(session):
    """Применяет настройки сессии когда все элементы готовы"""
    if not session:
        return

    try:
        print("🔄 Восстанавливаем предыдущую сессию...")

        applied_count = 0

        # Восстанавливаем никнейм
        if 'username' in globals() and session.get('username'):
            username.text_value.set(session['username'])
            username.entry.configure(fg='#2b2b2b')
            print(f"👤 Восстановлен ник: {session['username']}")
            applied_count += 1

        # Восстанавливаем версию
        if 'version_selector' in globals() and session.get('version'):
            try:
                target_version = session['version']
                # Устанавливаем значение напрямую
                version_selector.current_value.set(target_version)
                version_selector.draw_selector()
                print(f"🎯 Восстановлена версия: {target_version}")
                applied_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка восстановления версии: {e}")

        # Восстанавливаем память
        if session.get('memory'):
            CONFIG['jvm_memory'] = session['memory']
            print(f"💾 Восстановлена память: {session['memory']}")
            applied_count += 1

        # Восстанавливаем полноэкранный режим
        if 'enabled' in globals() and session.get('fullscreen'):
            enabled.set(True)
            fullsc()
            print("🖥️ Восстановлен полноэкранный режим")
            applied_count += 1

        # Восстанавливаем музыку
        if 'enabled1' in globals() and session.get('music'):
            enabled1.set(True)
            mscon()
            print("🎵 Восстановлена музыка")
            applied_count += 1

        print(f"✅ Сессия восстановлена: {applied_count} параметров")

    except Exception as e:
        print(f"⚠️ Не удалось применить некоторые настройки: {e}")


def on_closing():
    """При закрытии окна"""
    print("💾 Сохраняем настройки...")
    save_last_session()

    # Останавливаем музыку
    try:
        mixer.music.stop()
    except:
        pass

    win.destroy()
    sys.exit(0)


# Вешаем обработчик закрытия
win.protocol("WM_DELETE_WINDOW", on_closing)


def load_session_on_start():
    """Загружает сессию после полной инициализации интерфейса"""
    try:
        session = load_last_session()
        if session:
            print(f"🔄 Восстанавливаем сессию от {session.get('timestamp', 'неизвестно')}")
            # Даем время на создание всех элементов интерфейса
            win.after(3000, lambda: apply_session_settings(session))
        else:
            print("🔰 Сессия не найдена, используем настройки по умолчанию")
    except Exception as e:
        print(f"❌ Ошибка загрузки сессии: {e}")

# Запускаем загрузку сессии после полной инициализации
win.after(3500, load_session_on_start)

win.after(200, check_for_updates)  # NEW

# Вызываем перед созданием главного окна
setup_environment()

# Модифицируем блок инициализации звука:
mixer.init()
mixer.music.load(str(RESOURCE_DIR / "menu_song.mp3"))
mixer.music.set_volume(0.1)

# Модифицируем блок GUI элементов:
bag = tk.PhotoImage(file=str(RESOURCE_DIR / "logo.png"))
img = ttk.Label(win, image=bag)
img.place(x=0, y=-1)



# Функции для управления окном
def fullsc(): win.attributes("-fullscreen", True)
def outscrn(): win.attributes("-fullscreen", False)


def open_game_folder():
    minecraft_dir = CONFIG['minecraft_dir']
    try:
        if os.path.exists(minecraft_dir):
            if os.name == 'nt':  # Windows
                os.startfile(minecraft_dir)
            elif os.name == 'posix':  # Linux/MacOS
                subprocess.Popen(['xdg-open', minecraft_dir])
            print(f"Открыта папка с игрой: {minecraft_dir}")
        else:
            messagebox.showwarning("Папка не найдена", f"Папка {minecraft_dir} не существует!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")


import os
import zipfile
import shutil
import datetime
import tkinter as tk
from tkinter import ttk, messagebox


def create_backup(folder_path, backup_type):
    """Создает zip-бэкап указанной папки"""
    try:
        print(f"🔄 Создаем бэкап {backup_type} из: {folder_path}")

        # Проверяем существует ли папка
        if not os.path.exists(folder_path):
            print(f"❌ Папка {folder_path} не существует")
            return None

        # Проверяем есть ли файлы в папке
        files_in_folder = []
        if os.path.exists(folder_path):
            for root, dirs, files in os.walk(folder_path):
                files_in_folder.extend(files)

        print(f"📁 Файлов в папке {backup_type}: {len(files_in_folder)}")
        if files_in_folder:
            print(f"📄 Примеры файлов: {files_in_folder[:5]}")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(CONFIG['minecraft_dir'], 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        backup_filename = f"{backup_type}_backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)

        print(f"📦 Создаем архив: {backup_path}")

        created_files = []
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.exists(folder_path) and files_in_folder:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            arcname = os.path.relpath(file_path, folder_path)
                            zipf.write(file_path, arcname)
                            created_files.append(arcname)
                            if len(created_files) <= 10:
                                print(f"   + Добавлен файл: {arcname}")
            else:
                print(f"⚠️ Папка {folder_path} пустая или не существует")

        print(f"✅ Создан бэкап {backup_type}: {backup_path}")
        print(f"📊 Добавлено файлов: {len(created_files)}")

        # Проверяем что архив создан
        if os.path.exists(backup_path):
            file_size = os.path.getsize(backup_path) / 1024
            print(f"📏 Размер архива: {file_size:.1f} КБ")
        else:
            print("❌ ОШИБКА: Архив не создан!")

        return backup_path

    except Exception as e:
        print(f"❌ Ошибка создания бэкапа {backup_type}: {str(e)}")
        return None


def get_available_backups():
    """Возвращает список всех доступных бэкапов"""
    backup_dir = os.path.join(CONFIG['minecraft_dir'], 'backups')
    print(f"🔍 Поиск бэкапов в: {backup_dir}")

    if not os.path.exists(backup_dir):
        print("❌ Папка бэкапов не существует")
        return []

    # Получаем все файлы бэкапов
    backup_files = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip'):
            file_path = os.path.join(backup_dir, filename)
            time_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path))

            # ПРАВИЛЬНО определяем тип бэкапа - используем startswith вместо in
            if filename.startswith('mods_backup_'):
                timestamp = filename.replace('mods_backup_', '').replace('.zip', '')
                backup_type = 'mods'
            elif filename.startswith('versions_backup_'):
                timestamp = filename.replace('versions_backup_', '').replace('.zip', '')
                backup_type = 'versions'
            elif filename.startswith('world_backup_'):
                timestamp = filename.replace('world_backup_', '').replace('.zip', '')
                backup_type = 'world'
            else:
                continue  # Пропускаем файлы с другими именами

            backup_files.append({
                'filename': filename,
                'path': file_path,
                'type': backup_type,
                'date': time_created.strftime("%d.%m.%Y %H:%M"),
                'timestamp': timestamp
            })

    print(f"📁 Найдено файлов бэкапов: {len(backup_files)}")
    for bf in backup_files:
        print(f"   - {bf['filename']} (тип: {bf['type']})")

    if not backup_files:
        return []

    # Группируем по timestamp
    backup_groups = {}
    for backup in backup_files:
        ts = backup['timestamp']
        if ts not in backup_groups:
            backup_groups[ts] = {
                'timestamp': ts,
                'date': backup['date']
            }

        # Добавляем моды, версии или мир в группу
        backup_groups[ts][backup['type']] = backup

    # Преобразуем в список и сортируем
    result = list(backup_groups.values())
    result.sort(key=lambda x: x['timestamp'], reverse=True)

    print(f"🎯 Сформировано групп бэкапов: {len(result)}")
    for item in result:
        components = []
        if 'mods' in item:
            components.append('Моды')
        if 'versions' in item:
            components.append('Версии')
        if 'world' in item:
            components.append('Мир')
        print(f"   - {item['date']}: {', '.join(components)}")

    return result


def restore_single_component(backup_path, target_dir, component_name):
    """Восстанавливает один компонент с улучшенной обработкой ошибок"""
    try:
        print(f"📦 Восстанавливаем {component_name} из: {backup_path}")
        print(f"📁 В папку: {target_dir}")

        # Проверяем существует ли бэкап
        if not os.path.exists(backup_path):
            print(f"❌ Бэкап {component_name} не существует: {backup_path}")
            return False

        # Проверяем архив
        try:
            with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                print(f"📄 Файлов в архиве {component_name}: {len(file_list)}")

                if not file_list:
                    print(f"⚠️ Архив {component_name} пустой")
                    return False

                if file_list:
                    print(f"📄 Примеры файлов: {file_list[:5]}")
        except Exception as e:
            print(f"❌ Ошибка чтения архива {component_name}: {e}")
            return False

        # Удаляем старую папку
        if os.path.exists(target_dir):
            print(f"🗑️ Удаляем старые {component_name}")
            shutil.rmtree(target_dir)

        # Создаем новую папку
        os.makedirs(target_dir, exist_ok=True)
        print(f"📁 Создана новая папка {component_name}: {target_dir}")

        # Распаковываем
        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
            extracted_files = zip_ref.namelist()
            print(f"✅ Распаковано файлов {component_name}: {len(extracted_files)}")

        # Проверяем результат
        restored_files = []
        for root, dirs, files in os.walk(target_dir):
            restored_files.extend(files)

        print(f"📁 Файлов восстановлено в папке: {len(restored_files)}")
        if restored_files:
            print(f"📄 Примеры восстановленных файлов: {restored_files[:5]}")

        return True

    except Exception as e:
        print(f"❌ Ошибка восстановления {component_name}: {e}")
        return False


def restore_from_backup(backup_data):
    """Восстанавливает моды, версии и мир из выбранного бэкапа"""
    try:
        print(f"🔄 Начинаем восстановление...")
        print(f"📦 Данные для восстановления: {list(backup_data.keys())}")

        # Проверка что бэкапные файлы существуют
        for backup_type, backup_info in backup_data.items():
            if backup_type in ['mods', 'versions', 'world']:
                if not os.path.exists(backup_info['path']):
                    print(f"❌ Бэкап {backup_type} не существует: {backup_info['path']}")
                    messagebox.showerror("Ошибка", f"Бэкап {backup_type} не найден!")
                    return

        minecraft_dir = CONFIG['minecraft_dir']
        success_messages = []
        errors = []

        # Восстанавливаем моды если есть
        if 'mods' in backup_data:
            mods_backup = backup_data['mods']['path']
            mods_dir = os.path.join(minecraft_dir, 'mods')

            if restore_single_component(mods_backup, mods_dir, "моды"):
                success_messages.append("✅ Моды восстановлены")
            else:
                errors.append("❌ Ошибка восстановления модов")

        # Восстанавливаем версии если есть
        if 'versions' in backup_data:
            versions_backup = backup_data['versions']['path']
            versions_dir = os.path.join(minecraft_dir, 'versions')

            if restore_single_component(versions_backup, versions_dir, "версии"):
                success_messages.append("✅ Версии восстановлены")
            else:
                errors.append("❌ Ошибка восстановления версий")

        # Восстанавливаем мир если есть
        if 'world' in backup_data:
            world_backup = backup_data['world']['path']
            world_dir = os.path.join(minecraft_dir, 'world')

            if restore_single_component(world_backup, world_dir, "мир"):
                success_messages.append("✅ Мир восстановлен")
            else:
                errors.append("❌ Ошибка восстановления мира")

        # Формируем итоговое сообщение
        if success_messages:
            message = "🔄 Восстановление завершено!\n\n" + "\n".join(success_messages)
            if errors:
                message += "\n\n⚠️ Были ошибки:\n" + "\n".join(errors)
            messagebox.showinfo("Успех", message)
        elif errors:
            messagebox.showerror("Ошибка", "Не удалось восстановить данные:\n" + "\n".join(errors))
        else:
            messagebox.showwarning("Внимание", "Нечего восстанавливать")

    except Exception as e:
        print(f"❌ Общая ошибка восстановления: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось восстановить: {str(e)}")



def choose_backup_to_restore():
    """Показывает диалог выбора бэкапа для восстановления"""
    print("🎯 Запуск выбора бэкапа...")
    backups = get_available_backups()

    if not backups:
        print("❌ Нет бэкапов для показа")
        messagebox.showinfo("Восстановление", "Нет доступных бэкапов для восстановления")
        return

    # Создаем окно выбора
    backup_window = tk.Toplevel(win)
    backup_window.title("Выбор бэкапа для восстановления")
    backup_window.geometry("600x400")
    backup_window.transient(win)
    backup_window.grab_set()

    # Заголовок
    ttk.Label(backup_window, text="Выберите бэкап для восстановления:",
              font=('Comfortaa', 12, 'bold')).pack(pady=10)

    # Фрейм для списка
    frame = ttk.Frame(backup_window)
    frame.pack(fill='both', expand=True, padx=20, pady=10)

    # Создаем Treeview
    columns = ('date', 'components')
    tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)

    # Настраиваем колонки
    tree.heading('date', text='📅 Дата создания')
    tree.heading('components', text='🔄 Компоненты')

    tree.column('date', width=200)
    tree.column('components', width=350)

    # Добавляем данные
    for backup in backups:
        components = []
        if 'mods' in backup:
            components.append("Моды")
        if 'versions' in backup:
            components.append("Версии")
        if 'world' in backup:
            components.append("Мир")

        display_components = ' + '.join(components) if components else "Только частичный бэкап"
        tree.insert('', 'end', values=(backup['date'], display_components),
                    tags=(backup['timestamp'],))

    # Скроллбар
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Фрейм для кнопок
    button_frame = ttk.Frame(backup_window)
    button_frame.pack(pady=10)

    def on_restore():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Пожалуйста, выберите бэкап для восстановления")
            return

        selected_timestamp = tree.item(selection[0])['tags'][0]
        selected_backup = next((b for b in backups if b['timestamp'] == selected_timestamp), None)

        if selected_backup:
            # Подтверждение восстановления
            components = []
            if 'mods' in selected_backup:
                components.append("Моды")
            if 'versions' in selected_backup:
                components.append("Версии")
            if 'world' in selected_backup:
                components.append("Мир")

            result = messagebox.askyesno(
                "Подтверждение восстановления",
                f"Вы уверены, что хотите восстановить игру из бэкапа от {selected_backup['date']}?\n\n"
                f"Будет восстановлено: {', '.join(components) if components else 'частичные данные'}\n\n"
                f"Текущие данные будут заменены."
            )

            if result:
                backup_window.destroy()
                restore_from_backup(selected_backup)

    def on_cancel():
        backup_window.destroy()

    # Кнопки
    ttk.Button(button_frame, text="🔄 Восстановить",
               command=on_restore, style="Accent.TButton").pack(side='left', padx=5)
    ttk.Button(button_frame, text="❌ Отмена",
               command=on_cancel).pack(side='left', padx=5)


def create_manual_backup():
    """Создает бэкап вручную по кнопке с автоматическими тестовыми файлами"""
    print("💾 Запуск создания бэкапа...")
    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')
    versions_dir = os.path.join(minecraft_dir, 'versions')
    world_dir = os.path.join(minecraft_dir, 'world')

    backups_created = []

    # Создаем папки если их нет
    os.makedirs(mods_dir, exist_ok=True)
    os.makedirs(versions_dir, exist_ok=True)
    os.makedirs(world_dir, exist_ok=True)

    # Бэкап модов (с тестовым файлом если папка пустая)
    print("📦 Создаем бэкап модов...")
    if os.path.exists(mods_dir):
        # Если папка модов пустая, создаем тестовый файл
        if not os.listdir(mods_dir):
            test_mod = os.path.join(mods_dir, 'auto_created_mod.jar')
            with open(test_mod, 'w', encoding='utf-8') as f:
                f.write("# Автоматически созданный мод для бэкапа")
            print(f"✅ Создан тестовый файл мода: {test_mod}")

        backup_path = create_backup(mods_dir, "mods")
        if backup_path:
            backups_created.append(backup_path)
            print(f"✅ Создан бэкап модов: {os.path.basename(backup_path)}")
    else:
        print("❌ Папка модов не существует")

    # Бэкап версий (с тестовым файлом если папка пустая)
    print("📦 Создаем бэкап версий...")
    if os.path.exists(versions_dir):
        # Если папка версий пустая, создаем тестовый файл
        if not os.listdir(versions_dir):
            test_version = os.path.join(versions_dir, 'version_info.txt')
            with open(test_version, 'w', encoding='utf-8') as f:
                f.write("Автоматически созданная версия для бэкапа")
            print(f"✅ Создан тестовый файл версии: {test_version}")

        backup_path = create_backup(versions_dir, "versions")
        if backup_path:
            backups_created.append(backup_path)
            print(f"✅ Создан бэкап версий: {os.path.basename(backup_path)}")
    else:
        print("❌ Папка версий не существует")

    # Бэкап мира (с тестовым файлом если папка пустая)
    print("📦 Создаем бэкап мира...")
    if os.path.exists(world_dir):
        # Если папка мира пустая, создаем тестовый файл
        if not os.listdir(world_dir):
            test_world = os.path.join(world_dir, 'level.dat')
            with open(test_world, 'w', encoding='utf-8') as f:
                f.write("# Автоматически созданный мир для бэкапа")
            print(f"✅ Создан тестовый файл мира: {test_world}")

        backup_path = create_backup(world_dir, "world")
        if backup_path:
            backups_created.append(backup_path)
            print(f"✅ Создан бэкап мира: {os.path.basename(backup_path)}")
    else:
        print("❌ Папка мира не существует")

    # Показываем результат
    if backups_created:
        backup_info = "Созданы бэкапы:\n" + "\n".join([f"• {os.path.basename(b)}" for b in backups_created])
        messagebox.showinfo("Бэкапы созданы", backup_info)
    else:
        messagebox.showinfo("Бэкапы", "Не удалось создать бэкапы (папки не найдены)")


def show_backup_info():
    """Показывает информацию о бэкапах"""
    backup_dir = os.path.join(CONFIG['minecraft_dir'], 'backups')
    if not os.path.exists(backup_dir):
        messagebox.showinfo("Бэкапы", "Бэкапы не создавались")
        return

    backups = []
    total_size = 0
    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip'):
            file_path = os.path.join(backup_dir, filename)
            size = os.path.getsize(file_path) / (1024 * 1024)  # Размер в МБ
            total_size += size
            time_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path))

            # Определяем тип бэкапа
            if filename.startswith('mods_backup_'):
                backup_type = 'Моды'
            elif filename.startswith('versions_backup_'):
                backup_type = 'Версии'
            elif filename.startswith('world_backup_'):
                backup_type = 'Мир'
            else:
                backup_type = 'Другой'

            backups.append((filename, f"{size:.1f} МБ", time_created.strftime("%d.%m.%Y %H:%M"), backup_type))

    if not backups:
        messagebox.showinfo("Бэкапы", "Бэкапы не найдены")
        return

    backups.sort(key=lambda x: x[2], reverse=True)  # Сортируем по дате (новые сверху)

    info_text = f"Созданные бэкапы (всего: {len(backups)}, общий размер: {total_size:.1f} МБ):\n\n"
    for backup in backups:
        info_text += f"• {backup[0]}\n  Тип: {backup[3]}, Размер: {backup[1]}, Создан: {backup[2]}\n\n"

    messagebox.showinfo("Информация о бэкапах", info_text)


def delete_all_backups():
    """Удаляет все бэкапы (только по кнопке!)"""
    backup_dir = os.path.join(CONFIG['minecraft_dir'], 'backups')
    if not os.path.exists(backup_dir):
        messagebox.showinfo("Бэкапы", "Папка бэкапов не существует")
        return

    # Подсчитываем количество бэкапов
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
    if not backup_files:
        messagebox.showinfo("Бэкапы", "Бэкапов не найдено")
        return

    # Подтверждение удаления
    result = messagebox.askyesno(
        "Удаление бэкапов",
        f"Вы уверены, что хотите удалить ВСЕ бэкапы?\n\n"
        f"Будет удалено: {len(backup_files)} файлов\n"
        f"Это действие нельзя отменить!"
    )

    if not result:
        return

    try:
        # Удаляем все ZIP файлы в папке бэкапов
        deleted_count = 0
        for filename in backup_files:
            file_path = os.path.join(backup_dir, filename)
            os.remove(file_path)
            deleted_count += 1
            print(f"Удален бэкап: {filename}")

        # Если папка пустая, удаляем её
        if not os.listdir(backup_dir):
            os.rmdir(backup_dir)
            print("Удалена пустая папка бэкапов")

        messagebox.showinfo("Бэкапы", f"Удалено {deleted_count} бэкапов")
        print(f"Удалено бэкапов: {deleted_count}")

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить бэкапы: {str(e)}")


# Добавляем кнопки в интерфейс (пример)
def setup_backup_buttons(parent_frame):
    """Добавляет кнопки управления бэкапами в интерфейс"""
    backup_frame = ttk.LabelFrame(parent_frame, text="🔄 Управление бэкапами", padding=10)
    backup_frame.pack(fill='x', padx=10, pady=5)

    # Кнопки в ряд
    button_row1 = ttk.Frame(backup_frame)
    button_row1.pack(fill='x', pady=5)

    ttk.Button(button_row1, text="💾 Создать бэкап",
               command=create_manual_backup, width=15).pack(side='left', padx=5)
    ttk.Button(button_row1, text="🔄 Восстановить последний",

               command=choose_backup_to_restore, width=15).pack(side='left', padx=5)

    # Второй ряд кнопок
    button_row2 = ttk.Frame(backup_frame)
    button_row2.pack(fill='x', pady=5)

    ttk.Button(button_row2, text="📊 Информация о бэкапах",
               command=show_backup_info, width=20).pack(side='left', padx=5)
    ttk.Button(button_row2, text="🗑️ Удалить все бэкапы",
               command=delete_all_backups, width=18).pack(side='left', padx=5)

def fig1():
    """Очистка игры с созданием бэкапов"""
    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')
    versions_dir = os.path.join(minecraft_dir, 'versions')
    world_dir = os.path.join(minecraft_dir, 'world')

    # Создаем бэкапы перед удалением
    backups_created = []

    # Бэкап модов (только если папка существует и не пустая)
    if os.path.exists(mods_dir) and os.listdir(mods_dir):
        backup_path_mods = create_backup(mods_dir, "mods")
        if backup_path_mods:
            backups_created.append(backup_path_mods)

    # Бэкап версий (только если папка существует и не пустая)
    if os.path.exists(versions_dir) and os.listdir(versions_dir):
        backup_path_versions = create_backup(versions_dir, "versions")
        if backup_path_versions:
            backups_created.append(backup_path_versions)

    # Бэкап мира (только если папка существует и не пустая)
    if os.path.exists(world_dir) and os.listdir(world_dir):
        backup_path_world = create_backup(world_dir, "world")
        if backup_path_world:
            backups_created.append(backup_path_world)

    # Удаляем папки если они существуют (кроме мира)
    items_to_remove = [mods_dir, versions_dir]  # Мир не удаляем при очистке!
    for item in items_to_remove:
        if os.path.exists(item):
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"Удалено: {item}")
                else:
                    os.remove(item)
                    print(f"Удалено: {item}")
            except Exception as e:
                print(f"Ошибка удаления {item}: {str(e)}")

    # Показываем информацию о созданных бэкапах
    if backups_created:
        backup_info = "Созданы бэкапы:\n" + "\n".join([f"• {os.path.basename(b)}" for b in backups_created])
        messagebox.showinfo("Бэкапы созданы", f"Игра очищена!\n\n{backup_info}")
    else:
        messagebox.showinfo("Очистка", "Папки mods и versions очищены (бэкапы не создавались - папки были пустые)")


def repair_game_with_options():
    """Упрощенная версия починки - только то, что работает"""
    choice_window = tk.Toplevel(win)
    choice_window.title("Починить игру")
    choice_window.geometry("400x200")

    ttk.Label(choice_window, text="Выберите действие:",
              font=('Comfortaa', 14)).pack(pady=20)

    def simple_repair():
        choice_window.destroy()
        auto_repair_game_files()  # Наша новая простая функция

    def cleanup_only():
        choice_window.destroy()
        fig1()  # Старая функция очистки

    ttk.Button(choice_window, text="🔧 Проверить и починить файлы",
               command=simple_repair, width=25).pack(pady=10)

    ttk.Button(choice_window, text="🧹 Очистить игру (удалить моды и версии)",
               command=cleanup_only, width=25).pack(pady=10)

    ttk.Button(choice_window, text="❌ Отмена",
               command=choice_window.destroy).pack(pady=10)


def auto_repair_game_files():
    """Починка файлов игры с прогресс-баром"""
    try:
        minecraft_dir = CONFIG['minecraft_dir']

        # 1. Создаем папки если их нет
        for folder in ['mods', 'versions', 'config', 'shaderpacks']:
            path = os.path.join(minecraft_dir, folder)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                print(f"✅ Создана папка: {folder}")

        # 2. Проверяем и скачиваем моды ТОЛЬКО для YamalPixel с прогресс-баром
        if version_selector.get() == "YamalPixel":
            repair_missing_mods_with_progress()
        else:
            print(f"🚫 Версия {version_selector.get()} - моды не проверяются")

        # 3. Проверяем Fabric
        if not check_fabric_installed():
            print("🔧 Устанавливаем Fabric...")
            install_fabric_silent()

        messagebox.showinfo("✅ Готово", "Проверка и починка завершены!")
        return True

    except Exception as e:
        messagebox.showerror("❌ Ошибка", f"Не удалось починить игру: {e}")
        return False


def repair_missing_mods_with_progress():
    """Загрузка отсутствующих модов с прогресс-баром"""
    # Создаем окно прогресса (аналогично checker1)
    progress_window = tk.Toplevel(win)
    progress_window.title("Починка модов")
    progress_window.geometry("500x200")
    progress_window.resizable(False, False)
    progress_window.transient(win)
    progress_window.grab_set()

    # Центрируем окно
    progress_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (500 // 2)
    y = (win.winfo_screenheight() // 2) - (200 // 2)
    progress_window.geometry(f"500x200+{x}+{y}")

    # Элементы UI
    main_frame = ttk.Frame(progress_window, padding=20)
    main_frame.pack(fill='both', expand=True)

    title_label = ttk.Label(main_frame, text="🔧 Починка модов",
                            font=('Comfortaa', 14, 'bold'))
    title_label.pack(pady=(0, 15))

    total_progress_label = ttk.Label(main_frame, text="Общий прогресс: 0%")
    total_progress_label.pack()

    total_progress = ttk.Progressbar(main_frame, orient="horizontal",
                                     length=400, mode="determinate")
    total_progress.pack(pady=5)

    current_mod_label = ttk.Label(main_frame, text="Подготовка к загрузке...")
    current_mod_label.pack()

    status_label = ttk.Label(main_frame, text="Инициализация...",
                             font=('Comfortaa', 9), foreground='blue')
    status_label.pack(pady=10)

    def update_progress(current, total, mod_name="", status=""):
        """Обновляет прогресс в UI"""
        try:
            total_percent = (current * 100) // total if total > 0 else 0
            total_progress['value'] = total_percent
            total_progress_label.config(text=f"Общий прогресс: {total_percent}%")
            current_mod_label.config(text=f"Текущий мод: {mod_name}")
            if status:
                status_label.config(text=status)
            progress_window.update()
        except:
            pass

    def download_thread():
        """Поток загрузки модов"""
        try:
            mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
            base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'

            # Определяем какие моды нужно скачать
            mods_to_download = []
            for mod in CONFIG['mods']:
                mod_path = os.path.join(mods_dir, mod['file'])
                if not os.path.exists(mod_path):
                    mods_to_download.append(mod)

            total_mods = len(mods_to_download)
            success_count = 0

            if total_mods == 0:
                win.after(0, lambda: progress_window.destroy())
                return

            win.after(0, lambda: update_progress(0, total_mods, "Подготовка..."))

            for i, mod in enumerate(mods_to_download):
                try:
                    win.after(0, lambda idx=i, m=mod: update_progress(
                        idx, total_mods, m['file'], "Получение ссылки..."
                    ))

                    # Получаем прямую ссылку
                    params = {'public_key': mod['url']}
                    response = requests.get(base_url, params=params, timeout=30)
                    response.raise_for_status()
                    download_url = response.json().get('href')

                    if not download_url:
                        continue

                    # Загружаем файл
                    mod_path = os.path.join(mods_dir, mod['file'])

                    with requests.get(download_url, stream=True, timeout=60) as dl_response:
                        dl_response.raise_for_status()

                        total_size = int(dl_response.headers.get('content-length', 0))
                        downloaded_size = 0

                        with open(mod_path, 'wb') as f:
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)

                                    # Обновляем прогресс
                                    win.after(0, lambda: update_progress(
                                        i, total_mods, mod['file'],
                                        f"Загружено: {downloaded_size / (1024 * 1024):.1f}MB"
                                    ))

                        if os.path.exists(mod_path) and os.path.getsize(mod_path) > 0:
                            success_count += 1
                            win.after(0, lambda: update_progress(
                                i + 1, total_mods, mod['file'], "✅ Успешно"
                            ))
                        else:
                            win.after(0, lambda: update_progress(
                                i + 1, total_mods, mod['file'], "❌ Ошибка"
                            ))

                except Exception as e:
                    win.after(0, lambda: update_progress(
                        i + 1, total_mods, mod['file'], f"❌ Ошибка: {str(e)[:30]}"
                    ))

            # Закрываем окно
            win.after(1000, lambda: progress_window.destroy())

        except Exception as e:
            win.after(0, lambda: progress_window.destroy())

    # Запускаем загрузку в отдельном потоке
    threading.Thread(target=download_thread, daemon=True).start()
def launch_without_mods():
    """Запуск игры полностью без модов"""
    result = messagebox.askyesno(
        "Запуск без модов",
        "Запустить игру БЕЗ ВСЕХ модов?\n\n"
        "Это поможет определить:\n"
        "• Проблема в модах или в игре\n"
        "• Конфликтующие моды\n\n"
        "После проверки можно включить моды обратно.",
        icon='question'
    )

    if not result:
        return

    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')
    disabled_dir = os.path.join(minecraft_dir, 'mods_disabled_temp')

    # Создаем бэкап модов
    if os.path.exists(mods_dir) and os.listdir(mods_dir):
        backup_path = create_backup(mods_dir, "mods_before_clean_launch")
        if backup_path:
            print(f"Создан бэкап модов: {backup_path}")

    # Перемещаем ВСЕ моды
    os.makedirs(disabled_dir, exist_ok=True)

    moved_count = 0
    if os.path.exists(mods_dir):
        for filename in os.listdir(mods_dir):
            if filename.endswith('.jar'):
                try:
                    shutil.move(
                        os.path.join(mods_dir, filename),
                        os.path.join(disabled_dir, filename)
                    )
                    moved_count += 1
                    print(f"Отключен мод: {filename}")
                except Exception as e:
                    print(f"Ошибка отключения {filename}: {e}")

    if moved_count > 0:
        messagebox.showinfo(
            "Моды отключены",
            f"Отключено {moved_count} модов.\n\n"
            f"Теперь запустите игру через основную кнопку 'Войти в игру'.\n\n"
            f"Моды находятся в: {disabled_dir}"
        )
    else:
        messagebox.showinfo("Информация", "Модов для отключения не найдено")

def complete_reinstall():
    """Полная переустановка игры с очисткой всех файлов"""
    result = messagebox.askyesno(
        "Полная переустановка",
        "⚠️ ВНИМАНИЕ! Это удалит ВСЕ файлы игры и настроек.\n\n"
        "Будет выполнено:\n"
        "• Удаление папки YamalPixel\n"
        "• Удаление всех модов и конфигов\n"
        "• Удаление миров и сохранений\n"
        "• Создание чистых бэкапов\n\n"
        "Продолжить?",
        icon='warning'
    )

    if not result:
        return

    minecraft_dir = CONFIG['minecraft_dir']

    # Создаем полные бэкапы
    backups_created = []

    # Бэкап модов
    mods_dir = os.path.join(minecraft_dir, 'mods')
    if os.path.exists(mods_dir) and os.listdir(mods_dir):
        backup_path = create_backup(mods_dir, "mods_full_backup")
        if backup_path:
            backups_created.append(f"Моды: {os.path.basename(backup_path)}")

    # Бэкап мира
    world_dir = os.path.join(minecraft_dir, 'world')
    if os.path.exists(world_dir) and os.listdir(world_dir):
        backup_path = create_backup(world_dir, "world_full_backup")
        if backup_path:
            backups_created.append(f"Мир: {os.path.basename(backup_path)}")

    # Бэкап конфигов
    config_dir = os.path.join(minecraft_dir, 'config')
    if os.path.exists(config_dir) and os.listdir(config_dir):
        backup_path = create_backup(config_dir, "config_full_backup")
        if backup_path:
            backups_created.append(f"Настройки: {os.path.basename(backup_path)}")

    # Полностью удаляем папку Minecraft
    progress_window = tk.Toplevel(win)
    progress_window.title("Переустановка")
    progress_window.geometry("400x150")

    progress_label = ttk.Label(progress_window, text="Удаление старых файлов...")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="indeterminate")
    progress.pack(pady=10)
    progress.start()

    def reinstall_thread():
        try:
            # Полностью удаляем папку Minecraft
            if os.path.exists(minecraft_dir):
                shutil.rmtree(minecraft_dir)
                print(f"Полностью удалена папка: {minecraft_dir}")

            # Создаем чистую структуру
            os.makedirs(minecraft_dir, exist_ok=True)
            os.makedirs(os.path.join(minecraft_dir, 'mods'), exist_ok=True)
            os.makedirs(os.path.join(minecraft_dir, 'config'), exist_ok=True)
            os.makedirs(os.path.join(minecraft_dir, 'shaderpacks'), exist_ok=True)

            progress_label.config(text="Установка Minecraft...")

            # Чистая установка Minecraft
            minecraft_launcher_lib.install.install_minecraft_version(
                versionid=CONFIG['version'],
                minecraft_directory=minecraft_dir
            )

            progress_label.config(text="Установка Fabric...")

            # Чистая установка Fabric
            minecraft_launcher_lib.fabric.install_fabric(
                minecraft_version=CONFIG['version'],
                loader_version=CONFIG['fabric_loader'],
                minecraft_directory=minecraft_dir
            )

            progress_label.config(text="Установка модов...")

            # Скачиваем только ОСНОВНЫЕ моды (без проблемных)
            base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'

            essential_mods = [
        {'url': 'https://disk.yandex.ru/d/aJHjc2LrzS8ndA', 'file': 'XaerosWorldMap_1.39.12_Fabric_1.20.jar'},
        {'url': 'https://disk.yandex.ru/d/UzM5BWOXB9S7OA', 'file': 'AdvancedReborn-1.20.1-1.2.9.jar'},
        {'url': 'https://disk.yandex.ru/d/B48FGIIitm-olA', 'file': 'ae2-emi-crafting-1.3.1.jar'},
        {'url': 'https://disk.yandex.ru/d/YXPRt1scCMJ8kQ', 'file': 'antixray-fabric-1.4.6+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/ukmqzaHQaTP03g', 'file': 'appliedenergistics2-fabric-15.4.9.jar'},
        {'url': 'https://disk.yandex.ru/d/aH-BHO05_WeuLw', 'file': 'architectury-9.2.14-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/fo5V3PpaLtZ-gw', 'file': 'areas-1.20.1-6.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Tif04Xw7_kd8rQ', 'file': 'cardinal-components-api-5.2.3.jar'},
        {'url': 'https://disk.yandex.ru/d/k5xux5BX_T9-7g', 'file': 'choicetheorems-overhauled-village-friends-and-foes-add-on-1.1.jar'},
        {'url': 'https://disk.yandex.ru/d/378xaPNzlblGFA', 'file': 'cloth-config-11.1.136-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/5AivLjfk6Wgbog', 'file': 'collective-1.20.1-8.12.jar'},
        {'url': 'https://disk.yandex.ru/d/nSspzPB5G5ReWA', 'file': 'crafting_enchanted_golden_apple-1.0.0-fabric-1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Ox5-1T4a9qkXHg', 'file': 'ctov-beautify-compat-2.0.jar'},
        {'url': 'https://disk.yandex.ru/d/o2kPxeHul4byng', 'file': 'emi-1.1.22+1.20.1+fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/PNZi_54Tj4HP3Q', 'file': 'entityculling-fabric-1.9.1-mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/GNW5lwib5Xq9Eg', 'file': 'extra-mod-integrations-0.4.7+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/EHHAo7HSzH2mmg', 'file': 'fabric-api-0.92.6+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/IHBo3qyqAjR3fQ', 'file': 'fabric-language-kotlin-1.13.6+kotlin.2.2.20.jarr'},
        {'url': 'https://disk.yandex.ru/d/r8gwsUQF7Wy9BQ', 'file': 'fallingleaves-1.15.6+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/pddZ2W8za1yiSQ', 'file': 'indium-1.0.36+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/PghcNlFWKcgSeg', 'file': 'InventoryProfilesNext-fabric-1.20-1.10.19.jar'},
        {'url': 'https://disk.yandex.ru/d/AZHbvFGGX_JAKQ', 'file': 'iris-1.7.6+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/wwCGHqSxly5pXg', 'file': 'ironchests-5.0.2-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/OrlYw3O3rnSN1A', 'file': 'lambdynamiclights-4.4.0+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Sr4rPWBdFjEZfA', 'file': 'libIPN-fabric-1.20-4.0.2.jar'},
        {'url': 'https://disk.yandex.ru/d/7G3BPLxK1Dul1g', 'file': 'lithium-fabric-mc1.20.1-0.11.3.jar'},
        {'url': 'https://disk.yandex.ru/d/yE26wprToTM9hg', 'file': 'mavapi-1.1.4-mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Po8eTPEwzDAOpg', 'file': 'mavm-1.2.6-mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/8luIo8Ygz83BEg', 'file': 'mcpitanlib-3.3.9-1.20.1-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/EsACr5Ex3R9Zdg', 'file': 'modmenu-badges-lib-2023.6.1.jar'},
        {'url': 'https://disk.yandex.ru/d/6CF52_F3QbnCzQ', 'file': 'noindium-1.1.0+1.20.jar'},
        {'url': 'https://disk.yandex.ru/d/B10LX8LVEZg0DQ', 'file': 'Patchouli-1.20.1-84.1-FABRIC.jar'},
        {'url': 'https://disk.yandex.ru/d/fCkZvVrEqlU3Rg', 'file': 'RebornCore-5.8.3.jar'},
        {'url': 'https://disk.yandex.ru/d/_CgYmn4OYeGnBQ', 'file': 'servercore-fabric-1.5.2+1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/uI7zlr5Yg-7skQ', 'file': 'sodium-extra-0.5.9+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/Mft3dmbdbHjhHA', 'file': 'sodium-fabric-0.5.13+mc1.20.1.jar'},
        {'url': 'https://disk.yandex.ru/d/dncEQy1PhTcgrw', 'file': 'TechReborn-5.8.3.jar'},
        {'url': 'https://disk.yandex.ru/d/_c-mQTKC4UB1cw', 'file': 'Terralith_1.20.x_v2.5.4.jar'},
        {'url': 'https://disk.yandex.ru/d/trH1NQ3Hw2QjXQ', 'file': 'Xaeros_Minimap_25.2.10_Fabric_1.20.jar'},
        {'url': 'https://disk.yandex.ru/d/7ebHrjGobc89Og', 'file': 'travelersbackpack-fabric-1.20.1-9.1.41.jar'}
            ]

            for mod in essential_mods:
                try:
                    mods_dir_path = os.path.join(minecraft_dir, 'mods')
                    mod_path = os.path.join(mods_dir_path, mod['file'])

                    params = {'public_key': mod['url']}
                    response = requests.get(base_url, params=params)
                    response.raise_for_status()
                    download_url = response.json().get('href')

                    if download_url:
                        with open(mod_path, 'wb') as f:
                            dl_response = requests.get(download_url, stream=True)
                            dl_response.raise_for_status()
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        # Распаковываем ZIP если нужно
                        if mod['file'].endswith('.zip'):
                            try:
                                with zipfile.ZipFile(mod_path, 'r') as zip_file:
                                    zip_file.extractall(path=mods_dir_path)
                                print(f"Распакован: {mod['file']}")
                            except Exception as e:
                                print(f"Ошибка распаковки {mod['file']}: {e}")

                except Exception as e:
                    print(f"Ошибка загрузки мода {mod['file']}: {e}")

            progress_window.destroy()

            # Показываем отчет
            report = "✅ Переустановка завершена!\n\n"

            if backups_created:
                report += "📦 Созданы бэкапы:\n" + "\n".join([f"• {b}" for b in backups_created]) + "\n\n"

            report += "🔄 Установлено:\n"
            report += "• Чистая версия Minecraft 1.20.1\n"
            report += "• Fabric Loader 0.16.10\n"
            report += "• Основные моды (без проблемных)\n\n"
            report += "🎯 Теперь попробуйте запустить игру!"

            messagebox.showinfo("Переустановка завершена", report)

        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Ошибка", f"Ошибка переустановки: {str(e)}")

    threading.Thread(target=reinstall_thread, daemon=True).start()


def create_diagnostic_panel():
    """Создает панель диагностики с темным стилем"""
    diag_window = tk.Toplevel(win)
    diag_window.title("Диагностика проблем")
    diag_window.geometry("700x550")
    diag_window.configure(bg='#2b2b2b')  # Темный фон окна

    # Заголовок
    header_frame = ttk.Frame(diag_window)
    header_frame.pack(fill='x', padx=20, pady=15)

    ttk.Label(header_frame,
              text="Диагностика проблем",
              font=('Comfortaa', 16, 'bold'),
              foreground='white',
              background='#2b2b2b').pack()

    ttk.Label(header_frame,
              text="Автоматическая проверка и решение проблем",
              font=('Comfortaa', 10),
              foreground='#cccccc',
              background='#2b2b2b').pack(pady=(5, 0))

    # Прогресс-бар
    progress_frame = ttk.Frame(diag_window)
    progress_frame.pack(fill='x', padx=20, pady=10)

    progress_label = ttk.Label(progress_frame,
                               text="Проводим диагностику...",
                               foreground='white',
                               background='#2b2b2b')
    progress_label.pack()

    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal",
                                   length=650, mode="indeterminate")
    progress_bar.pack(pady=5)
    progress_bar.start()

    # Окно результатов - ЧЕРНОЕ с цветным текстом
    results_frame = ttk.Frame(diag_window)
    results_frame.pack(fill='both', expand=True, padx=20, pady=10)

    results_text = tk.Text(results_frame, height=12, wrap='word',
                           font=('Consolas', 9),
                           bg='#1a1a1a',  # Черный фон
                           fg='#00ff88',  # Зеленый текст по умолчанию
                           relief='solid', borderwidth=1,
                           padx=10, pady=10)

    scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=results_text.yview)
    results_text.configure(yscrollcommand=scrollbar.set)

    results_text.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Статус
    status_frame = ttk.Frame(diag_window)
    status_frame.pack(fill='x', padx=20, pady=5)

    status_label = ttk.Label(status_frame,
                             text="Начинаем проверку...",
                             foreground='#ffaa00',
                             background='#2b2b2b')
    status_label.pack()

    # Кнопки
    button_frame = ttk.Frame(diag_window)
    button_frame.pack(fill='x', padx=20, pady=15)

    # Первый ряд
    row1 = ttk.Frame(button_frame)
    row1.pack(fill='x', pady=5)

    ttk.Button(row1, text="Быстрая починка",
               command=lambda: auto_repair_game_files(),
               width=18).pack(side='left', padx=5)

    ttk.Button(row1, text="Запуск без модов",
               command=launch_without_mods,
               width=18).pack(side='left', padx=5)

    # Второй ряд
    row2 = ttk.Frame(button_frame)
    row2.pack(fill='x', pady=5)

    ttk.Button(row2, text="Полная переустановка",
               command=complete_reinstall,
               width=18).pack(side='left', padx=5)

    ttk.Button(row2, text="Создать отчет",
               command=lambda: create_debug_report(results_text),
               width=15).pack(side='left', padx=5)

    ttk.Button(row2, text="Закрыть",
               command=diag_window.destroy,
               width=12).pack(side='right', padx=5)

    # Функции диагностики с цветным текстом
    def add_result(text, color='#00ff88'):  # Зеленый по умолчанию
        results_text.insert('end', f"{text}\n", color)
        results_text.see('end')
        diag_window.update()

    def run_diagnostic():
        try:
            problems_found = []
            minecraft_dir = CONFIG['minecraft_dir']

            # Проверка структуры - зеленый
            for folder in ['mods', 'versions', 'config']:
                path = os.path.join(minecraft_dir, folder)
                if os.path.exists(path):
                    add_result(f"✅ Папка {folder} найдена", '#00ff88')
                else:
                    problems_found.append(f"Отсутствует папка {folder}")
                    add_result(f"❌ Папка {folder} не найдена", '#ff4444')  # Красный для ошибок

            # Проверка модов - голубой
            mods_dir = os.path.join(minecraft_dir, 'mods')
            if os.path.exists(mods_dir):
                mod_files = [f for f in os.listdir(mods_dir) if f.endswith('.jar')]
                add_result(f"📦 Найдено модов: {len(mod_files)}", '#00ccff')  # Голубой

                if len(mod_files) == 0:
                    problems_found.append("Папка модов пустая")
                    add_result("⚠️ Папка модов пуста", '#ffaa00')  # Желтый для предупреждений

            # Проверка ресурсов - зеленый/желтый
            memory = psutil.virtual_memory()
            if memory.available < 3 * 1024 * 1024 * 1024:
                problems_found.append("Мало оперативной памяти")
                add_result(f"⚠️ Мало ОЗУ: {memory.available // 1024 // 1024}MB свободно", '#ffaa00')
            else:
                add_result(f"✅ ОЗУ: {memory.available // 1024 // 1024}MB свободно", '#00ff88')

            disk = psutil.disk_usage(minecraft_dir)
            if disk.free < 2 * 1024 * 1024 * 1024:
                problems_found.append("Мало места на диске")
                add_result(f"⚠️ Мало места: {disk.free // 1024 // 1024}MB свободно", '#ffaa00')
            else:
                add_result(f"✅ Диск: {disk.free // 1024 // 1024}MB свободно", '#00ff88')

            # Java - зеленый/красный
            java_ok = check_java_version()
            if java_ok:
                add_result("✅ Java установлена и работает", '#00ff88')
            else:
                problems_found.append("Проблемы с Java")
                add_result("❌ Java не найдена", '#ff4444')

            # Финальный отчет
            progress_bar.stop()

            if problems_found:
                add_result(f"\n🚨 Найдено проблем: {len(problems_found)}", '#ff4444')
                for problem in problems_found:
                    add_result(f"• {problem}", '#ffaa00')
                status_label.config(text=f"Обнаружено {len(problems_found)} проблем", foreground='#ff4444')
            else:
                add_result("\n🎉 Все системы в норме!", '#00ff88')
                add_result("Игра должна запускаться без проблем", '#00ccff')
                status_label.config(text="Проблем не обнаружено", foreground='#00ff88')

        except Exception as e:
            add_result(f"❌ Ошибка диагностики: {str(e)}", '#ff4444')
            status_label.config(text="Ошибка при диагностике", foreground='#ff4444')

    # Настройка цветов для текста
    results_text.tag_configure('#00ff88', foreground='#00ff88')  # Зеленый
    results_text.tag_configure('#ff4444', foreground='#ff4444')  # Красный
    results_text.tag_configure('#ffaa00', foreground='#ffaa00')  # Желтый
    results_text.tag_configure('#00ccff', foreground='#00ccff')  # Голубой

    # Запускаем диагностику
    diag_window.after(500, run_diagnostic)
    diag_window.focus_force()


def create_debug_report(text_widget):
    """Создает отчет"""
    report_path = os.path.join(CONFIG['minecraft_dir'], 'diagnostic_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(text_widget.get('1.0', 'end'))

    messagebox.showinfo("Отчет создан", f"Отчет сохранен в:\n{report_path}")


def show_version_info():
    """Показывает информацию о версии лаунчера"""
    messagebox.showinfo(
        "О лаунчере",
        f"YamalPixel Launcher\nВерсия: {CURRENT_VERSION}\n\n"
        f"Разработано с ❤️ для комьюнити"
    )

def create_diagnostic_panel():
    """Создает панель диагностики с цветными сообщениями"""
    diag_window = tk.Toplevel(win)
    diag_window.title("Диагностика проблем")
    diag_window.geometry("700x550")

    # ВСЕ ОСТАЛЬНОЕ ОБЫЧНОЕ, БЕЗ ТЕМНЫХ ФОНОВ

    # Заголовок
    header_frame = ttk.Frame(diag_window)
    header_frame.pack(fill='x', padx=20, pady=15)

    ttk.Label(header_frame,
              text="Диагностика проблем",
              font=('Comfortaa', 16, 'bold')).pack()

    ttk.Label(header_frame,
              text="Автоматическая проверка и решение проблем",
              font=('Comfortaa', 10),
              foreground='gray').pack(pady=(5, 0))

    # Прогресс-бар
    progress_frame = ttk.Frame(diag_window)
    progress_frame.pack(fill='x', padx=20, pady=10)

    progress_label = ttk.Label(progress_frame, text="Проводим диагностику...")
    progress_label.pack()

    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal",
                                   length=650, mode="indeterminate")
    progress_bar.pack(pady=5)
    progress_bar.start()

    # Окно результатов - ОБЫЧНОЕ, белый фон, черный текст
    results_frame = ttk.LabelFrame(diag_window, text="Результаты диагностики", padding=10)
    results_frame.pack(fill='both', expand=True, padx=20, pady=10)

    results_text = tk.Text(results_frame, height=12, wrap='word',
                           font=('Consolas', 9))  # Обычный белый фон

    scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=results_text.yview)
    results_text.configure(yscrollcommand=scrollbar.set)

    results_text.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Статус
    status_frame = ttk.Frame(diag_window)
    status_frame.pack(fill='x', padx=20, pady=5)

    status_label = ttk.Label(status_frame, text="Начинаем проверку...")
    status_label.pack()

    # Кнопки
    button_frame = ttk.Frame(diag_window)
    button_frame.pack(fill='x', padx=20, pady=15)

    # Первый ряд
    row1 = ttk.Frame(button_frame)
    row1.pack(fill='x', pady=5)

    ttk.Button(row1, text="Быстрая починка",
               command=lambda: auto_repair_game_files(),
               width=18).pack(side='left', padx=5)

    ttk.Button(row1, text="Запуск без модов",
               command=launch_without_mods,
               width=18).pack(side='left', padx=5)

    # Второй ряд
    row2 = ttk.Frame(button_frame)
    row2.pack(fill='x', pady=5)

    ttk.Button(row2, text="Полная переустановка",
               command=complete_reinstall,
               width=18).pack(side='left', padx=5)

    ttk.Button(row2, text="Создать отчет",
               command=lambda: create_debug_report(results_text),
               width=15).pack(side='left', padx=5)

    ttk.Button(row2, text="Закрыть",
               command=diag_window.destroy,
               width=12).pack(side='right', padx=5)


    # Функции диагностики - ТОЛЬКО ЗДЕСЬ ЦВЕТНЫЙ ТЕКСТ
    def add_result(text, color='black'):  # По умолчанию черный
        results_text.insert('end', f"{text}\n", color)
        results_text.see('end')
        diag_window.update()

    def run_diagnostic():
        try:
            problems_found = []
            minecraft_dir = CONFIG['minecraft_dir']

            # Проверка структуры - зеленый
            for folder in ['mods', 'versions', 'config']:
                path = os.path.join(minecraft_dir, folder)
                if os.path.exists(path):
                    add_result(f"✅ Папка {folder} найдена", 'green')
                else:
                    problems_found.append(f"Отсутствует папка {folder}")
                    add_result(f"❌ Папка {folder} не найдена", 'red')

            # Проверка модов - синий
            mods_dir = os.path.join(minecraft_dir, 'mods')
            if os.path.exists(mods_dir):
                mod_files = [f for f in os.listdir(mods_dir) if f.endswith('.jar')]
                add_result(f"📦 Найдено модов: {len(mod_files)}", 'blue')

                if len(mod_files) == 0:
                    problems_found.append("Папка модов пустая")
                    add_result("⚠️ Папка модов пуста", 'orange')

            # Проверка ресурсов
            memory = psutil.virtual_memory()
            if memory.available < 3 * 1024 * 1024 * 1024:
                problems_found.append("Мало оперативной памяти")
                add_result(f"⚠️ Мало ОЗУ: {memory.available // 1024 // 1024}MB свободно", 'orange')
            else:
                add_result(f"✅ ОЗУ: {memory.available // 1024 // 1024}MB свободно", 'green')

            disk = psutil.disk_usage(minecraft_dir)
            if disk.free < 2 * 1024 * 1024 * 1024:
                problems_found.append("Мало места на диске")
                add_result(f"⚠️ Мало места: {disk.free // 1024 // 1024}MB свободно", 'orange')
            else:
                add_result(f"✅ Диск: {disk.free // 1024 // 1024}MB свободно", 'green')

            # Java
            java_ok = check_java_version()
            if java_ok:
                add_result("✅ Java установлена и работает", 'green')
            else:
                problems_found.append("Проблемы с Java")
                add_result("❌ Java не найдена", 'red')

            # Финальный отчет
            progress_bar.stop()

            if problems_found:
                add_result(f"\n🚨 Найдено проблем: {len(problems_found)}", 'red')
                for problem in problems_found:
                    add_result(f"• {problem}", 'orange')
                status_label.config(text=f"Обнаружено {len(problems_found)} проблем")
            else:
                add_result("\n🎉 Все системы в норме!", 'green')
                add_result("Игра должна запускаться без проблем", 'blue')
                status_label.config(text="Проблем не обнаружено")

        except Exception as e:
            add_result(f"❌ Ошибка диагностики: {str(e)}", 'red')
            status_label.config(text="Ошибка при диагностике")

    # Настройка цветов для текста
    results_text.tag_configure('green', foreground='green')
    results_text.tag_configure('red', foreground='red')
    results_text.tag_configure('orange', foreground='orange')
    results_text.tag_configure('blue', foreground='blue')

    # Запускаем диагностику
    diag_window.after(500, run_diagnostic)
    diag_window.focus_force()


def format_changelog(changelog):
    """Форматирует changelog для красивого отображения"""
    if not changelog:
        return "Нет описания изменений"

    # Убираем Markdown-разметку
    changelog = re.sub(r'#{2,}', '', changelog)
    changelog = re.sub(r'\- ', '• ', changelog)
    changelog = re.sub(r'\*\*(.*?)\*\*', r'▸ \1', changelog)
    changelog = re.sub(r'\*(.*?)\*', r'\1', changelog)
    changelog = re.sub(r'`(.*?)`', r'\1', changelog)

    # Ограничиваем длину
    if len(changelog) > 1000:
        changelog = changelog[:1000] + "...\n\n[Описание обрезано, полная версия на GitHub]"

    return changelog.strip()


def is_latest_version():
    """Проверяет, является ли текущая версия последней"""
    try:
        response = requests.get(
            "https://api.github.com/repos/XxMoonmenxX/YamalPixel/releases/latest",
            timeout=5
        )
        response.raise_for_status()

        latest_release = response.json()
        latest_version = latest_release['tag_name'].lstrip('v')

        return latest_version == CURRENT_VERSION
    except:
        return True  # Если не удалось проверить, считаем что актуальная


def set_launch_state(launching=False):
    """Управляет состоянием кнопок во время запуска"""
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME

    LAUNCH_IN_PROGRESS = launching
    if launching:
        LAUNCH_START_TIME = time.time()
        # Блокируем только основные кнопки
        launch_btn.config(state="disabled")  # Блокируем кастомную кнопку

        # Для кастомных кнопок меняем текст через их собственные методы
        quick_btn.itemconfig("text", text="⏳ Запуск...")
        quick_btn.itemconfig("shadow", text="⏳ Запуск...")
    else:
        # Разблокируем кнопки
        launch_btn.config(state="normal")  # Разблокируем кастомную кнопку

        # Возвращаем оригинальный текст
        quick_btn.itemconfig("text", text="🚀 Быстрый запуск (оффлайн)")
        quick_btn.itemconfig("shadow", text="🚀 Быстрый запуск (оффлайн)")

def is_launch_timeout():
    """Проверяет, не завис ли запуск"""
    if LAUNCH_START_TIME and time.time() - LAUNCH_START_TIME > 120:  # 2 минуты таймаут
        return True
    return False


def is_game_process_running():
    """Проверяет, запущен ли уже процесс Minecraft"""
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(
                ['tasklist', '/fi', 'imagename eq javaw.exe', '/fo', 'csv'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            # Если есть процессы javaw.exe, считаем что игра может быть запущена
            return "javaw.exe" in result.stdout
        else:  # Linux/MacOS
            result = subprocess.run(['pgrep', '-f', 'minecraft'], capture_output=True, text=True)
            return result.returncode == 0
    except:
        return False


def create_progress_window():
    """Создает окно прогресса с защитой от множественного создания"""
    progress_window = tk.Toplevel(win)
    progress_window.title("YamalPixel - Запуск игры")
    progress_window.geometry("500x300")
    progress_window.resizable(False, False)
    progress_window.transient(win)
    progress_window.grab_set()

    # Запрещаем закрытие через крестик
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

    # Центрируем окно
    progress_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (500 // 2)
    y = (win.winfo_screenheight() // 2) - (300 // 2)
    progress_window.geometry(f"500x300+{x}+{y}")

    # Стилизуем окно прогресса
    main_frame = ttk.Frame(progress_window, padding=25)
    main_frame.pack(fill='both', expand=True)

    # Заголовок
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill='x', pady=(0, 20))

    ttk.Label(header_frame, text="🚀 Запуск YamalPixel",
              font=('Comfortaa', 16, 'bold')).pack()

    ttk.Label(header_frame, text="Подготовка к запуску игры...",
              font=('Comfortaa', 11), foreground='gray').pack(pady=(5, 0))

    # Прогресс-бар
    progress_frame = ttk.Frame(main_frame)
    progress_frame.pack(fill='x', pady=10)

    progress = ttk.Progressbar(progress_frame, orient="horizontal",
                               length=400, mode="indeterminate")
    progress.pack(pady=5)
    progress.start()

    # Статус запуска
    status_label = ttk.Label(progress_frame, text="Инициализация запуска...",
                             font=('Comfortaa', 10))
    status_label.pack()

    # Таймер
    timer_frame = ttk.Frame(main_frame)
    timer_frame.pack(fill='x', pady=10)

    timer_label = ttk.Label(timer_frame, text="⏱️ Прошло времени: 0 сек.",
                            font=('Comfortaa', 9))
    timer_label.pack()

    # Кнопка отмены
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill='x', pady=20)

    def cancel_launch():
        progress_window.destroy()
        set_launch_state(False)
        messagebox.showinfo("Отменено", "✅ Запуск игры отменен")

    cancel_btn = ttk.Button(button_frame, text="❌ Отменить запуск",
                            command=cancel_launch)
    cancel_btn.pack()

    # Функция обновления таймера
    def update_timer():
        if LAUNCH_IN_PROGRESS and progress_window.winfo_exists():
            elapsed = int(time.time() - LAUNCH_START_TIME)
            timer_label.config(text=f"⏱️ Прошло времени: {elapsed} сек.")
            progress_window.after(1000, update_timer)

    update_timer()

    return progress_window



def monitor_game_process(process):
    """Мониторит процесс игры и разблокирует интерфейс при завершении"""
    process.wait()
    # Если процесс завершился, разблокируем интерфейс
    win.after(0, lambda: set_launch_state(False))



menu_bar = tk.Menu(win)
win.config(menu=menu_bar)
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_separator(background='#FFB6C1')

settings_menu.configure(
    tearoffcommand=lambda: None,
    postcommand=lambda: settings_menu.configure(bg='#FFB6C1')
)
menu_bar.add_cascade(label="Инструменты", menu=settings_menu)


# ОБНОВЛЕННЫЕ ПУНКТЫ МЕНЮ:
settings_menu.add_command(label="🎨 Скачать шейдеры", command=download_shaders)  # НОВАЯ КНОПКА
settings_menu.add_separator()
settings_menu.add_command(label="🔧 Починка файлов", command=auto_repair_game_files)
settings_menu.add_command(label="🛠️ Починить игру", command=repair_game_with_options)
settings_menu.add_separator()
settings_menu.add_command(label="📂 Открыть папку с игрой", command=open_game_folder)
settings_menu.add_command(label="💾 Сделать бэкап", command=create_manual_backup)
settings_menu.add_command(label="📊 Показать бэкапы", command=show_backup_info)
settings_menu.add_command(label="🗑️ Удалить ВСЕ бэкапы", command=delete_all_backups)
settings_menu.add_separator()
settings_menu.add_command(label="🔄 Полная переустановка", command=complete_reinstall)
settings_menu.add_separator()
settings_menu.add_command(label="🔧 Диагностика проблем", command=create_diagnostic_panel)
settings_menu.add_command(label="🚀 Тест скорости", command=speed_test)


# Или если хотите в выпадающем меню "Справка":
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="О лаунчере", command=show_version_info)
help_menu.add_separator()
help_menu.add_command(label="Проверить обновления", command=check_for_updates)
menu_bar.add_cascade(label="Справка", menu=help_menu)




# Функция для открытия настроек
def open_settings():
    settings_window = tk.Toplevel(win)
    settings_window.title("Настройки")

    ttk.Label(settings_window, text="Выделено памяти (ГБ):").grid(row=0, column=0)

    memory_var = tk.StringVar(value="8")
    memory_spinbox = ttk.Spinbox(
        settings_window,
        from_=1,  # Минимум
        to=64,  # Максимум
        textvariable=memory_var,
        width=10,
        validate="key",
        validatecommand=(settings_window.register(lambda p: p.isdigit() or p == ""), '%P')
    )
    memory_spinbox.grid(row=0, column=1)

    def save_settings():
        if not memory_var.get().isdigit():
            messagebox.showerror("Ошибка", "Введите число!")
            return

        memory_gb = int(memory_var.get())
        new_memory = f"-Xmx{memory_gb}G"
        CONFIG['jvm_memory'] = new_memory
        messagebox.showinfo("Сохранено", f"Память установлена: {memory_gb} ГБ")
        settings_window.destroy()

    ttk.Button(settings_window, text="Сохранить", command=save_settings).grid(row=1, columnspan=2)


# Добавление в меню
settings_menu.add_command(label="Настройки", command=open_settings)
settings_menu.add_separator()


# Функция для проверки и загрузки модов
def checker1():
    """НАДЕЖНАЯ функция проверки и загрузки модов с прогресс-баром - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    if version_selector.get() != "YamalPixel":
        print("Выбрана версия, отличная от YamalPixel. Загрузка модов пропущена.")
        return

    # Создаем окно прогресса
    progress_window = tk.Toplevel(win)
    progress_window.title("Загрузка модов")
    progress_window.geometry("500x200")
    progress_window.resizable(False, False)
    progress_window.transient(win)
    progress_window.grab_set()

    # Центрируем окно
    progress_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (500 // 2)
    y = (win.winfo_screenheight() // 2) - (200 // 2)
    progress_window.geometry(f"500x200+{x}+{y}")

    # Элементы UI
    main_frame = ttk.Frame(progress_window, padding=20)
    main_frame.pack(fill='both', expand=True)

    # Заголовок
    title_label = ttk.Label(main_frame, text="📥 Загрузка модов",
                            font=('Comfortaa', 14, 'bold'))
    title_label.pack(pady=(0, 15))

    # Общий прогресс-бар
    total_progress_label = ttk.Label(main_frame, text="Общий прогресс: 0%")
    total_progress_label.pack()

    total_progress = ttk.Progressbar(main_frame, orient="horizontal",
                                     length=400, mode="determinate")
    total_progress.pack(pady=5)

    # Прогресс текущего мода
    current_mod_label = ttk.Label(main_frame, text="Подготовка к загрузке...")
    current_mod_label.pack()

    current_progress = ttk.Progressbar(main_frame, orient="horizontal",
                                       length=400, mode="determinate")
    current_progress.pack(pady=5)

    # Счетчик
    counter_label = ttk.Label(main_frame, text="Мод 0/0")
    counter_label.pack()

    # Статус
    status_label = ttk.Label(main_frame, text="Инициализация...",
                             font=('Comfortaa', 9), foreground='blue')
    status_label.pack(pady=10)

    def update_progress(current, total, mod_name="", file_progress=0, file_total=1):
        """Обновляет прогресс в UI"""
        try:
            # Общий прогресс
            total_percent = (current * 100) // total if total > 0 else 0
            total_progress['value'] = total_percent
            total_progress_label.config(text=f"Общий прогресс: {total_percent}%")

            # Прогресс текущего файла
            file_percent = (file_progress * 100) // file_total if file_total > 0 else 0
            current_progress['value'] = file_percent

            # Тексты
            current_mod_label.config(text=f"Текущий мод: {mod_name}")
            counter_label.config(text=f"Мод {current}/{total}")
            status_label.config(
                text=f"Загрузка: {file_progress / (1024 * 1024):.1f}MB / {file_total / (1024 * 1024):.1f}MB"
                if file_total > 0 else "Подготовка...")

            progress_window.update()
        except:
            pass

    def download_thread():
        """Поток загрузки модов"""
        nonlocal progress_window

        try:
            mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
            os.makedirs(mods_dir, exist_ok=True)
            base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'

            # Определяем какие моды нужно скачать
            mods_to_download = []
            for mod in CONFIG['mods']:
                mod_path = os.path.join(mods_dir, mod['file'])
                if not os.path.exists(mod_path):
                    mods_to_download.append(mod)

            total_mods = len(mods_to_download)
            success_count = 0

            if total_mods == 0:
                win.after(0, lambda: show_completion_result(progress_window, 0, 0, True))
                return

            win.after(0, lambda: update_progress(0, total_mods, "Подготовка..."))

            for i, mod in enumerate(mods_to_download):
                try:
                    mod_path = os.path.join(mods_dir, mod['file'])

                    win.after(0, lambda idx=i, m=mod: update_progress(
                        idx, total_mods, m['file'], 0, 1
                    ))

                    print(f"⬇️  Загружаем мод ({i + 1}/{total_mods}): {mod['file']}")

                    # Получаем ссылку для скачивания
                    params = {'public_key': mod['url']}
                    response = requests.get(base_url, params=params, timeout=30)
                    response.raise_for_status()
                    download_url = response.json().get('href')

                    if not download_url:
                        print(f"❌ Не удалось получить ссылку для {mod['file']}")
                        continue

                    # Загружаем файл с прогрессом
                    with requests.get(download_url, stream=True, timeout=60) as dl_response:
                        dl_response.raise_for_status()

                        total_size = int(dl_response.headers.get('content-length', 0))
                        downloaded_size = 0

                        with open(mod_path, 'wb') as f:
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)

                                    # Обновляем прогресс текущего файла
                                    win.after(0, lambda idx=i, m=mod, ds=downloaded_size, ts=total_size:
                                    update_progress(idx, total_mods, m['file'], ds, ts))

                        print(f"✅ Мод {mod['file']} успешно установлен")
                        success_count += 1

                except Exception as e:
                    print(f"❌ Ошибка загрузки мода {mod['file']}: {str(e)}")
                    win.after(0, lambda: status_label.config(
                        text=f"Ошибка: {str(e)[:50]}..."
                    ))

            # Распаковываем ZIP-файлы
            win.after(0, lambda: status_label.config(text="Распаковка архивов..."))
            zip_count = 0
            for mod in mods_to_download:
                if mod['file'].endswith('.zip'):
                    zip_path = os.path.join(mods_dir, mod['file'])
                    if os.path.exists(zip_path):
                        try:
                            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                                zip_file.extractall(path=mods_dir)
                            print(f"📦 Содержимое архива {mod['file']} успешно извлечено")
                            zip_count += 1
                        except Exception as e:
                            print(f"❌ Ошибка распаковки архива {mod['file']}: {str(e)}")

            # ПОСЛЕ ПОЛНОЙ ЗАГРУЗКИ ВСЕХ МОДОВ - закрываем окно
            win.after(0, lambda: show_completion_result(
                progress_window, success_count, total_mods, False
            ))

        except Exception as e:
            print(f"💥 Критическая ошибка в потоке загрузки: {e}")
            win.after(0, lambda: show_completion_result(progress_window, 0, 0, True))

    def show_completion_result(window, success, total, all_exist):
        """Показывает результат загрузки и ЗАКРЫВАЕТ окно"""
        window.destroy()

        if all_exist:
            messagebox.showinfo("Загрузка модов", "✅ Все моды уже установлены!")
            # ЗАПУСКАЕМ ИГРУ ПОСЛЕ ЗАКРЫТИЯ ОКНА ЗАГРУЗКИ
            win.after(100, runn)
        elif success == total:
            messagebox.showinfo("Загрузка модов",
                                f"🎉 Все моды успешно загружены!\n\n"
                                f"• Загружено: {success} модов\n"
                                f"Запускайте игру!")
            # ЗАПУСКАЕМ ИГРУ ПОСЛЕ ЗАКРЫТИЯ ОКНА ЗАГРУЗКИ
            win.after(100, runn)
        elif success > 0:
            result = messagebox.askyesno("Загрузка модов",
                                   f"📊 Загрузка завершена с ошибками\n\n"
                                   f"• Успешно: {success} модов\n"
                                   f"• Всего: {total} модов\n"
                                   f"• Не загружено: {total - success} модов\n\n"
                                   f"Запустить игру с доступными модами?")
            if result:
                # ЗАПУСКАЕМ ИГРУ ПОСЛЕ ЗАКРЫТИЯ ОКНА ЗАГРУЗКИ
                win.after(100, runn)
        else:
            messagebox.showerror("Ошибка загрузки",
                                 "❌ Не удалось загрузить ни одного мода!\n\n"
                                 "Возможные причины:\n"
                                 "• Проблемы с интернет-соединением\n"
                                 "• Яндекс.Диск блокирует загрузки\n"
                                 "• Антивирус блокирует загрузки")

    # Запускаем загрузку в отдельном потоке
    threading.Thread(target=download_thread, daemon=True).start()


# Функция для проверки установки Minecraft и Fabric
def check_minecraft_and_fabric_installed():
    minecraft_versions_dir = os.path.join(CONFIG['minecraft_dir'], 'versions')
    fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
    fabric_version_dir = os.path.join(minecraft_versions_dir, fabric_version)
    if os.path.exists(fabric_version_dir):
        print("Fabric уже установлен.")
        return True
    else:
        print("Fabric не установлен.")
        return False


def is_fabric_needed(selected_version):
    # Список версий, где Fabric поддерживается
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
        "Minecraft 1.21 + Fabric",
        "Minecraft 1.21.1 + Fabric",
        "Minecraft 1.21.2 + Fabric",
        "Minecraft 1.21.3 + Fabric",
        "Minecraft 1.21.4 + Fabric"
    ]
    return selected_version in fabric_supported_versions


def install_minecraft_version(version, progress_callback=None):
    """
    Устанавливает указанную версию Minecraft, если она отсутствует.
    """
    versions_dir = os.path.join(CONFIG['minecraft_dir'], 'versions')
    version_dir = os.path.join(versions_dir, version)

    if not os.path.exists(version_dir):
        print(f"Версия {version} не найдена. Начинаем установку...")
        minecraft_launcher_lib.install.install_minecraft_version(
            versionid=version,
            minecraft_directory=CONFIG['minecraft_dir'],
            callback=progress_callback
        )
    else:
        print(f"Версия {version} уже установлена.")


def clear_auth_cache():
    """Очищает кэш аутентификации Minecraft"""
    minecraft_dir = CONFIG['minecraft_dir']
    cache_files = [
        os.path.join(minecraft_dir, 'usercache.json'),
        os.path.join(minecraft_dir, 'launcher_profiles.json'),
        os.path.join(minecraft_dir, 'launcher_accounts.json')
    ]

    for cache_file in cache_files:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"Удален: {cache_file}")
            except Exception as e:
                print(f"Ошибка удаления {cache_file}: {e}")

def show_random_launch_message():
    import random
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
        "Сервак запущен, а ты - опущен"
    ]
    return random.choice(messages)


def check_and_download_missing_mods():
    """Проверяет и загружает отсутствующие моды перед запуском"""
    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')

    # Проверяем какие моды отсутствуют
    missing_mods = []
    for mod in CONFIG['mods']:
        mod_path = os.path.join(mods_dir, mod['file'])
        if not os.path.exists(mod_path):
            missing_mods.append(mod)

    # Если есть отсутствующие моды - загружаем их
    if missing_mods:
        print(f"🔍 Найдено отсутствующих модов: {len(missing_mods)}")
        download_mods_turbo_ui(missing_mods)
        return True
    else:
        print("✅ Все моды на месте")
        return False





# ЗАГРУЗКА МОДОВ ТОЛЬКО ДЛЯ YamalPixel
def runn():
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME, progress_window, status_label, details_label, timer_label, log_label

    if LAUNCH_IN_PROGRESS:
        elapsed = int(time.time() - LAUNCH_START_TIME)
        messagebox.showwarning(
            "Запуск уже выполняется",
            f"🔄 Игра уже запускается!\n\nПрошло: {elapsed} секунд\nПожалуйста, дождитесь завершения запуска."
        )
        return

    try:
        if not username.get().strip() or username.get().strip() == "Введите никнейм":
            messagebox.showerror("Ошибка", "❌ Введите имя пользователя!")
            return

        # НЕМЕДЛЕННО блокируем интерфейс
        set_launch_state(True)

        # Создаем окно прогресса запуска
        progress_window = tk.Toplevel(win)
        progress_window.title("YamalPixel - Запуск игры")
        progress_window.geometry("500x350")
        progress_window.resizable(False, False)
        progress_window.transient(win)
        progress_window.grab_set()
        progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

        # Центрируем окно
        progress_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (500 // 2)
        y = (win.winfo_screenheight() // 2) - (350 // 2)
        progress_window.geometry(f"500x350+{x}+{y}")

        # Стилизуем окно прогресса
        main_frame = ttk.Frame(progress_window, padding=25)
        main_frame.pack(fill='both', expand=True)

        # Заголовок
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        ttk.Label(header_frame, text="🚀 Запуск YamalPixel", font=('Comfortaa', 16, 'bold')).pack()
        ttk.Label(header_frame, text="Подготовка к запуску игры...", font=('Comfortaa', 11), foreground='gray').pack(
            pady=(5, 0))

        # Прогресс-бар
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill='x', pady=10)
        progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="indeterminate")
        progress_bar.pack(pady=5)
        progress_bar.start()

        # Статус запуска
        status_label = ttk.Label(progress_frame, text="Инициализация запуска...", font=('Comfortaa', 10))
        status_label.pack()

        # Таймер
        timer_frame = ttk.Frame(main_frame)
        timer_frame.pack(fill='x', pady=10)
        timer_label = ttk.Label(timer_frame, text="⏱️ Прошло времени: 0 сек.", font=('Comfortaa', 9))
        timer_label.pack()

        # Детали запуска
        details_label = ttk.Label(main_frame, text="", font=('Comfortaa', 8), foreground='blue')
        details_label.pack()

        # Лог запуска
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill='x', pady=5)
        log_label = ttk.Label(log_frame, text="", font=('Consolas', 7), foreground='green')
        log_label.pack()

        # Кнопка отмены
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        def cancel_launch():
            progress_window.destroy()
            set_launch_state(False)
            messagebox.showinfo("Отменено", "✅ Запуск игры отменен")

        cancel_btn = ttk.Button(button_frame, text="❌ Отменить запуск", command=cancel_launch, style="Accent.TButton")
        cancel_btn.pack()

        # Функция обновления UI
        update_progress_ui()




        def update_status(text, detail=""):
            if progress_window.winfo_exists():
                win.after(0, lambda: status_label.config(text=text))
                if detail:
                    win.after(0, lambda: details_label.config(text=detail))

        def update_log(message):
            """Обновляет лог с проверкой существования окна и элементов"""
            try:
                # Всегда пишем в консоль
                print(f"[LAUNCHER] {message}")

                # Проверяем существует ли окно прогресса и лейбл
                if 'progress_window' in globals() and progress_window and progress_window.winfo_exists():
                    if 'log_label' in globals() and log_label and log_label.winfo_exists():
                        win.after(0, lambda: log_label.config(text=message))
            except Exception as e:
                # В случае ошибки просто логируем в консоль
                print(f"[LAUNCHER UPDATE ERROR] {message}")

        def update_status(text, detail=""):
            """Обновляет статус с проверкой существования окна и элементов"""
            try:
                if 'progress_window' in globals() and progress_window and progress_window.winfo_exists():
                    if 'status_label' in globals() and status_label and status_label.winfo_exists():
                        win.after(0, lambda: status_label.config(text=text))
                    if detail and 'details_label' in globals() and details_label and details_label.winfo_exists():
                        win.after(0, lambda: details_label.config(text=detail))
            except Exception as e:
                print(f"[STATUS UPDATE ERROR] {text}")

        update_progress_ui()


        # ГЛАВНОЕ ИСПРАВЛЕНИЕ: Загрузка модов ДО запуска игры
        def start_launch_process():
            """Запускает процесс загрузки модов и только ПОТОМ игру"""

            def mods_loading_completed():
                """Вызывается когда ВСЕ моды загружены"""
                update_status("Моды загружены", "Запускаем игру...")
                update_log("✅ Все моды успешно загружены, запускаем игру")
                launch_game_after_mods()

            def mods_loading_failed(error_msg):
                """Вызывается при ошибке загрузки модов"""
                update_log(f"❌ Ошибка загрузки модов: {error_msg}")
                # Спрашиваем запускать ли игру без модов
                result = messagebox.askyesno(
                    "Ошибка загрузки модов",
                    f"Не удалось загрузить некоторые моды:\n{error_msg}\n\nЗапустить игру без недостающих модов?"
                )
                if result:
                    update_log("🔄 Запускаем игру без некоторых модов")
                    launch_game_after_mods()
                else:
                    # Отменяем запуск
                    win.after(0, progress_window.destroy)
                    win.after(0, lambda: set_launch_state(False))

            # ЗАПУСКАЕМ ЗАГРУЗКУ МОДОВ ДЛЯ YamalPixel
            if version_selector.get() == "YamalPixel":
                update_status("Загрузка модов", "Скачиваем и проверяем моды...")
                update_log("🔄 Запускаем загрузку модов для YamalPixel")

                # Запускаем checker1() с колбэками завершения
                run_mods_download_with_callbacks(mods_loading_completed, mods_loading_failed)
            else:
                # Для других версий сразу запускаем игру
                update_log(f"🚫 Версия {version_selector.get()} - загрузка модов не требуется")
                launch_game_after_mods()

        def run_mods_download_with_callbacks(success_callback, error_callback):
            """Запускает загрузку модов с колбэками завершения"""

            def mods_download_thread():
                try:
                    mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
                    os.makedirs(mods_dir, exist_ok=True)

                    # Проверяем какие моды нужно скачать
                    mods_to_download = []
                    for mod in CONFIG['mods']:
                        mod_path = os.path.join(mods_dir, mod['file'])
                        if not os.path.exists(mod_path):
                            mods_to_download.append(mod)

                    if not mods_to_download:
                        update_log("✅ Все моды уже установлены")
                        win.after(0, success_callback)
                        return

                    update_log(f"📥 Начинаем загрузку {len(mods_to_download)} модов...")

                    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
                    success_count = 0
                    failed_mods = []

                    for i, mod in enumerate(mods_to_download):
                        try:
                            update_status(f"Загрузка модов ({i + 1}/{len(mods_to_download)})",
                                          f"Скачиваем: {mod['file']}")

                            # Получаем ссылку для скачивания
                            params = {'public_key': mod['url']}
                            response = requests.get(base_url, params=params, timeout=30)
                            response.raise_for_status()
                            download_url = response.json().get('href')

                            if not download_url:
                                failed_mods.append(f"{mod['file']} - не удалось получить ссылку")
                                continue

                            # Загружаем файл
                            mod_path = os.path.join(mods_dir, mod['file'])
                            with requests.get(download_url, stream=True, timeout=60) as dl_response:
                                dl_response.raise_for_status()
                                with open(mod_path, 'wb') as f:
                                    for chunk in dl_response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)

                            success_count += 1
                            update_log(f"✅ Успешно: {mod['file']}")

                        except Exception as e:
                            failed_mods.append(f"{mod['file']} - {str(e)}")
                            update_log(f"❌ Ошибка: {mod['file']} - {str(e)}")

                    # Обрабатываем результат загрузки
                    if failed_mods:
                        error_msg = f"Не удалось загрузить {len(failed_mods)} модов:\n" + "\n".join(failed_mods[:3])
                        if len(failed_mods) > 3:
                            error_msg += f"\n...и еще {len(failed_mods) - 3} модов"
                        win.after(0, lambda: error_callback(error_msg))
                    else:
                        win.after(0, success_callback)

                except Exception as e:
                    win.after(0, lambda: error_callback(str(e)))

            # Запускаем загрузку в отдельном потоке
            threading.Thread(target=mods_download_thread, daemon=True).start()

        def launch_game_after_mods():
            """Запускает игру ПОСЛЕ загрузки всех модов"""
            try:
                update_status("Подготовка игры", "Завершаем настройку...")

                # Быстрая проверка файлов
                quick_file_check()
                update_log("✅ Проверка файлов завершена")

                # Очистка кэша аутентификации
                clear_auth_cache()
                update_log("✅ Кэш аутентификации очищен")

                selected_version = version_selector.get()
                selected_memory = CONFIG.get('jvm_memory', '4G')

                if selected_memory.startswith('-Xmx'):
                    selected_memory = selected_memory[4:]
                elif selected_memory.startswith('-Xms'):
                    selected_memory = selected_memory[4:]

                update_status("Проверка Fabric", "Проверяем установку Fabric...")

                # Проверяем и устанавливаем Fabric если нужно
                if is_fabric_needed(selected_version):
                    fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
                    update_log(f"🔧 Проверяем Fabric: {fabric_version}")

                    if not check_fabric_installed():
                        update_status("Установка Fabric", "Устанавливаем Fabric Loader...")
                        update_log("Fabric не установлен, начинаем установку...")

                        try:
                            minecraft_launcher_lib.fabric.install_fabric(
                                minecraft_version=CONFIG['version'],
                                loader_version=CONFIG['fabric_loader'],
                                minecraft_directory=CONFIG['minecraft_dir']
                            )
                            update_log("✅ Fabric успешно установлен")
                        except Exception as fabric_error:
                            update_log(f"❌ Ошибка установки Fabric: {fabric_error}")
                            raise Exception(f"Не удалось установить Fabric: {fabric_error}")
                    else:
                        update_log("✅ Fabric уже установлен")
                else:
                    update_log("🚫 Fabric не требуется для этой версии")

                update_status("Запуск игры", "Формируем команду запуска...")
                update_log(f"🎯 Запускаем версию: {selected_version}")
                update_log(f"💾 Память: {selected_memory}")

                # Оптимизированные настройки запуска
                jvm_args = [
                    f"-Xmx{selected_memory}", f"-Xms{selected_memory}",
                    "-XX:+UseG1GC", "-XX:+UnlockExperimentalVMOptions",
                    "-XX:G1NewSizePercent=20", "-XX:G1ReservePercent=20",
                    "-XX:MaxGCPauseMillis=50", "-XX:G1HeapRegionSize=32M",
                    "-Duser.language=ru", "-Duser.country=RU", "-Dfile.encoding=UTF-8"
                ]

                options = {
                    'username': username.get(),
                    'uuid': str(hash(username.get())),
                    'token': '',
                    'jvmArguments': jvm_args,
                    'gameLocale': 'ru_RU'
                }

                # Формируем команду запуска
                if is_fabric_needed(selected_version):
                    command = minecraft_launcher_lib.command.get_minecraft_command(
                        version=f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}",
                        minecraft_directory=CONFIG['minecraft_dir'],
                        options=options
                    )
                    update_log(
                        f"⚙️ Используем Fabric версию: fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}")
                else:
                    command = minecraft_launcher_lib.command.get_minecraft_command(
                        version=CONFIG['version'],
                        minecraft_directory=CONFIG['minecraft_dir'],
                        options=options
                    )
                    update_log(f"⚙️ Используем vanilla версию: {CONFIG['version']}")

                update_status("Запуск Minecraft", "Запускаем процесс...")
                update_log("🚀 Запускаем процесс Minecraft...")

                # Запускаем процесс
                process = launch_minecraft_process(command, update_log)

                if process:
                    update_log("✅ Процесс Minecraft успешно запущен!")
                    update_status("Игра запущена", "Minecraft загружается...")

                    # Ждем и проверяем статус
                    time.sleep(5)

                    if is_minecraft_process_running(process):
                        update_log("🎮 Minecraft загружается...")

                        # Закрываем окно прогресса и разблокируем интерфейс
                        win.after(0, progress_window.destroy)
                        win.after(0, lambda: set_launch_state(False))

                        win.after(100, lambda: messagebox.showinfo(
                            "Успешный запуск",
                            f"✅ Игра успешно запущена!\n\n• Игрок: {username.get()}\n• Версия: {selected_version}\n• Память: {selected_memory}\n\n{show_random_launch_message()}"
                        ))

                        # Мониторим процесс в фоне
                        threading.Thread(target=monitor_game_process, args=(process,), daemon=True).start()
                    else:
                        update_log("❌ Процесс Minecraft завершился неожиданно")
                        raise Exception("Minecraft не запустился")
                else:
                    update_log("❌ Не удалось запустить процесс Minecraft")
                    raise Exception("Не удалось создать процесс Minecraft")

            except Exception as e:
                error_msg = f"Ошибка запуска: {str(e)}"
                update_log(f"❌ {error_msg}")
                win.after(0, progress_window.destroy)
                win.after(0, lambda: set_launch_state(False))
                win.after(0, lambda: messagebox.showerror(
                    "Ошибка запуска",
                    f"❌ Не удалось запустить игру:\n\n{error_msg}\n\nПроверьте:\n• Достаточно ли памяти\n• Целостность игровых файлов\n• Антивирусные блокировки"
                ))

        # ЗАПУСКАЕМ ПРОЦЕСС ЗАГРУЗКИ МОДОВ И ИГРЫ
        start_launch_process()

    except Exception as e:
        set_launch_state(False)
        messagebox.showerror("Критическая ошибка", f"❌ Не удалось подготовить запуск:\n\n{str(e)}")
def safe_destroy_window(window):
    """Безопасно уничтожает окно с проверкой существования"""
    try:
        if window and window.winfo_exists():
            window.destroy()
    except Exception as e:
        print(f"Ошибка при закрытии окна: {e}")
def launch_minecraft_process(command, log_callback=None):
    """Запускает процесс Minecraft с перехватом вывода"""
    try:
        if log_callback:
            log_callback("Запускаем Minecraft...")

        # Запускаем процесс с перехватом stdout и stderr
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Объединяем stderr в stdout
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Запускаем поток для чтения вывода в реальном времени
        def read_output():
            try:
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line and log_callback:
                        # Фильтруем и форматируем вывод
                        formatted_line = format_minecraft_output(line.strip())
                        if formatted_line:
                            log_callback(formatted_line)
            except Exception as e:
                if log_callback:
                    log_callback(f"❌ Ошибка чтения вывода: {str(e)}")

        # Запускаем поток чтения вывода
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()

        if log_callback:
            log_callback("✅ Minecraft запущен, читаем вывод...")
        return process

    except Exception as e:
        if log_callback:
            log_callback(f"❌ Ошибка запуска: {str(e)}")
        return None

def format_minecraft_output(line):
    """Форматирует вывод Minecraft для отображения в лаунчере"""
    if not line:
        return None

    # Фильтруем только важные сообщения
    important_patterns = [
        'Loading Minecraft',
        'Loading mods',
        'WARN',
        'ERROR',
        'INFO',
        'Shaders',
        'OpenGL',
        'Sound engine',
        'Setting user',
        'Failed to'
    ]

    # Пропускаем менее важные сообщения
    skip_patterns = [
        'FabricLoader',
        'SpongePowered',
        'Backend library',
        'Reloading ResourceManager',
        'Created:',
        'Successfully reloaded'
    ]

    # Проверяем, содержит ли строка важные паттерны
    if any(pattern in line for pattern in important_patterns):
        # Укорачиваем слишком длинные строки
        if len(line) > 100:
            line = line[:100] + "..."

        # Добавляем эмодзи для разных типов сообщений
        if 'ERROR' in line or 'Failed to' in line:
            return f"❌ {line}"
        elif 'WARN' in line:
            return f"⚠️ {line}"
        elif 'Loading Minecraft' in line:
            return f"🎮 {line}"
        elif 'Loading mods' in line:
            return f"📦 {line}"
        elif 'Setting user' in line:
            return f"👤 {line}"
        else:
            return f"ℹ️ {line}"

    # Пропускаем строки с неважными паттернами
    elif any(pattern in line for pattern in skip_patterns):
        return None

    return None

def is_minecraft_process_running(process):
    """Проверяет, запущен ли процесс Minecraft"""
    try:
        # Проверяем наш процесс
        if process.poll() is None:
            return True

        # Дополнительная проверка через tasklist
        if os.name == 'nt':
            result = subprocess.run(
                ['tasklist', '/fi', 'imagename eq javaw.exe', '/fo', 'csv'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "javaw.exe" in result.stdout
        else:
            result = subprocess.run(['pgrep', '-f', 'minecraft'], capture_output=True, text=True)
            return result.returncode == 0

    except:
        return False

def monitor_game_process(process):
    """Мониторит процесс игры в фоне"""
    try:
        # Ждем завершения процесса
        process.wait()

        # Читаем вывод если есть
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stdout:
                print(f"[MINECRAFT STDOUT] {stdout[:500]}...")
            if stderr:
                print(f"[MINECRAFT STDERR] {stderr[:500]}...")
        except:
            pass

        print("[LAUNCHER] Процесс Minecraft завершен")

    except Exception as e:
        print(f"[LAUNCHER] Ошибка мониторинга: {e}")
def update_log(message):
    """Просто логирует в консоль, без обновления UI"""
    print(f"[LAUNCHER] {message}")

def update_status(text, detail=""):
    """Просто логирует статус в консоль"""
    print(f"[STATUS] {text}")
    if detail:
        print(f"[DETAIL] {detail}")

def update_progress_ui():
    """Упрощенная версия без обновления UI"""
    if LAUNCH_IN_PROGRESS:
        elapsed = int(time.time() - LAUNCH_START_TIME)
        print(f"[TIMER] Прошло времени: {elapsed} сек.")
        win.after(1000, update_progress_ui)


def format_minecraft_output(line):
    """Форматирует вывод Minecraft для отображения в лаунчере"""
    if not line:
        return None

    # Фильтруем только важные сообщения
    important_patterns = [
        'Loading Minecraft',
        'Loading mods',
        'WARN',
        'ERROR',
        'INFO',
        'Shaders',
        'OpenGL',
        'Sound engine',
        'Setting user',
        'Failed to'
    ]

    # Пропускаем менее важные сообщения
    skip_patterns = [
        'FabricLoader',
        'SpongePowered',
        'Backend library',
        'Reloading ResourceManager',
        'Created:',
        'Successfully reloaded'
    ]

    # Проверяем, содержит ли строка важные паттерны
    if any(pattern in line for pattern in important_patterns):
        # Укорачиваем слишком длинные строки
        if len(line) > 100:
            line = line[:100] + "..."

        # Добавляем эмодзи для разных типов сообщений
        if 'ERROR' in line or 'Failed to' in line:
            return f"❌ {line}"
        elif 'WARN' in line:
            return f"⚠️ {line}"
        elif 'Loading Minecraft' in line:
            return f"🎮 {line}"
        elif 'Loading mods' in line:
            return f"📦 {line}"
        elif 'Setting user' in line:
            return f"👤 {line}"
        else:
            return f"ℹ️ {line}"

    # Пропускаем строки с неважными паттернами
    elif any(pattern in line for pattern in skip_patterns):
        return None

    return None


def is_minecraft_process_running(process):
    """Проверяет, запущен ли процесс Minecraft"""
    try:
        # Проверяем наш процесс
        if process.poll() is None:
            return True

        # Дополнительная проверка через tasklist
        if os.name == 'nt':
            result = subprocess.run(
                ['tasklist', '/fi', 'imagename eq javaw.exe', '/fo', 'csv'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "javaw.exe" in result.stdout
        else:
            result = subprocess.run(['pgrep', '-f', 'minecraft'], capture_output=True, text=True)
            return result.returncode == 0

    except:
        return False


def monitor_game_process(process):
    """Мониторит процесс игры в фоне"""
    try:
        # Ждем завершения процесса
        process.wait()

        # Читаем вывод если есть
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stdout:
                print(f"[MINECRAFT STDOUT] {stdout[:500]}...")
            if stderr:
                print(f"[MINECRAFT STDERR] {stderr[:500]}...")
        except:
            pass

        print("[LAUNCHER] Процесс Minecraft завершен")

    except Exception as e:
        print(f"[LAUNCHER] Ошибка мониторинга: {e}")


class ModernButton(tk.Canvas):
    def __init__(self, master=None,
                 text="Кнопка",
                 width=200,
                 height=50,
                 gradient=("#FF6B6B", "#4ECDC4"),
                 glow_color="#FF6B6B",
                 animation="pulse",
                 command=None,
                 font_size=14,
                 corner_radius=15,
                 **kwargs):

        super().__init__(master, width=width, height=height,
                         highlightthickness=0,**kwargs)

        self.text = text
        self.width = width
        self.height = height
        self.gradient = gradient
        self.glow_color = glow_color
        self.animation_type = animation
        self.command = command
        self.font_size = font_size
        self.corner_radius = corner_radius

        # Состояния кнопки
        self.is_pressed = False
        self.animation_running = True
        self.pulse_phase = 0

        # Цвета для разных состояний
        self.normal_gradient = gradient
        self.pressed_gradient = (self.darken_color(gradient[0]),
                                 self.darken_color(gradient[1]))

        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

        # Начальная отрисовка
        self.draw_button()

        # Запускаем анимацию
        if animation == "pulse":
            self.animate_pulse()
        elif animation == "glow":
            self.animate_glow()

    def draw_button(self):
        """Отрисовывает кнопку"""
        self.delete("all")

        # Выбираем градиент в зависимости от состояния
        if self.is_pressed:
            grad_colors = self.pressed_gradient
        else:
            grad_colors = self.normal_gradient

        # Применяем пульсацию к цветам
        if self.animation_type == "pulse" and self.animation_running:
            pulse_factor = 0.1 * math.sin(self.pulse_phase)
            brightened_colors = (
                self.lighten_color(grad_colors[0], 0.1 + pulse_factor),
                self.lighten_color(grad_colors[1], 0.1 + pulse_factor)
            )
            grad_colors = brightened_colors

        # Простой прямоугольник со скругленными углами (без сложной геометрии)
        self.create_rectangle(2, 2, self.width - 2, self.height - 2,
                              fill=grad_colors[0], outline="",
                              width=0, tags="bg")

        # Упрощенный градиент
        steps = 10
        for i in range(steps):
            ratio = i / steps
            r = int((1 - ratio) * self.hex_to_rgb(grad_colors[0])[0] +
                    ratio * self.hex_to_rgb(grad_colors[1])[0])
            g = int((1 - ratio) * self.hex_to_rgb(grad_colors[0])[1] +
                    ratio * self.hex_to_rgb(grad_colors[1])[1])
            b = int((1 - ratio) * self.hex_to_rgb(grad_colors[0])[2] +
                    ratio * self.hex_to_rgb(grad_colors[1])[2])

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)
            self.create_rectangle(x1, 2, x2, self.height - 2,
                                  fill=color, outline="", tags="gradient")

        # Добавляем текст
        text_color = "white"
        self.create_text(self.width / 2, self.height / 2,
                         text=self.text,
                         fill=text_color,
                         font=('Comfortaa', self.font_size, 'bold'),
                         tags="text")

        # Добавляем свечение
        if self.animation_type == "pulse" and self.animation_running:
            glow_intensity = abs(math.sin(self.pulse_phase)) * 0.3
            glow_width = 2 + int(glow_intensity * 4)
            self.create_rectangle(0, 0, self.width, self.height,
                                  outline=self.glow_color,
                                  width=glow_width, tags="glow")

    def animate_pulse(self):
        """Анимация пульсации"""
        if not self.animation_running:
            return

        self.pulse_phase += 0.1
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase = 0

        self.draw_button()
        self.after(50, self.animate_pulse)

    def animate_glow(self):
        """Анимация свечения"""
        if not self.animation_running:
            return

        self.pulse_phase += 0.15
        self.draw_button()
        self.after(80, self.animate_glow)

    def on_hover(self, event):
        """При наведении курсора"""
        self.draw_button()

    def on_leave(self, event):
        """При уходе курсора"""
        self.draw_button()

    def on_press(self, event):
        """При нажатии"""
        self.is_pressed = True
        self.pulse_phase += 0.5
        self.draw_button()

    def on_release(self, event):
        """При отпускании"""
        self.is_pressed = False
        self.draw_button()

        if self.command:
            self.command()

    def lighten_color(self, color, factor=0.2):
        """Осветляет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [min(255, c + int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def darken_color(self, color, factor=0.2):
        """Затемняет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [max(0, c - int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def stop_animation(self):
        """Останавливает анимацию"""
        self.animation_running = False

    def start_animation(self):
        """Запускает анимацию"""
        self.animation_running = True
        if self.animation_type == "pulse":
            self.animate_pulse()
        elif self.animation_type == "glow":
            self.animate_glow()

# А затем создавайте кнопку с правильной ссылкой на функцию:
def launch_game():
    print("🚀 Запускаем игру!")
    runn()  # Вызываем вашу основную функцию запуска

# Создание кастомной кнопки:
launch_btn = ModernButton(
    win,
    text="🚀 ВОЙТИ В ИГРУ",
    width=220,
    height=60,
    gradient=("#FF6B6B", "#4ECDC4"),  # От красного к бирюзе
    glow_color="#FF6B6B",
    animation="pulse",
    command=launch_game,
    font_size=16,
    corner_radius=20
)
launch_btn.place(relx=0.5, rely=0.5, anchor="c")

# Запускаем анимацию
launch_btn.start_animation()





def disable_problematic_mods():
    """Временно отключает потенциально проблемные моды"""
    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')
    disabled_dir = os.path.join(minecraft_dir, 'mods_disabled')

    os.makedirs(disabled_dir, exist_ok=True)

    # Моды которые могут вызывать проблемы при подключении
    problematic_mods = [
        'antixray-fabric-1.4.6+1.20.1.jar',
        'servercore-fabric-1.5.2+1.20.1.jar',
        'auth-1.0.0.jar'
    ]

    moved_mods = []
    for mod in problematic_mods:
        mod_path = os.path.join(mods_dir, mod)
        if os.path.exists(mod_path):
            try:
                shutil.move(mod_path, os.path.join(disabled_dir, mod))
                moved_mods.append(mod)
                print(f"Отключен мод: {mod}")
            except Exception as e:
                print(f"Ошибка отключения мода {mod}: {e}")

    if moved_mods:
        messagebox.showinfo("Моды отключены",
                            f"Временно отключены моды:\n" + "\n".join(moved_mods) +
                            f"\n\nОни перемещены в: {disabled_dir}")


class ModernQuickLaunchButton(tk.Canvas):
    def __init__(self, master=None,
                 text="🚀 Быстрый запуск",
                 width=250,
                 height=45,
                 gradient=("#667eea", "#764ba2"),
                 command=None,
                 font_size=12,
                 corner_radius=12,
                 **kwargs):

        super().__init__(master, width=width, height=height,
                         highlightthickness=0,  **kwargs)

        self.text = text
        self.width = width
        self.height = height
        self.gradient = gradient
        self.command = command
        self.font_size = font_size
        self.corner_radius = corner_radius

        # Состояния кнопки
        self.is_pressed = False

        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

        # Начальная отрисовка
        self.draw_button()

    def draw_button(self):
        """Отрисовывает кнопку"""
        self.delete("all")

        # Создаем скругленный прямоугольник с градиентом
        self.create_round_rect(2, 2, self.width - 2, self.height - 2,
                               self.corner_radius,
                               fill=self.gradient[0], outline="", tags="bg")

        # Добавляем градиентный эффект
        steps = 8
        for i in range(steps):
            ratio = i / steps
            r = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[0] +
                    ratio * self.hex_to_rgb(self.gradient[1])[0])
            g = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[1] +
                    ratio * self.hex_to_rgb(self.gradient[1])[1])
            b = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[2] +
                    ratio * self.hex_to_rgb(self.gradient[1])[2])

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)
            self.create_round_rect(x1, 2, x2, self.height - 2,
                                   self.corner_radius,
                                   fill=color, outline="", tags="gradient")

        # Добавляем текст
        text_color = "white"

        # Основной текст
        self.create_text(self.width / 2, self.height / 2,
                         text=self.text,
                         fill=text_color,
                         font=('Comfortaa', self.font_size, 'bold'),
                         tags="text")

    def create_round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Создает скругленный прямоугольник"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_press(self, event):
        """При нажатии"""
        self.is_pressed = True
        # Временно затемняем кнопку при нажатии
        self.itemconfig("bg", fill=self.darken_color(self.gradient[0]))
        self.itemconfig("gradient", fill=self.darken_color(self.gradient[1]))

    def on_release(self, event):
        """При отпускании"""
        self.is_pressed = False
        # Возвращаем нормальные цвета
        self.itemconfig("bg", fill=self.gradient[0])
        self.itemconfig("gradient", fill=self.gradient[1])

        if self.command:
            self.command()

    def darken_color(self, color, factor=0.1):
        """Затемняет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [max(0, c - int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)



def quick_launch_action():
    """Действие для быстрого запуска"""
    print("🚀 Быстрый запуск игры!")
    quick_launch_offline()

quick_btn = ModernQuickLaunchButton(
    win,
    text="🚀 Быстрый запуск (оффлайн)",
    width=260,
    height=48,
    gradient=("#667eea", "#764ba2"),  # Фиолетовый градиент
    command=quick_launch_action,
    font_size=12,
    corner_radius=15
)

# Размещаем кнопку
quick_btn.place(relx=0.5, rely=0.56, anchor="c")




def quick_launch_offline():
    """Быстрый запуск в оффлайн-режиме с отключенными проблемными модами"""
    result = messagebox.askyesno(
        "Быстрый запуск",
        "Запустить игру в оффлайн-режиме?\n\n" +
        "Это может помочь если есть проблемы с:\n" +
        "• Аутентификацией\n" +
        "• Подключением к серверу\n" +
        "• Зависаниями при входе\n\n" +
        "Попробуйте этот режим если обычный запуск не работает."
    )

    if result:
        # Временно отключаем проблемные моды
        disable_problematic_mods()

        # Запускаем в оффлайн режиме
        runn()  # Функция runn() теперь будет использовать оффлайн режим из выбора


def quick_file_check():
    """Быстрая проверка основных файлов"""
    minecraft_dir = CONFIG['minecraft_dir']
    required_dirs = ['mods', 'versions', 'config']

    for dir_name in required_dirs:
        dir_path = os.path.join(minecraft_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)


def check_mods_quick():
    """Быстрая проверка модов без скачивания"""
    mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
    if not os.path.exists(mods_dir):
        os.makedirs(mods_dir)
        return

    # Просто проверяем существование папки mods
    print("Быстрая проверка модов выполнена")

def enable_all_mods():
    """Включает все отключенные моды"""
    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')
    disabled_dir = os.path.join(minecraft_dir, 'mods_disabled')

    if os.path.exists(disabled_dir):
        for mod in os.listdir(disabled_dir):
            try:
                shutil.move(os.path.join(disabled_dir, mod), os.path.join(mods_dir, mod))
                print(f"Включен мод: {mod}")
            except Exception as e:
                print(f"Ошибка включения мода {mod}: {e}")

        # Удаляем пустую папку
        if not os.listdir(disabled_dir):
            os.rmdir(disabled_dir)
# Стили
style = ttk.Style()
style.configure("BW.TLabel", background="pink")
app = ttk.Style()
style.configure("Accent.TButton", background='#0078D7', foreground='white')
app.configure('TLabel', font=('Comfortaa', 12))
app.configure('TButton', font=('Comfortaa', 12))

# Элементы интерфейса
enabled = tk.IntVar()
ttk.Checkbutton(
    text="Полный экран", variable=enabled, command=lambda: fullsc() if enabled.get() else outscrn(),
    style='BW2.TLabel'
).pack(padx=6, pady=6, anchor=tk.NE)





style.configure("CenterText.TLabel", layout=('Center',))





# Функции для управления музыкой
def mscon():
    mixer.music.play()


def mscoff():
    mixer.music.stop()


enabled1 = tk.IntVar()
ttk.Checkbutton(
    text="Включить музыку", style='BW2.TLabel', variable=enabled1,
    command=lambda: mscon() if enabled1.get() else mscoff(),
).pack(padx=6, pady=6, anchor=tk.NE)





# Добавьте в интерфейс где-нибудь внизу
status_frame = ttk.Frame(win, relief='sunken', padding=5)
status_frame.place(relx=0.5, rely=0.95, anchor='center')

status_label = ttk.Label(status_frame, text="✅ Готов к запуску",
                        font=('Comfortaa', 9), foreground='green')
status_label.pack()

def update_status():
    if LAUNCH_IN_PROGRESS:
        elapsed = int(time.time() - LAUNCH_START_TIME)
        status_label.config(text=f"🔄 Запуск игры... ({elapsed} сек.)",
                          foreground='orange')
    else:
        status_label.config(text="✅ Готов к запуску", foreground='green')
    win.after(1000, update_status)

# Запускаем обновление статуса
win.after(1000, update_status)


class ModernEntry(tk.Canvas):
    def __init__(self, master=None,
                 placeholder="Введите никнейм",
                 width=280,
                 height=48,
                 gradient=("#667eea", "#764ba2"),
                 corner_radius=15,
                 **kwargs):

        super().__init__(master, width=width, height=height,
                         highlightthickness=0, **kwargs)

        self.configure(bg='#2b2b2b')

        self.placeholder = placeholder
        self.width = width
        self.height = height
        self.gradient = gradient
        self.corner_radius = corner_radius
        self.is_focused = False
        self.text_value = tk.StringVar()

        # ВАЖНО: сначала рисуем градиент, потом создаем Entry поверх
        self.draw_background()

        # Создаем Entry ПОВЕРХ градиента
        self.entry = tk.Entry(self,
                              textvariable=self.text_value,
                              font=('Comfortaa', 12),
                              border=0,
                              relief='flat',
                              bg='white',
                              fg='#2b2b2b',
                              justify='center',
                              insertbackground='#2b2b2b',
                              highlightthickness=0)

        # Размещаем Entry поверх всего
        self.entry.place(x=10, y=10, width=width - 20, height=height - 20)

        # Бинды
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.bind('<KeyRelease>', self.on_key_release)

        self.update_placeholder()

    def draw_background(self):
        """Отрисовывает градиентный фон"""
        self.delete("all")

        # Градиентный фон
        steps = 12
        for i in range(steps):
            ratio = i / steps
            r = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[0] +
                    ratio * self.hex_to_rgb(self.gradient[1])[0])
            g = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[1] +
                    ratio * self.hex_to_rgb(self.gradient[1])[1])
            b = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[2] +
                    ratio * self.hex_to_rgb(self.gradient[1])[2])

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)

            self.create_rectangle(x1, 0, x2, self.height,
                                  fill=color, outline="", tags="gradient")

        # Обводка
        border_color = '#ffffff' if self.is_focused else self.gradient[1]
        border_width = 3 if self.is_focused else 2
        self.create_rectangle(2, 2, self.width - 2, self.height - 2,
                              outline=border_color, width=border_width, tags="border")

    def on_focus_in(self, event):
        """При фокусе"""
        self.is_focused = True
        self.draw_background()
        if self.text_value.get() == self.placeholder:
            self.entry.configure(fg='#2b2b2b')
            self.text_value.set('')

    def on_focus_out(self, event):
        """При потере фокуса"""
        self.is_focused = False
        self.draw_background()
        self.update_placeholder()

    def on_key_release(self, event):
        """При вводе текста"""
        pass  # Не нужно перерисовывать

    def update_placeholder(self):
        """Обновляет плейсхолдер"""
        if not self.text_value.get() and not self.is_focused:
            self.entry.configure(fg='#666666')
            self.text_value.set(self.placeholder)
        else:
            self.entry.configure(fg='#2b2b2b')

    def get(self):
        """Возвращает текст (без плейсхолдера)"""
        text = self.text_value.get()
        return '' if text == self.placeholder else text

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)


# Создание поля ввода
username = ModernEntry(
    win,
    placeholder="Введите никнейм",
    width=300,
    height=50,
    gradient=("#667eea", "#764ba2"),
    corner_radius=15
)
username.place(relx=0.5, rely=0.44, anchor="c")


class ModernOnlineButton(tk.Canvas):
    def __init__(self, master=None,
                 text="🌐 ПОКАЗАТЬ ОНЛАЙН",
                 width=220,
                 height=45,
                 gradient=("#4A90E2", "#357ABD"),
                 glow_color="#4A90E2",
                 animation="glow",
                 command=None,
                 font_size=12,
                 corner_radius=15,
                 **kwargs):

        super().__init__(master, width=width, height=height,
                         highlightthickness=0, **kwargs)

        self.configure(bg='#2b2b2b')

        self.text = text
        self.width = width
        self.height = height
        self.gradient = gradient
        self.glow_color = glow_color
        self.animation_type = animation
        self.command = command
        self.font_size = font_size
        self.corner_radius = corner_radius

        # Состояния кнопки
        self.is_pressed = False
        self.animation_running = True
        self.pulse_phase = 0

        # Цвета для разных состояний
        self.normal_gradient = gradient
        self.pressed_gradient = (self.darken_color(gradient[0]),
                                 self.darken_color(gradient[1]))

        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

        # Начальная отрисовка
        self.draw_button()

        # Запускаем анимацию
        if animation == "glow":
            self.animate_glow()

    def draw_button(self):
        """Отрисовывает кнопку с градиентом"""
        self.delete("all")

        # Выбираем градиент в зависимости от состояния
        if self.is_pressed:
            grad_colors = self.pressed_gradient
        else:
            grad_colors = self.normal_gradient

        # Применяем анимацию к цветам
        if self.animation_type == "glow" and self.animation_running:
            glow_intensity = abs(math.sin(self.pulse_phase)) * 0.2
            brightened_colors = (
                self.lighten_color(grad_colors[0], glow_intensity),
                self.lighten_color(grad_colors[1], glow_intensity)
            )
            grad_colors = brightened_colors

        # Создаем градиентный фон
        steps = 12
        for i in range(steps):
            ratio = i / steps
            r = int((1 - ratio) * self.hex_to_rgb(grad_colors[0])[0] +
                    ratio * self.hex_to_rgb(grad_colors[1])[0])
            g = int((1 - ratio) * self.hex_to_rgb(grad_colors[0])[1] +
                    ratio * self.hex_to_rgb(grad_colors[1])[1])
            b = int((1 - ratio) * self.hex_to_rgb(grad_colors[0])[2] +
                    ratio * self.hex_to_rgb(grad_colors[1])[2])

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)

            self.create_rectangle(x1, 2, x2, self.height - 2,
                                  fill=color, outline="", tags="gradient")

        # Добавляем свечение
        if self.animation_type == "glow" and self.animation_running:
            glow_width = 1 + int(abs(math.sin(self.pulse_phase)) * 3)
            self.create_rectangle(1, 1, self.width - 1, self.height - 1,
                                  outline=self.glow_color,
                                  width=glow_width, tags="glow")

        # Добавляем текст
        text_color = "white"
        self.create_text(self.width / 2, self.height / 2,
                         text=self.text,
                         fill=text_color,
                         font=('Comfortaa', self.font_size, 'bold'),
                         tags="text")

    def animate_glow(self):
        """Анимация свечения - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if not self.animation_running:
            return

        self.pulse_phase += 0.15
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase = 0

        self.draw_button()
        # ИСПРАВЛЕНИЕ: передаем ссылку на функцию, а не вызываем её
        self.after(80, self.animate_glow)

    def on_press(self, event):
        """При нажатии"""
        self.is_pressed = True
        self.draw_button()

    def on_release(self, event):
        """При отпускании"""
        self.is_pressed = False
        self.draw_button()

        if self.command:
            self.command()

    def lighten_color(self, color, factor=0.2):
        """Осветляет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [min(255, c + int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def darken_color(self, color, factor=0.2):
        """Затемняет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [max(0, c - int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def stop_animation(self):
        """Останавливает анимацию"""
        self.animation_running = False

    def start_animation(self):
        """Запускает анимацию"""
        self.animation_running = True
        self.animate_glow()


# Улучшенная функция показа онлайн игроков
def show_online_players():
    """Красивое отображение онлайн игроков"""
    try:
        # Создаем красивое окно с информацией
        online_window = tk.Toplevel(win)
        online_window.title("🌐 Статус сервера")
        online_window.geometry("300x200")
        online_window.resizable(False, False)
        online_window.configure(bg='#2b2b2b')
        online_window.transient(win)
        online_window.grab_set()

        # Центрируем окно
        online_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (300 // 2)
        y = (win.winfo_screenheight() // 2) - (200 // 2)
        online_window.geometry(f"300x200+{x}+{y}")

        # Основной фрейм
        main_frame = ttk.Frame(online_window, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Заголовок
        title_label = ttk.Label(main_frame,
                                text="🌐 Статус сервера",
                                font=('Comfortaa', 16, 'bold'),
                                foreground='white',
                                background='#2b2b2b')
        title_label.pack(pady=(0, 15))

        # Получаем статус сервера
        server = JavaServer.lookup("90.151.59.120:25565")
        status = server.status()

        players_online = status.players.online
        max_players = status.players.max

        # Определяем цвет статуса
        if players_online > 0:
            status_color = "#4CAF50"  # Зеленый
            status_text = "🟢 СЕРВЕР ОНЛАЙН"
            players_text = f"👥 Игроков: {players_online}/{max_players}"
        else:
            status_color = "#f44336"  # Красный
            status_text = "🔴 СЕРВЕР ПУСТ"
            players_text = f"👥 Игроков: {players_online}/{max_players}"

        # Статус сервера
        status_label = ttk.Label(main_frame,
                                 text=status_text,
                                 font=('Comfortaa', 12, 'bold'),
                                 foreground=status_color,
                                 background='#2b2b2b')
        status_label.pack(pady=5)

        # Количество игроков
        players_label = ttk.Label(main_frame,
                                  text=players_text,
                                  font=('Comfortaa', 11),
                                  foreground='#cccccc',
                                  background='#2b2b2b')
        players_label.pack(pady=5)

        # Пинг
        ping_label = ttk.Label(main_frame,  # ИСПРАВЛЕНО: main_frame вместо main_server
                               text=f"📡 Пинг: {status.latency:.1f} мс",
                               font=('Comfortaa', 10),
                               foreground='#888888',
                               background='#2b2b2b')
        ping_label.pack(pady=5)

        # Версия
        version_label = ttk.Label(main_frame,
                                  text=f"⚙️ Версия: {status.version.name}",
                                  font=('Comfortaa', 9),
                                  foreground='#666666',
                                  background='#2b2b2b')
        version_label.pack(pady=5)

        # Кнопка закрытия
        close_btn = ttk.Button(main_frame,
                               text="Закрыть",
                               command=online_window.destroy,
                               width=15)
        close_btn.pack(pady=15)

    except Exception as e:
        # Красивое окно ошибки
        error_window = tk.Toplevel(win)
        error_window.title("❌ Ошибка")
        error_window.geometry("250x150")
        error_window.configure(bg='#2b2b2b')

        ttk.Label(error_window,
                  text="❌ Ошибка подключения",
                  font=('Comfortaa', 12, 'bold'),
                  foreground='#f44336',
                  background='#2b2b2b').pack(pady=20)

        ttk.Label(error_window,
                  text="Сервер недоступен",
                  font=('Comfortaa', 10),
                  foreground='#cccccc',
                  background='#2b2b2b').pack(pady=5)

        ttk.Button(error_window,
                   text="Закрыть",
                   command=error_window.destroy).pack(pady=15)



online_btn = ModernOnlineButton(
    win,
    text="🌐 ПОКАЗАТЬ ОНЛАЙН",
    width=220,
    height=45,
    gradient=("#4A90E2", "#357ABD"),  # Синий градиент
    glow_color="#4A90E2",
    animation="glow",
    command=show_online_players,
    font_size=12,
    corner_radius=15
)

# Размещаем кнопку
online_btn.place(relx=0.5, rely=0.61, anchor="c")

# Запускаем анимацию
online_btn.start_animation()

# Список версий для селектора
versions = [
    "YamalPixel",
    "Minecraft 1.7.10",
    "Minecraft 1.8.9",
    "Minecraft 1.12.2",
    "Minecraft 1.14.4",
    "Minecraft 1.14.4 + Fabric",
    "Minecraft 1.15.2",
    "Minecraft 1.15.2 + Fabric",
    "Minecraft 1.16.5",
    "Minecraft 1.16.5 + Fabric",
    "Minecraft 1.17.1",
    "Minecraft 1.17.1 + Fabric",
    "Minecraft 1.18.2",
    "Minecraft 1.18.2 + Fabric",
    "Minecraft 1.19.2",
    "Minecraft 1.19.2 + Fabric",
    "Minecraft 1.20.1",
    "Minecraft 1.20.1 + Fabric",
    "Minecraft 1.20.2",
    "Minecraft 1.20.2 + Fabric",
    "Minecraft 1.21",
    "Minecraft 1.21 + Fabric",
    "Minecraft 1.21.1",
    "Minecraft 1.21.1 + Fabric",
    "Minecraft 1.21.2",
    "Minecraft 1.21.2 + Fabric",
    "Minecraft 1.21.3",
    "Minecraft 1.21.3 + Fabric",
    "Minecraft 1.21.4",
    "Minecraft 1.21.4 + Fabric"
]


class ModernVersionSelector(tk.Canvas):
    def __init__(self, master=None,
                 width=300,
                 height=50,
                 gradient=("#667eea", "#764ba2"),
                 corner_radius=15,
                 versions_list=None,
                 **kwargs):

        super().__init__(master, width=width, height=height,
                         highlightthickness=0, **kwargs)

        self.configure(bg='#2b2b2b')

        self.width = width
        self.height = height
        self.gradient = gradient
        self.corner_radius = corner_radius
        self.is_open = False

        self.versions = versions_list if versions_list else versions

        # Создаем скрытый комбобокс
        self.combobox = ttk.Combobox(master, values=self.versions, state="readonly", font=('Comfortaa', 11))
        self.combobox.current(0)
        self.combobox.configure(width=22, state="readonly")
        self.combobox.place_forget()

        # Текущее значение
        self.current_value = tk.StringVar(value=self.versions[0])

        # Бинды
        self.bind("<Button-1>", self.toggle_dropdown)
        self.combobox.bind("<<ComboboxSelected>>", self.on_select)

        # Начальная отрисовка
        self.draw_selector()

    def draw_selector(self):
        """Отрисовывает селектор версий"""
        self.delete("all")

        # Градиентный фон
        steps = 12
        for i in range(steps):
            ratio = i / steps
            r = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[0] +
                    ratio * self.hex_to_rgb(self.gradient[1])[0])
            g = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[1] +
                    ratio * self.hex_to_rgb(self.gradient[1])[1])
            b = int((1 - ratio) * self.hex_to_rgb(self.gradient[0])[2] +
                    ratio * self.hex_to_rgb(self.gradient[1])[2])

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)

            self.create_rectangle(x1, 2, x2, self.height - 2,
                                  fill=color, outline="", tags="gradient")

        # Текст выбранной версии
        display_text = self.current_value.get()
        if len(display_text) > 20:
            display_text = display_text[:20] + "..."

        self.create_text(self.width // 2 - 10, self.height // 2,
                         text=display_text,
                         fill='white',
                         font=('Comfortaa', 11),
                         anchor='e',
                         tags="text")

        # Стрелка
        arrow_size = 6
        center_x = self.width - 20
        center_y = self.height // 2

        if self.is_open:
            # Стрелка вверх
            points = [
                center_x, center_y - arrow_size // 2,
                          center_x - arrow_size, center_y + arrow_size // 2,
                          center_x + arrow_size, center_y + arrow_size // 2
            ]
        else:
            # Стрелка вниз
            points = [
                center_x, center_y + arrow_size // 2,
                          center_x - arrow_size, center_y - arrow_size // 2,
                          center_x + arrow_size, center_y - arrow_size // 2
            ]

        self.create_polygon(points, fill='white', tags="arrow")

        # Иконка версии
        icon_text = "🎮" if "YamalPixel" in self.current_value.get() else "⚙️"
        self.create_text(25, self.height // 2,
                         text=icon_text,
                         fill='white',
                         font=('Comfortaa', 14),
                         tags="icon")

    def toggle_dropdown(self, event):
        """Открывает/закрывает выпадающий список"""
        if not self.is_open:
            self.combobox.place(x=self.winfo_x(), y=self.winfo_y() + self.height,
                                width=self.width, height=200)
            self.combobox.focus()
            self.combobox.event_generate('<Button-1>')
        else:
            self.hide_dropdown()

        self.is_open = not self.is_open
        self.draw_selector()

    def hide_dropdown(self):
        """Скрывает выпадающий список"""
        self.combobox.place_forget()

    def on_select(self, event):
        """Обрабатывает выбор версии"""
        selected = self.combobox.get()
        self.current_value.set(selected)
        self.is_open = False
        self.hide_dropdown()
        self.draw_selector()
        select_version(event)

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def get(self):
        """Возвращает выбранное значение"""
        return self.current_value.get()


# Создаем красивый селектор версий
version_selector = ModernVersionSelector(
    win,
    width=320,
    height=48,
    gradient=("#667eea", "#764ba2"),
    corner_radius=20,
    versions_list=versions
)
version_selector.place(relx=0.5, rely=0.4, anchor="c")


# Функция выбора версии
def select_version(event):
    selected_version = version_selector.get()

    # Обновляем конфигурацию в зависимости от выбранной версии
    version_configs = {
        "YamalPixel": ('1.20.1', '0.16.10'),
        "Minecraft 1.7.10": ('1.7.10', None),
        "Minecraft 1.8.9": ('1.8.9', None),
        "Minecraft 1.12.2": ('1.12.2', None),
        "Minecraft 1.14.4": ('1.14.4', None),
        "Minecraft 1.14.4 + Fabric": ('1.14.4', '0.16.10'),
        "Minecraft 1.15.2": ('1.15.2', None),
        "Minecraft 1.15.2 + Fabric": ('1.15.2', '0.16.10'),
        "Minecraft 1.16.5": ('1.16.5', None),
        "Minecraft 1.16.5 + Fabric": ('1.16.5', '0.16.10'),
        "Minecraft 1.17.1": ('1.17.1', None),
        "Minecraft 1.17.1 + Fabric": ('1.17.1', '0.16.10'),
        "Minecraft 1.18.2": ('1.18.2', None),
        "Minecraft 1.18.2 + Fabric": ('1.18.2', '0.16.10'),
        "Minecraft 1.19.2": ('1.19.2', None),
        "Minecraft 1.19.2 + Fabric": ('1.19.2', '0.16.10'),
        "Minecraft 1.20.1": ('1.20.1', '0.16.10'),
        "Minecraft 1.20.1 + Fabric": ('1.20.1', '0.16.10'),
        "Minecraft 1.20.2": ('1.20.2', None),
        "Minecraft 1.20.2 + Fabric": ('1.20.2', '0.16.10'),
        "Minecraft 1.21": ('1.21', None),
        "Minecraft 1.21 + Fabric": ('1.21', '0.16.10'),
        "Minecraft 1.21.1": ('1.21.1', None),
        "Minecraft 1.21.1 + Fabric": ('1.21.1', '0.16.10'),
        "Minecraft 1.21.2": ('1.21.2', None),
        "Minecraft 1.21.2 + Fabric": ('1.21.2', '0.16.10'),
        "Minecraft 1.21.3": ('1.21.3', None),
        "Minecraft 1.21.3 + Fabric": ('1.21.3', '0.16.10'),
        "Minecraft 1.21.4": ('1.21.4', None),
        "Minecraft 1.21.4 + Fabric": ('1.21.4', '0.16.10')
    }

    if selected_version in version_configs:
        CONFIG['version'], CONFIG['fabric_loader'] = version_configs[selected_version]

        # Красивое сообщение об изменении версии
        show_version_change_message(selected_version)


def show_version_change_message(version_name):
    """Показывает красивое сообщение об изменении версии"""
    message_window = tk.Toplevel(win)
    message_window.title("Версия изменена")
    message_window.geometry("300x150")
    message_window.resizable(False, False)
    message_window.configure(bg='#2b2b2b')
    message_window.transient(win)
    message_window.grab_set()

    # Центрируем окно
    message_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (300 // 2)
    y = (win.winfo_screenheight() // 2) - (150 // 2)
    message_window.geometry(f"300x150+{x}+{y}")

    # Содержимое окна
    main_frame = ttk.Frame(message_window, padding=20)
    main_frame.pack(fill='both', expand=True)

    # Иконка
    icon = "🎮" if "YamalPixel" in version_name else "⚙️"
    ttk.Label(main_frame, text=icon, font=('Comfortaa', 24),
              background='#2b2b2b').pack(pady=(0, 10))

    # Текст
    ttk.Label(main_frame, text="Версия изменена",
              font=('Comfortaa', 14, 'bold'),
              foreground='white', background='#2b2b2b').pack()

    ttk.Label(main_frame, text=version_name,
              font=('Comfortaa', 12),
              foreground='#4ECDC4', background='#2b2b2b').pack(pady=(5, 15))

    # Кнопка
    ttk.Button(main_frame, text="OK",
               command=message_window.destroy,
               width=10).pack()

    # Автоматическое закрытие через 2 секунды
    message_window.after(2000, message_window.destroy)

# Вызываем функцию обновления статуса Discord после создания окна
win.after(300, update_discord_status)


class ModrinthAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://api.modrinth.com/v2"
        self.session.headers.update({
            'User-Agent': 'YamalPixel-Launcher/1.0 (moonmen@example.com)'
        })

    def search_mods(self, query, limit=20):
        """Поиск модов на Modrinth"""
        try:
            url = f"{self.base_url}/search"
            params = {
                'query': query,
                'limit': limit
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка поиска модов: {e}")
            return None

    def get_mod_versions(self, mod_id, minecraft_version, loader):
        """Получение версий мода с улучшенной обработкой файлов"""
        try:
            url = f"{self.base_url}/project/{mod_id}/version"
            params = {
                'game_versions': f'["{minecraft_version}"]',
                'loaders': f'["{loader}"]'
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            versions = response.json()

            # Фильтруем версии, у которых есть файлы
            versions_with_files = []
            for version in versions:
                if 'files' in version and version['files']:
                    # Проверяем, что есть primary файл или любой JAR файл
                    primary_file = None
                    for file_info in version['files']:
                        if file_info.get('primary', False) or file_info['filename'].endswith('.jar'):
                            primary_file = file_info
                            break

                    if primary_file:
                        versions_with_files.append(version)

            return versions_with_files if versions_with_files else versions

        except Exception as e:
            print(f"Ошибка получения версий мода {mod_id}: {e}")
            return None

    def download_mod(self, project_slug, version_id, filename, mods_dir):
        """Скачивание мода с правильным URL"""
        try:
            # ПРАВИЛЬНЫЙ URL для скачивания файлов Modrinth
            # Формат: https://cdn.modrinth.com/data/PROJECT_SLUG/versions/VERSION_ID/FILENAME
            file_url = f"https://cdn.modrinth.com/data/{project_slug}/versions/{version_id}/{filename}"

            print(f"📥 Скачиваем: {file_url}")

            response = self.session.get(file_url, stream=True, timeout=30)
            response.raise_for_status()

            filepath = os.path.join(mods_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"✅ Успешно скачан: {filename}")
            return True

        except Exception as e:
            print(f"❌ Ошибка скачивания мода {filename}: {e}")

            # Альтернативный метод через API
            return self.download_mod_alternative(project_slug, version_id, filename, mods_dir)

    def download_mod_alternative(self, project_slug, version_id, filename, mods_dir):
        """Альтернативный метод скачивания через получение информации о версии"""
        try:
            # Получаем информацию о версии
            version_url = f"{self.base_url}/version/{version_id}"
            response = self.session.get(version_url, timeout=30)
            response.raise_for_status()
            version_data = response.json()

            print(f"🔍 Ищем файл в информации о версии: {filename}")

            if 'files' in version_data and version_data['files']:
                # Ищем нужный файл по имени
                target_file = None
                for file_info in version_data['files']:
                    if file_info['filename'] == filename:
                        target_file = file_info
                        break

                if target_file and 'url' in target_file:
                    download_url = target_file['url']
                    print(f"📥 Альтернативное скачивание: {download_url}")

                    response = self.session.get(download_url, stream=True, timeout=30)
                    response.raise_for_status()

                    filepath = os.path.join(mods_dir, filename)
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    print(f"✅ Успешно скачан альтернативным методом: {filename}")
                    return True

            print(f"❌ Файл {filename} не найден в информации о версии")
            return False

        except Exception as e:
            print(f"❌ Альтернативный метод скачивания также не удался: {e}")
            return False
# Функция создания новой сборки с выбором модов
def create_new_collection():
    global current_sort_col, current_sort_reverse
    current_sort_col = 'downloads'
    current_sort_reverse = False
    collection_window = tk.Toplevel(win)
    collection_window.title("Создать сборку")
    collection_window.geometry("900x1080")
    collection_window.transient(win)
    collection_window.grab_set()

    main_frame = ttk.Frame(collection_window, padding=20)
    main_frame.pack(fill='both', expand=True)

    ttk.Label(main_frame, text="📦 Новая сборка модов", font=('Comfortaa', 16, 'bold')).pack(pady=(0, 20))

    # Основные настройки
    settings_frame = ttk.Frame(main_frame)
    settings_frame.pack(fill='x', pady=(0, 20))

    ttk.Label(settings_frame, text="Название:").pack(anchor='w')
    name_var = tk.StringVar()
    ttk.Entry(settings_frame, textvariable=name_var, width=50).pack(fill='x', pady=(0, 10))

    # Версия и загрузчик
    meta_frame = ttk.Frame(settings_frame)
    meta_frame.pack(fill='x')

    ttk.Label(meta_frame, text="Версия:").pack(side='left')
    version_var = tk.StringVar(value="1.20.1")
    version_combo = ttk.Combobox(meta_frame, textvariable=version_var,
                                 values=["1.20.1", "1.19.2", "1.18.2", "1.17.1", "1.16.5"],
                                 state="readonly", width=12)
    version_combo.pack(side='left', padx=(5, 20))

    ttk.Label(meta_frame, text="Загрузчик:").pack(side='left')
    loader_var = tk.StringVar(value="Fabric")
    loader_combo = ttk.Combobox(meta_frame, textvariable=loader_var,
                                values=["Fabric", "Forge", "Quilt"],
                                state="readonly", width=12)
    loader_combo.pack(side='left', padx=5)

    # Вкладки выбора модов
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill='both', expand=True, pady=(0, 20))

    # Вкладка 1: Локальные моды
    local_frame = ttk.Frame(notebook, padding=10)
    notebook.add(local_frame, text="📁 Мои моды")

    # Поиск в локальных модах
    local_search_frame = ttk.Frame(local_frame)
    local_search_frame.pack(fill='x', pady=(0, 10))

    ttk.Label(local_search_frame, text="Поиск:").pack(side='left')
    local_search_var = tk.StringVar()
    local_search_entry = ttk.Entry(local_search_frame, textvariable=local_search_var, width=30)
    local_search_entry.pack(side='left', padx=(5, 10))

    def search_local_mods():
        query = local_search_var.get().lower()
        load_local_mods(query)

    ttk.Button(local_search_frame, text="🔍 Поиск", command=search_local_mods).pack(side='left', padx=(0, 10))
    ttk.Button(local_search_frame, text="🔄 Обновить", command=lambda: load_local_mods()).pack(side='left')

    # Список локальных модов
    local_tree_frame = ttk.Frame(local_frame)
    local_tree_frame.pack(fill='both', expand=True)

    local_mods_tree = ttk.Treeview(local_tree_frame, columns=('name', 'file', 'size'), show='headings', height=10)
    local_mods_tree.heading('name', text='Название')
    local_mods_tree.heading('file', text='Файл')
    local_mods_tree.heading('size', text='Размер')

    local_mods_tree.column('name', width=250)
    local_mods_tree.column('file', width=200)
    local_mods_tree.column('size', width=80)

    # Загрузка локальных модов
    def load_local_mods(search_query=None):
        local_mods_tree.delete(*local_mods_tree.get_children())
        mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')

        if not os.path.exists(mods_dir):
            return

        for file in os.listdir(mods_dir):
            if file.endswith('.jar'):
                if search_query and search_query not in file.lower():
                    continue

                file_path = os.path.join(mods_dir, file)
                try:
                    size = os.path.getsize(file_path) / 1024 / 1024
                    name = ' '.join([word.capitalize() for word in
                                     file.replace('.jar', '').replace('_', ' ').replace('-', ' ').split()])

                    local_mods_tree.insert('', 'end',
                                           values=(name, file, f"{size:.1f} MB"),
                                           tags=(file,))
                except:
                    pass

    local_scrollbar = ttk.Scrollbar(local_tree_frame, orient='vertical', command=local_mods_tree.yview)
    local_mods_tree.configure(yscrollcommand=local_scrollbar.set)

    local_mods_tree.pack(side='left', fill='both', expand=True)
    local_scrollbar.pack(side='right', fill='y')

    load_local_mods()

    # Вкладка 2: Поиск на Modrinth
    modrinth_frame = ttk.Frame(notebook, padding=10)
    notebook.add(modrinth_frame, text="🌐 Modrinth")

    # Поиск
    search_frame = ttk.Frame(modrinth_frame)
    search_frame.pack(fill='x', pady=(0, 10))

    ttk.Label(search_frame, text="Поиск модов:").pack(side='left')
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side='left', padx=(5, 10))

    def search_modrinth():
        query = search_var.get().strip()
        if not query:
            messagebox.showwarning("Поиск", "Введите название мода")
            return

        # Показываем прогресс
        progress_window = tk.Toplevel(collection_window)
        progress_window.title("Поиск")
        progress_window.geometry("300x100")
        progress_window.transient(collection_window)
        progress_window.grab_set()

        ttk.Label(progress_window, text="Ищем моды на Modrinth...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, orient="horizontal", mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        def do_search():
            api = ModrinthAPI()
            results = api.search_mods(query)

            collection_window.after(0, progress_window.destroy)

            if results and 'hits' in results:
                collection_window.after(0, lambda: display_modrinth_results(results['hits']))
            else:
                collection_window.after(0, lambda: messagebox.showinfo("Результат", "Моды не найдены"))

        threading.Thread(target=do_search, daemon=True).start()

    def display_modrinth_results(mods):
        modrinth_tree.delete(*modrinth_tree.get_children())

        # Сортируем моды по количеству загрузок (по убыванию)
        sorted_mods = sorted(mods, key=lambda x: x.get('downloads', 0), reverse=True)

        for mod in sorted_mods:
            # Форматируем число загрузок с разделителями тысяч
            downloads = f"{mod.get('downloads', 0):,}"

            modrinth_tree.insert('', 'end',
                                 values=(mod['title'], mod['author'], downloads, mod['description']),
                                 tags=(mod['project_id'],))

    # Добавляем возможность сортировки по клику на заголовок
    def on_treeview_sort(col):
        """Функция для сортировки Treeview по столбцу"""
        global current_sort_col, current_sort_reverse

        # Получаем все элементы
        items = [(modrinth_tree.set(item, col), item) for item in modrinth_tree.get_children('')]

        # Определяем тип данных для сортировки
        if col == 'downloads':
            # Для загрузок преобразуем в числа (убираем разделители)
            items = [(int(item[0].replace(',', '')), item[1]) for item in items]
        else:
            # Для текстовых колонок оставляем как есть
            items = [(item[0].lower(), item[1]) for item in items]

        # Сортируем
        items.sort(reverse=current_sort_reverse)

        # Переставляем элементы в Treeview
        for index, (_, item) in enumerate(items):
            modrinth_tree.move(item, '', index)

        # Меняем направление сортировки для следующего клика
        current_sort_reverse = not current_sort_reverse

        # Обновляем заголовки для показа направления сортировки
        update_sort_indicators(col)

    def update_sort_indicators(sorted_col):
        """Обновляет заголовки для показа направления сортировки"""
        for col in modrinth_tree['columns']:
            current_text = modrinth_tree.heading(col)['text']
            # Убираем предыдущие индикаторы сортировки
            clean_text = current_text.replace(' ▲', '').replace(' ▼', '')

            if col == sorted_col:
                # Добавляем индикатор направления сортировки
                indicator = ' ▼' if current_sort_reverse else ' ▲'
                modrinth_tree.heading(col, text=clean_text + indicator)
            else:
                modrinth_tree.heading(col, text=clean_text)

    # Переменные для отслеживания сортировки
    current_sort_col = 'downloads'  # По умолчанию сортируем по загрузкам
    current_sort_reverse = False  # По убыванию (самые популярные сначала)

    ttk.Button(search_frame, text="🔍 Поиск", command=search_modrinth).pack(side='left', padx=(0, 10))

    # Список модов Modrinth
    modrinth_tree_frame = ttk.Frame(modrinth_frame)
    modrinth_tree_frame.pack(fill='both', expand=True)

    modrinth_tree = ttk.Treeview(modrinth_tree_frame,
                                 columns=('name', 'author', 'downloads', 'description'),
                                 show='headings', height=10)
    modrinth_tree.heading('name', text='Название')
    modrinth_tree.heading('author', text='Автор')
    modrinth_tree.heading('downloads', text='Загрузки')
    modrinth_tree.heading('description', text='Описание')

    # Привязываем клик по заголовкам к функции сортировки
    modrinth_tree.heading('name', text='Название', command=lambda: on_treeview_sort('name'))
    modrinth_tree.heading('author', text='Автор', command=lambda: on_treeview_sort('author'))
    modrinth_tree.heading('downloads', text='Загрузки', command=lambda: on_treeview_sort('downloads'))
    modrinth_tree.heading('description', text='Описание', command=lambda: on_treeview_sort('description'))

    modrinth_tree.column('name', width=200)
    modrinth_tree.column('author', width=120)
    modrinth_tree.column('downloads', width=100)  # Увеличим ширину для чисел
    modrinth_tree.column('description', width=280)

    modrinth_scrollbar = ttk.Scrollbar(modrinth_tree_frame, orient='vertical', command=modrinth_tree.yview)
    modrinth_tree.configure(yscrollcommand=modrinth_scrollbar.set)

    modrinth_tree.pack(side='left', fill='both', expand=True)
    modrinth_scrollbar.pack(side='right', fill='y')

    # Список выбранных модов
    selected_frame = ttk.LabelFrame(main_frame, text="✅ Выбранные моды", padding=10)
    selected_frame.pack(fill='x', pady=(0, 20))

    selected_tree = ttk.Treeview(selected_frame, columns=('source', 'name', 'file'), show='headings', height=4)
    selected_tree.heading('source', text='Источник')
    selected_tree.heading('name', text='Название')
    selected_tree.heading('file', text='Файл')

    selected_tree.column('source', width=80)
    selected_tree.column('name', width=250)
    selected_tree.column('file', width=200)

    selected_scrollbar = ttk.Scrollbar(selected_frame, orient='vertical', command=selected_tree.yview)
    selected_tree.configure(yscrollcommand=selected_scrollbar.set)

    selected_tree.pack(side='left', fill='both', expand=True)
    selected_scrollbar.pack(side='right', fill='y')

    # Кнопки управления выбранными модами
    selected_buttons = ttk.Frame(selected_frame)
    selected_buttons.pack(fill='x', pady=(10, 0))

    def add_selected_mods():
        current_tab = notebook.index(notebook.select())

        if current_tab == 0:  # Локальные моды
            for item in local_mods_tree.selection():
                values = local_mods_tree.item(item)['values']
                # Проверяем, нет ли уже такого мода
                existing = False
                for sel_item in selected_tree.get_children():
                    sel_values = selected_tree.item(sel_item)['values']
                    if sel_values[2] == values[1]:  # Сравниваем по имени файла
                        existing = True
                        break

                if not existing:
                    selected_tree.insert('', 'end',
                                         values=('Локальный', values[0], values[1]),
                                         tags=('local', values[1]))

        elif current_tab == 1:  # Modrinth
            for item in modrinth_tree.selection():
                values = modrinth_tree.item(item)['values']
                mod_id = modrinth_tree.item(item)['tags'][0]
                filename = f"{values[0]}.jar"

                # Проверяем, нет ли уже такого мода
                existing = False
                for sel_item in selected_tree.get_children():
                    sel_values = selected_tree.item(sel_item)['values']
                    if sel_values[1] == values[0]:  # Сравниваем по названию
                        existing = True
                        break

                if not existing:
                    selected_tree.insert('', 'end',
                                         values=('Modrinth', values[0], filename),
                                         tags=('modrinth', mod_id, filename))

    def remove_selected_mods():
        for item in selected_tree.selection():
            selected_tree.delete(item)

    def clear_all_mods():
        if selected_tree.get_children():
            if messagebox.askyesno("Подтверждение", "Очистить все выбранные моды?"):
                selected_tree.delete(*selected_tree.get_children())

    ttk.Button(selected_buttons, text="➕ Добавить выбранные",
               command=add_selected_mods, width=18).pack(side='left', padx=5)
    ttk.Button(selected_buttons, text="🗑️ Удалить выбранные",
               command=remove_selected_mods, width=18).pack(side='left', padx=5)
    ttk.Button(selected_buttons, text="🗑️ Очистить все",
               command=clear_all_mods, width=15).pack(side='left', padx=5)

    # Создание сборки
    def create_collection():
        name = name_var.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название сборки!")
            return

        # Собираем информацию о модах
        mods = []
        failed_mods = []

        # Окно прогресса для обработки модов
        progress_window = tk.Toplevel(collection_window)
        progress_window.title("Обработка модов")
        progress_window.geometry("500x300")
        progress_window.transient(collection_window)
        progress_window.grab_set()

        ttk.Label(progress_window, text="Получение информации о модах...", font=('Comfortaa', 12)).pack(pady=10)

        progress = ttk.Progressbar(progress_window, orient="horizontal", mode="determinate")
        progress.pack(fill='x', padx=20, pady=10)

        status_var = tk.StringVar(value="Подготовка...")
        status_label = ttk.Label(progress_window, textvariable=status_var)
        status_label.pack()

        log_text = tk.Text(progress_window, height=10, width=60)
        log_text.pack(fill='both', expand=True, padx=20, pady=10)

        def process_mods_thread():
            nonlocal mods, failed_mods

            api = ModrinthAPI()
            total_mods = len(selected_tree.get_children())

            for i, item in enumerate(selected_tree.get_children()):
                values = selected_tree.item(item)['values']
                tags = selected_tree.item(item)['tags']

                progress_window.after(0, lambda idx=i: progress.config(value=(idx * 100) // total_mods))
                progress_window.after(0, lambda v=values: status_var.set(f"Обработка: {v[1]}"))

                mod_info = {
                    'source': tags[0],
                    'name': values[1],
                    'filename': values[2]
                }

                if tags[0] == 'local':
                    # Для локальных модов ищем на Modrinth
                    progress_window.after(0, lambda: log_text.insert('end', f"🔍 Ищем на Modrinth: {values[1]}...\n"))
                    progress_window.after(0, lambda: log_text.see('end'))

                    modrinth_info = find_mod_on_modrinth(api, values[1], version_var.get(), loader_var.get())
                    if modrinth_info:
                        mod_info.update({
                            'source': 'modrinth',
                            'modrinth_id': modrinth_info['id'],
                            'modrinth_slug': modrinth_info['slug'],
                            'correct_filename': modrinth_info['filename']
                        })
                        mods.append(mod_info)
                        progress_window.after(0,
                                              lambda: log_text.insert('end', f"✅ Найден: {modrinth_info['title']}\n"))
                    else:
                        failed_mods.append(values[1])
                        progress_window.after(0,
                                              lambda: log_text.insert('end', f"❌ Не найден на Modrinth: {values[1]}\n"))

                elif tags[0] == 'modrinth':
                    # Для модов с Modrinth просто сохраняем информацию
                    mod_info['modrinth_id'] = tags[1]
                    mods.append(mod_info)
                    progress_window.after(0, lambda: log_text.insert('end', f"✅ Modrinth мод: {values[1]}\n"))

                progress_window.after(0, lambda: log_text.see('end'))

            # Завершаем обработку
            progress_window.after(0, progress_window.destroy)
            progress_window.after(0, lambda: finalize_collection_creation(name, mods, failed_mods))

        def finalize_collection_creation(name, mods, failed_mods):
            if not mods:
                messagebox.showerror("Ошибка", "Не удалось найти ни одного мода на Modrinth!")
                return

            # Показываем предупреждение о ненайденных модах
            if failed_mods:
                messagebox.showwarning("Внимание",
                                       f"Следующие моды не найдены на Modrinth и будут пропущены:\n" +
                                       "\n".join(failed_mods))

            # Создаем данные сборки
            collection_data = {
                'name': name,
                'minecraft_version': version_var.get(),
                'loader': loader_var.get(),
                'created_at': datetime.datetime.now().isoformat(),
                'mods': mods,
                'mod_count': len(mods)
            }

            # Сохраняем файл
            safe_name = "".join(c for c in name if c not in '/\\:*?"<>|')
            filename = f"{safe_name}.json"
            filepath = os.path.join(COLLECTIONS_CONFIG['collections_dir'], filename)

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(collection_data, f, indent=2, ensure_ascii=False)

                message = (f"Сборка '{name}' создана!\n\n"
                           f"• Модов: {len(mods)}\n"
                           f"• Версия: {version_var.get()}\n"
                           f"• Загрузчик: {loader_var.get()}")

                if failed_mods:
                    message += f"\n• Пропущено: {len(failed_mods)}"

                messagebox.showinfo("Успех", message)
                collection_window.destroy()
                show_collection_manager()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать сборку: {e}")

        threading.Thread(target=process_mods_thread, daemon=True).start()

    # Кнопки создания/отмены
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill='x')

    ttk.Button(button_frame, text="✅ Создать сборку",
               command=create_collection).pack(side='left', padx=5)
    ttk.Button(button_frame, text="❌ Отмена",
               command=collection_window.destroy).pack(side='right', padx=5)





def find_mod_on_modrinth(api, mod_name, minecraft_version, loader):
    """Улучшенный поиск модов на Modrinth"""
    try:
        print(f"🔍 Улучшенный поиск: '{mod_name}' для {minecraft_version} {loader}")

        # Более агрессивная очистка названия
        clean_name = aggressive_clean_name(mod_name)
        print(f"🧹 Очищенное название: '{clean_name}'")

        # Расширенный список поисковых запросов
        search_queries = generate_search_queries(mod_name, clean_name)
        print(f"📋 Запросы поиска: {search_queries[:5]}")  # Показываем первые 5

        # Пробуем найти по точному названию файла
        exact_match = try_find_by_filename(api, mod_name, minecraft_version, loader)
        if exact_match:
            return exact_match

        # Поиск по всем запросам
        for query in search_queries:
            if not query or len(query) < 2:
                continue

            print(f"🔎 Ищем: '{query}'")
            results = api.search_mods(query, limit=20)

            if not results or 'hits' not in results or not results['hits']:
                continue

            print(f"📦 Найдено результатов: {len(results['hits'])}")

            # Проверяем все результаты
            best_match = find_best_match(results['hits'], mod_name, clean_name,
                                         minecraft_version, loader, api)
            if best_match:
                return best_match

        # Последняя попытка: поиск по ключевым словам
        return try_keyword_search(api, mod_name, minecraft_version, loader)

    except Exception as e:
        print(f"💥 Ошибка поиска мода {mod_name}: {e}")
        return None


def aggressive_clean_name(mod_name):
    """Более агрессивная очистка названия мода"""
    import re

    # Удаляем версии, загрузчики и другие мусорные слова
    patterns_to_remove = [
        r'[\d\.\-_]+(?:fabric|forge|quilt|mc|minecraft)',
        r'\b(?:fabric|forge|quilt|mc|minecraft|mod|jar)\b',
        r'[\(\\)\[\]\{\}]',
        r'\s+'
    ]

    cleaned = mod_name.lower()
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)

    # Удаляем лишние пробелы и возвращаем
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Если после очистки ничего не осталось, используем оригинал
    return cleaned if cleaned else mod_name.lower()


def generate_search_queries(original_name, clean_name):
    """Генерирует расширенный список поисковых запросов"""
    queries = set()

    # Добавляем различные варианты
    variants = [
        clean_name,
        original_name,
        clean_name.replace(' ', ''),
        clean_name.replace(' ', '-'),
        clean_name.replace(' ', '_'),
        extract_core_name(original_name),
        remove_version_info(original_name),
        get_acronym(clean_name)
    ]

    # Добавляем отдельные слова из названия
    words = clean_name.split()
    for word in words:
        if len(word) > 3 and not word.isdigit():
            queries.add(word)

    # Добавляем комбинации слов
    if len(words) > 1:
        queries.add(' '.join(words[:2]))  # Первые два слова
        queries.add(' '.join(words[-2:]))  # Последние два слова

    # Фильтруем и возвращаем
    return [q for q in variants if q and len(q) > 1]


def extract_core_name(mod_name):
    """Извлекает ядро названия мода"""
    # Удаляем все, что выглядит как версия
    import re
    core = re.sub(r'[\d\.\-_]+.*$', '', mod_name)
    return core.strip()


def remove_version_info(mod_name):
    """Удаляет информацию о версии"""
    import re
    # Удаляем паттерны версий типа 1.2.3, 1.2.3+1.20.1 и т.д.
    cleaned = re.sub(r'[\d\.\-_]+\+?[\d\.\-_]*', '', mod_name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def get_acronym(mod_name):
    """Создает акроним из названия"""
    words = mod_name.split()
    if len(words) > 1:
        return ''.join(word[0].upper() for word in words if word)
    return ''


def try_find_by_filename(api, filename, minecraft_version, loader):
    """Пытается найти мод по точному имени файла"""
    try:
        # Извлекаем название из имени файла (без .jar и версии)
        base_name = filename.replace('.jar', '')

        # Удаляем информацию о версии и загрузчике
        clean_file_name = re.sub(r'[\d\.\-_]+(?:fabric|forge|quilt).*$', '', base_name)
        clean_file_name = re.sub(r'\s+', ' ', clean_file_name).strip()

        if len(clean_file_name) > 3:
            print(f"📁 Поиск по имени файла: '{clean_file_name}'")
            results = api.search_mods(clean_file_name, limit=10)

            if results and 'hits' in results and results['hits']:
                for mod in results['hits']:
                    similarity = calculate_similarity(mod['title'].lower(), clean_file_name.lower())
                    if similarity > 0.4:
                        versions = api.get_mod_versions(
                            mod['project_id'], minecraft_version, loader.lower()
                        )
                        if versions:
                            latest_version = versions[0]
                            file = latest_version['files'][0]
                            print(f"✅ Найден по имени файла: {mod['title']}")
                            return {
                                'id': mod['project_id'],
                                'slug': mod['slug'],
                                'title': mod['title'],
                                'filename': file['filename']
                            }
    except Exception as e:
        print(f"⚠️ Ошибка поиска по файлу: {e}")

    return None


def find_best_match(mods, original_name, clean_name, minecraft_version, loader, api):
    """Находит лучший совпадающий мод"""
    best_similarity = 0
    best_mod = None

    for mod in mods:
        mod_title = mod['title'].lower()

        # Вычисляем несколько метрик схожести
        similarity1 = calculate_similarity(mod_title, original_name.lower())
        similarity2 = calculate_similarity(mod_title, clean_name)
        similarity3 = calculate_word_overlap(mod_title, clean_name)

        # Общая схожесть (максимум из всех метрик)
        total_similarity = max(similarity1, similarity2, similarity3)

        print(f"  📊 '{mod['title']}' - схожесть: {total_similarity:.2f}")

        if total_similarity > best_similarity:
            # Проверяем поддержку версии
            versions = api.get_mod_versions(mod['project_id'], minecraft_version, loader.lower())
            if versions:
                best_similarity = total_similarity
                latest_version = versions[0]
                file = latest_version['files'][0]
                best_mod = {
                    'id': mod['project_id'],
                    'slug': mod['slug'],
                    'title': mod['title'],
                    'filename': file['filename']
                }

    # Понижаем порог для принятия решения
    if best_mod and best_similarity > 0.2:  # Был 0.6
        print(f"✅ Лучшее совпадение: {best_mod['title']} (схожесть: {best_similarity:.2f})")
        return best_mod

    return None


def calculate_word_overlap(str1, str2):
    """Вычисляет пересечение слов между строками"""
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())

    if not words1 or not words2:
        return 0.0

    common_words = words1.intersection(words2)
    return len(common_words) / min(len(words1), len(words2))


def try_keyword_search(api, mod_name, minecraft_version, loader):
    """Поиск по ключевым словам когда точный поиск не сработал"""
    print(f"🔍 Переходим к поиску по ключевым словам: {mod_name}")

    # Ключевые слова для специфичных модов
    keyword_map = {
        'appliedenergistics': 'applied energistics 2',
        'xaeros': 'xaero',
        'inventoryprofiles': 'inventory profiles next',
        'travelersbackpack': 'traveler backpack',
        'lambdynamiclights': 'lamb dynamic lights',
        'fallingleaves': 'falling leaves',
        'ironchests': 'iron chests',
        'techreborn': 'tech reborn',
        'reborncore': 'reborn core',
        'mavapi': 'more axolotl variants api',
        'mavm': 'more axolotl variants mod',
        'noindium': 'no indium'
    }

    # Проверяем по ключевым словам
    for key, search_term in keyword_map.items():
        if key in mod_name.lower():
            print(f"🔑 Используем ключевое слово: {search_term}")
            results = api.search_mods(search_term, limit=5)

            if results and 'hits' in results and results['hits']:
                mod = results['hits'][0]
                versions = api.get_mod_versions(mod['project_id'], minecraft_version, loader.lower())
                if versions:
                    latest_version = versions[0]
                    file = latest_version['files'][0]
                    print(f"✅ Найден по ключевому слову: {mod['title']}")
                    return {
                        'id': mod['project_id'],
                        'slug': mod['slug'],
                        'title': mod['title'],
                        'filename': file['filename']
                    }

    return None


MANUAL_MOD_MAPPINGS = {
    'appliedenergistics2 fabric 15.4.9': 'ae2',
    'xaeros minimap 25.2.10 fabric 1.20': 'xaeros-minimap',
    'xaerosworldmap 1.39.12 fabric 1.20': 'xaeros-world-map',
    'travelersbackpack fabric 1.20.1 9.1.41': 'travelers-backpack',
    'ironchests 5.0.2 fabric': 'iron-chests',
    'fallingleaves 1.15.6+1.20.1': 'falling-leaves',
    'lambdynamiclights 4.4.0+1.20.1': 'lambdynamiclights',
    'techreborn 5.8.3': 'techreborn',
    'reborncore 5.8.3': 'reborn-core',
    'inventoryprofilesnext fabric 1.20 1.10.19': 'inventory-profiles-next',
    'noindium 1.1.0+1.20': 'no-indium',
    'mavapi 1.1.4 mc1.20.1': 'more-axolotl-variants-api',
    'mavm 1.2.6 mc1.20.1': 'more-axolotl-variants-mod'
}


def try_manual_mapping(api, mod_name, minecraft_version, loader):
    """Пробует найти мод по ручным сопоставлениям"""
    clean_mod_name = mod_name.lower().strip()

    for key, slug in MANUAL_MOD_MAPPINGS.items():
        if key in clean_mod_name:
            print(f"🔧 Используем ручное сопоставление: {slug}")
            try:
                # Прямой запрос к API по slug
                project_url = f"{api.base_url}/project/{slug}"
                response = api.session.get(project_url)

                if response.status_code == 200:
                    project_data = response.json()
                    versions = api.get_mod_versions(
                        project_data['id'], minecraft_version, loader.lower()
                    )
                    if versions:
                        latest_version = versions[0]
                        file = latest_version['files'][0]
                        print(f"✅ Найден через ручное сопоставление: {project_data['title']}")
                        return {
                            'id': project_data['id'],
                            'slug': project_data['slug'],
                            'title': project_data['title'],
                            'filename': file['filename']
                        }
            except Exception as e:
                print(f"⚠️ Ошибка ручного сопоставления: {e}")

    return None

def clean_mod_name(mod_name):
    """Очищает название мода от версий и лишних частей"""
    # Удаляем версии типа 1.20.1, 1.19.2 и т.д.
    import re
    cleaned = re.sub(r'[\d\.\-_]+(?:fabric|forge|quilt)?', ' ', mod_name, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:fabric|forge|quilt|mc|minecraft|mod)\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Если после очистки ничего не осталось, возвращаем оригинал
    return cleaned if cleaned else mod_name


def extract_main_words(mod_name):
    """Извлекает основные слова из названия"""
    words = mod_name.split()
    # Оставляем только слова длиной > 3 символов и не являющиеся версиями
    main_words = [word for word in words if len(word) > 3 and not re.match(r'^[\d\.\-_]+$', word)]
    return ' '.join(main_words[:3])  # Берем до 3 слов


def calculate_similarity(str1, str2):
    """Вычисляет схожесть между двумя строками"""
    # Простой алгоритм схожести
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
COLLECTIONS_CONFIG = {
    'collections_dir': os.path.join(os.path.expanduser('~'), 'YamalPixel', 'collections')
}
# Функция показа менеджера сборок
def show_collection_manager():
    manager_window = tk.Toplevel(win)
    manager_window.title("Менеджер  (Бета)")
    manager_window.geometry("1000x500")
    manager_window.transient(win)
    manager_window.grab_set()

    main_frame = ttk.Frame(manager_window, padding=20)
    main_frame.pack(fill='both', expand=True)

    ttk.Label(main_frame, text="📦 Менеджер сборок модов", font=('Comfortaa', 16, 'bold')).pack(pady=(0, 20))

    # Информация о папке
    collections_dir = COLLECTIONS_CONFIG['collections_dir']
    info_label = ttk.Label(main_frame, text=f"Папка: {collections_dir}", foreground='gray')
    info_label.pack(pady=(0, 10))

    # Список сборок
    tree = ttk.Treeview(main_frame, columns=('name', 'version', 'loader', 'mods', 'created'), show='headings')
    tree.heading('name', text='Название')
    tree.heading('version', text='Версия')
    tree.heading('loader', text='Загрузчик')
    tree.heading('mods', text='Модов')
    tree.heading('created', text='Создана')

    tree.column('name', width=200)
    tree.column('version', width=100)
    tree.column('loader', width=80)
    tree.column('mods', width=60)
    tree.column('created', width=100)

    # Статус сборок
    status_var = tk.StringVar(value="Загрузка...")
    status_label = ttk.Label(main_frame, textvariable=status_var, foreground='blue')
    status_label.pack(pady=5)

    def load_collections():
        tree.delete(*tree.get_children())
        collections_dir = COLLECTIONS_CONFIG['collections_dir']

        if not os.path.exists(collections_dir):
            status_var.set("Папка сборок не существует!")
            return

        try:
            files = os.listdir(collections_dir)
            json_files = [f for f in files if f.endswith('.json')]
            status_var.set(f"Найдено сборок: {len(json_files)}")

            for file in json_files:
                filepath = os.path.join(collections_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Проверяем структуру данных
                    if all(field in data for field in
                           ['name', 'minecraft_version', 'loader', 'mod_count', 'created_at']):
                        created = datetime.datetime.fromisoformat(data['created_at']).strftime("%d.%m.%Y")
                        tree.insert('', 'end',
                                    values=(data['name'], data['minecraft_version'], data['loader'],
                                            data['mod_count'], created),
                                    tags=(file,))
                    else:
                        print(f"Неполные данные в файле {file}")

                except Exception as e:
                    print(f"Ошибка загрузки {file}: {e}")

        except Exception as e:
            status_var.set(f"Ошибка: {e}")

    tree.pack(fill='both', expand=True)
    load_collections()

    # Кнопки управления
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill='x', pady=10)

    def refresh_collections():
        status_var.set("Обновление...")
        load_collections()

    def open_collections_folder():
        os.makedirs(COLLECTIONS_CONFIG['collections_dir'], exist_ok=True)
        if os.name == 'nt':
            os.startfile(COLLECTIONS_CONFIG['collections_dir'])
        else:
            subprocess.Popen(['xdg-open', COLLECTIONS_CONFIG['collections_dir']])

    def load_to_game():
        selection = tree.selection()
        if selection:
            filename = tree.item(selection[0])['tags'][0]
            load_collection_to_game(filename)
        else:
            messagebox.showwarning("Выбор", "Выберите сборку для загрузки")

    def delete_collection():
        selection = tree.selection()
        if selection:
            filename = tree.item(selection[0])['tags'][0]
            filepath = os.path.join(COLLECTIONS_CONFIG['collections_dir'], filename)
            if messagebox.askyesno("Подтверждение", "Удалить сборку?"):
                try:
                    os.remove(filepath)
                    load_collections()
                    messagebox.showinfo("Успех", "Сборка удалена")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    ttk.Button(button_frame, text="🔄 Обновить", command=refresh_collections).pack(side='left', padx=5)
    ttk.Button(button_frame, text="📁 Открыть папку", command=open_collections_folder).pack(side='left', padx=5)
    ttk.Button(button_frame, text="🎮 Загрузить в игру", command=load_to_game).pack(side='left', padx=5)
    ttk.Button(button_frame, text="🗑️ Удалить", command=delete_collection).pack(side='left', padx=5)
    ttk.Button(button_frame, text="➕ Новая сборка",
               command=lambda: (manager_window.destroy(), create_new_collection())).pack(side='right', padx=5)
    ttk.Button(button_frame, text="❌ Закрыть", command=manager_window.destroy).pack(side='right', padx=5)


# Функция загрузки сборки в игру
def load_collection_to_game(filename):
    filepath = os.path.join(COLLECTIONS_CONFIG['collections_dir'], filename)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            collection = json.load(f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить сборку: {e}")
        return

    # Создаем окно прогресса с логом
    progress_window = tk.Toplevel(win)
    progress_window.title(f"Загрузка сборки: {collection['name']}")
    progress_window.geometry("700x500")
    progress_window.transient(win)
    progress_window.grab_set()

    main_frame = ttk.Frame(progress_window, padding=15)
    main_frame.pack(fill='both', expand=True)

    ttk.Label(main_frame, text=f"📦 Загрузка сборки: {collection['name']}",
              font=('Comfortaa', 14, 'bold')).pack(pady=(0, 10))

    # Информация о сборке
    info_text = f"Версия: {collection['minecraft_version']} | Загрузчик: {collection['loader']} | Модов: {collection['mod_count']}"
    ttk.Label(main_frame, text=info_text).pack(pady=(0, 15))

    # Прогресс-бар
    progress = ttk.Progressbar(main_frame, orient="horizontal", length=600, mode="determinate")
    progress.pack(fill='x', pady=5)

    # Статус и счетчик
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill='x', pady=5)

    status_var = tk.StringVar(value="Подготовка...")
    status_label = ttk.Label(status_frame, textvariable=status_var, font=('Comfortaa', 10))
    status_label.pack(side='left')

    counter_var = tk.StringVar(value="0/0")
    counter_label = ttk.Label(status_frame, textvariable=counter_var, font=('Comfortaa', 10))
    counter_label.pack(side='right')

    # Детальный лог
    log_frame = ttk.LabelFrame(main_frame, text="Детальный лог загрузки", padding=10)
    log_frame.pack(fill='both', expand=True, pady=(10, 0))

    log_text = tk.Text(log_frame, height=15, width=80, font=('Consolas', 9))
    log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=log_text.yview)
    log_text.configure(yscrollcommand=log_scrollbar.set)

    log_text.pack(side='left', fill='both', expand=True)
    log_scrollbar.pack(side='right', fill='y')

    def log_message(message):
        win.after(0, lambda: log_text.insert('end', f"{message}\n"))
        win.after(0, lambda: log_text.see('end'))

    def download_thread():
        mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
        os.makedirs(mods_dir, exist_ok=True)

        log_message(f"📁 Папка модов: {mods_dir}")
        log_message(f"🔄 Начинаем загрузку {len(collection['mods'])} модов...")

        # Бэкап и очистка
        backup_path = create_mods_backup(collection['name'])
        if backup_path:
            log_message(f"📂 Создан бэкап: {os.path.basename(backup_path)}")

        cleared_count = clear_mods_directory(mods_dir)
        log_message(f"🗑️ Очищено модов: {cleared_count}")

        # Скачиваем моды
        success_count = 0
        total_mods = len(collection['mods'])
        api = ModrinthAPI()

        for i, mod in enumerate(collection['mods']):
            # Обновляем UI
            win.after(0, lambda idx=i, total=total_mods: progress.config(value=(idx * 100) // total))
            win.after(0, lambda m=mod: status_var.set(f"Загрузка: {m['name']}"))
            win.after(0, lambda s=success_count, t=total_mods: counter_var.set(f"{s}/{t}"))

            log_message(f"\n🔍 Мод {i + 1}/{total_mods}: {mod['name']}")

            if mod['source'] == 'modrinth':
                log_message(f"   📡 Источник: Modrinth (ID: {mod.get('modrinth_id', 'N/A')})")

                # Получаем версии мода
                versions = api.get_mod_versions(
                    mod['modrinth_id'],
                    collection['minecraft_version'],
                    collection['loader'].lower()
                )

                if not versions:
                    log_message("   ❌ Не найдены версии мода")
                    continue

                log_message(f"   📦 Найдено версий: {len(versions)}")

                # Берем последнюю версию
                latest_version = versions[0]

                # Находим primary файл или первый JAR файл
                target_file = None
                for file_info in latest_version['files']:
                    if file_info.get('primary', False) or file_info['filename'].endswith('.jar'):
                        target_file = file_info
                        break

                if not target_file and latest_version['files']:
                    target_file = latest_version['files'][0]  # Берем первый файл, если нет primary

                if not target_file:
                    log_message("   ❌ Не найден файл для скачивания")
                    continue

                filename = target_file['filename']
                version_id = latest_version['id']
                project_slug = mod.get('modrinth_slug', mod['modrinth_id'])

                log_message(f"   ⬇️  Скачиваем: {filename}")
                log_message(f"   🔗 Project: {project_slug}")
                log_message(f"   🆔 Version: {version_id}")

                # Скачиваем мод
                if api.download_mod(project_slug, version_id, filename, mods_dir):
                    success_count += 1
                    log_message("   ✅ Успешно скачан")
                else:
                    log_message("   ❌ Ошибка скачивания")
            else:
                log_message(f"   ⚠️  Неподдерживаемый источник: {mod['source']}")

        # Завершение
        log_message(f"\n🎉 ЗАВЕРШЕНО! Успешно: {success_count}/{total_mods}")
        win.after(0, lambda: finish_loading(progress_window, collection, success_count, total_mods, backup_path))

    def show_download_result(collection, success_count, total_mods, backup_path):
        message = (f"Загрузка сборки '{collection['name']}' завершена!\n\n"
                   f"✅ Успешно загружено: {success_count}/{total_mods} модов")

        if backup_path:
            message += f"\n\n📂 Создан бэкап предыдущих модов"

        if success_count == 0:
            message += "\n\n❌ Не удалось загрузить ни одного мода!\nПроверьте подключение к интернету и логи."
        elif success_count < total_mods:
            message += f"\n\n⚠️  Не загружено {total_mods - success_count} модов\nПроверьте детальный лог для информации."

        messagebox.showinfo("Результат загрузки", message)

    threading.Thread(target=download_thread, daemon=True).start()


# Добавляем в меню
settings_menu.add_separator()
settings_menu.add_command(label="📦 Сборки модов (Бета)", command=show_collection_manager)


def create_mods_backup(collection_name):
    """Создание бэкапа модов"""
    mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
    backup_dir = os.path.join(CONFIG['minecraft_dir'], 'mods_backup')
    os.makedirs(backup_dir, exist_ok=True)

    if os.path.exists(mods_dir) and any(f.endswith('.jar') for f in os.listdir(mods_dir)):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{collection_name}_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)
        try:
            shutil.copytree(mods_dir, backup_path)
            return backup_path
        except Exception as e:
            print(f"Ошибка бэкапа: {e}")
    return None


def clear_mods_directory(mods_dir):
    """Очистка папки модов"""
    count = 0
    if os.path.exists(mods_dir):
        for file in os.listdir(mods_dir):
            if file.endswith('.jar'):
                try:
                    os.remove(os.path.join(mods_dir, file))
                    count += 1
                except Exception as e:
                    print(f"Не удалось удалить {file}: {e}")
    return count


def handle_local_mod(mod, mods_dir):
    """Обработка локального мода"""
    # Пробуем найти файл в нескольких местах
    possible_paths = [
        os.path.join(CONFIG['minecraft_dir'], 'mods', mod['filename']),
        os.path.join(COLLECTIONS_CONFIG['collections_dir'], 'mods', mod['filename']),
        os.path.join(os.path.dirname(CONFIG['minecraft_dir']), 'mods', mod['filename'])
    ]

    for src_path in possible_paths:
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, os.path.join(mods_dir, mod['filename']))
                return True
            except Exception as e:
                print(f"Ошибка копирования {src_path}: {e}")

    print(f"Локальный файл не найден: {mod['filename']}")
    return False


def handle_modrinth_mod(mod, collection, api, mods_dir, log_callback):
    """Обработка мода с Modrinth с правильным скачиванием"""
    try:
        log_callback(f"🔍 Получаем информацию о {mod['name']}...")

        versions = api.get_mod_versions(
            mod['modrinth_id'],
            collection['minecraft_version'],
            collection['loader'].lower()
        )

        if not versions:
            log_callback(f"❌ Не найдены версии для {mod['name']}")
            return False

        # Выбираем последнюю версию
        latest_version = versions[0]
        version_id = latest_version['id']

        if 'files' not in latest_version or not latest_version['files']:
            log_callback(f"❌ Нет информации о файлах для {mod['name']}")
            return False

        file_info = latest_version['files'][0]
        filename = file_info['filename']

        # Получаем slug проекта для скачивания
        project_slug = mod.get('modrinth_slug') or mod['modrinth_id']

        log_callback(f"📥 Скачиваем {filename}...")
        log_callback(f"🆔 Version ID: {version_id}")
        log_callback(f"🔗 Project: {project_slug}")

        # Скачиваем мод
        if api.download_mod(project_slug, version_id, filename, mods_dir):
            log_callback(f"✅ Успешно скачан: {filename}")
            return True
        else:
            # Пробуем через прямой URL из file_info
            if 'url' in file_info and file_info['url']:
                log_callback(f"🔄 Пробуем прямую ссылку...")
                direct_url = file_info['url']
                try:
                    response = api.session.get(direct_url, timeout=30, stream=True)
                    response.raise_for_status()

                    filepath = os.path.join(mods_dir, filename)
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    log_callback(f"✅ Успешно скачан (прямая ссылка): {filename}")
                    return True
                except Exception as e:
                    log_callback(f"❌ Ошибка прямой ссылки: {str(e)}")

            log_callback(f"❌ Не удалось скачать: {filename}")
            return False

    except Exception as e:
        log_callback(f"💥 Критическая ошибка {mod['name']}: {str(e)}")
        return False


def finish_loading(progress_window, collection, success_count, total_mods, backup_path):
    """Завершение загрузки"""
    progress_window.destroy()

    message = (f"Сборка '{collection['name']}' загружена!\n\n"
               f"✅ Успешно: {success_count}/{total_mods} модов")

    if backup_path:
        message += f"\n\n📂 Бэкап создан: {os.path.basename(backup_path)}"

    if success_count < total_mods:
        message += "\n\n⚠️ Некоторые моды не удалось загрузить. Проверьте лог для деталей."

    messagebox.showinfo("Загрузка завершена", message)


import signal
import sys


def graceful_shutdown(signum, frame):
    """Красивое завершение работы"""
    print("\n🎮 Закрываем лаунчер...")

    # Останавливаем музыку
    try:
        mixer.music.stop()
    except:
        pass

    # Сохраняем настройки
    try:
        save_last_session()
    except:
        pass

    # Закрываем окно
    try:
        win.quit()
        win.destroy()
    except:
        pass

    sys.exit(0)


# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, graceful_shutdown)  # Ctrl+C
signal.signal(signal.SIGTERM, graceful_shutdown)  # Завершение процесса


# Добавь обработчик закрытия окна
def on_closing():
    """При закрытии окна"""
    print("💾 Сохраняем настройки и выходим...")
    save_last_session()

    # Останавливаем музыку
    try:
        mixer.music.stop()
    except:
        pass

    win.destroy()
    sys.exit(0)


# Вешаем обработчик
win.protocol("WM_DELETE_WINDOW", on_closing)


# Добавь защиту от KeyboardInterrupt в mainloop
def safe_mainloop():
    """Безопасный mainloop с обработкой прерываний"""
    try:
        win.mainloop()
    except KeyboardInterrupt:
        on_closing()
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)
# Запуск главного цикла
if __name__ == "__main__":
    safe_mainloop()
import json
from pathlib import Path

# Папка для файла состояния
JAVA_STATE_FILE = Path.home() / "YamalPixelRes" / "java_state.json"

# Создаем папку если не существует
JAVA_STATE_FILE.parent.mkdir(exist_ok=True)


def load_java_state():
    """Загружает состояние установки Java из файла"""
    try:
        if JAVA_STATE_FILE.exists():
            with open(JAVA_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                return state.get('java_installed', False)
        return False
    except Exception as e:
        print(f"Ошибка чтения файла состояния Java: {e}")
        return False


def save_java_state(installed=True):
    """Сохраняет состояние установки Java в файл"""
    try:
        state = {
            'java_installed': installed,
            'last_check': datetime.now().isoformat(),
            'version': CURRENT_VERSION
        }
        with open(JAVA_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        print(f"✅ Состояние Java сохранено: {'установлена' if installed else 'не установлена'}")
    except Exception as e:
        print(f"❌ Ошибка сохранения файла состояния Java: {e}")


def should_skip_java_check():
    """Проверяет, нужно ли пропускать проверку Java"""
    return load_java_state()


def check_java_version_simple():
    """
    Упрощенная проверка Java с системой пропуска
    """
    # Если ранее уже устанавливали Java - пропускаем проверку
    if should_skip_java_check():
        print("✅ Проверка Java пропущена (ранее уже устанавливали)")
        return True

    print("🔍 Проверяем установленную Java...")

    try:
        # Используем твою существующую функцию проверки
        return check_java_version()

    except Exception as e:
        print(f"❌ Ошибка проверки Java: {e}")
        return False


def initial_check_simple():
    """
    Упрощенная начальная проверка с системой пропуска
    """
    print("🎯 Запускаем проверку системы...")

    # Если ранее уже устанавливали Java - просто сообщаем и пропускаем
    if should_skip_java_check():
        print("✅ Java ранее уже устанавливалась - проверка пропущена")
        return True

    # Используем твою существующую проверку Java
    if not check_java_version():
        print("❌ Java 17 не найдена")

        # Показываем простое окно выбора
        choice = messagebox.askyesno(
            "Требуется Java 17",
            "Для работы лаунчера нужна Java 17.\n\n"
            "Установить её автоматически?\n\n"
            "Если вы уже устанавливали Java, нажмите 'Нет'",
            icon='info'
        )

        if choice:
            # Используем твою существующую установку Java
            install_java_with_progress()

            # После установки проверяем еще раз
            if check_java_version():
                save_java_state(True)  # Сохраняем что установили
                return True
            else:
                return False
        else:
            # Пользователь отказался - предлагаем пропустить навсегда
            skip_forever = messagebox.askyesno(
                "Пропустить проверку Java",
                "Пропускать проверку Java в будущем?\n\n"
                "Вы сможете сбросить это в настройках.",
                icon='question'
            )
            if skip_forever:
                save_java_state(True)  # Сохраняем как "установлено" чтобы больше не проверять
            return True
    else:
        print("✅ Правильная версия Java установлена")
        save_java_state(True)  # Сохраняем что Java уже установлена
        return True


def reset_java_state():
    """Сбрасывает файл состояния Java (для исправления проблем)"""
    try:
        if JAVA_STATE_FILE.exists():
            JAVA_STATE_FILE.unlink()
            messagebox.showinfo("Сброс", "Файл состояния Java сброшен. Проверка будет выполняться снова.")
        else:
            messagebox.showinfo("Информация", "Файл состояния Java не найден.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сбросить состояние: {e}")


def check_java_now():
    """Принудительная проверка Java"""
    if check_java_version():
        messagebox.showinfo("Java", "✅ Java установлена и работает правильно!")
    else:
        messagebox.showwarning("Java", "❌ Java не найдена или устаревшая версия!")


def add_java_tools_to_menu():
    """Добавляет инструменты Java в меню"""
    # Добавляем в существующее меню "Инструменты"
    settings_menu.add_separator()
    settings_menu.add_command(label="🔄 Сбросить проверку Java", command=reset_java_state)
    settings_menu.add_command(label="ℹ️ Проверить Java сейчас", command=check_java_now)

win.after(100, initial_check_simple)


win.after(300, add_java_tools_to_menu)