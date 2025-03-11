import tkinter as tk
from tkinter import ttk
from tkinter import *
import minecraft_launcher_lib
import subprocess
from pygame import mixer
import threading

mixer.init()
mixer.music.load('Obuse - Menu song.mp3')
mixer.music.play()
mixer.music.set_volume(0.1)

ver = '1.12.2'

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
        minecraft_launcher_lib.install.install_minecraft_version(versionid=ver, minecraft_directory=minecraft_directory,
                                                                callback=callback)

        options = {
            'username': username.get(),
            'server': '90.151.59.120',
            'port': '25565',
        }

        progress_window.destroy()  # Закрываем окно прогрессбара после завершения установки
        subprocess.call(
            minecraft_launcher_lib.command.get_minecraft_command(version=ver, minecraft_directory=minecraft_directory,
                                                                options=options))

    threading.Thread(target=install_minecraft).start()  # Запускаем установку в отдельном потоке

FONT_PATH = '/Comfortaa-VariableFont_wght.ttf'


style = ttk.Style()
style.configure("BW.TLabel", background="pink")
app = ttk.Style()
app.configure('TLabel', font=('Comfortaa', 12)) # Задаем шрифт и размер для всех меток
app.configure('TButton', font=('Comfortaa', 12)) # Задаем шрифт и размер для всех кнопок

# Создание и размещение поля ввода

username = ttk.Entry(win, style="BW.TLabel", width=20)
username.place(relx=.5, rely=0.45, anchor="c")

# Создание и размещение кнопки
btn = ttk.Button(win, text="Войти в игру", width=15, style="BW.TLabel", command=runn)
btn.place(relx=0.5, rely=0.5, width=100, height=50, anchor="c")
#btn.justify=CENTER

# Увеличение кнопки и задание стиля для центрирования текста
# Задаем ширину и высоту кнопки

# Создание стиля для кнопки с центрированным текстом

style.configure("CenterText.TLabel", layout=('Center',))  # Задаем параметры для центрирования текста
style.configure("BW.TLabel", background="pink")  # Подтверждаем стиль фона

# Применение стиля к кнопке





win.mainloop()