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
from zipfile import ZipFile
import platform
import urllib.request
import sys
import shutil
import logging
from pypresence import Presence
from pathlib import Path

CURRENT_VERSION = "0.2.123" #обновление
logging.basicConfig(filename='launcher.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Конфигурация ресурсов
RESOURCE_DIR = Path.home() / "YamalPixelRes"
RESOURCES = {
    "logo.png": "https://disk.yandex.ru/i/ztKpQOZEjQDE_Q",
    "menu_song.mp3": "https://disk.yandex.ru/d/Ahqnmj2T8YlNKg"
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

        # Убираем Markdown-разметку
        changelog = re.sub(r'\#{2,}', '', changelog)
        changelog = re.sub(r'\- ', '• ', changelog)

        release_data = response.json()
        latest_version = release_data['tag_name'].lstrip('v')

        if latest_version != CURRENT_VERSION:
            logging.info(f"Найдена новая версия: {latest_version}")
            answer = messagebox.askyesno(
                "Обновление",
                f"Доступна версия {latest_version}.\n\n{changelog}\n\n Обновить?"
            )
            if answer:
                # Ищем любой EXE-файл в ассетах
                update_asset = next(
                    (asset for asset in release_data['assets']
                     if asset['name'].lower().endswith('.exe') and "yamalpixel" in asset['name'].lower()),
                    None
                )

                if update_asset:
                    download_and_install_update(update_asset['browser_download_url'])
                else:
                    messagebox.showerror("Ошибка",
                                         "EXE-файл не найден в релизе. Постучите разрабу по голове.")
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

        # Создаем бэкап старой версии
        if os.path.exists(old_exe):
            os.rename(old_exe, backup_exe)

        # Устанавливаем новую версию
        os.rename(temp_exe, old_exe)

        # Удаляем бэкап и временные файлы
        for file_to_remove in [backup_exe, temp_exe]:
            if os.path.exists(file_to_remove):
                try:
                    os.remove(file_to_remove)
                except Exception as e:
                    logging.error(f"Ошибка удаления {file_to_remove}: {str(e)}")

        # Перезапускаем лаунчер
        subprocess.Popen([old_exe], shell=True)

        # Удаляем старую версию после успешного запуска новой
        if os.path.exists(backup_exe):
            try:
                os.remove(backup_exe)
                logging.info("Старая версия лаунчера успешно удалена.")
            except Exception as e:
                logging.error(f"Ошибка удаления старой версии: {str(e)}")

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
    items_to_remove = [
        os.path.join(launcher_dir, 'config'),
        os.path.join(launcher_dir, 'patchouli_books'),
        os.path.join(launcher_dir, 'patchouli_data.json'),
        os.path.join(launcher_dir, 'logs'),
        os.path.join(launcher_dir, 'logo.png'),
        os.path.join(launcher_dir, 'Obuse - Menu song.mp3'),
        os.path.join(launcher_dir, 'YamalPixelLauncer_V_0.2.06.exe')
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


# Конфигурация
CONFIG = {
    'version': '1.18.2',
    'fabric_loader': '0.16.10',
    'minecraft_dir': os.path.expanduser("~/YamalPixel"),
    'mods': [
        {'url': 'https://disk.yandex.ru/d/Qe__28HSua0MTg', 'file': 'fabric-api-0.77.0.jar'},
        {'url': 'https://disk.yandex.ru/d/WuCdSbKpHyF-1Q', 'file': 'sodium-fabric-mc1.18.2-0.4.1+build.15.jar'},
        {'url': 'https://disk.yandex.ru/d/LTHdaKPKw6OeBw', 'file': 'indium-0.7.10+mc1.18.2.zip'},
        {'url': 'https://disk.yandex.ru/d/LiTGqt32O3EYTQ', 'file': 'AdvancedReborn-1.18.2-1.0.6.jar'},
        {'url': 'https://disk.yandex.ru/d/mnHcD27ReV24Nw', 'file': 'RebornCore-5.2.0.jar'},
        {'url': 'https://disk.yandex.ru/d/-ZDLDoU0aMVIBw', 'file': 'TechReborn-5.2.0.jar'},
        {'url': 'https://disk.yandex.ru/d/7O1h0pGQFD553g', 'file': 'Xaeros_Minimap_22.14.1_Fabric_1.18.2.jar'},
        {'url': 'https://disk.yandex.ru/d/vNOUfe3TeIPSDg', 'file': 'architectury-4.9.83-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/7hbnmzKH_dB6_w', 'file': 'betterdroppeditems-1.3.2-1.18.2.jar'},
        {'url': 'https://disk.yandex.ru/d/agV4dqkgBjLRJg', 'file': 'cloth-config-6.3.81-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/5_I5Q7SE6WmExw', 'file': 'fabric-language-kotlin-1.7.3+kotlin.1.6.20.jar'},
        {'url': 'https://disk.yandex.ru/d/kGgcgJGlg9Bhvg', 'file': 'lithium-fabric-mc1.18.2-0.7.10.jar'},
        {'url': 'https://disk.yandex.ru/d/UJn-CCA_Uc2QPA', 'file': 'JEI.zip'},
        {'url': 'https://disk.yandex.ru/d/ISYwMEs6GCkOUQ', 'file': 'modmenu-3.2.5.jar'},
        {'url': 'https://disk.yandex.ru/d/Qmd74h8szwpglQ', 'file': 'autoconfig1u-3.4.0.jar'},
        {'url': 'https://disk.yandex.ru/d/sEMe8EGrqKfxcA', 'file': 'NoIndium-1.0.2+1.18.2.jar'},
        {'url': 'https://disk.yandex.ru/d/1d7-rrBDObktmg', 'file': 'omega-config-base-1.2.3-1.18.1.jar'},
        {'url': 'https://disk.yandex.ru/d/5Zv2QC9-SelwDA', 'file': 'pal-1.5.0.jar'},
        {'url': 'https://disk.yandex.ru/d/ahOdVWSraF65xQ', 'file': 'Patchouli-1.18.2-66-FABRIC.jar'}
    ]
}

# Инициализация звука
mixer.init()
#mixer.music.load('Obuse - Menu song.mp3')
mixer.music.set_volume(0.1)

# Создание главного окна
win = ThemedTk(theme="arc")
win.geometry("1920x1080")
win.title('YamPixel')
win.attributes("-fullscreen", True)
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

# Функция для удаления модов
def fig1():
    mods_dir = os.path.join(CONFIG['minecraft_dir'],'mods')
    items_to_remove2 = [
        os.path.join(mods_dir, 'fabric-api-0.77.0.jar'),
        os.path.join(mods_dir, 'sodium-fabric-mc1.18.2-0.4.1+build.15.jar'),
        os.path.join(mods_dir, 'indium-0.7.10+mc1.18.2.zip'),
        os.path.join(mods_dir, 'RebornCore-5.2.0.jar'),
        os.path.join(mods_dir, 'TechReborn-5.2.0.jar'),
        os.path.join(mods_dir, 'Xaeros_Minimap_22.14.1_Fabric_1.18.2.jar'),
        os.path.join(mods_dir, 'architectury-4.9.83-fabric.jar'),
        os.path.join(mods_dir, 'betterdroppeditems-1.3.2-1.18.2.jar'),
        os.path.join(mods_dir, 'cloth-config-6.3.81-fabric.jar'),
        os.path.join(mods_dir, 'fabric-language-kotlin-1.7.3+kotlin.1.6.20.jar'),
        os.path.join(mods_dir, 'iris-mc1.18.2-1.3.1.jar'),
        os.path.join(mods_dir, 'lithium-fabric-mc1.18.2-0.7.10.jar'),
        os.path.join(mods_dir, 'supplementaries-1.18.2-1.4.11.jar'),
        os.path.join(mods_dir, 'modmenu-3.2.5.jar'),
        os.path.join(mods_dir, 'autoconfig1u-3.4.0.jar'),
        os.path.join(mods_dir, 'NoIndium-1.0.2+1.18.2.jar'),
        os.path.join(mods_dir, 'omega-config-base-1.2.3-1.18.1.jar'),
        os.path.join(mods_dir, 'pal-1.5.0.jar'),
        os.path.join(mods_dir, 'Patchouli-1.18.2-66-FABRIC.jar')
    ]
    for item2 in items_to_remove2:
        if os.path.exists(item2):
            if os.path.isdir(item2):
                shutil.rmtree(item2)
            else:
                os.remove(item2)
            print(f"Удалено: {item2}")

# Меню "Инструменты"
menu_bar = tk.Menu(win)
win.config(menu=menu_bar)
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_separator(background='#FFB6C1')
settings_menu.configure(
    tearoffcommand=lambda: None,
    postcommand=lambda: settings_menu.configure(bg='#FFB6C1')
)
menu_bar.add_cascade(label="Инструменты", menu=settings_menu)
settings_menu.add_command(label="Починить игру", command=fig1)

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
        "Minecraft 1.20.1 + Fabric"
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
        CONFIG['fabric_loader'] = '0.4.8'  # Пример версии Fabric для 1.14.4
    elif selected_version == "Minecraft 1.14.4 + Fabric":
        CONFIG['version'] = '1.14.4'
        CONFIG['fabric_loader'] = '0.4.8'
    elif selected_version == "Minecraft 1.15.2":
        CONFIG['version'] = '1.15.2'
        CONFIG['fabric_loader'] = '0.6.1'  # Пример версии Fabric для 1.15.2
    elif selected_version == "Minecraft 1.15.2 + Fabric":
        CONFIG['version'] = '1.15.2'
        CONFIG['fabric_loader'] = '0.6.1'
    elif selected_version == "Minecraft 1.16.5":
        CONFIG['version'] = '1.16.5'
        CONFIG['fabric_loader'] = None  # Fabric не используется
    elif selected_version == "Minecraft 1.16.5 + Fabric":
        CONFIG['version'] = '1.16.5'
        CONFIG['fabric_loader'] = '0.11.6'  # Пример версии Fabric для 1.16.5
    elif selected_version == "Minecraft 1.17.1":
        CONFIG['version'] = '1.17.1'
        CONFIG['fabric_loader'] = '0.12.0'  # Пример версии Fabric для 1.17.1
    elif selected_version == "Minecraft 1.17.1 + Fabric":
        CONFIG['version'] = '1.17.1'
        CONFIG['fabric_loader'] = '0.12.0'
    elif selected_version == "Minecraft 1.18.2":
        CONFIG['version'] = '1.18.2'
        CONFIG['fabric_loader'] = '0.13.3'  # Пример версии Fabric для 1.18.2
    elif selected_version == "Minecraft 1.18.2 + Fabric":
        CONFIG['version'] = '1.18.2'
        CONFIG['fabric_loader'] = '0.13.3'
    elif selected_version == "Minecraft 1.19.2":
        CONFIG['version'] = '1.19.2'
        CONFIG['fabric_loader'] = '0.14.22'  # Пример версии Fabric для 1.19.2
    elif selected_version == "Minecraft 1.19.2 + Fabric":
        CONFIG['version'] = '1.19.2'
        CONFIG['fabric_loader'] = '0.14.22'
    elif selected_version == "Minecraft 1.20.1":
        CONFIG['version'] = '1.20.1'
        CONFIG['fabric_loader'] = '0.14.22'  # Пример версии Fabric для 1.20.1
    elif selected_version == "Minecraft 1.20.1 + Fabric":
        CONFIG['version'] = '1.20.1'
        CONFIG['fabric_loader'] = '0.14.22'
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
    "Minecraft 1.20.1 + Fabric"
]

version_combobox = ttk.Combobox(win, values=versions, state="readonly")
version_combobox.current(0)
version_combobox.place(relx=0.5, rely=0.4, anchor="c")
version_combobox.bind("<<ComboboxSelected>>", select_version)

# Запуск главного цикла
win.mainloop()