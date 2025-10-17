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
CURRENT_VERSION = "0.4.1" #обновление
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
# Вызываем функцию обновления статуса Discord
update_discord_status()


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
                update_asset = next(
                    (asset for asset in release_data['assets']
                     if asset['name'].lower().endswith('.exe') and "yamalpixel" in asset['name'].lower()),
                    None
                )

                if update_asset and CURRENT_VERSION <='0.3.0':
                    download_and_install_update(update_asset['browser_download_url'])
                else:
                    messagebox.showerror("Ошибка", "EXE-файл не найден в релизе.")

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
    try:
        result = subprocess.run(['java', '-version'],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                text=True,
                                timeout=5)
        version_line = [line for line in result.stderr.split('\n') if 'version "' in line][0]
        version_match = re.search(r'version "([1-9]\d*\.\d+\.\d+)', version_line)

        if version_match:
            major_version = int(version_match.group(1).split('.')[0])
            return major_version >= 17
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError, TimeoutError) as e:
        logging.warning(f"Java check failed: {str(e)}")
    return False




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
    if not check_java_version():
        response = messagebox.askyesno("Java не установлена",
                                       "Для работы лаунчера требуется Java 17. Установить сейчас?")
        if response:
            install_java_with_progress()
        else:
            sys.exit()
    else:
        print("Необходимая версия JAVA установлена.")

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


def create_backup(folder_path, backup_type):
    """Создает zip-бэкап указанной папки"""
    if not os.path.exists(folder_path):
        return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(CONFIG['minecraft_dir'], 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    backup_filename = f"{backup_type}_backup_{timestamp}.zip"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
        print(f"Создан бэкап: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Ошибка создания бэкапа: {str(e)}")
        return None


# Новая функция для ручного создания бэкапа
def create_manual_backup():
    """Создает бэкап вручную по кнопке"""
    minecraft_dir = CONFIG['minecraft_dir']
    mods_dir = os.path.join(minecraft_dir, 'mods')
    versions_dir = os.path.join(minecraft_dir, 'versions')

    backups_created = []

    # Бэкап модов
    if os.path.exists(mods_dir):
        backup_path = create_backup(mods_dir, "mods")
        if backup_path:
            backups_created.append(backup_path)

    # Бэкап версий
    if os.path.exists(versions_dir):
        backup_path = create_backup(versions_dir, "versions")
        if backup_path:
            backups_created.append(backup_path)

    # Показываем результат
    if backups_created:
        backup_info = "Созданы бэкапы:\n" + "\n".join([f"• {os.path.basename(b)}" for b in backups_created])
        messagebox.showinfo("Бэкапы созданы", backup_info)
    else:
        messagebox.showinfo("Бэкапы", "Не удалось создать бэкапы (папки не найдены)")


# Функция для удаления всех бэкапов
def delete_all_backups():
    """Удаляет все бэкапы (только по кнопке!)"""
    backup_dir = os.path.join(CONFIG['minecraft_dir'], 'backups')
    if not os.path.exists(backup_dir):
        messagebox.showinfo("Бэкапы", "Папка бэкапов не существует")
        return

    # Подтверждение удаления
    result = messagebox.askyesno(
        "Удаление бэкапов",
        "Вы уверены, что хотите удалить ВСЕ бэкапы?\nЭто действие нельзя отменить!"
    )

    if not result:
        return

    try:
        shutil.rmtree(backup_dir)
        messagebox.showinfo("Бэкапы", "Все бэкапы удалены")
        print("Удалены все бэкапы")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить бэкапы: {str(e)}")


# Функция для показа информации о бэкапах
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
            backups.append((filename, f"{size:.1f} МБ", time_created.strftime("%d.%m.%Y %H:%M")))

    if not backups:
        messagebox.showinfo("Бэкапы", "Бэкапы не найдены")
        return

    backups.sort(key=lambda x: x[2], reverse=True)  # Сортируем по дате (новые сверху)

    info_text = f"Созданные бэкапы (всего: {len(backups)}, общий размер: {total_size:.1f} МБ):\n\n"
    for backup in backups:
        info_text += f"• {backup[0]}\n  Размер: {backup[1]}, Создан: {backup[2]}\n\n"

    messagebox.showinfo("Информация о бэкапах", info_text)


# Обновленная функция для удаления модов с бэкапами
def fig1():
    mods_dir = os.path.join(CONFIG['minecraft_dir'])
    items_to_remove2 = [
        os.path.join(mods_dir, 'mods'),
        os.path.join(mods_dir, 'versions')
    ]

    # Создаем бэкапы перед удалением
    backups_created = []
    for item in items_to_remove2:
        if os.path.exists(item):
            backup_type = "mods" if "mods" in item else "versions"
            backup_path = create_backup(item, backup_type)
            if backup_path:
                backups_created.append(backup_path)

    # Удаляем папки
    for item2 in items_to_remove2:
        if os.path.exists(item2):
            try:
                if os.path.isdir(item2):
                    shutil.rmtree(item2)
                else:
                    os.remove(item2)
                print(f"Удалено: {item2}")
            except Exception as e:
                print(f"Ошибка удаления {item2}: {str(e)}")

    # Показываем информацию о созданных бэкапах
    if backups_created:
        backup_info = "Созданы бэкапы:\n" + "\n".join([f"• {os.path.basename(b)}" for b in backups_created])
        messagebox.showinfo("Бэкапы созданы", backup_info)
    else:
        messagebox.showinfo("Очистка", "Папки mods и versions очищены (бэкапы не создавались)")


# Функция для получения списка доступных бэкапов
def get_available_backups():
    """Возвращает список доступных бэкапов с датами"""
    backup_dir = os.path.join(CONFIG['minecraft_dir'], 'backups')
    if not os.path.exists(backup_dir):
        return []

    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip'):
            file_path = os.path.join(backup_dir, filename)
            time_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
            backups.append({
                'filename': filename,
                'path': file_path,
                'type': 'mods' if 'mods' in filename else 'versions',
                'date': time_created.strftime("%d.%m.%Y %H:%M"),
                'timestamp': time_created
            })

    # Группируем бэкапы по времени создания
    backup_groups = {}
    for backup in backups:
        base_name = backup['filename'].split('_backup_')[1].replace('.zip', '')
        if base_name not in backup_groups:
            backup_groups[base_name] = {}
        backup_groups[base_name][backup['type']] = backup

    # Формируем список полных бэкапов (у которых есть и моды и версии)
    complete_backups = []
    for base_name, group in backup_groups.items():
        if 'mods' in group and 'versions' in group:
            complete_backups.append({
                'timestamp': base_name,
                'mods': group['mods'],
                'versions': group['versions'],
                'date': group['mods']['date']  # Берем дату из модов
            })

    # Сортируем по дате (новые сверху)
    complete_backups.sort(key=lambda x: x['mods']['timestamp'], reverse=True)
    return complete_backups


# Функция восстановления из бэкапа
def restore_from_backup(backup_data):
    """Восстанавливает моды и версии из выбранного бэкапа"""
    try:
        minecraft_dir = CONFIG['minecraft_dir']
        mods_dir = os.path.join(minecraft_dir, 'mods')
        versions_dir = os.path.join(minecraft_dir, 'versions')

        # Создаем бэкап текущего состояния перед восстановлением
        current_backup_created = []
        if os.path.exists(mods_dir):
            current_backup = create_backup(mods_dir, "current_mods_before_restore")
            if current_backup:
                current_backup_created.append(current_backup)

        if os.path.exists(versions_dir):
            current_backup = create_backup(versions_dir, "current_versions_before_restore")
            if current_backup:
                current_backup_created.append(current_backup)

        # Восстанавливаем моды
        if 'mods' in backup_data:
            mods_backup = backup_data['mods']['path']
            if os.path.exists(mods_dir):
                shutil.rmtree(mods_dir)
            os.makedirs(mods_dir)

            with zipfile.ZipFile(mods_backup, 'r') as zip_ref:
                zip_ref.extractall(mods_dir)
            print(f"Восстановлены моды из: {os.path.basename(mods_backup)}")

        # Восстанавливаем версии
        if 'versions' in backup_data:
            versions_backup = backup_data['versions']['path']
            if os.path.exists(versions_dir):
                shutil.rmtree(versions_dir)
            os.makedirs(versions_dir)

            with zipfile.ZipFile(versions_backup, 'r') as zip_ref:
                zip_ref.extractall(versions_dir)
            print(f"Восстановлены версии из: {os.path.basename(versions_backup)}")

        # Показываем результат
        backup_info = f"✅ Восстановление завершено!\n\n"
        backup_info += f"📅 Дата бэкапа: {backup_data['date']}\n"
        if 'mods' in backup_data:
            backup_info += f"📦 Моды: восстановлено\n"
        if 'versions' in backup_data:
            backup_info += f"⚙️ Версии: восстановлено\n"

        if current_backup_created:
            backup_info += f"\n📋 Создан бэкап текущего состояния перед восстановлением"

        messagebox.showinfo("Восстановление завершено", backup_info)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось восстановить из бэкапа: {str(e)}")
        print(f"Ошибка восстановления: {str(e)}")


# Функция выбора бэкапа для восстановления
def choose_backup_to_restore():
    """Показывает диалог выбора бэкапа для восстановления"""
    backups = get_available_backups()

    if not backups:
        messagebox.showinfo("Восстановление", "Нет доступных бэкапов для восстановления")
        return

    # Создаем окно выбора бэкапа
    backup_window = tk.Toplevel(win)
    backup_window.title("Выбор бэкапа для восстановления")
    backup_window.geometry("600x400")
    backup_window.configure(bg='#2b2b2b')
    backup_window.transient(win)
    backup_window.grab_set()

    # Заголовок
    title_label = ttk.Label(backup_window, text="Выберите бэкап для восстановления:",
                            font=('Comfortaa', 12, 'bold'))
    title_label.pack(pady=10)

    # Фрейм для списка бэкапов
    frame = ttk.Frame(backup_window)
    frame.pack(fill='both', expand=True, padx=20, pady=10)

    # Создаем Treeview для отображения бэкапов
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

        tree.insert('', 'end', values=(
            backup['date'],
            ' + '.join(components)
        ), tags=(backup['timestamp'],))

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
            result = messagebox.askyesno(
                "Подтверждение восстановления",
                f"Вы уверены, что хотите восстановить игру из бэкапа от {selected_backup['date']}?\n\n"
                f"Текущие моды и версии будут заменены."
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


# Обновленная функция "Починить игру" с выбором действия
def repair_game_with_options():
    """Расширенная функция починки игры с выбором действия"""
    choice_window = tk.Toplevel(win)
    choice_window.title("Починить игру")
    choice_window.geometry("400x250")
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

    def restore_backup():
        choice_window.destroy()
        choose_backup_to_restore()

    def cancel():
        choice_window.destroy()

    # Кнопки действий
    ttk.Button(choice_window, text="🧹 Очистить игру (удалить моды и версии)",
               command=cleanup_only, width=30).pack(pady=10)

    ttk.Button(choice_window, text="🔄 Восстановить из бэкапа",
               command=restore_backup, width=30).pack(pady=10)

    ttk.Button(choice_window, text="❌ Отмена",
               command=cancel, width=20).pack(pady=20)


# Функция быстрого восстановления из последнего бэкапа
def restore_latest_backup():
    """Быстрое восстановление из самого свежего бэкапа"""
    backups = get_available_backups()

    if not backups:
        messagebox.showinfo("Восстановление", "Нет доступных бэкапов")
        return

    latest_backup = backups[0]  # Самый свежий бэкап

    result = messagebox.askyesno(
        "Восстановление из последнего бэкапа",
        f"Восстановить игру из последнего бэкапа?\n\n"
        f"📅 Дата: {latest_backup['date']}\n"
        f"🔄 Будет восстановлено: Моды + Версии\n\n"
        f"Текущие данные будут заменены."
    )

    if result:
        restore_from_backup(latest_backup)

# Обновляем меню "Инструменты"
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
settings_menu.add_command(label="Починить игру", command=repair_game_with_options)  # Теперь с выбором!
settings_menu.add_command(label="Восстановить из последнего бэкапа", command=restore_latest_backup)
settings_menu.add_separator()
settings_menu.add_command(label="Открыть папку с игрой", command=open_game_folder)
settings_menu.add_command(label="Сделать бэкап", command=create_manual_backup)
settings_menu.add_command(label="Показать бэкапы", command=show_backup_info)
settings_menu.add_command(label="Удалить ВСЕ бэкапы", command=delete_all_backups)
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
                with ZipFile(zip_path, 'r') as zip_file:
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
        servers_file_path = os.path.join(CONFIG['minecraft_dir'], 'servers.dat')

        # Проверяем существование файла
        if not os.path.exists(servers_file_path):
            print("Файл servers.dat не найден, начинаем загрузку...")

            # Обновляем ссылку на актуальную
            params = {'public_key': 'https://disk.yandex.ru/d/WM_flS--BathOQ'}
            base_url1 = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
            response = requests.get(base_url1, params=params)
            response.raise_for_status()
            download_url = response.json().get('href')

            if not download_url:
                return

            with open(servers_file_path, 'wb') as f:
                dl_response = requests.get(download_url, stream=True)
                dl_response.raise_for_status()
                for chunk in dl_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print("Файл servers.dat успешно установлен в папку YamalPixel")
        else:
            print("Файл servers.dat уже существует, загрузка не требуется")

    except Exception as e:
        print(f"Ошибка загрузки servers.dat: {str(e)}")



    if not username.get().strip():
        messagebox.showerror("Ошибка", "Введите имя пользователя!")
        return
    os.makedirs(CONFIG['minecraft_dir'], exist_ok=True)

    progress_window = tk.Toplevel(win)
    progress_window.title("Запуск Minecraft")
    progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=20)

    def install_and_run():
        try:
            selected_version = version_combobox.get()

            # Устанавливаем Minecraft версию, если она отсутствует
            install_minecraft_version(
                version=CONFIG['version'],
                progress_callback={
                    "setStatus": lambda t: None,
                    "setProgress": lambda v: progress.configure(value=v),
                    "setMax": lambda m: progress.configure(maximum=m)
                }
            )

            # Устанавливаем Fabric только если он нужен для выбранной версии
            if is_fabric_needed(selected_version):
                if not check_minecraft_and_fabric_installed():
                    minecraft_launcher_lib.fabric.install_fabric(
                        minecraft_version=CONFIG['version'],
                        loader_version=CONFIG['fabric_loader'],
                        minecraft_directory=CONFIG['minecraft_dir'],
                        callback={
                            "setStatus": lambda t: None,
                            "setProgress": lambda v: progress.configure(value=v),
                            "setMax": lambda m: progress.configure(maximum=m)
                        }
                    )
                else:
                    print("Пропуск установки Fabric, так как он уже установлен.")
            else:
                print("Fabric не требуется для выбранной версии. Пропуск установки.")

            # Загрузка модов только для YamalPixel
            if selected_version == "YamalPixel":
                checker1()

            # Формирование команды запуска
            if is_fabric_needed(selected_version):
                # Запуск с Fabric
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
                # Запуск без Fabric (чистая версия)
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
    text="Включить музыку",style='BW2.TLabel', variable=enabled1, command=lambda: mscoff() if enabled1.get() else mscon(),
).pack(padx=6, pady=6, anchor=tk.NE)

# Функция для показа онлайн игроков
def show_online_players():
    try:
        server = JavaServer.lookup("90.151.59.120:25565")
        status = server.status()
        label_online.config(text=f"Онлайн: {status.players.online}", background="green" if status.players.online > 0 else "red")
    except Exception as e:
        label_online.config(text="Ошибка подключения", background="red")

btn_update_online = ttk.Button(win, text="Показать онлайн", style="BW.TLabel", command=show_online_players)
btn_update_online.place(relx=.5, rely=0.58, width=150, height=25, anchor="c")

# Функция для выбора версии игры
def select_version(event):
    selected_version = version_combobox.get()
    if selected_version == "YamalPixel + mods":
        CONFIG['version'] = '1.18.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.7.10":
        CONFIG['version'] = '1.7.10'
        CONFIG['fabric_loader'] = None  # Fabric не поддерживает 1.7.10
    elif selected_version == "Minecraft 1.8.9":
        CONFIG['version'] = '1.8.9'
        CONFIG['fabric_loader'] = None  # Fabric не поддерживает 1.8.9
    elif selected_version == "Minecraft 1.12.2":
        CONFIG['version'] = '1.12.2'
        CONFIG['fabric_loader'] = None  # Fabric не поддерживает 1.12.2 напрямую
    elif selected_version == "Minecraft 1.14.4":
        CONFIG['version'] = '1.14.4'
        CONFIG['fabric_loader'] = None  # Пример версии Fabric для 1.14.4
    elif selected_version == "Minecraft 1.14.4 + Fabric":
        CONFIG['version'] = '1.14.4'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.15.2":
        CONFIG['version'] = '1.15.2'
        CONFIG['fabric_loader'] = None  # Пример версии Fabric для 1.15.2
    elif selected_version == "Minecraft 1.15.2 + Fabric":
        CONFIG['version'] = '1.15.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.16.5":
        CONFIG['version'] = '1.16.5'
        CONFIG['fabric_loader'] = None  # Fabric не используется
    elif selected_version == "Minecraft 1.16.5 + Fabric":
        CONFIG['version'] = '1.16.5'
        CONFIG['fabric_loader'] = '0.16.10'  # Пример версии Fabric для 1.16.5
    elif selected_version == "Minecraft 1.17.1":
        CONFIG['version'] = '1.17.1'
        CONFIG['fabric_loader'] = None  # Пример версии Fabric для 1.17.1
    elif selected_version == "Minecraft 1.17.1 + Fabric":
        CONFIG['version'] = '1.17.1'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.18.2":
        CONFIG['version'] = '1.18.2'
        CONFIG['fabric_loader'] = None  # Пример версии Fabric для 1.18.2
    elif selected_version == "Minecraft 1.18.2 + Fabric":
        CONFIG['version'] = '1.18.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.19.2":
        CONFIG['version'] = '1.19.2'
        CONFIG['fabric_loader'] = None  # Пример версии Fabric для 1.19.2
    elif selected_version == "Minecraft 1.19.2 + Fabric":
        CONFIG['version'] = '1.19.2'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.20.1":
        CONFIG['version'] = '1.20.1'
        CONFIG['fabric_loader'] = '0.16.10'  # Пример версии Fabric для 1.20.1
    elif selected_version == "Minecraft 1.20.1 + Fabric":
        CONFIG['version'] = '1.20.1'
        CONFIG['fabric_loader'] = '0.16.10'
    elif selected_version == "Minecraft 1.20.2":
        CONFIG['version'] = '1.20.2'
        CONFIG['fabric_loader'] = None
    elif selected_version == "Minecraft 1.20.2 + Fabric":
        CONFIG['version'] = '1.20.2'
        CONFIG['fabric_loader'] = '0.16.10'
    # Версия 1.21.x
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
        CONFIG['fabric_loader'] = None

    elif selected_version == "Minecraft 1.21.3":
        CONFIG['version'] = '1.21.3'
        CONFIG['fabric_loader'] = None

    elif selected_version == "Minecraft 1.21.3 + Fabric":
        CONFIG['version'] = '1.21.3'
        CONFIG['fabric_loader'] = None

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

# Запуск главного цикла
win.mainloop()