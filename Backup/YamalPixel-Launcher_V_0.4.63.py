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


#Пишется при помощи DeepSeek, каждый может сделать тоже самое хоть немного зная python!!!
CURRENT_VERSION = "0.4.63" #обновление
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

    async def get_turbo_link(self, public_key):
        """Быстрое получение ссылки через асинхронность"""
        if public_key in self.cache:
            return self.cache[public_key]

        api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(api_url, params={"public_key": public_key}) as response:
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
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    total_size = int(response.headers.get('content-length', 0))

                    with open(file_path, 'wb') as f:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(8192 * 8):  # Ещё больше буфер
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
        return asyncio.run(self.download_file_async(url, file_path, progress_callback))


# 🔥 ОБНОВЛЕННЫЕ ФУНКЦИИ ДЛЯ МОДОВ:

def download_single_mod_turbo(mod_info):
    """Турбо-загрузка одного мода"""
    try:
        downloader = TurboDownloader()

        # Получаем прямую ссылку
        direct_link = asyncio.run(downloader.get_turbo_link(mod_info['url']))
        if not direct_link:
            logging.error(f"Не удалось получить ссылку для {mod_info['file']}")
            return False

        # Путь для сохранения
        mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
        os.makedirs(mods_dir, exist_ok=True)
        file_path = os.path.join(mods_dir, mod_info['file'])

        # Загружаем файл
        success = downloader.download_file_sync(direct_link, file_path)

        if success and mod_info['file'].endswith('.zip'):
            # Распаковываем ZIP
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(mods_dir)
                logging.info(f"Мод распакован: {mod_info['file']}")
            except Exception as e:
                logging.error(f"Ошибка распаковки {mod_info['file']}: {e}")

        return success

    except Exception as e:
        logging.error(f"Ошибка загрузки мода {mod_info['file']}: {e}")
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
    """Тест скорости загрузки с исправлениями"""
    try:
        # Список альтернативных серверов для теста скорости
        test_servers = [
            "https://proof.ovh.net/files/100Mb.dat",  # Основной
            "http://ipv4.download.thinkbroadband.com/100MB.zip",  # Резервный (HTTP)
            "https://ash-speed.hetzner.com/100MB.bin"  # Альтернативный Hetzner
        ]

        # Пробуем серверы по порядку
        for test_url in test_servers:
            try:
                # Быстрая проверка доступности сервера
                response = requests.head(test_url, timeout=5)
                if response.status_code == 200:
                    break  # Сервер доступен, используем его
            except:
                continue  # Пробуем следующий сервер
        else:
            # Если все серверы недоступны
            messagebox.showerror("Ошибка", "Все серверы для теста скорости недоступны")
            return

        test_file = "test_speed.bin"
        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        progress_window.title("Тест скорости")
        progress_window.geometry("300x120")

        progress_label = ttk.Label(progress_window, text="Тестирование скорости...")
        progress_label.pack(pady=10)

        progress = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        status_label = ttk.Label(progress_window, text="Подготовка...")
        status_label.pack()

        def test_thread():
            try:
                start_time = time.time()

                # Используем requests для надежности
                response = requests.get(test_url, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(test_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192 * 8):  # Большой чанк для скорости
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Обновляем прогресс
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                win.after(0, lambda: status_label.config(
                                    text=f"Скачано: {downloaded // 1024 // 1024}MB/{total_size // 1024 // 1024}MB"
                                ))

                end_time = time.time()

                # Расчет скорости
                if os.path.exists(test_file):
                    file_size_mb = os.path.getsize(test_file) / 1024 / 1024
                    time_seconds = end_time - start_time
                    speed_mbps = file_size_mb / time_seconds

                    # Очистка
                    os.remove(test_file)

                    # Показываем результат
                    win.after(0, lambda: show_speed_result(speed_mbps, progress_window))
                else:
                    win.after(0, lambda: show_speed_error("Файл не был скачан", progress_window))

            except Exception as e:
                win.after(0, lambda: show_speed_error(str(e), progress_window))
                # Очистка при ошибке
                if os.path.exists(test_file):
                    os.remove(test_file)

        def show_speed_result(speed, window):
            window.destroy()
            messagebox.showinfo(
                "Результат теста скорости",
                f"📊 Ваша скорость загрузки:\n\n"
                f"🚀 {speed:.2f} MB/сек\n"
                f"💨 {speed * 8:.2f} Mbit/сек\n\n"
                f"Для сравнения:\n"
                f"• 1-5 MB/сек - Медленно\n"
                f"• 5-10 MB/сек - Нормально\n"
                f"• 10-20 MB/сек - Быстро\n"
                f"• 20+ MB/сек - Очень быстро"
            )

        def show_speed_error(error, window):
            window.destroy()
            messagebox.showerror("Ошибка теста", f"Не удалось измерить скорость:\n{error}")

        threading.Thread(target=test_thread, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка запуска теста: {str(e)}")





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
    shaders_window.geometry("700x550")
    shaders_window.resizable(True, True)
    shaders_window.transient(win)
    shaders_window.grab_set()

    # Центрируем окно
    shaders_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (700 // 2)
    y = (win.winfo_screenheight() // 2) - (550 // 2)
    shaders_window.geometry(f"700x550+{x}+{y}")

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
               command=download_selected, style="Accent.TButton").pack(side='left', padx=5)
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


def auto_repair_game_files(silent=False):
    global LAUNCH_IN_PROGRESS

    # Проверяем, не запущена ли игра
    if LAUNCH_IN_PROGRESS:
        if not silent:
            messagebox.showwarning(
                "Запуск в процессе",
                "❌ Нельзя чинить файлы во время запуска игры!\n\n"
                "Дождитесь завершения запуска игры, затем повторите попытку."
            )
        return False

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

    # Кнопка отмены
    cancel_btn = ttk.Button(main_frame, text="❌ Отменить починку",
                            state='disabled')  # Пока отключена
    cancel_btn.pack(pady=10)

    issues_found = []
    fixes_applied = []

    def repair_thread():
        nonlocal issues_found, fixes_applied

        try:
            minecraft_dir = CONFIG['minecraft_dir']
            mods_dir = os.path.join(minecraft_dir, 'mods')
            versions_dir = os.path.join(minecraft_dir, 'versions')
            config_dir = os.path.join(minecraft_dir, 'config')

            win.after(0, lambda: status_label.config(text="Проверка папок..."))
            win.after(0, lambda: details_label.config(text="Проверяем структуру папок"))
            progress['value'] = 10

            # Проверяем наличие основных папок
            if not os.path.exists(mods_dir):
                issues_found.append("Папка mods отсутствует")
                add_log("❌ Папка mods отсутствует", 'red')
                os.makedirs(mods_dir, exist_ok=True)
                fixes_applied.append("Создана папка mods")
                add_log("✅ Создана папка mods", 'green')

            if not os.path.exists(versions_dir):
                issues_found.append("Папка versions отсутствует")
                add_log("❌ Папка versions отсутствует", 'red')
                os.makedirs(versions_dir, exist_ok=True)
                fixes_applied.append("Создана папка versions")
                add_log("✅ Создана папка versions", 'green')

            if not os.path.exists(config_dir):
                issues_found.append("Папка config отсутствует")
                add_log("❌ Папка config отсутствует", 'red')
                os.makedirs(config_dir, exist_ok=True)
                fixes_applied.append("Создана папка config")
                add_log("✅ Создана папка config", 'green')

            progress['value'] = 30
            win.after(0, lambda: status_label.config(text="Проверка servers.dat..."))
            win.after(0, lambda: details_label.config(text="Проверяем файл серверов"))

            # Проверяем servers.dat
            servers_file = os.path.join(minecraft_dir, 'servers.dat')
            if not os.path.exists(servers_file):
                issues_found.append("Файл servers.dat отсутствует")
                add_log("❌ Файл servers.dat отсутствует", 'red')
                try:
                    # Восстанавливаем servers.dat
                    params = {'public_key': 'https://disk.yandex.ru/d/WM_flS--BathOQ'}
                    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
                    response = requests.get(base_url, params=params)
                    download_url = response.json().get('href')

                    if download_url:
                        with open(servers_file, 'wb') as f:
                            dl_response = requests.get(download_url, stream=True)
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        fixes_applied.append("Восстановлен файл servers.dat")
                        add_log("✅ Восстановлен файл servers.dat", 'green')
                except Exception as e:
                    add_log(f"⚠️ Не удалось восстановить servers.dat: {str(e)}", 'orange')

            progress['value'] = 50
            win.after(0, lambda: status_label.config(text="Проверка модов..."))
            win.after(0, lambda: details_label.config(text="Проверяем основные моды"))

            # 🔥 ВАЖНОЕ ИЗМЕНЕНИЕ: ВСЕГДА ПРОВЕРЯЕМ И ЗАГРУЖАЕМ ОТСУТСТВУЮЩИЕ МОДЫ
            mods_dir_path = os.path.join(minecraft_dir, 'mods')
            base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'

            # Считаем общее количество модов для прогресса
            total_mods = len(CONFIG['mods'])
            missing_mods = []
            existing_mods = []

            # Сначала проверяем какие моды отсутствуют
            for i, mod in enumerate(CONFIG['mods']):
                mod_path = os.path.join(mods_dir_path, mod['file'])
                if not os.path.exists(mod_path):
                    missing_mods.append(mod)
                else:
                    existing_mods.append(mod['file'])

            # Логируем что нашли
            if existing_mods:
                add_log(f"📁 Найдено модов: {len(existing_mods)}", 'green')
                if len(existing_mods) <= 5:  # Показываем только первые 5
                    for mod_file in existing_mods:
                        add_log(f"   ✅ {mod_file}", 'green')

            if missing_mods:
                issues_found.append(f"Отсутствуют {len(missing_mods)} модов")
                add_log(f"❌ Отсутствует модов: {len(missing_mods)}", 'red')

                # ВСЕГДА загружаем отсутствующие моды, независимо от silent режима
                for i, mod in enumerate(missing_mods):
                    try:
                        win.after(0, lambda: details_label.config(
                            text=f"Загружаем мод: {mod['file']} ({i + 1}/{len(missing_mods)})"
                        ))

                        # Обновляем прогресс
                        current_progress = 50 + (i * 30 / len(missing_mods))
                        progress['value'] = current_progress

                        params = {'public_key': mod['url']}
                        response = requests.get(base_url, params=params)
                        response.raise_for_status()
                        download_url = response.json().get('href')

                        if download_url:
                            mod_path = os.path.join(mods_dir_path, mod['file'])
                            with open(mod_path, 'wb') as f:
                                dl_response = requests.get(download_url, stream=True)
                                dl_response.raise_for_status()
                                total_size = int(dl_response.headers.get('content-length', 0))
                                downloaded = 0

                                for chunk in dl_response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)

                            # Распаковываем ZIP если нужно
                            if mod['file'].endswith('.zip'):
                                try:
                                    with zipfile.ZipFile(mod_path, 'r') as zip_file:
                                        zip_file.extractall(path=mods_dir_path)
                                    fixes_applied.append(f"Загружен и распакован {mod['file']}")
                                    add_log(f"✅ Загружен и распакован {mod['file']}", 'green')
                                except Exception as e:
                                    fixes_applied.append(f"Загружен {mod['file']} (ошибка распаковки)")
                                    add_log(f"⚠️ Загружен {mod['file']} (ошибка распаковки: {e})", 'orange')
                            else:
                                fixes_applied.append(f"Загружен {mod['file']}")
                                add_log(f"✅ Загружен {mod['file']}", 'green')

                    except Exception as e:
                        add_log(f"❌ Ошибка загрузки мода {mod['file']}: {str(e)}", 'red')

            elif not os.path.exists(mods_dir) or not os.listdir(mods_dir):
                # Старая логика для полностью пустой папки
                issues_found.append("Папка mods пустая")
                add_log("❌ Папка mods пустая", 'red')
                # ... (старый код загрузки всех модов)

            progress['value'] = 80
            win.after(0, lambda: status_label.config(text="Проверка Fabric..."))
            win.after(0, lambda: details_label.config(text="Проверяем установку Fabric"))

            # Проверяем Fabric
            fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
            fabric_version_dir = os.path.join(versions_dir, fabric_version)
            if not os.path.exists(fabric_version_dir):
                issues_found.append("Fabric не установлен")
                add_log("❌ Fabric не установлен", 'red')
                try:
                    minecraft_launcher_lib.fabric.install_fabric(
                        minecraft_version=CONFIG['version'],
                        loader_version=CONFIG['fabric_loader'],
                        minecraft_directory=CONFIG['minecraft_dir']
                    )
                    fixes_applied.append("Установлен Fabric")
                    add_log("✅ Установлен Fabric", 'green')
                except Exception as e:
                    add_log(f"❌ Ошибка установки Fabric: {str(e)}", 'red')

            progress['value'] = 90
            win.after(0, lambda: status_label.config(text="Проверка Minecraft..."))
            win.after(0, lambda: details_label.config(text="Проверяем версию Minecraft"))

            # Проверяем версию Minecraft
            minecraft_version_dir = os.path.join(versions_dir, CONFIG['version'])
            if not os.path.exists(minecraft_version_dir):
                issues_found.append(f"Версия Minecraft {CONFIG['version']} не установлена")
                add_log(f"❌ Версия Minecraft {CONFIG['version']} не установлена", 'red')
                try:
                    minecraft_launcher_lib.install.install_minecraft_version(
                        versionid=CONFIG['version'],
                        minecraft_directory=CONFIG['minecraft_dir']
                    )
                    fixes_applied.append(f"Установлена версия Minecraft {CONFIG['version']}")
                    add_log(f"✅ Установлена версия Minecraft {CONFIG['version']}", 'green')
                except Exception as e:
                    add_log(f"❌ Ошибка установки Minecraft: {str(e)}", 'red')

            progress['value'] = 100
            win.after(0, lambda: status_label.config(text="Проверка завершена!"))

            # Формируем отчет
            win.after(1000, lambda: show_repair_result(issues_found, fixes_applied, progress_window))

        except Exception as e:
            win.after(0, progress_window.destroy)
            if not silent:
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

        report += "🎯 Рекомендации:\n"
        if issues and not fixes:
            report += "• Попробуйте полную переустановку\n"
            report += "• Проверьте подключение к интернету\n"
        elif not issues:
            report += "• Игра готова к запуску!\n"

        if not silent:
            messagebox.showinfo("Автопочинка", report)

    # Запускаем починку в отдельном потоке
    threading.Thread(target=repair_thread, daemon=True).start()

    return True
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


cleanup_before_launch()

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
#mixer.music.load('Obuse - Menu song.mp3')
mixer.music.set_volume(0.1)

# Создание главного окна
win = ThemedTk(theme="arc")
win.geometry("1920x1080")
win.title('YamPixel')
#win.attributes("-fullscreen", True)

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
    """Расширенная функция починки игры с выбором действия"""
    choice_window = tk.Toplevel(win)
    choice_window.title("Починить игру")
    choice_window.geometry("400x300")
    choice_window.configure(bg='#2b2b2b')
    choice_window.transient(win)
    choice_window.grab_set()

    title_label = ttk.Label(choice_window,
                            text="Выберите действие:",
                            font=('Comfortaa', 14, 'bold'))
    title_label.pack(pady=20)

    def cleanup_only():
        choice_window.destroy()
        fig1()  # Старая функция очистки



    def cancel():
        choice_window.destroy()

    # Кнопки действий
    ttk.Button(choice_window, text="🧹 Очистить игру (удалить моды и версии)",
               command=cleanup_only, width=30).pack(pady=10)


    ttk.Button(choice_window, text="❌ Отмена",
               command=cancel, width=20).pack(pady=20)
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
    """Создает панель диагностики проблем"""
    diag_window = tk.Toplevel(win)
    diag_window.title("Диагностика проблем")
    diag_window.geometry("500x400")

    # Заголовок
    ttk.Label(diag_window, text="🔧 Диагностика проблем с запуском",
              font=('Comfortaa', 14, 'bold')).pack(pady=10)

    # Описание проблем
    problems_text = tk.Text(diag_window, height=12, width=60, wrap='word')
    problems_text.pack(pady=10, padx=10, fill='both', expand=True)

    problems_info = """
    ВАША ПРОБЛЕМА: Игра зависает при подключении к серверу

    ВОЗМОЖНЫЕ ПРИЧИНЫ:
    1. 🚫 Конфликт модов - некоторые моды несовместимы
    2. 🔄 Поврежденные файлы игры
    3. 🔐 Проблемы с аутентификацией
    4. 💾 Нехватка памяти

    РЕКОМЕНДУЕМЫЕ РЕШЕНИЯ:

    🎯 БЫСТРОЕ РЕШЕНИЕ (попробуйте по порядку):
    1. Запуск без модов - определит проблему в модах
    2. Полная переустановка - чистая установка игры
    3. Запуск с 2GB памяти - исключит проблемы с памятью
    """

    problems_text.insert('1.0', problems_info)
    problems_text.config(state='disabled')

    # Кнопки решений
    button_frame = ttk.Frame(diag_window)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="🚀 Запуск без модов",
               command=launch_without_mods).pack(side='left', padx=5)
    ttk.Button(button_frame, text="🔄 Полная переустановка",
               command=complete_reinstall).pack(side='left', padx=5)
    ttk.Button(button_frame, text="❌ Закрыть",
               command=diag_window.destroy).pack(side='left', padx=5)


def show_version_info():
    """Показывает информацию о версии и историю обновлений с GitHub"""
    try:
        # Создаем окно информации
        info_window = tk.Toplevel(win)
        info_window.title(f"YamalPixel Launcher v{CURRENT_VERSION}")
        info_window.geometry("700x900")
        info_window.resizable(True, True)
        info_window.transient(win)
        info_window.grab_set()

        # Центрируем окно
        info_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (700 // 2)
        y = (win.winfo_screenheight() // 2) - (900 // 2)
        info_window.geometry(f"700x900+{x}+{y}")

        # Основной фрейм
        main_frame = ttk.Frame(info_window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Заголовок
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(header_frame,
                  text=f"YamalPixel Launcher",
                  font=('Comfortaa', 16, 'bold')).pack()

        ttk.Label(header_frame,
                  text=f"Текущая версия: {CURRENT_VERSION}",
                  font=('Comfortaa', 12),
                  foreground='green' if is_latest_version() else 'orange').pack(pady=(5, 0))

        # Информация о системе
        sys_frame = ttk.LabelFrame(main_frame, text="📊 Системная информация", padding=10)
        sys_frame.pack(fill='x', pady=(0, 15))

        sys_info = f"""
• ОС: {platform.system()} {platform.release()}
• Архитектура: {platform.machine()}
• Python: {platform.python_version()}
• Папка игры: {CONFIG['minecraft_dir']}
• Java: {'✅ Установлена' if check_java_version() else '❌ Не найдена'}
• Статус: {'🎯 Актуальная версия' if is_latest_version() else '🔄 Доступно обновление'}
        """.strip()

        ttk.Label(sys_frame, text=sys_info, font=('Consolas', 9)).pack(anchor='w')

        # Дерево обновлений
        updates_frame = ttk.LabelFrame(main_frame, text="🔄 История обновлений", padding=10)
        updates_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Создаем Treeview для отображения версий
        columns = ('version', 'date', 'type')
        tree = ttk.Treeview(updates_frame, columns=columns, show='tree headings', height=8)

        # Настраиваем колонки
        tree.heading('version', text='Версия')
        tree.heading('date', text='Дата выпуска')
        tree.heading('type', text='Тип обновления')

        tree.column('version', width=120, anchor='w')
        tree.column('date', width=120, anchor='center')
        tree.column('type', width=150, anchor='center')

        # Скроллбар для дерева
        scrollbar_tree = ttk.Scrollbar(updates_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_tree.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar_tree.pack(side='right', fill='y')

        # Детали обновления
        details_frame = ttk.LabelFrame(main_frame, text="📋 Детали обновления", padding=10)
        details_frame.pack(fill='x', pady=(0, 15))

        # Текст с прокруткой для деталей
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill='both', expand=True)

        details_text = tk.Text(text_frame,
                               wrap='word',
                               height=6,
                               font=('Comfortaa', 9),
                               bg='#f8f9fa',
                               relief='solid',
                               borderwidth=1,
                               padx=10,
                               pady=10)

        scrollbar_text = ttk.Scrollbar(text_frame, orient='vertical', command=details_text.yview)
        details_text.configure(yscrollcommand=scrollbar_text.set)

        details_text.pack(side='left', fill='both', expand=True)
        scrollbar_text.pack(side='right', fill='y')

        # Показываем загрузку
        details_text.insert('1.0', "🔄 Загружаем историю обновлений...")
        details_text.configure(state='disabled')

        # Фрейм для кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))

        def check_updates():
            info_window.destroy()
            check_for_updates()

        def open_github():
            import webbrowser
            webbrowser.open("https://github.com/XxMoonmenxX/YamalPixel")

        def open_releases():
            import webbrowser
            webbrowser.open("https://github.com/XxMoonmenxX/YamalPixel/releases")

        # Кнопки
        ttk.Button(button_frame, text="🔄 Проверить обновления",
                   command=check_updates).pack(side='left', padx=5)

        ttk.Button(button_frame, text="🌐 GitHub",
                   command=open_github).pack(side='left', padx=5)

        ttk.Button(button_frame, text="📦 Все релизы",
                   command=open_releases).pack(side='left', padx=5)

        ttk.Button(button_frame, text="❌ Закрыть",
                   command=info_window.destroy).pack(side='right', padx=5)

        # Функция для обработки выбора версии в дереве
        def on_tree_select(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                changelog = tree.item(item, 'tags')[0] if tree.item(item, 'tags') else "Нет описания"

                details_text.configure(state='normal')
                details_text.delete('1.0', 'end')
                details_text.insert('1.0', changelog)
                details_text.configure(state='disabled')

        tree.bind('<<TreeviewSelect>>', on_tree_select)

        def load_releases_thread():
            try:
                response = requests.get(
                    "https://api.github.com/repos/XxMoonmenxX/YamalPixel/releases",
                    timeout=10
                )
                response.raise_for_status()

                releases = response.json()

                # Берем последние 5 релизов
                recent_releases = releases[:5]

                # Обновляем дерево в основном потоке
                info_window.after(0, update_releases_tree, recent_releases)

            except Exception as e:
                error_text = f"❌ Не удалось загрузить историю обновлений\n\nОшибка: {str(e)}"
                info_window.after(0, update_releases_tree, [])

        def update_releases_tree(releases):
            # Очищаем дерево
            for item in tree.get_children():
                tree.delete(item)

            if not releases:
                details_text.configure(state='normal')
                details_text.delete('1.0', 'end')
                details_text.insert('1.0', "Не удалось загрузить данные об обновлениях")
                details_text.configure(state='disabled')
                return

            # Добавляем релизы в дерево
            for release in releases:
                version = release['tag_name'].lstrip('v')
                date = release['created_at'][:10]  # Берем только дату
                prerelease = release.get('prerelease', False)
                draft = release.get('draft', False)

                # Определяем тип обновления
                if draft:
                    release_type = "📝 Черновик"
                elif prerelease:
                    release_type = "🧪 Пре-релиз"
                else:
                    release_type = "🚀 Стабильный"

                # Форматируем changelog
                changelog = release.get('body', 'Нет описания изменений')
                changelog = format_changelog(changelog)

                # Добавляем в дерево
                tree.insert('', 'end', values=(
                    version,
                    date,
                    release_type
                ), tags=(changelog,))

            # Выбираем первый элемент
            if tree.get_children():
                first_item = tree.get_children()[0]
                tree.selection_set(first_item)
                tree.focus(first_item)
                # Вызываем обработчик выбора чтобы показать детали
                on_tree_select(None)

        # Запускаем загрузку в отдельном потоке
        threading.Thread(target=load_releases_thread, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть информацию о версии: {str(e)}")


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
        btn.config(state="disabled", text="🚀 Запускается...")
        quick_btn.config(state="disabled", text="⏳ Запуск...")
    else:
        # Разблокируем кнопки
        btn.config(state="normal", text="Войти в игру")
        quick_btn.config(state="normal", text="🚀 Быстрый запуск (оффлайн)")


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
                            command=cancel_launch, style="Accent.TButton")
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
    ttk.Entry(settings_window, textvariable=memory_var).grid(row=0, column=1)

    def save_settings():
        new_memory = f"-Xmx{memory_var.get()}G"
        CONFIG['jvm_memory'] = new_memory
        messagebox.showinfo("Сохранено", "Настройки применены!")
        settings_window.destroy()

    ttk.Button(settings_window, text="Сохранить", command=save_settings).grid(row=1, columnspan=2)


# Добавление в меню
settings_menu.add_command(label="Настройки", command=open_settings)
settings_menu.add_separator()


# Функция для проверки и загрузки модов
def checker1():
    """ОБНОВЛЕННАЯ функция проверки и загрузки модов"""
    if version_combobox.get() != "YamalPixel":
        print("Выбрана версия, отличная от YamalPixel. Загрузка модов пропущена.")
        return

    mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
    os.makedirs(mods_dir, exist_ok=True)

    # Проверяем какие моды отсутствуют
    missing_mods = []
    for mod in CONFIG['mods']:
        mod_path = os.path.join(mods_dir, mod['file'])
        if not os.path.exists(mod_path):
            missing_mods.append(mod)

    if missing_mods:
        print(f"Найдено отсутствующих модов: {len(missing_mods)}")
        # Запускаем турбо-загрузку
        download_mods_turbo_ui(missing_mods)
    else:
        print("Все моды установлены")


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
def runn():
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME

    # УСИЛЕННАЯ проверка - предотвращаем любой повторный запуск
    if LAUNCH_IN_PROGRESS:
        elapsed = int(time.time() - LAUNCH_START_TIME)
        messagebox.showwarning(
            "Запуск уже выполняется",
            f"🔄 Игра уже запускается!\n\n"
            f"Прошло: {elapsed} секунд\n"
            f"Пожалуйста, дождитесь завершения запуска."
        )
        return

    try:
        if not username.get().strip():
            messagebox.showerror("Ошибка", "❌ Введите имя пользователя!")
            return

        # НЕМЕДЛЕННО блокируем интерфейс
        set_launch_state(True)

        # 🔧 ДОБАВЛЕН ВЫЗОВ АВТОПОЧИНКИ ПЕРЕД ЗАПУСКОМ - БЕЗ SILENT MODE
        # Проверяем и восстанавливаем файлы, включая отсутствующие моды
        auto_repair_game_files(silent=False)  # ИЗМЕНЕНО: silent=False для загрузки модов

        # Создаем окно прогресса запуска
        progress_window = tk.Toplevel(win)
        progress_window.title("YamalPixel - Запуск игры")
        progress_window.geometry("500x350")
        progress_window.resizable(False, False)
        progress_window.transient(win)
        progress_window.grab_set()

        # Запрещаем закрытие через крестик
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

        ttk.Label(header_frame, text="🚀 Запуск YamalPixel",
                  font=('Comfortaa', 16, 'bold')).pack()

        ttk.Label(header_frame, text="Подготовка к запуску игры...",
                  font=('Comfortaa', 11), foreground='gray').pack(pady=(5, 0))

        # Прогресс-бар
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill='x', pady=10)

        progress_bar = ttk.Progressbar(progress_frame, orient="horizontal",
                                       length=400, mode="indeterminate")
        progress_bar.pack(pady=5)
        progress_bar.start()

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

        # Детали запуска
        details_label = ttk.Label(main_frame, text="",
                                  font=('Comfortaa', 8), foreground='blue')
        details_label.pack()

        # Лог запуска
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill='x', pady=5)

        log_label = ttk.Label(log_frame, text="",
                              font=('Consolas', 7), foreground='green')
        log_label.pack()

        # Кнопка отмены
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        def cancel_launch():
            progress_window.destroy()
            set_launch_state(False)
            messagebox.showinfo("Отменено", "✅ Запуск игры отменен")

        cancel_btn = ttk.Button(button_frame, text="❌ Отменить запуск",
                                command=cancel_launch, style="Accent.TButton")
        cancel_btn.pack()

        # Функция обновления UI
        def update_progress_ui():
            if LAUNCH_IN_PROGRESS and progress_window.winfo_exists():
                elapsed = int(time.time() - LAUNCH_START_TIME)
                timer_label.config(text=f"⏱️ Прошло времени: {elapsed} сек.")
                progress_window.after(1000, update_progress_ui)

        # Запускаем обновление UI
        update_progress_ui()

        def update_status(text, detail=""):
            if progress_window.winfo_exists():
                win.after(0, lambda: status_label.config(text=text))
                if detail:
                    win.after(0, lambda: details_label.config(text=detail))

        def update_log(message):
            if progress_window.winfo_exists():
                win.after(0, lambda: log_label.config(text=message))
                print(f"[LAUNCHER] {message}")

        # Запускаем установку и запуск в отдельном потоке
        def install_and_run_thread():
            """Поток установки и запуска с улучшенным логированием"""
            try:
                update_status("Проверка файлов...", "Проверяем игровые файлы")
                update_log("Начинаем запуск игры...")

                # Быстрая проверка файлов
                quick_file_check()
                update_log("✅ Проверка файлов завершена")

                # Очистка кэша аутентификации
                clear_auth_cache()
                update_log("✅ Кэш аутентификации очищен")

                selected_version = version_combobox.get()
                selected_memory = "4G"

                update_status("Подготовка запуска...", "Формируем команду запуска")
                update_log(f"🎯 Запускаем версию: {selected_version}")

                # Оптимизированные настройки запуска
                jvm_args = [
                    f"-Xmx{selected_memory}",
                    f"-Xms{selected_memory}",
                    "-XX:+UseG1GC",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:G1NewSizePercent=20",
                    "-XX:G1ReservePercent=20",
                    "-XX:MaxGCPauseMillis=50",
                    "-XX:G1HeapRegionSize=32M",
                    "-Duser.language=ru",
                    "-Duser.country=RU",
                    "-Dfile.encoding=UTF-8"
                ]

                options = {
                    'username': username.get(),
                    'uuid': str(hash(username.get())),
                    'token': '',
                    'jvmArguments': jvm_args,
                    'gameLocale': 'ru_RU'
                }

                update_status("Формирование команды...", "Создаем команду запуска")

                # Формируем команду запуска
                if is_fabric_needed(selected_version):
                    command = minecraft_launcher_lib.command.get_minecraft_command(
                        version=f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}",
                        minecraft_directory=CONFIG['minecraft_dir'],
                        options=options
                    )
                else:
                    command = minecraft_launcher_lib.command.get_minecraft_command(
                        version=CONFIG['version'],
                        minecraft_directory=CONFIG['minecraft_dir'],
                        options=options
                    )

                update_log(f"⚙️ Команда сформирована")
                update_log(f"💾 Память: {selected_memory}")
                update_log(f"👤 Игрок: {username.get()}")

                update_status("Запуск игры...", "Запускаем Minecraft")
                update_log("🚀 Запускаем процесс Minecraft...")

                # Запускаем процесс с перехватом вывода
                process = launch_minecraft_process(command, update_log)

                if process:
                    update_log("✅ Процесс Minecraft успешно запущен!")
                    update_status("Игра запускается...", "Читаем логи загрузки...")

                    # Ждем немного и проверяем статус
                    time.sleep(5)

                    if is_minecraft_process_running(process):
                        update_log("🎮 Minecraft загружается...")
                        update_log("⏳ Ожидаем завершения загрузки модов...")

                        # Даем больше времени на загрузку
                        time.sleep(10)

                        # Закрываем окно прогресса и разблокируем интерфейс
                        win.after(0, progress_window.destroy)
                        win.after(0, lambda: set_launch_state(False))

                        win.after(100, lambda: messagebox.showinfo(
                            "Успешный запуск",
                            f"✅ Игра успешно запущена!\n\n" +
                            f"• Игрок: {username.get()}\n" +
                            f"• Версия: {selected_version}\n" +
                            f"• Память: {selected_memory}\n\n" +
                            f"{show_random_launch_message()}"
                        ))

                        # Мониторим процесс в фоне
                        threading.Thread(
                            target=monitor_game_process,
                            args=(process,),
                            daemon=True
                        ).start()
                    else:
                        update_log("❌ Процесс Minecraft завершился неожиданно")
                        raise Exception("Minecraft не запустился")
                else:
                    update_log("❌ Не удалось запустить процесс Minecraft")
                    raise Exception("Не удалось создать процесс Minecraft")

            except Exception as e:
                error_msg = f"Ошибка запуска: {str(e)}"
                update_log(f"❌ {error_msg}")
                print(f"[ERROR] {error_msg}")

                win.after(0, progress_window.destroy)
                win.after(0, lambda: set_launch_state(False))
                win.after(0, lambda: messagebox.showerror(
                    "Ошибка запуска",
                    f"❌ Не удалось запустить игру:\n\n{error_msg}\n\n"
                    f"Проверьте:\n"
                    f"• Достаточно ли памяти\n"
                    f"• Целостность игровых файлов\n"
                    f"• Антивирусные блокировки"
                ))

        # Запускаем в отдельном потоке
        threading.Thread(target=install_and_run_thread, daemon=True).start()

    except Exception as e:
        # Если ошибка на этапе подготовки - разблокируем кнопки
        set_launch_state(False)
        messagebox.showerror(
            "Критическая ошибка",
            f"❌ Не удалось подготовить запуск:\n\n{str(e)}"
        )


def launch_minecraft_process(command, log_callback=None):
    """Запускает процесс Minecraft с перехватом и отображением вывода"""
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

# А затем создавайте кнопку с правильной ссылкой на функцию:
btn = ttk.Button(win, text="Войти в игру", width=15, style="BW.TLabel", command=runn)
btn.place(relx=0.5, rely=0.5, width=100, height=50, anchor="c")


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


quick_btn = ttk.Button(win, text="🚀 Быстрый запуск (оффлайн)",
                       width=20, style="BW.TLabel",
                       command=lambda: quick_launch_offline())
quick_btn.place(relx=0.5, rely=0.55, width=150, height=30, anchor="c")


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

username = ttk.Entry(win, style="BW.TLabel", width=20)
username.place(relx=.5, rely=0.45, anchor="c")

btn = ttk.Button(win, text="Войти в игру", width=15, style="BW.TLabel", command=runn)
btn.place(relx=0.5, rely=0.5, width=100, height=50, anchor="c")

style.configure("CenterText.TLabel", layout=('Center',))

label_online = ttk.Label(win, text="Онлайн: 0", style="BW.TLabel")
label_online.place(relx=0.5, rely=0.61, anchor="c")



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


# Функция для показа онлайн игроков
def show_online_players():
    try:
        server = JavaServer.lookup("90.151.59.120:25565")
        status = server.status()
        label_online.config(text=f"Онлайн: {status.players.online}",
                            background="green" if status.players.online > 0 else "red")
    except Exception as e:
        label_online.config(text="Ошибка подключения", background="red")



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



btn_update_online = ttk.Button(win, text="Показать онлайн", style="BW.TLabel", command=show_online_players)
btn_update_online.place(relx=.5, rely=0.58, width=150, height=25, anchor="c")


# Функция для выбора версии игры
def select_version(event):
    selected_version = version_combobox.get()
    if selected_version == "YamalPixel":
        CONFIG['version'] = '1.20.1'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.7.10":
        CONFIG['version'] = '1.7.10'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.8.9":
        CONFIG['version'] = '1.8.9'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.12.2":
        CONFIG['version'] = '1.12.2'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.14.4":
        CONFIG['version'] = '1.14.4'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.14.4 + Fabric":
        CONFIG['version'] = '1.14.4'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.15.2":
        CONFIG['version'] = '1.15.2'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.15.2 + Fabric":
        CONFIG['version'] = '1.15.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.16.5":
        CONFIG['version'] = '1.16.5'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.16.5 + Fabric":
        CONFIG['version'] = '1.16.5'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.17.1":
        CONFIG['version'] = '1.17.1'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.17.1 + Fabric":
        CONFIG['version'] = '1.17.1'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.18.2":
        CONFIG['version'] = '1.18.2'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.18.2 + Fabric":
        CONFIG['version'] = '1.18.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.19.2":
        CONFIG['version'] = '1.19.2'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.19.2 + Fabric":
        CONFIG['version'] = '1.19.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.20.1":
        CONFIG['version'] = '1.20.1'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.20.1 + Fabric":
        CONFIG['version'] = '1.20.1'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.20.2":
        CONFIG['version'] = '1.20.2'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.20.2 + Fabric":
        CONFIG['version'] = '1.20.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.21":
        CONFIG['version'] = '1.21'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.21 + Fabric":
        CONFIG['version'] = '1.21'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.21.1":
        CONFIG['version'] = '1.21.1'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.21.1 + Fabric":
        CONFIG['version'] = '1.21.1'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.21.2":
        CONFIG['version'] = '1.21.2'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.21.2 + Fabric":
        CONFIG['version'] = '1.21.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.21.3":
        CONFIG['version'] = '1.21.3'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.21.3 + Fabric":
        CONFIG['version'] = '1.21.3'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.21.4":
        CONFIG['version'] = '1.21.4'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.21.4 + Fabric":
        CONFIG['version'] = '1.21.4'
        CONFIG['fabric_loader'] = '0.16.10'

    messagebox.showinfo("Версия изменена", f"Выбрана версия: {selected_version}")


# Добавление выпадающего списка для выбора версии
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

version_combobox = ttk.Combobox(win, values=versions, state="readonly")
version_combobox.current(0)
version_combobox.place(relx=0.5, rely=0.4, anchor="c")
version_combobox.bind("<<ComboboxSelected>>", select_version)

# Вызываем функцию обновления статуса Discord после создания окна
win.after(300, update_discord_status)

# Запуск главного цикла
win.mainloop()
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