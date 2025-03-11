import tkinter as tk
from tkinter import ttk
from tkinter import *
import minecraft_launcher_lib
import subprocess
from pygame import mixer
import threading
from mcstatus import JavaServer



mixer.init()
mixer.music.load('Obuse - Menu song.mp3')
mixer.music.play()
mixer.music.set_volume(0.1)

ver = '1.16.5'

win = tk.Tk()
win.geometry("1920x1080")
win.title('YamPixel')

bag = tk.PhotoImage(file="logo.png")
img = ttk.Label(win, image=bag)
img.place(x=0, y=-1)

def fullsc():  # Функция для входа в полноэкранный режим
    win.attributes("-fullscreen", True)

def outscrn():
    win.attributes("-fullscreen", False)

def checkbutton_changed():
    if enabled.get() == 1:
        fullsc()
    else:
        outscrn()

style2 = ttk.Style()
style2.configure("BW2.TLabel", background="pink")

enabled = IntVar()
enabled_checkbutton = ttk.Checkbutton(
    text="Полный экран", variable=enabled, command=checkbutton_changed, style='BW2.TLabel'
)
enabled_checkbutton.pack(padx=6, pady=6, anchor=NE)


def runn():
    minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
    mixer.music.stop()

    # Создаем окно для прогрессбара
    progress_window = tk.Toplevel()
    progress_window.title("Установка Minecraft")

    # Инициализируем прогрессбар
    progress = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=20)

    def printProgressBar(iteration, total):
        progress['value'] = (iteration / total) * 100
        progress_window.update_idletasks()  # Обновляем окно

    def maximum(max_value, value):
        max_value[0] = value

    max_value = [0]

    callback = {
        "setStatus": lambda text: print(text, end='\r'),
        "setProgress": lambda value: printProgressBar(value, max_value[0]),
        "setMax": lambda value: maximum(max_value, value)
    }

    def install_minecraft():
        try:
            # Убедитесь, что версия существует
            if not minecraft_launcher_lib.utils.is_version_valid(ver, minecraft_directory):
                minecraft_launcher_lib.install.install_minecraft_version(ver, minecraft_directory, callback=callback)

            # Дополнительно: установите Forge, если требуется (для модификаций)
            # forge_version = "14.23.5.2855"
            # minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directory)

            # Проверьте наличие всех библиотек
            if not minecraft_launcher_lib.utils.is_version_valid(ver, minecraft_directory):
                raise Exception(f"Версия {ver} не установлена!")
            server_adress = '90.151.59.120'
            options = {
                'username': username.get(),
                'server': server_adress,
                'port': '25565',
                'version': ver,
                'jvmArguments': [
                    f"-Djava.library.path={minecraft_directory}/versions/{ver}/{ver}-natives",  # Путь к нативным файлам
                    f"-cp",
                    minecraft_launcher_lib.command.get_classpath(ver, minecraft_directory)
                    # Автоматическое получение classpath
                ]
            }

            progress_window.destroy()  # Закрываем окно прогрессбара после завершения установки
            subprocess.call(
                minecraft_launcher_lib.command.get_minecraft_command(version=ver, minecraft_directory=minecraft_directory,
                                                                   options=options)
            )
        except Exception as e:
            print(f"Ошибка установки: {e}")


    threading.Thread(target=install_minecraft).start()  # Запускаем установку в отдельном потоке


FONT_PATH = '/Comfortaa-VariableFont_wght.ttf'


style = ttk.Style()
style.configure("BW.TLabel", background="pink")
app = ttk.Style()
app.configure('TLabel', font=('Comfortaa', 12)) # Задаем шрифт и размер для всех меток
app.configure('TButton', font=('Comfortaa', 12)) # Задаем шрифт и размер для всех кнопок



username = ttk.Entry(win, style="BW.TLabel", width=20)
username.place(relx=.5, rely=0.45, anchor="c")

# Создание и размещение кнопки
btn = ttk.Button(win, text="Войти в игру", width=15, style="BW.TLabel", command=runn)
btn.place(relx=0.5, rely=0.5, width=100, height=50, anchor="c")
#btn.justify=CENTER

style.configure("CenterText.TLabel", layout=('Center',))  # Задаем параметры для центрирования текста
style.configure("BW.TLabel", background="pink")  # Подтверждаем стиль фона


style1 = ttk.Style()
style1.configure("BW1.TLabel", background="red")
app1 = ttk.Style()
# Метка для отображения онлайна
label_online = ttk.Label(win, text="Онлайн: 0", style="BW1.TLabel")
label_online.place(relx=.5, rely=0.61, anchor="c")

def show_online_players():
    # Укажите IP-адрес и порт вашего сервера
    server_address = JavaServer.lookup("90.151.59.120:25565")

    # Создаем объект статуса сервера
    status = server_address.status()
    # Обновляем метку с онлайном
    label_online.config(text=f"Онлайн: {status.players.online}")
    label_online.place(relx=.5, rely=0.61, anchor="c")
    if status.players.online > 0:
        label_online.config(text=f"Онлайн: {status.players.online}",background="green")
        label_online.config(style="CenterText.TLabel")
    else:
        label_online.config(text="Онлайн: 0", background="red")

def update_online_button():
    btn_update_online = ttk.Button(win, text="Показать онлайн",style="BW.TLabel", command=show_online_players)
    btn_update_online.place(relx=.5, rely=0.58, width=150, height=25, anchor="c")

# Добавляем кнопку для обновления онлайна
update_online_button()


win.mainloop()