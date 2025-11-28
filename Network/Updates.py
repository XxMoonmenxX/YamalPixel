import logging
import requests
import re
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from ttkthemes import ThemedTk
from ConfDir.Versions import CURRENT_VERSION
from pathlib import Path
import subprocess


# УДАЛИТЬ эту строку - не создаем отдельное окно здесь
# updsc = ThemedTk(theme="arc")

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = Path.home() / "YamalPixelRes"
    return os.path.join(base_path, relative_path)


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


def check_for_updates_local(parent_window=None):
    """
    Проверка обновлений с передачей родительского окна
    parent_window: главное окно лаунчера (win)
    """
    try:
        logging.info("Проверка обновлений...")

        # Проверяем права доступа
        if not can_update_launcher():
            logging.warning("Недостаточно прав для автоматического обновления")
            return

        response = requests.get(
            "https://api.github.com/repos/XxMoonmenxX/YamalPixel/releases/latest"
        )
        response.raise_for_status()

        release_data = response.json()
        changelog = release_data.get("body", "Нет описания изменений")

        # Убираем Markdown-разметку и форматируем
        changelog = re.sub(r"\#{2,}", "", changelog)  # noqa
        changelog = re.sub(r"\- ", "• ", changelog)  # noqa
        changelog = re.sub(r"\*\*(.*?)\*\*", r"\1", changelog)
        changelog = re.sub(r"\*(.*?)\*", r"\1", changelog)
        changelog = changelog.strip()

        latest_version = release_data["tag_name"].lstrip("v")

        if latest_version != CURRENT_VERSION:
            logging.info(f"Найдена новая версия: {latest_version}")

            # Создаем окно обновления относительно родительского окна
            update_window = tk.Toplevel(parent_window)
            set_window_icon(update_window)
            update_window.title(f"YamalPixel - Обновление до v{latest_version}")
            update_window.geometry("550x450")
            update_window.resizable(True, True)
            update_window.transient(parent_window)
            update_window.grab_set()

            # Устанавливаем минимальный размер окна
            update_window.minsize(500, 400)

            # Делаем светлую тему для лучшей читаемости
            update_window.configure(bg="white")

            # Центрируем окно относительно родителя
            update_window.update_idletasks()
            if parent_window:
                x = parent_window.winfo_x() + (parent_window.winfo_width() - 550) // 2
                y = parent_window.winfo_y() + (parent_window.winfo_height() - 450) // 2
            else:
                # Если родителя нет, центрируем на экране
                x = (update_window.winfo_screenwidth() // 2) - (550 // 2)
                y = (update_window.winfo_screenheight() // 2) - (450 // 2)

            update_window.geometry(f"550x450+{x}+{y}")

            # Используем grid для всего окна
            update_window.columnconfigure(0, weight=1)
            update_window.rowconfigure(2, weight=1)  # Текстовое поле будет расширяться

            # Заголовок
            header_frame = tk.Frame(update_window, bg="white")
            header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
            header_frame.columnconfigure(0, weight=1)

            tk.Label(
                header_frame,
                text=f"Доступно обновление!",
                font=("Comfortaa", 14, "bold"),
                bg="white",
                fg="#2c3e50",
            ).grid(row=0, column=0)

            tk.Label(
                header_frame,
                text=f"Версия {latest_version}",
                font=("Comfortaa", 11),
                bg="white",
                fg="#7f8c8d",
            ).grid(row=1, column=0, pady=(5, 0))

            # Разделитель
            separator = ttk.Separator(update_window, orient="horizontal")
            separator.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

            # Метка "Что нового"
            label_frame = tk.Frame(update_window, bg="white")
            label_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))
            label_frame.columnconfigure(0, weight=1)

            tk.Label(
                label_frame,
                text="Что нового в этой версии:",
                font=("Comfortaa", 10, "bold"),
                bg="white",
                fg="#2c3e50",
            ).grid(row=0, column=0, sticky="w")

            # Фрейм для текста с прокруткой
            text_frame = tk.Frame(update_window, bg="white")
            text_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
            text_frame.columnconfigure(0, weight=1)
            text_frame.rowconfigure(0, weight=1)

            # Текстовое поле
            text_widget = tk.Text(
                text_frame,
                wrap="word",
                width=60,
                height=15,
                font=("Comfortaa", 9),
                bg="#f8f9fa",
                fg="#2c3e50",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=10,
            )

            scrollbar = ttk.Scrollbar(
                text_frame, orient="vertical", command=text_widget.yview
            )
            text_widget.configure(yscrollcommand=scrollbar.set)

            # Вставляем текст
            text_widget.insert("1.0", changelog)
            text_widget.configure(state="disabled")

            # Упаковываем с grid
            text_widget.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

            # Фрейм для кнопок
            button_frame = tk.Frame(update_window, bg="white")
            button_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=15)
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)

            def install_update():
                update_window.destroy()

                # Ищем ЛЮБОЙ EXE-файл в ассетах
                update_asset = next(
                    (
                        asset
                        for asset in release_data["assets"]
                        if asset["name"].lower().endswith(".exe")
                    ),
                    None,
                )

                if update_asset:
                    download_and_install_update(update_asset["browser_download_url"], parent_window)
                else:
                    # Если EXE не найден, показываем какие файлы есть
                    available_files = "\n".join(
                        [f"• {asset['name']}" for asset in release_data["assets"]]
                    )
                    messagebox.showerror(
                        "Файл не найден",
                        f"EXE-файл не найден в релизе.\n\nДоступные файлы:\n{available_files}",
                    )

            def skip_update():
                update_window.destroy()
                logging.info("Пользователь отказался от обновления")

            # Кнопки - используем grid для фиксированного размера
            btn_install = tk.Button(
                button_frame,
                text="🔄 УСТАНОВИТЬ ОБНОВЛЕНИЕ",
                font=("Comfortaa", 10, "bold"),
                bg="#27ae60",
                fg="white",
                relief="flat",
                padx=20,
                pady=10,
                command=install_update,
            )
            btn_install.grid(row=0, column=0, padx=(0, 10), sticky="ew")

            btn_skip = tk.Button(
                button_frame,
                text="ПРОПУСТИТЬ",
                font=("Comfortaa", 10),
                bg="#95a5a6",
                fg="white",
                relief="flat",
                padx=20,
                pady=10,
                command=skip_update,
            )
            btn_skip.grid(row=0, column=1, sticky="ew")

            # Фокус и прокрутка
            text_widget.focus_set()
            text_widget.see("1.0")

            # Добавляем ховер-эффекты для кнопок
            def on_enter_install(_e):
                btn_install.configure(bg="#219653")

            def on_leave_install(_e):
                btn_install.configure(bg="#27ae60")

            def on_enter_skip(_e):
                btn_skip.configure(bg="#7f8c8d")

            def on_leave_skip(_e):
                btn_skip.configure(bg="#95a5a6")

            btn_install.bind("<Enter>", on_enter_install)
            btn_install.bind("<Leave>", on_leave_install)
            btn_skip.bind("<Enter>", on_enter_skip)
            btn_skip.bind("<Leave>", on_leave_skip)

        else:
            messagebox.showinfo("Обновление", "Вы используете последнюю версию: " + CURRENT_VERSION)

    except Exception as e:
        logging.error(f"Ошибка проверки обновлений: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось проверить обновления: {str(e)}")


def can_update_launcher():
    """Проверяет, можно ли обновить лаунчер"""
    try:
        # Пробуем создать тестовый файл в той же директории
        test_file = os.path.join(os.path.dirname(sys.argv[0]), "test_write.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except:  # noqa
        return False


def download_and_install_update(download_url, parent_window=None):
    """Улучшенная функция обновления с обработкой прав доступа"""
    import tempfile
    import stat

    temp_dir = tempfile.gettempdir()
    temp_exe = os.path.join(temp_dir, "YamalPixelLauncher_New.exe")
    current_exe = os.path.abspath(sys.argv[0])  # Текущий исполняемый файл
    backup_exe = os.path.join(
        os.path.dirname(current_exe), "YamalPixelLauncher_Backup.exe"
    )

    progress_window = None

    try:
        # Создаем окно прогресса относительно родителя
        progress_window = tk.Toplevel(parent_window) if parent_window else tk.Toplevel()
        set_window_icon(progress_window)
        progress_window.title("Обновление")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)

        progress = ttk.Progressbar(
            progress_window, orient="horizontal", length=300, mode="determinate"
        )
        progress.pack(pady=20)
        status_label = ttk.Label(progress_window, text="Скачивание обновления...")
        status_label.pack()

        # Скачиваем новую версию во временную папку
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))

            with open(temp_exe, "wb") as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (
                            int((downloaded / total_size) * 100)
                            if total_size > 0
                            else 0
                        )
                        progress["value"] = percent
                        status_label.config(text=f"Загружено {percent}%")
                        progress_window.update()

        # Делаем файл исполняемым (для Linux/MacOS)
        if os.name != "nt":
            os.chmod(temp_exe, os.stat(temp_exe).st_mode | stat.S_IEXEC)

        progress["value"] = 100
        status_label.config(text="Подготовка к обновлению...")
        progress_window.update()

        # Создаем скрипт обновления
        if os.name == "nt":  # Windows
            bat_path = os.path.join(temp_dir, "yamalpixel_update.bat")
            with open(bat_path, "w") as bat_file:
                bat_file.write(
                    f"""
@echo off
chcp 65001 >nul
echo YamalPixel - Обновление
timeout /t 2 /nobreak >nul

:: Закрываем лаунчер
taskkill /f /im "{os.path.basename(current_exe)}" >nul 2>&1

:: ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ PYINSTALLER
del /q /f "%TEMP%\\_MEI*" >nul 2>&1
for /d %%i in ("%TEMP%\\_MEI*") do rd /s /q "%%i" >nul 2>&1
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
"""
                )

            # Запускаем батник
            subprocess.Popen(
                [bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

        else:  # Linux/MacOS
            sh_path = os.path.join(temp_dir, "yamalpixel_update.sh")
            with open(sh_path, "w") as sh_file:
                sh_file.write(
                    f"""#!/bin/bash
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
"""
                )
            os.chmod(sh_path, 0o755)
            subprocess.Popen(
                ["nohup", "bash", sh_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Закрываем текущий лаунчер
        if progress_window:
            progress_window.destroy()

        if parent_window:
            parent_window.after(100, lambda: sys.exit(0))
        else:
            sys.exit(0)

    except Exception as e:
        logging.error(f"Ошибка обновления: {str(e)}")

        # Очистка при ошибке
        try:
            if os.path.exists(temp_exe):
                os.remove(temp_exe)
        except:  # noqa
            pass

        if progress_window:
            progress_window.destroy()

        # Предлагаем альтернативный способ обновления
        show_manual_update_option(download_url, parent_window)


def show_manual_update_option(download_url, parent_window=None):
    """Показывает опцию ручного обновления при ошибке автоматического"""
    result = messagebox.askyesno(
        "Ошибка автоматического обновления",
        "Не удалось автоматически обновиться.\n\n"
        "Причины:\n"
        "• Недостаточно прав\n"
        "• Антивирус заблокировал обновление\n"
        "• Файл занят другим процессом\n\n"
        "Хотите скачать новую версию вручную?",
        icon="warning",
    )

    if result:
        import webbrowser

        webbrowser.open(download_url)
        messagebox.showinfo(
            "Ручное обновление",
            "Скачайте новую версию и замените текущий файл лаунчера.\n\n"
            "Текущий лаунчер будет закрыт.",
        )
        sys.exit(0)