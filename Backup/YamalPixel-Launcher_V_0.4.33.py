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

#Пишется при помощи DeepSeek, каждый может сделать тоже самое хоть немного зная python!!!
CURRENT_VERSION = "0.4.33" #обновление
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
        {'url': 'https://disk.yandex.ru/d/62ECRecsfaGF6Q', 'file': 'mods.zip'}
    ]
}


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

# Конфигурация
CONFIG = {
    'version': '1.20.1',
    'fabric_loader': '0.16.10',
    'minecraft_dir': os.path.expanduser("~/YamalPixel"),
    'mods': [
        {'url': 'https://disk.yandex.ru/d/62ECRecsfaGF6Q', 'file': 'mods.zip'}
    ]
}


# Функция для скачивания шейдеров
def download_shaders():
    """Показывает диалог выбора и скачивания шейдеров"""
    shaders_window = tk.Toplevel(win)
    shaders_window.title("Скачать шейдеры")
    shaders_window.geometry("600x500")
    shaders_window.transient(win)
    shaders_window.grab_set()

    # Заголовок
    ttk.Label(shaders_window, text="Выберите шейдеры для скачивания:",
              font=('Comfortaa', 12, 'bold')).pack(pady=10)

    # Фрейм для списка шейдеров
    frame = ttk.Frame(shaders_window)
    frame.pack(fill='both', expand=True, padx=20, pady=10)

    # Создаем Treeview с чекбоксами
    columns = ('selected', 'name')
    tree = ttk.Treeview(frame, columns=columns, show='tree headings', height=15)

    # Настраиваем колонки
    tree.heading('selected', text='✓')
    tree.heading('name', text='Название шейдера')

    tree.column('selected', width=50, anchor='center')
    tree.column('name', width=500, anchor='w')

    # Добавляем данные
    for shader in SHADERS_CONFIG['shaders']:
        tree.insert('', 'end', values=('☐', shader['name']), tags=(shader['url'], shader['file']))

    # Скроллбар
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Переменная для хранения выбранных шейдеров
    selected_shaders = []

    def toggle_selection(event):
        item = tree.selection()[0]
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

    tree.bind('<Button-1>', toggle_selection)

    # Фрейм для кнопок
    button_frame = ttk.Frame(shaders_window)
    button_frame.pack(pady=10)

    def download_selected():
        if not selected_shaders:
            messagebox.showwarning("Выбор", "Пожалуйста, выберите хотя бы один шейдер")
            return

        shaders_window.destroy()

        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        progress_window.title("Скачивание шейдеров")
        progress_window.geometry("400x150")

        progress_label = ttk.Label(progress_window, text="Подготовка к скачиванию...")
        progress_label.pack(pady=10)

        progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress.pack(pady=10)

        status_label = ttk.Label(progress_window, text="")
        status_label.pack()

        def download_thread():
            try:
                shaders_dir = os.path.join(CONFIG['minecraft_dir'], 'shaderpacks')
                os.makedirs(shaders_dir, exist_ok=True)

                total = len(selected_shaders)
                success_count = 0

                for i, shader in enumerate(selected_shaders, 1):
                    status_label.config(text=f"Скачивание: {shader['name']}...")
                    progress['value'] = (i - 1) * 100 / total
                    progress_window.update()

                    try:
                        # Получаем прямую ссылку для скачивания
                        download_url = get_yandex_direct_link(shader['url'])
                        if not download_url:
                            logging.error(f"Не удалось получить ссылку для шейдера: {shader['name']}")
                            continue

                        shader_path = os.path.join(shaders_dir, shader['file'])

                        # Скачиваем файл
                        response = requests.get(download_url, stream=True)
                        response.raise_for_status()

                        with open(shader_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        success_count += 1
                        logging.info(f"Успешно скачан шейдер: {shader['name']}")

                    except Exception as e:
                        logging.error(f"Ошибка скачивания шейдера {shader['name']}: {str(e)}")

                progress_window.destroy()

                if success_count > 0:
                    messagebox.showinfo(
                        "Скачивание завершено",
                        f"Успешно скачано {success_count} из {total} шейдеров.\n\n"
                        f"Шейдеры сохранены в папке: {shaders_dir}"
                    )
                else:
                    messagebox.showerror("Ошибка", "Не удалось скачать ни одного шейдера")

            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Ошибка", f"Ошибка при скачивании шейдеров: {str(e)}")

        threading.Thread(target=download_thread, daemon=True).start()

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

    def deselect_all():
        selected_shaders.clear()
        for item in tree.get_children():
            tree.set(item, 'selected', '☐')

    def open_shaders_folder():
        shaders_dir = os.path.join(CONFIG['minecraft_dir'], 'shaderpacks')
        try:
            if not os.path.exists(shaders_dir):
                os.makedirs(shaders_dir)
            if os.name == 'nt':  # Windows
                os.startfile(shaders_dir)
            elif os.name == 'posix':  # Linux/MacOS
                subprocess.Popen(['xdg-open', shaders_dir])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")

    # Кнопки управления
    ttk.Button(button_frame, text="✅ Выбрать все",
               command=select_all).pack(side='left', padx=5)
    ttk.Button(button_frame, text="❌ Снять все",
               command=deselect_all).pack(side='left', padx=5)
    ttk.Button(button_frame, text="📥 Скачать выбранные",
               command=download_selected).pack(side='left', padx=5)
    ttk.Button(button_frame, text="📁 Открыть папку шейдеров",
               command=open_shaders_folder).pack(side='left', padx=5)
    ttk.Button(button_frame, text="❌ Закрыть",
               command=shaders_window.destroy).pack(side='left', padx=5)












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


def auto_repair_game_files():
    """Автоматически проверяет и восстанавливает поврежденные файлы игры"""

    # Создаем окно прогресса
    progress_window = tk.Toplevel(win)
    progress_window.title("Автопочинка")
    progress_window.geometry("400x150")

    progress_label = ttk.Label(progress_window, text="Проверка файлов...")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="indeterminate")
    progress.pack(pady=10)
    progress.start()

    status_label = ttk.Label(progress_window, text="")
    status_label.pack()

    def repair_thread():
        minecraft_dir = CONFIG['minecraft_dir']
        mods_dir = os.path.join(minecraft_dir, 'mods')
        versions_dir = os.path.join(minecraft_dir, 'versions')

        issues_found = []
        fixes_applied = []

        try:
            # Проверяем наличие основных папок
            status_label.config(text="Проверка папок...")
            if not os.path.exists(mods_dir):
                issues_found.append("Папка mods отсутствует")
                os.makedirs(mods_dir, exist_ok=True)
                fixes_applied.append("Создана папка mods")

            if not os.path.exists(versions_dir):
                issues_found.append("Папка versions отсутствует")
                os.makedirs(versions_dir, exist_ok=True)
                fixes_applied.append("Создана папка versions")

            # Проверяем servers.dat
            status_label.config(text="Проверка servers.dat...")
            servers_file = os.path.join(minecraft_dir, 'servers.dat')
            if not os.path.exists(servers_file):
                issues_found.append("Файл servers.dat отсутствует")
                try:
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
                except Exception as e:
                    print(f"Ошибка восстановления servers.dat: {str(e)}")

            # Проверяем и загружаем моды
            status_label.config(text="Проверка модов...")
            if os.path.exists(mods_dir) and not os.listdir(mods_dir):
                issues_found.append("Папка mods пустая")
                try:
                    mods_dir_path = os.path.join(minecraft_dir, 'mods')
                    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'

                    for mod in CONFIG['mods']:
                        mod_path = os.path.join(mods_dir_path, mod['file'])
                        if not os.path.exists(mod_path):
                            try:
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

                                    if mod['file'].endswith('.zip'):
                                        try:
                                            with zipfile.ZipFile(mod_path, 'r') as zip_file:
                                                zip_file.extractall(path=mods_dir_path)
                                            fixes_applied.append(f"Загружен и распакован {mod['file']}")
                                        except Exception as e:
                                            fixes_applied.append(f"Загружен {mod['file']} (ошибка распаковки)")
                                    else:
                                        fixes_applied.append(f"Загружен {mod['file']}")

                            except Exception as e:
                                print(f"Ошибка загрузки мода {mod['file']}: {str(e)}")

                except Exception as e:
                    print(f"Ошибка загрузки модов: {str(e)}")

            # Проверяем Fabric
            status_label.config(text="Проверка Fabric...")
            fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
            fabric_version_dir = os.path.join(versions_dir, fabric_version)
            if not os.path.exists(fabric_version_dir):
                issues_found.append("Fabric не установлен")
                try:
                    minecraft_launcher_lib.fabric.install_fabric(
                        minecraft_version=CONFIG['version'],
                        loader_version=CONFIG['fabric_loader'],
                        minecraft_directory=CONFIG['minecraft_dir']
                    )
                    fixes_applied.append("Установлен Fabric")
                except Exception as e:
                    print(f"Ошибка установки Fabric: {str(e)}")

            # Проверяем версию Minecraft
            status_label.config(text="Проверка Minecraft...")
            minecraft_version_dir = os.path.join(versions_dir, CONFIG['version'])
            if not os.path.exists(minecraft_version_dir):
                issues_found.append(f"Версия Minecraft {CONFIG['version']} не установлена")
                try:
                    minecraft_launcher_lib.install.install_minecraft_version(
                        versionid=CONFIG['version'],
                        minecraft_directory=CONFIG['minecraft_dir']
                    )
                    fixes_applied.append(f"Установлена версия Minecraft {CONFIG['version']}")
                except Exception as e:
                    print(f"Ошибка установки Minecraft: {str(e)}")

            # Формируем отчет
            progress_window.destroy()
            report = "🔍 Автопочинка завершена!\n\n"

            if issues_found:
                report += "📋 Найдены проблемы:\n• " + "\n• ".join(issues_found) + "\n\n"

            if fixes_applied:
                report += "✅ Исправления:\n• " + "\n• ".join(fixes_applied)

            if not issues_found and not fixes_applied:
                report += "✅ Проблем не обнаружено! Все файлы в порядке."

            messagebox.showinfo("Автопочинка", report)

        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Ошибка", f"Ошибка автопочинки: {str(e)}")

    threading.Thread(target=repair_thread, daemon=True).start()

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


def download_and_install_update(download_url):
    progress_window = None
    temp_exe = os.path.join(os.getcwd(), "YamalPixelLauncher_New.exe")
    old_exe = os.path.join(os.getcwd(), "YamalPixelLauncher.exe")
    backup_exe = os.path.join(os.getcwd(), "YamalPixelLauncher_Backup.exe")

    try:
        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        progress_window.title("Обновление")
        progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress.pack(pady=20)
        status_label = ttk.Label(progress_window, text="Скачивание обновления...")
        status_label.pack()

        # Скачиваем новую версию
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))

            with open(temp_exe, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int((downloaded / total_size) * 100) if total_size > 0 else 0
                    progress['value'] = percent
                    status_label.config(text=f"Загружено {percent}%")
                    progress_window.update()

        # Создаем батник для завершения обновления
        if os.name == 'nt':  # Windows
            bat_path = os.path.join(os.getcwd(), "update.bat")
            with open(bat_path, 'w') as bat_file:
                bat_file.write(f"""
                @echo off
                timeout /t 1 /nobreak >nul
                del "{old_exe}"
                rename "{temp_exe}" "{os.path.basename(old_exe)}"
                start "" "{old_exe}"
                del "{backup_exe}" 2>nul
                del "%~f0"
                """)
        else:  # Linux/MacOS
            sh_path = os.path.join(os.getcwd(), "update.sh")
            with open(sh_path, 'w') as sh_file:
                sh_file.write(f"""
                #!/bin/bash
                sleep 1
                rm -f "{old_exe}"
                mv "{temp_exe}" "{old_exe}"
                chmod +x "{old_exe}"
                "{old_exe}" &
                rm -f "{backup_exe}"
                rm -f "$0"
                """)
            os.chmod(sh_path, 0o755)  # Делаем скрипт исполняемым

        # Создаем бэкап старой версии
        if os.path.exists(old_exe):
            os.rename(old_exe, backup_exe)

        # Запускаем скрипт обновления
        if os.name == 'nt':
            subprocess.Popen([bat_path], shell=True)
        else:
            subprocess.Popen([sh_path], shell=True)

        # Закрываем лаунчер
        sys.exit()

    except Exception as e:
        logging.error(f"Ошибка обновления: {str(e)}")

        # Восстанавливаем из бэкапа при ошибке
        if os.path.exists(backup_exe):
            if os.path.exists(old_exe):
                os.remove(old_exe)
            os.rename(backup_exe, old_exe)
            messagebox.showinfo("Восстановление", "Произведен откат к предыдущей версии")

        if progress_window:
            progress_window.destroy()

        messagebox.showerror("Ошибка", f"Ошибка при обновлении: {str(e)}")



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


def initial_check():
    """
    Улучшенная начальная проверка Java
    """
    print("🔍 Проверка установленной Java...")

    if not check_java_version():
        print("❌ Java 17 не найдена")

        # Более информативное сообщение
        response = messagebox.askyesno(
            "Требуется Java 17",
            "Для работы лаунчера требуется Java 17.\n\n"
            "Без Java игра не запустится.\n\n"
            "Установить Java 17 автоматически?",
            icon='warning',
            default='yes'
        )

        if response:
            install_java_with_progress()
        else:
            # Предлагаем альтернативу
            response2 = messagebox.askyesno(
                "Ручная установка",
                "Вы можете установить Java 17 вручную:\n\n"
                "1. Скачайте с adoptium.net\n"
                "2. Установите как обычную программу\n"
                "3. Перезапустите лаунчер\n\n"
                "Открыть сайт для скачивания?",
                default='yes'
            )
            if response2:
                import webbrowser
                webbrowser.open("https://adoptium.net/temurin/releases/?version=17")
            sys.exit()
    else:
        print("✅ Правильная версия Java установлена")


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
def initial_check():
    print("🔍 Проверка установленной Java...")

    if not check_java_version():
        print("❌ Java 17 не найдена")

        choice = messagebox.askyesnocancel(
            "Требуется Java 17",
            "Для работы лаунчера рекомендуется Java 17.\n\n"
            "Выберите действие:\n"
            "• Да - установить автоматически\n"
            "• Нет - пропустить проверку\n"
            "• Отмена - выйти из лаунчера"
        )

        if choice is None:  # Отмена
            sys.exit()
        elif choice:  # Да - установить
            install_java_with_progress()
        else:  # Нет - пропустить
            print("⚠️ Проверка Java пропущена пользователем")
    else:
        print("✅ Правильная версия Java установлена")
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
win.after(100, initial_check)
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
    # Если выбрана не YamalPixel, пропускаем загрузку модов
    if version_combobox.get() != "YamalPixel":
        print("Выбрана версия, отличная от YamalPixel. Загрузка модов пропущена.")
        return

    mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
    os.makedirs(mods_dir, exist_ok=True)
    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
    missing_mods = []
    for mod in CONFIG['mods']:
        mod_path = os.path.join(mods_dir, mod['file'])
        if not os.path.exists(mod_path):
            missing_mods.append(mod)
    for mod in missing_mods:
        mod_path = os.path.join(mods_dir, mod['file'])
        try:
            params = {'public_key': mod['url']}
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            download_url = response.json().get('href')
            if not download_url:
                continue
            with open(mod_path, 'wb') as f:
                dl_response = requests.get(download_url, stream=True)
                dl_response.raise_for_status()
                for chunk in dl_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Мод {mod['file']} успешно установлен")
        except Exception as e:
            print(f"Ошибка загрузки мода {mod['file']}: {str(e)}")
    for mod in missing_mods:
        if mod['file'].endswith('.zip'):
            zip_path = os.path.join(mods_dir, mod['file'])
            extract_dir = os.path.join(mods_dir)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall(path=extract_dir)
                    print(f"Содержимое архива {mod['file']} успешно извлечено в папку mods")
            except Exception as e:
                print(f"Ошибка распаковки архива {mod['file']}: {str(e)}")


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


def runn():
    try:
        if not username.get().strip():
            messagebox.showerror("Ошибка", "Введите имя пользователя!")
            return

        # Автоматическая проверка файлов перед запуском
        auto_repair_game_files()

        os.makedirs(CONFIG['minecraft_dir'], exist_ok=True)

        progress_window = tk.Toplevel(win)
        progress_window.title("Запуск Minecraft")
        progress_window.geometry("300x100")
        progress = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="indeterminate")
        progress.pack(pady=20)
        progress.start()

        status_label = ttk.Label(progress_window, text="Подготовка к запуску...")
        status_label.pack()

        def install_and_run():
            try:
                selected_version = version_combobox.get()
                status_label.config(text="Проверка версии Minecraft...")

                # Устанавливаем Minecraft версию, если она отсутствует
                install_minecraft_version(
                    version=CONFIG['version'],
                    progress_callback={
                        "setStatus": lambda t: status_label.config(text=t),
                        "setProgress": lambda v: progress.configure(value=v) if progress[
                                                                                    'mode'] == 'determinate' else None,
                        "setMax": lambda m: progress.configure(maximum=m) if progress['mode'] == 'determinate' else None
                    }
                )

                status_label.config(text="Установка Fabric...")

                # Устанавливаем Fabric только если он нужен
                if is_fabric_needed(selected_version):
                    if not check_minecraft_and_fabric_installed():
                        minecraft_launcher_lib.fabric.install_fabric(
                            minecraft_version=CONFIG['version'],
                            loader_version=CONFIG['fabric_loader'],
                            minecraft_directory=CONFIG['minecraft_dir'],
                            callback={
                                "setStatus": lambda t: status_label.config(text=t),
                                "setProgress": lambda v: progress.configure(value=v),
                                "setMax": lambda m: progress.configure(maximum=m)
                            }
                        )

                status_label.config(text="Загрузка модов...")

                # Загрузка модов только для YamalPixel
                if selected_version == "YamalPixel":
                    checker1()

                status_label.config(text="Запуск игры...")

                # Формирование команды запуска
                if is_fabric_needed(selected_version):
                    command = minecraft_launcher_lib.command.get_minecraft_command(
                        version=f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}",
                        minecraft_directory=CONFIG['minecraft_dir'],
                        options={
                            'username': username.get(),
                            'jvmArguments': [
                                "-Xmx8G",
                                "-Duser.language=ru",
                                "-Duser.country=RU",
                                "-Dfile.encoding=UTF-8"
                            ],
                            'gameLocale': 'ru_RU'
                        }
                    )
                else:
                    command = minecraft_launcher_lib.command.get_minecraft_command(
                        version=CONFIG['version'],
                        minecraft_directory=CONFIG['minecraft_dir'],
                        options={
                            'username': username.get(),
                            'jvmArguments': [
                                "-Xmx8G",
                                "-Duser.language=ru",
                                "-Duser.country=RU",
                                "-Dfile.encoding=UTF-8"
                            ],
                            'gameLocale': 'ru_RU'
                        }
                    )

                progress_window.destroy()
                subprocess.Popen(command)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка запуска: {str(e)}")
                progress_window.destroy()

        threading.Thread(target=install_and_run, daemon=True).start()

    except Exception as e:
        print(f"Ошибка в основной функции запуска: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось запустить игру: {str(e)}")


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