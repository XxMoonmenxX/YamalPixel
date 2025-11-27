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
#import ctypes







# ============== НОВЫЙ КОД ДЛЯ ПРОВЕРКИ И УСТАНОВКИ JAVA ==============
def check_java_version():
    try:
        result = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT, text=True)
        version_match = re.search(r'version "([1-9]\d*\.\d+\.\d+)', result)
        if version_match:
            version = version_match.group(1)
            major_version = int(version.split('.')[0])
            if major_version >= 17:
                print(f"Установлена Java версии {version}")
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
            messagebox.showinfo("Успех :D", "Java 17 успешно установлена! ЗАПУСКАЙ!!!")
        except Exception as e:
            messagebox.showerror("АШЫПКА :D", f"Java 17 установлена. ЗАПУСКАЙ!!!!")
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
        # ============= ОСНОВНЫЕ БИБЛИОТЕКИ =============
        # Fabric API (обязательно первый!)
        {'url': 'https://disk.yandex.ru/d/Qe__28HSua0MTg', 'file': 'fabric-api-0.77.0.jar'},

        # Графические оптимизации
        {'url': 'https://disk.yandex.ru/d/WuCdSbKpHyF-1Q', 'file': 'sodium-fabric-mc1.18.2-0.4.1+build.15.jar'},       #
        {'url': 'https://disk.yandex.ru/d/LTHdaKPKw6OeBw', 'file': 'indium-0.7.10+mc1.18.2.zip'},       #
        {'url': 'https://disk.yandex.ru/d/hWGlklVaUIuB9g', 'file': 'sodium-extra-0.4.1.jar'}, #

        # ============= ОСНОВНЫЕ МОДЫ =============
        {'url': 'https://disk.yandex.ru/d/LiTGqt32O3EYTQ', 'file': 'AdvancedReborn-1.18.2-1.0.6.jar'}, #


        # ============= ДОПОЛНИТЕЛЬНЫЕ МОДЫ =============
        {'url': 'https://disk.yandex.ru/d/mnHcD27ReV24Nw', 'file': 'RebornCore-5.2.0.jar'},    #
        {'url': 'https://disk.yandex.ru/d/-ZDLDoU0aMVIBw', 'file': 'TechReborn-5.2.0.jar'},     # mod6.jar
        {'url': 'https://disk.yandex.ru/d/7O1h0pGQFD553g', 'file': 'Xaeros_Minimap_22.14.1_Fabric_1.18.2.jar'}, # mod7.jar
        {'url': 'https://disk.yandex.ru/d/9nygMaFFsDLx1Q', 'file': 'agape_space_18_2-0.5.16.jar'}, # mod8.jar

         {'url': 'https://disk.yandex.ru/d/vNOUfe3TeIPSDg', 'file': 'architectury-4.9.83-fabric.jar'},          # Дополнительный мод
      #
        {'url': 'https://disk.yandex.ru/d/7hbnmzKH_dB6_w', 'file': 'betterdroppeditems-1.3.2-1.18.2.jar'},
        {'url': 'https://disk.yandex.ru/d/agV4dqkgBjLRJg', 'file': 'cloth-config-6.3.81-fabric.jar'},
        {'url': 'https://disk.yandex.ru/d/5_I5Q7SE6WmExw', 'file': 'fabric-language-kotlin-1.7.3+kotlin.1.6.20.jar'},
        {'url': 'https://disk.yandex.ru/d/jw-XOiWffqRRvw', 'file': 'iris-mc1.18.2-1.3.1.jar'},

        {'url': 'https://disk.yandex.ru/d/kGgcgJGlg9Bhvg', 'file': 'lithium-fabric-mc1.18.2-0.7.10.jar'},
        {'url': 'https://disk.yandex.ru/d/UJn-CCA_Uc2QPA', 'file': 'JEI.zip'},
        {'url': 'https://disk.yandex.ru/d/uDx4tECrIo_4HQ', 'file': 'supplementaries-1.18.2-1.4.11.jar'},
        {'url': 'https://disk.yandex.ru/d/ISYwMEs6GCkOUQ', 'file': 'modmenu-3.2.5.jar'},

        #добавленные зависимости
        {'url': 'https://disk.yandex.ru/d/Qmd74h8szwpglQ', 'file': 'autoconfig1u-3.4.0.jar'},
        {'url': 'https://disk.yandex.ru/d/sEMe8EGrqKfxcA', 'file': 'NoIndium-1.0.2+1.18.2.jar'},
        {'url': 'https://disk.yandex.ru/d/1d7-rrBDObktmg', 'file': 'omega-config-base-1.2.3-1.18.1.jar'},
        {'url': 'https://disk.yandex.ru/d/5Zv2QC9-SelwDA', 'file': 'pal-1.5.0.jar'},
        {'url': 'https://disk.yandex.ru/d/ahOdVWSraF65xQ', 'file': 'Patchouli-1.18.2-66-FABRIC.jar'}


    ]
}


mixer.init()
mixer.music.load('Obuse - Menu song.mp3')

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

    # Проверка наличия файлов перед загрузкой
    missing_mods = []
    for mod in CONFIG['mods']:
        mod_path = os.path.join(mods_dir, mod['file'])
        if not os.path.exists(mod_path):
            missing_mods.append(mod)

    # Загрузка отсутствующих файлов
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

    # Распаковка zip-файлов
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

def runn():
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
                        "-Xmx6G",
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
            messagebox.showerror("Ошибка", f"Ошибка запуска: {str(e)}   начинается повторный запуск...\n Ожидайте...\n После третьей ошибки попробуйте VPN")
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
label_online.place(relx=0.5, rely=0.61, anchor="c")

def mscon():
    mixer.music.play()
def mscoff():
    mixer.music.stop()

enabled1 = tk.IntVar()
ttk.Checkbutton(
    text="Включить музыку",style='BW2.TLabel', variable=enabled1, command=lambda: mscoff() if enabled1.get() else mscon(),

).pack(padx=6, pady=6, anchor=tk.NE)




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