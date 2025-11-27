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


# ============== НОВЫЙ КОД ДЛЯ ПРОВЕРКИ И УСТАНОВКИ JAVA ==============
def check_java_version():
    try:
        result = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT, text=True)
        version_match = re.search(r'version "17\.(\d+)\.(\d+)', result)
        if version_match:
            print("Необходимая версия JAVA установлена.")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return False


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
                # Ссылка на последнюю версию Java 17 для Windows
                url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_windows_hotspot_17.0.11_9.msi"
                msi_path = os.path.join(os.environ['TEMP'], 'OpenJDK17.msi')

                urllib.request.urlretrieve(url, msi_path, reporthook=lambda c, b, t: download_progress_hook(c, b, t))

                subprocess.run(f'msiexec /i "{msi_path}" /quiet', shell=True, check=True)
                os.remove(msi_path)

            elif system == "Linux":
                # Установка для Linux (Debian/Ubuntu)
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
                # Установка для macOS через Homebrew
                subprocess.run(
                    '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                    shell=True, check=True)
                subprocess.run('brew tap adoptium/temurin', shell=True, check=True)
                subprocess.run('brew install --cask temurin17', shell=True, check=True)

            java_window.destroy()
            messagebox.showinfo("Успех", "Java 17 успешно установлена!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка установки Java: {str(e)}")
            sys.exit(1)

    if not check_java_version():
        threading.Thread(target=install_thread, daemon=True).start()
    else:
        java_window.destroy()


# ============== ИНИЦИАЛИЗАЦИЯ ПРОВЕРКИ JAVA ПРИ ЗАПУСКЕ ==============
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




CONFIG = {
    'version': '1.18.2',
    'fabric_loader': '0.16.10',
    'minecraft_dir': os.path.expanduser("~/YamalPixel"),
    'mods': [
        #{'url': 'https://disk.yandex.ru/d/mpSRVb3HqSmd7g', 'file': 'mod.jar'},#fallingtree

        #{'url': 'https://disk.yandex.ru/d/jXdwfw88pt9ALA', 'file': 'mod2.jar'},#reborncore
        #{'url': 'https://disk.yandex.ru/d/hVkWitZvruEcOQ', 'file': 'mod3.jar'},#techreborn
        #{'url': 'https://disk.yandex.ru/d/znHvWPCIHLO3Jw', 'file': 'mod4.jar'},#twilightforest
        #{'url': 'https://disk.yandex.ru/d/L6juClC1bifrKA', 'file': 'mod4.jar'},#xaeros minimap
        #{'url': 'https://disk.yandex.ru/d/3c1hfaQJqOrzyw', 'file': 'mod5.jar'},#appliedenegretics2
        #{'url': 'https://disk.yandex.ru/d/HkF6B5uZOoU1qw', 'file': 'mod6.jar'},#fabricAPI
        {'url': 'https://disk.yandex.ru/d/7nvQi6Ox5JwOOw', 'file': 'mod8.zip'},#indium.zip
       # {'url': 'https://disk.yandex.ru/d/cyBsn5tNkuym1g', 'file': 'mod7.jar'},#modernfix
        #{'url': 'https://disk.yandex.ru/d/2iNrg9e6x0alnA', 'file': 'mod8.jar'},#moreculling
        #{'url': 'https://disk.yandex.ru/d/UJn-CCA_Uc2QPA', 'file': 'mod9.zip'},#jei.zip
        {'url': 'https://disk.yandex.ru/d/PNJeUWo4UIe37A', 'file': 'mod10.jar'},#omegaconfig
        #{'url': 'https://disk.yandex.ru/d/o-os2Ev6VrlWQg', 'file': 'mod11.jar'}#sodium
    ]
}


mixer.init()
mixer.music.load('Obuse - Menu song.mp3')
mixer.music.play()
mixer.music.set_volume(0.1)

win = ThemedTk(theme="arc")
win.geometry("1920x1080")
win.title('YamPixel')
win.attributes("-fullscreen", True)
win.after(100, initial_check)

# GUI элементы
bag = tk.PhotoImage(file="logo.png")
img = ttk.Label(win, image=bag)
img.place(x=0, y=-1)


def fullsc(): win.attributes("-fullscreen", True)


def outscrn(): win.attributes("-fullscreen", False)


def checker1():
    mods_dir = os.path.join(CONFIG['minecraft_dir'], 'mods')
    os.makedirs(mods_dir, exist_ok=True)
    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'

    for mod in CONFIG['mods']:
        mod_path = os.path.join(mods_dir, mod['file'])
        if os.path.exists(mod_path):
            continue

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

    for mod in CONFIG['mods']:
        if mod['file'].endswith('.zip'):
            zip_path = os.path.join(mods_dir, mod['file'])
            extract_dir = os.path.join(mods_dir)

            try:
                with ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall(path=extract_dir)
                    print(f"Содержимое архива {mod['file']} успешно извлечено в папку mods")
            except Exception as e:
                print(f"Ошибка распаковки архива {mod['file']}: {str(e)}")

def runn():

    if not username.get().strip():
        messagebox.showerror("Ошибка", "Введите имя пользователя!")
        return
    #mixer.music.stop()
    os.makedirs(CONFIG['minecraft_dir'], exist_ok=True)

    progress_window = tk.Toplevel(win)
    progress_window.title("Запуск Minecraft")

    progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=20)

    def install_and_run():
        try:
            # Установка Fabric
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

            # Проверка и загрузка модов
            checker1()

            # Запуск игры
            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}",
                minecraft_directory=CONFIG['minecraft_dir'],
                options={
                    'username': username.get(),
                    'jvmArguments': [
                        "-Xmx4G",
                        "-Duser.language=ru",
                        "-Duser.country=RU",
                        "-Dfile.encoding=UTF-8"
                    ],
                    'server': '90.151.59.120',
                    'port': '25565',
                    'gameLocale': 'ru_RU'
                }
            )

            progress_window.destroy()
            subprocess.Popen(command)
        except Exception as e:
            runn()
            messagebox.showerror("Ошибка", f"Ошибка запуска: {str(e)}   начинается повторный запуск...")
            progress_window.destroy()

    threading.Thread(target=install_and_run, daemon=True).start()

style = ttk.Style()
style.configure("BW.TLabel", background="pink")
app = ttk.Style()
app.configure('TLabel', font=('Comfortaa', 12))
app.configure('TButton', font=('Comfortaa', 12))



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
label_online.place(relx=.5, rely=0.61, anchor="c")

def show_online_players():
    try:
        server = JavaServer.lookup("90.151.59.120:25565")
        status = server.status()
        label_online.config(text=f"Онлайн: {status.players.online}", background="green" if status.players.online > 0 else "red")
    except Exception as e:
        label_online.config(text="Ошибка подключения", background="red")

btn_update_online = ttk.Button(win, text="Показать онлайн", style="BW.TLabel", command=show_online_players)
btn_update_online.place(relx=.5, rely=0.58, width=150, height=25, anchor="c")



win.mainloop()