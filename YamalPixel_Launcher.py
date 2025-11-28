import tkinter as tk # Графический интерфейс
from tkinter import ttk, messagebox # Для стилизации и сообщений
import minecraft_launcher_lib # Для запуска лаунчера
from minecraft_launcher_lib.mod_loader import get_mod_loader #Кастомная сборка minecraft_launcher_lib, пришлось повозиться с _neoforge.py
import subprocess # Для запуска лаунчера
import threading # Для асинхронного запуска лаунчера
import os # Для работы с файлами
import requests # Для запросов
import re # Для регулярных выражений
from ttkthemes import ThemedTk # Для темы
from mcstatus import JavaServer # Для проверки статуса сервера
from pygame import mixer # Для музыки
import zipfile # Для работы с ZIP-файлами
import platform # Для проверки ОС
import urllib.request # Для загрузки файлов
import sys # Для работы с системными путями
import shutil # Для копирования файлов
import logging # Для логирования
from pypresence import Presence # Для Discord Rich Presence
from pathlib import Path # Для работы с путями
import datetime # Для даты
import asyncio # Для асинхронных операций
import aiohttp # Для асинхронных HTTP-запросов
from concurrent.futures import ThreadPoolExecutor # Для асинхронного выполнения задач
import hashlib # Для хеширования
import time # Для таймеров
from datetime import datetime as dt # Для даты

import psutil # Для получения информации о процессах
import math # Для математики
import json # Для работы с JSON
from PIL import Image, ImageTk # Для работы с изображениями

from ConfDir.utils import (aggressive_clean_name, calculate_similarity,
                           extract_core_name, MANUAL_MOD_MAPPINGS, COLLECTIONS_CONFIG)

from ConfDir.ScaleRes import RESOLUTION_MAP, ratios, resolution_ratios, backgrounds

from ConfDir.Configs import (CONFIG, RESOURCE_DIR, RESOURCES, SHADERS_CONFIG, essential_mods,
                             get_minecraft_version, version_configs)

from ConfDir.Versions import (version_configs, fabric_supported_versions, neoforge_supported_versions,
                              versions, all_versions, CURRENT_VERSION)

from Network.Updates import check_for_updates_local
from Network.Downloader import download_single_mod_turbo, download_mods_turbo_ui, TurboDownloader, LauncherCache
from Network.ModrinthLoader import ModrinthAPI

from Ui.UiComponents import (
    ModernButton,
    ModernCheckbutton,
    ModernCloseButton,
    ModernEntry,
    ModernOnlineButton,
    ModernVersionSelector
)
import tempfile # Для временных файлов


def fix_python314_dll_issue():
    """Critical fix for Python 3.14 + PyInstaller 6.16.0 DLL loading"""
    if getattr(sys, 'frozen', False):  # Проверяем, запущен ли PyInstaller
        # Основной фикс - добавляем MEIPASS в начало PATH
        if hasattr(sys, '_MEIPASS'):
            meipass_path = Path(sys._MEIPASS)
            current_paths = os.environ['PATH'].split(os.pathsep)

            # Убираем дубликаты и ставим MEIPASS первым
            new_paths = [str(meipass_path)]
            for path in current_paths:
                if path != str(meipass_path) and Path(path).exists():  # Проверяем, что путь существует
                    new_paths.append(path)

            os.environ['PATH'] = os.pathsep.join(new_paths)
            os.chdir(meipass_path)  # Меняем рабочую директорию

            print(f"Fixed PATH for DLL loading: {meipass_path}")



fix_python314_dll_issue()


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

def old_repair_with_ui():
    """Полная версия починки с UI"""
    try:
        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        set_window_icon(progress_window)
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
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(
            main_frame,
            text="🔧 Автопочинка файлов игры",
            font=("Comfortaa", 16, "bold"),
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text="Проверяем и восстанавливаем игровые файлы",
            font=("Comfortaa", 11),
            foreground="gray",
        ).pack(pady=(0, 20))

        # Прогресс-бар
        progress = ttk.Progressbar(
            main_frame, orient="horizontal", length=400, mode="determinate"
        )
        progress.pack(pady=10)

        status_label = ttk.Label(
            main_frame, text="Начинаем проверку...", font=("Comfortaa", 10)
        )
        status_label.pack()

        details_label = ttk.Label(
            main_frame, text="", font=("Comfortaa", 9), foreground="blue"
        )
        details_label.pack()

        # Список найденных проблем и исправлений
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill="both", expand=True, pady=10)

        log_text = tk.Text(
            log_frame,
            height=8,
            width=60,
            wrap="word",
            font=("Consolas", 8),
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)

        log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def add_log(message, color="black"):
            log_text.configure(state="normal")
            log_text.insert("end", f"• {message}\n", color)
            log_text.see("end")
            log_text.configure(state="disabled")
            progress_window.update()

        issues_found = []
        fixes_applied = []

        def repair_thread():
            nonlocal issues_found, fixes_applied

            try:
                minecraft_dir = CONFIG["minecraft_dir"]
                mods_dir = os.path.join(minecraft_dir, "mods")
                versions_dir = os.path.join(minecraft_dir, "versions")
                config_dir = os.path.join(minecraft_dir, "config")

                # Проверка папок
                win.after(0, lambda: status_label.config(text="Проверка папок...")) # noqa
                win.after(0, lambda: details_label.config(text="Проверяем структуру папок"))# noqa
                progress["value"] = 10

                for folder, path in [
                    ("mods", mods_dir),
                    ("versions", versions_dir),
                    ("config", config_dir),
                ]:
                    if not os.path.exists(path):
                        issues_found.append(f"Папка {folder} отсутствует")
                        add_log(f"❌ Папка {folder} отсутствует", "red")
                        os.makedirs(path, exist_ok=True)
                        fixes_applied.append(f"Создана папка {folder}")
                        add_log(f"✅ Создана папка {folder}", "green")

                # Проверка модов
                progress["value"] = 50
                win.after(0, lambda: status_label.config(text="Проверка модов...")) # noqa

                missing_mods = []
                for mod in CONFIG["mods"]:
                    mod_path = os.path.join(mods_dir, mod["file"])
                    if not os.path.exists(mod_path):
                        missing_mods.append(mod)

                if missing_mods:
                    issues_found.append(f"Отсутствуют {len(missing_mods)} модов")
                    add_log(f"❌ Отсутствует модов: {len(missing_mods)}", "red")

                    # Загружаем моды
                    for i, mod in enumerate(missing_mods):
                        win.after(
                            0,
                            lambda: details_label.config(text=f"Загружаем мод: {mod['file']} ({i + 1}/{len(missing_mods)})"),) # noqa
                        if download_single_mod_turbo(mod):
                            fixes_applied.append(f"Загружен {mod['file']}")
                            add_log(f"✅ Загружен {mod['file']}", "green")
                        else:
                            add_log(f"❌ Ошибка загрузки {mod['file']}", "red")

                # Проверка Fabric
                progress["value"] = 80
                win.after(0, lambda: status_label.config(text="Проверка Fabric...")) # noqa

                if not check_fabric_installed():
                    issues_found.append("Fabric не установлен")
                    add_log("❌ Fabric не установлен", "red")
                    if install_fabric_silent():
                        fixes_applied.append("Установлен Fabric")
                        add_log("✅ Установлен Fabric", "green")

                progress["value"] = 100
                win.after(0, lambda: status_label.config(text="Проверка завершена!")) # noqa

                # Показываем результат
                win.after(1000,lambda: show_repair_result(issues_found, fixes_applied, progress_window),) # noqa

            except Exception as e:
                win.after(0, progress_window.destroy) # noqa
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


# Пишется при помощи DeepSeek, каждый может сделать то же самое хоть немного зная python!!!

logging.basicConfig(
    filename="launcher.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)



LAUNCH_IN_PROGRESS = False
LAUNCH_START_TIME = None











# 🎯 ОБНОВЛЕННАЯ ФУНКЦИЯ ДЛЯ ШЕЙДЕРОВ:


def download_shaders_turbo(selected_shaders, progress_callback=None):
    """Турбо-загрузка шейдеров"""

    def download_shaders_thread():
        shaders_dir = os.path.join(CONFIG["minecraft_dir"], "shaderpacks")
        os.makedirs(shaders_dir, exist_ok=True)

        downloader = TurboDownloader()
        total = len(selected_shaders)
        success_count = 0

        with ThreadPoolExecutor(max_workers=2) as executor:  # 2 потока для шейдеров
            futures = []

            for shader in selected_shaders:
                future = executor.submit(
                    download_single_shader_turbo, downloader, shader, shaders_dir
                )
                futures.append(future)

            for i, future in enumerate(futures):
                try:
                    success = future.result(timeout=300)  # 5 минут на шейдер
                    if success:
                        success_count += 1

                    if progress_callback:
                        progress = (i + 1) * 100 // total
                        win.after(0,lambda: progress_callback(progress, f"Шейдер {i + 1}/{total}"),) # noqa

                except Exception as e:
                    logging.error(f"Ошибка загрузки шейдера: {e}")

        return success_count, total

    threading.Thread(target=download_shaders_thread, daemon=True).start()


def download_single_shader_turbo(downloader, shader, shaders_dir):
    """Загрузка одного шейдера"""
    try:
        direct_link = asyncio.run(downloader.get_turbo_link(shader["url"]))
        if not direct_link:
            return False

        shader_path = os.path.join(shaders_dir, shader["file"])
        return downloader.download_file_sync(direct_link, shader_path)

    except Exception as e:
        logging.error(f"Ошибка загрузки шейдера {shader['name']}: {e}")
        return False


def fig1():
    """Очистка игры с созданием бэкапов"""
    minecraft_dir = CONFIG["minecraft_dir"]
    mods_dir = os.path.join(minecraft_dir, "mods")
    versions_dir = os.path.join(minecraft_dir, "versions")

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
        backup_info = "Созданы бэкапы:\n" + "\n".join(
            [f"• {os.path.basename(b)}" for b in backups_created]
        )
        messagebox.showinfo("Бэкапы созданы", f"Игра очищена!\n\n{backup_info}")
    else:
        messagebox.showinfo("Очистка", "Папки mods и versions очищены")





def speed_test():
    """НОРМАЛЬНЫЙ тест скорости с гарантированно работающими серверами"""
    try:
        # РЕАЛЬНО РАБОТАЮЩИЕ серверы для теста
        test_servers = [
            {
                "url": "https://cdn.windows93.net/img/logo.png",  # Маленький файл - быстро
                "name": "Тестовый файл 1",
                "size": 0.05,  # ~50KB
            },
            {
                "url": "https://httpbin.org/bytes/102400",  # Генерирует 100KB данных
                "name": "Тестовые данные 100KB",
                "size": 0.1,
            },
            {
                "url": "https://httpbin.org/bytes/512000",  # Генерирует 500KB данных
                "name": "Тестовые данные 500KB",
                "size": 0.5,
            },
        ]

        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        set_window_icon(progress_window)
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
        title_label = ttk.Label(
            progress_window,
            text="🚀 Тест скорости интернета",
            font=("Comfortaa", 14, "bold"),
        )
        title_label.pack(pady=10)

        # Статус
        status_label = ttk.Label(
            progress_window, text="Подготовка к тесту...", font=("Comfortaa", 10)
        )
        status_label.pack(pady=5)

        # Прогресс-бар
        progress = ttk.Progressbar(
            progress_window, orient="horizontal", length=380, mode="determinate"
        )
        progress.pack(pady=10)

        # Детали
        details_label = ttk.Label(
            progress_window,
            text="Инициализация...",
            font=("Comfortaa", 9),
            foreground="blue",
        )
        details_label.pack()

        # Время
        time_label = ttk.Label(
            progress_window, text="Время: 0 сек", font=("Comfortaa", 8)
        )
        time_label.pack()

        # Кнопка отмены
        cancel_flag = threading.Event()

        def cancel_test():
            cancel_flag.set()
            progress_window.destroy()
            messagebox.showinfo("Отменено", "Тест скорости отменен")

        cancel_btn = ttk.Button(
            progress_window, text="❌ Отменить тест", command=cancel_test
        )
        cancel_btn.pack(pady=10)

        def test_thread():
            try:
                best_speed_mbps = 0
                best_speed_mb_sec = 0
                test_results = []

                for i, server in enumerate(test_servers):
                    if cancel_flag.is_set():
                        return

                    win.after(0,lambda: status_label.config(text=f"Тест {i + 1}/{len(test_servers)}: {server['name']}"),) # noqa
                    win.after(0,lambda: details_label.config(text=f"Размер: {server['size']} MB"),) # noqa
                    win.after(0, lambda: progress.config(value=(i * 100 / len(test_servers)))) # noqa

                    try:
                        # Тестируем скорость для этого сервера
                        speed_mbps, speed_mb_sec = test_single_server(
                            server["url"], server["size"], progress_window, cancel_flag
                        )

                        if speed_mbps > best_speed_mbps:
                            best_speed_mbps = speed_mbps
                            best_speed_mb_sec = speed_mb_sec

                        test_results.append(
                            {
                                "server": server["name"],
                                "speed_mbps": speed_mbps,
                                "speed_mb_sec": speed_mb_sec,
                            }
                        )

                        # Небольшая пауза между тестами
                        time.sleep(1)

                    except Exception as e:
                        print(f"Ошибка теста {server['name']}: {e}")
                        continue

                if cancel_flag.is_set():
                    return

                # Показываем лучший результат
                if best_speed_mbps > 0:
                    win.after(
                        0,
                        lambda: show_speed_result(
                            best_speed_mb_sec,
                            best_speed_mbps,
                            test_results,
                            progress_window,),) # noqa
                else:
                    win.after(
                        0,
                        lambda: show_speed_error("Все тесты завершились ошибкой", progress_window),) # noqa

            except Exception as e:
                if not cancel_flag.is_set():
                    win.after(0, lambda: show_speed_error(str(e), progress_window)) # noqa

        def test_single_server(url, _expected_size, _window, cancel_flag):
            """Тестирует скорость для одного сервера"""
            start_time = time.time()
            downloaded = 0

            try:
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0)) # noqa
                chunk_size = 8192

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if cancel_flag.is_set():
                        raise Exception("Тест отменен")

                    if chunk:
                        downloaded += len(chunk)

                        # Обновляем прогресс в реальном времени
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            current_speed_mbps = (
                                downloaded / elapsed
                            ) / 125000  # Mbit/s

                            win.after(
                                0,
                                lambda: details_label.config(
                                    text=f"Скорость: {current_speed_mbps:.1f} Mbit/s"),) # noqa
                            win.after(
                                0,
                                lambda: time_label.config(
                                    text=f"Время: {elapsed:.1f} сек"),) # noqa

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
            result_window.configure(bg="#2b2b2b")
            result_window.resizable(False, False)

            # Центрируем
            result_window.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (500 // 2)
            y = (win.winfo_screenheight() // 2) - (400 // 2)
            result_window.geometry(f"500x400+{x}+{y}")

            # Содержимое
            main_frame = ttk.Frame(result_window, padding=25)
            main_frame.pack(fill="both", expand=True)

            # Заголовок
            ttk.Label(
                main_frame,
                text="🎯 РЕЗУЛЬТАТЫ ТЕСТА СКОРОСТИ",
                font=("Comfortaa", 16, "bold"),
                foreground="white",
                background="#2b2b2b",
            ).pack(pady=(0, 20))

            # Основные метрики
            metrics_frame = ttk.Frame(main_frame)
            metrics_frame.pack(fill="x", pady=10)

            ttk.Label(
                metrics_frame,
                text=f"🚀 СКОРОСТЬ ЗАГРУЗКИ: {mb_per_sec:.2f} MB/сек",
                font=("Comfortaa", 14, "bold"),
                foreground="#4ECDC4",
                background="#2b2b2b",
            ).pack()

            ttk.Label(
                metrics_frame,
                text=f"💨 ПРОПУСКНАЯ СПОСОБНОСТЬ: {mbit_per_sec:.2f} Mbit/сек",
                font=("Comfortaa", 14, "bold"),
                foreground="#4ECDC4",
                background="#2b2b2b",
            ).pack(pady=5)

            # Оценка
            ttk.Label(
                main_frame,
                text=f"🏆 ОЦЕНКА: {rating}",
                font=("Comfortaa", 16, "bold"),
                foreground=color,
                background="#2b2b2b",
            ).pack(pady=15)

            # Детали тестов
            ttk.Label(
                main_frame,
                text="Результаты по серверам:",
                font=("Comfortaa", 10, "bold"),
                foreground="#cccccc",
                background="#2b2b2b",
            ).pack()

            for result in test_results:
                ttk.Label(
                    main_frame,
                    text=f"• {result['server']}: {result['speed_mbps']:.1f} Mbit/s",
                    font=("Comfortaa", 9),
                    foreground="#888888",
                    background="#2b2b2b",
                ).pack()

            # Рекомендации
            ttk.Label(
                main_frame,
                text="💡 РЕКОМЕНДАЦИИ:",
                font=("Comfortaa", 11, "bold"),
                foreground="#ffcc00",
                background="#2b2b2b",
            ).pack(pady=(20, 5))

            ttk.Label(
                main_frame,
                text=issues,
                font=("Comfortaa", 9),
                foreground="#cccccc",
                background="#2b2b2b",
                justify="left",
            ).pack()

            ttk.Label(
                main_frame,
                text="Для комфортной игры рекомендуется 10+ Mbit/сек",
                font=("Comfortaa", 9),
                foreground="#666666",
                background="#2b2b2b",
            ).pack(pady=10)

            ttk.Button(
                main_frame, text="✅ Закрыть", command=result_window.destroy, width=20
            ).pack(pady=10)

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
                f"📞 Если проблема повторяется - обратитесь к провайдеру",
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
            "Дождитесь завершения запуска игры, затем повторите попытку.",
        )
        return

    # Проверяем наличие папки shaderpacks
    shaders_dir = os.path.join(CONFIG["minecraft_dir"], "shaderpacks")
    if not os.path.exists(shaders_dir):
        os.makedirs(shaders_dir)

    # Создаем окно выбора шейдеров
    shaders_window = tk.Toplevel(win)
    set_window_icon(shaders_window)
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
    header_frame.pack(fill="x")

    ttk.Label(
        header_frame,
        text="🎨 Выберите шейдеры для установки",
        font=("Comfortaa", 14, "bold"),
    ).pack(pady=(0, 5))

    ttk.Label(
        header_frame,
        text="Выберите один или несколько шейдеров для загрузки",
        font=("Comfortaa", 10),
        foreground="gray",
    ).pack()

    # Фрейм для списка шейдеров с прокруткой
    tree_frame = ttk.Frame(shaders_window)
    tree_frame.pack(fill="both", expand=True, padx=15, pady=10)

    # Создаем Treeview с чекбоксами
    columns = ("selected", "name", "size")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)

    # Настраиваем колонки
    tree.heading("selected", text="✓")
    tree.heading("name", text="Название шейдера")
    tree.heading("size", text="Размер")

    tree.column("selected", width=50, anchor="center")
    tree.column("name", width=450, anchor="w")
    tree.column("size", width=100, anchor="center")

    # Добавляем данные
    for shader in SHADERS_CONFIG["shaders"]:
        tree.insert(
            "",
            "end",
            values=("☐", shader["name"], "~10-50MB"),
            tags=(shader["url"], shader["file"]),
        )

    # Скроллбар
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Переменная для хранения выбранных шейдеров
    selected_shaders = []

    def toggle_selection(_event):
        item = tree.selection()
        if item:
            item = item[0]
            current_values = tree.item(item, "values")
            if current_values[0] == "☐":
                tree.set(item, "selected", "☑")
                selected_shaders.append(
                    {
                        "name": current_values[1],
                        "url": tree.item(item, "tags")[0],
                        "file": tree.item(item, "tags")[1],
                    }
                )
            else:
                tree.set(item, "selected", "☐")
                # Удаляем из выбранных
                for shader in selected_shaders[:]:
                    if shader["name"] == current_values[1]:
                        selected_shaders.remove(shader)

        # Обновляем счетчик выбранных
        update_selection_count()

    tree.bind("<Button-1>", toggle_selection)

    # Счетчик выбранных шейдеров
    counter_label = ttk.Label(
        shaders_window, text="Выбрано: 0 шейдеров", font=("Comfortaa", 9)
    )
    counter_label.pack()

    def update_selection_count():
        count = len(selected_shaders)
        counter_label.config(text=f"Выбрано: {count} шейдеров")

        # Предупреждение при большом количестве
        if count > 5:
            counter_label.config(foreground="orange")
        else:
            counter_label.config(foreground="black")

    # Фрейм для кнопок
    button_frame = ttk.Frame(shaders_window, padding=10)
    button_frame.pack(fill="x")

    def download_selected():
        if not selected_shaders:
            messagebox.showwarning(
                "Выбор", "❌ Пожалуйста, выберите хотя бы один шейдер"
            )
            return

        total_size = len(selected_shaders) * 50  # Примерный расчет размера
        confirm = messagebox.askyesno(
            "Подтверждение загрузки",
            f"📥 Начать загрузку {len(selected_shaders)} шейдеров?\n\n"
            f"Примерный размер: ~{total_size} MB\n"
            f"Время загрузки: 1-5 минут\n\n"
            f"Шейдеры будут сохранены в папку:\n{shaders_dir}",
        )

        if confirm:
            shaders_window.destroy()
            download_shaders_turbo_ui(selected_shaders)

    def select_all():
        selected_shaders.clear()
        for item in tree.get_children():
            tree.set(item, "selected", "☑")
            values = tree.item(item, "values")
            selected_shaders.append(
                {
                    "name": values[1],
                    "url": tree.item(item, "tags")[0],
                    "file": tree.item(item, "tags")[1],
                }
            )
        update_selection_count()

    def deselect_all():
        selected_shaders.clear()
        for item in tree.get_children():
            tree.set(item, "selected", "☐")
        update_selection_count()

    def open_shaders_folder():
        try:
            if not os.path.exists(shaders_dir):
                os.makedirs(shaders_dir)
            if os.name == "nt":  # Windows
                os.startfile(shaders_dir)
            elif os.name == "posix":  # Linux/MacOS
                subprocess.Popen(["xdg-open", shaders_dir])
            messagebox.showinfo(
                "Папка открыта", f"📁 Открыта папка шейдеров:\n{shaders_dir}"
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")

    # Кнопки управления
    ttk.Button(button_frame, text="✅ Выбрать все", command=select_all, width=15).pack(
        side="left", padx=5
    )
    ttk.Button(button_frame, text="❌ Снять все", command=deselect_all, width=15).pack(
        side="left", padx=5
    )
    ttk.Button(
        button_frame, text="📥 Скачать выбранные", command=download_selected
    ).pack(side="left", padx=5)
    ttk.Button(
        button_frame, text="📁 Открыть папку", command=open_shaders_folder, width=15
    ).pack(side="left", padx=5)
    ttk.Button(button_frame, text="❌ Закрыть", command=shaders_window.destroy).pack(
        side="right", padx=5
    )


def download_shaders_turbo_ui(selected_shaders):
    """UI для загрузки шейдеров с прогрессом"""
    progress_window = tk.Toplevel(win)
    set_window_icon(progress_window)
    progress_window.title("Скачивание шейдеров")
    progress_window.geometry("500x200")
    progress_window.transient(win)
    progress_window.grab_set()
    progress_window.configure(bg="white")

    # Центрируем окно
    progress_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (500 // 2)
    y = (win.winfo_screenheight() // 2) - (200 // 2)
    progress_window.geometry(f"500x200+{x}+{y}")

    # Стили
    title_label = ttk.Label(
        progress_window, text="📥 Скачивание шейдеров", font=("Comfortaa", 12, "bold")
    )
    title_label.pack(pady=10)

    progress_label = ttk.Label(progress_window, text="Подготовка к скачиванию...")
    progress_label.pack(pady=5)

    progress = ttk.Progressbar(
        progress_window, orient="horizontal", length=400, mode="determinate"
    )
    progress.pack(pady=10)

    status_label = ttk.Label(progress_window, text="", wraplength=450)
    status_label.pack(pady=5)

    current_file_label = ttk.Label(progress_window, text="", foreground="blue")
    current_file_label.pack()

    def update_progress(percent, status, current_file=""):
        progress["value"] = percent
        status_label.config(text=status)
        current_file_label.config(text=current_file)
        progress_window.update()

    def completion_callback(success_count, total, error_messages=None):
        progress_window.destroy()
        if success_count > 0:
            messagebox.showinfo(
                "Скачивание завершено",
                f"✅ Успешно скачано {success_count} из {total} шейдеров!\n\n"
                f"Шейдеры сохранены в папке shaderpacks",
            )
        else:
            error_text = "❌ Не удалось скачать ни одного шейдера"
            if error_messages:
                error_text += f"\n\nОшибки:\n" + "\n".join(
                    error_messages[:3]
                )  # Показываем первые 3 ошибки
            messagebox.showerror("Ошибка", error_text)

    # Запускаем загрузку в отдельном потоке
    def download_thread():
        shaders_dir = os.path.join(CONFIG["minecraft_dir"], "shaderpacks")
        os.makedirs(shaders_dir, exist_ok=True)

        total = len(selected_shaders)
        success_count = 0
        error_messages = []

        for i, shader in enumerate(selected_shaders):
            try:
                current_percent = (i * 100) // total
                win.after(
                    0,
                    lambda: update_progress(
                        current_percent,
                        f"Обработка {i + 1}/{total}...",
                        f"Текущий: {shader['name']}",),) # noqa

                # ПРОСТОЕ СКАЧИВАНИЕ БЕЗ ТУРБО-РЕЖИМА
                shader_path = os.path.join(shaders_dir, shader["file"])

                # Используем прямые ссылки на скачивание
                direct_url = convert_to_direct_link(shader["url"])

                if download_file_simple(direct_url, shader_path):
                    success_count += 1
                    logging.info(f"✅ Успешно скачан шейдер: {shader['name']}")
                else:
                    error_msg = f"Ошибка загрузки: {shader['name']}"
                    error_messages.append(error_msg)
                    logging.error(error_msg)

            except Exception as e:
                error_msg = f"Исключение при загрузке {shader['name']}: {str(e)}"
                error_messages.append(error_msg)
                logging.error(error_msg)

            # Обновляем прогресс после каждой попытки
            win.after(
                0,
                lambda: update_progress(
                    ((i + 1) * 100) // total,
                    f"Завершено {i + 1}/{total}...",
                    f"Текущий: {shader['name']}",),) # noqa

        win.after(0, lambda: completion_callback(success_count, total, error_messages)) # noqa

    threading.Thread(target=download_thread, daemon=True).start()


def convert_to_direct_link(yandex_url):
    """Конвертируем ссылку Яндекс.Диска в прямую для скачивания"""
    try:
        # Для публичных ссылок Яндекс.Диска
        if "disk.yandex.ru/d/" in yandex_url or "disk.yandex.ru/d/" in yandex_url:
            # Получаем download URL через Яндекс API
            api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={yandex_url}"

            response = requests.get(api_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'href' in data:
                    return data['href']  # Это прямая ссылка для скачивания

        return yandex_url  # Если не получилось, возвращаем оригинальную ссылку

    except Exception as e:
        logging.error(f"Ошибка конвертации ссылки {yandex_url}: {str(e)}")
        return yandex_url


def download_file_simple(url, filepath):
    """Простое скачивание файла"""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(filepath, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

        # Проверяем, что файл скачался нормально
        if os.path.getsize(filepath) > 1000:  # Минимум 1KB
            return True
        else:
            os.remove(filepath)  # Удаляем битый файл
            return False

    except Exception as e:
        logging.error(f"Ошибка скачивания {url}: {str(e)}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


def get_yandex_direct_link(public_key):
    """Получаем прямую ссылку для скачивания через API Яндекс.Диска"""
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    try:
        response = requests.get(api_url, params={"public_key": public_key})
        response.raise_for_status()
        return response.json().get("href")
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
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logging.info(f"Файл {filename} успешно загружен")

    except Exception as e:
        logging.error(f"Ошибка инициализации: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось загрузить ресурсы: {str(e)}")
        sys.exit(1)


def download_missing_mods_silent():
    """Тихая загрузка отсутствующих модов без UI"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        mods_dir = os.path.join(minecraft_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)

        # Проверяем какие моды отсутствуют
        missing_mods = []
        for mod in CONFIG["mods"]:
            mod_path = os.path.join(mods_dir, mod["file"])
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


def install_fabric_silent():
    """Тихая установка Fabric"""
    try:
        print("🔧 Устанавливаем Fabric...")
        minecraft_launcher_lib.fabric.install_fabric(
            minecraft_version=CONFIG["version"],
            loader_version=CONFIG["fabric_loader"],
            minecraft_directory=CONFIG["minecraft_dir"],
        )
        print("✅ Fabric установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Fabric: {e}")
        return False


def check_fabric_installed():
    """Проверяет установлен ли Fabric"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        versions_dir = os.path.join(minecraft_dir, "versions")
        fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
        fabric_version_dir = os.path.join(versions_dir, fabric_version)
        return os.path.exists(fabric_version_dir)
    except: # noqa
        return False


def install_fabric_silent():
    """Тихая установка Fabric"""
    try:
        print("🔧 Устанавливаем Fabric...")
        minecraft_launcher_lib.fabric.install_fabric(
            minecraft_version=CONFIG["version"],
            loader_version=CONFIG["fabric_loader"],
            minecraft_directory=CONFIG["minecraft_dir"],
        )
        print("✅ Fabric установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Fabric: {e}")
        return False


def is_discord_installed():
    # Проверяем, установлен ли Discord (пример для Windows)
    if os.name == "nt":  # Windows
        discord_path = os.path.join(os.getenv("LOCALAPPDATA"), "Discord")
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
            buttons=[
                {"label": "Скачать", "url": "https://disk.yandex.ru/d/WaJwp2ThduRrgQ"}
            ],
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
        response = requests.get(
            "https://api.github.com/repos/XxMoonmenxX/YamalPixel/releases/latest"
        )
        response.raise_for_status()

        release_data = response.json()
        changelog = release_data.get("body", "Нет описания изменений")

        # Убираем Markdown-разметку и форматируем
        changelog = re.sub(r"\#{2,}", "", changelog) # noqa
        changelog = re.sub(r"\- ", "• ", changelog) # noqa
        changelog = re.sub(r"\*\*(.*?)\*\*", r"\1", changelog)
        changelog = re.sub(r"\*(.*?)\*", r"\1", changelog)
        changelog = changelog.strip()

        latest_version = release_data["tag_name"].lstrip("v")

        if latest_version != CURRENT_VERSION:
            logging.info(f"Найдена новая версия: {latest_version}")

            # Создаем окно обновления
            update_window = tk.Toplevel(win)
            set_window_icon(update_window)
            update_window.title(f"YamalPixel - Обновление до v{latest_version}")
            update_window.geometry("550x450")
            update_window.resizable(True, True)
            update_window.transient(win)
            update_window.grab_set()

            # Устанавливаем минимальный размер окна
            update_window.minsize(500, 400)

            # Делаем светлую тему для лучшей читаемости
            update_window.configure(bg="white")

            # Центрируем окно
            update_window.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (550 // 2)
            y = (win.winfo_screenheight() // 2) - (450 // 2)
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
                    download_and_install_update(update_asset["browser_download_url"])
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
            logging.info("Лаунчер актуален")

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
    except: # noqa
        return False


def download_and_install_update(download_url):
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
        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
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

        win.after(100, lambda: sys.exit(0)) # noqa

    except Exception as e:
        logging.error(f"Ошибка обновления: {str(e)}")

        # Очистка при ошибке
        try:
            if os.path.exists(temp_exe):
                os.remove(temp_exe)
        except: # noqa
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


# Функция очистки перед запуском
def cleanup_before_launch():
    try:
        # Закрываем возможные висящие процессы Minecraft
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/f", "/im", "javaw.exe"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.run(["pkill", "-f", "minecraft"], capture_output=True)

        # Небольшая пауза для завершения процессов
        time.sleep(2)

    except Exception as e:
        print(f"Очистка перед запуском: {e}")
    launcher_dir = os.getcwd()
    minecraft_dir = os.path.expanduser("~/YamalPixel/versions")
    old_Mods = os.path.expanduser("~/YamalPixel/mods")
    items_to_remove = [
        os.path.join(launcher_dir, "config"),
        os.path.join(launcher_dir, "patchouli_books"),
        os.path.join(launcher_dir, "patchouli_data.json"),
        os.path.join(launcher_dir, "logs"),
        os.path.join(launcher_dir, "logo.png"),
        os.path.join(launcher_dir, "Obuse - Menu song.mp3"),
        os.path.join(launcher_dir, "YamalPixelLauncer_V_0.2.06.exe"),
        os.path.join(launcher_dir, "YamalPixelLauncer_V_0.3.0.exe"),
        os.path.join(old_Mods, "fabric-language-kotlin-1.13.6+kotlin.2.2.20.jarr"),
        # Старые моды 1.18.2 которые могут конфликтовать
        os.path.join(old_Mods, "jei-1.18.2-fabric-10.2.1.283.jar"),
        os.path.join(old_Mods, "Xaeros_Minimap_22.14.1_Fabric_1.18.2.jar"),
        os.path.join(old_Mods, "fabric-language-kotlin-1.7.3+kotlin.1.6.20.jar"),
        os.path.join(old_Mods, "JEI.zip"),
        # Старые версии Fabric
        os.path.join(minecraft_dir, "fabric-loader-0.15.11-1.20.1"),
        os.path.join(minecraft_dir, "fabric-loader-0.16.10-1.18.2"),
        # Все моды из твоего конфига 1.18.2
        os.path.join(old_Mods, "fabric-api-0.77.0.jar"),
        os.path.join(old_Mods, "sodium-fabric-mc1.18.2-0.4.1+build.15.jar"),
        os.path.join(old_Mods, "indium-0.7.10+mc1.18.2.zip"),
        os.path.join(old_Mods, "AdvancedReborn-1.18.2-1.0.6.jar"),
        os.path.join(old_Mods, "RebornCore-5.2.0.jar"),
        os.path.join(old_Mods, "TechReborn-5.2.0.jar"),
        os.path.join(old_Mods, "Xaeros_Minimap_25.2.10_Fabric_1.18.2.jar"),
        os.path.join(old_Mods, "architectury-4.9.83-fabric.jar"),
        os.path.join(old_Mods, "betterdroppeditems-1.3.2-1.18.2.jar"),
        os.path.join(old_Mods, "cloth-config-6.3.81-fabric.jar"),
        os.path.join(old_Mods, "lithium-fabric-mc1.18.2-0.7.10.jar"),
        os.path.join(old_Mods, "modmenu-3.2.5.jar"),
        os.path.join(old_Mods, "autoconfig1u-3.4.0.jar"),
        os.path.join(old_Mods, "NoIndium-1.0.2+1.18.2.jar"),
        os.path.join(old_Mods, "omega-config-base-1.2.3-1.18.1.jar"),
        os.path.join(old_Mods, "pal-1.5.0.jar"),
        os.path.join(old_Mods, "Patchouli-1.18.2-66-FABRIC.jar"),
        os.path.join(old_Mods, "cardinal-components-api-4.2.0.jar"),
        os.path.join(old_Mods, "ctov-2.9.4.jar"),
        os.path.join(old_Mods, "emi-0.7.3+1.18.2.jar"),
        os.path.join(old_Mods, "lambdynamiclights-2.1.0+1.17.jar"),
        os.path.join(old_Mods, "more-axolotls-1.1.0-1.18.jar"),
        os.path.join(old_Mods, "enchanted-golden-apple-addition-2.0.jar"),
        os.path.join(old_Mods, "mvs-2.2.6-1.18.2.jar"),
        os.path.join(old_Mods, "ironchests-2.0.5-fabric.jar"),
        os.path.join(old_Mods, "appliedenergistics2-fabric-11.7.6.jar"),
        os.path.join(old_Mods, "lovely_snails-1.0.4+1.18.jar"),
        os.path.join(old_Mods, "PresenceFootsteps-1.5.1.jar"),
        os.path.join(old_Mods, "cloth-config-6.5.102-fabric.jar"),
        os.path.join(old_Mods, "fallingleaves-1.11.1+1.18.2.jar"),
        os.path.join(old_Mods, "InventoryProfilesNext-fabric-1.18.2-1.10.19.jar"),
        os.path.join(old_Mods, "XaerosWorldMap_1.39.12_Fabric_1.18.2.jar"),
        os.path.join(old_Mods, "libIPN-fabric-1.18.2-4.0.2.jar"),
        os.path.join(old_Mods, "Frogmod.jar"),
        os.path.join(old_Mods, "geckolib-fabric-1.18-3.0.80.jar"),
        os.path.join(old_Mods, "extra-mod-integrations-0.0.31.18.2.jar"),
        os.path.join(old_Mods, "travelersbackpack-fabric-1.18.2-7.1.43.jar"),
    ]

    for item in items_to_remove:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
            print(f"Удалено: {item}")
    auth_cache_files = [
        os.path.join(CONFIG["minecraft_dir"], "launcher_accounts.json"),
        os.path.join(CONFIG["minecraft_dir"], "launcher_profiles.json"),
        os.path.join(CONFIG["minecraft_dir"], "usercache.json")
    ]

    for cache_file in auth_cache_files:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"Очищен кэш: {cache_file}")
            except Exception as e:
                print(f"Не удалось очистить {cache_file}: {e}")


# Функция проверки версии Java
def check_java_version():
    """
    Улучшенная проверка версии Java с несколькими методами
    """
    java_versions = []

    # Метод 1: Проверка через java -version (основной)
    try:
        result = subprocess.run(
            ["java", "-version"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        # Ищем версию в stderr (обычно там вывод)
        version_output = result.stderr or result.stdout

        # Несколько паттернов для поиска версии
        patterns = [
            r'version "([1-9]\d*\.\d+\.\d+[_\d]*)',  # OpenJDK/Oracle
            r'java version "([1-9]\d*\.\d+\.\d+[_\d]*)',  # Старые версии
            r'openjdk version "([1-9]\d*\.\d+\.\d+[_\d]*)',  # OpenJDK
            r"\"([1-9]\d*\.\d+\.\d+[_\d]*)",  # Общий паттерн
        ]

        for pattern in patterns:
            version_match = re.search(pattern, version_output)
            if version_match:
                version_str = version_match.group(1)
                major_version = extract_major_version(version_str)
                java_versions.append(major_version)
                print(f"Найдена Java версия: {version_str} (major: {major_version})")
                break

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        IndexError,
        TimeoutError,
    ) as e:
        print(f"Метод 1 (java -version) не сработал: {str(e)}")

    # Метод 2: Проверка через where/java (поиск в PATH)
    try:
        if os.name == "nt":  # Windows
            result = subprocess.run(
                ["where", "java"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:  # Linux/MacOS
            result = subprocess.run(
                ["which", "java"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )

        if result.returncode == 0:
            java_path = result.stdout.strip().split("\n")[0]
            print(f"Java найдена по пути: {java_path}")

            # Проверяем версию найденной Java
            version_result = subprocess.run(
                [java_path, "-version"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                timeout=5,
            )

            version_output = version_result.stderr or version_result.stdout
            version_match = re.search(
                r'version "([1-9]\d*\.\d+\.\d+[_\d]*)', version_output
            )
            if version_match:
                version_str = version_match.group(1)
                major_version = extract_major_version(version_str)
                java_versions.append(major_version)
                print(f"Java из PATH: {version_str} (major: {major_version})")

    except Exception as e:
        print(f"Метод 2 (поиск в PATH) не сработал: {str(e)}")

    # Метод 3: Проверка переменных среды JAVA_HOME
    try:
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java_exe = os.path.join(
                java_home, "bin", "java.exe" if os.name == "nt" else "java"
            )
            if os.path.exists(java_exe):
                version_result = subprocess.run(
                    [java_exe, "-version"],
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                    timeout=5,
                )

                version_output = version_result.stderr or version_result.stdout
                version_match = re.search(
                    r'version "([1-9]\d*\.\d+\.\d+[_\d]*)', version_output
                )
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
        clean_version = version_str.split("_")[0]  # Убираем update версии

        parts = clean_version.split(".")

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
        if "64" in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_windows_hotspot_17.0.11_9.msi"
        else:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x86-32_windows_hotspot_17.0.11_9.msi"

    elif system == "Linux":
        if "x86_64" in architecture or "amd64" in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_linux_hotspot_17.0.11_9.tar.gz"
        elif "aarch64" in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_aarch64_linux_hotspot_17.0.11_9.tar.gz"

    elif system == "Darwin":  # macOS
        if "arm" in architecture:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_aarch64_mac_hotspot_17.0.11_9.tar.gz"
        else:
            return "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_mac_hotspot_17.0.11_9.tar.gz"

    return None

def install_java_with_progress():
    java_window = tk.Toplevel(win)
    java_window.title("Установка Java 17")
    java_window.geometry("400x150")

    progress_label = ttk.Label(java_window, text="Прогресс установки Java 17:")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(
        java_window, orient="horizontal", length=300, mode="determinate"
    )
    progress.pack(pady=10)

    status_label = ttk.Label(java_window, text="")
    status_label.pack()

    def download_progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            progress["value"] = percent
            status_label.config(text=f"Скачано {percent}%")
            java_window.update_idletasks()

    def install_thread():
        try:
            system = platform.system()
            if system == "Windows":
                url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.11%2B9/OpenJDK17U-jdk_x64_windows_hotspot_17.0.11_9.msi"
                msi_path = os.path.join(os.environ["TEMP"], "OpenJDK17.msi")
                urllib.request.urlretrieve(
                    url,
                    msi_path,
                    reporthook=lambda c, b, t: download_progress_hook(c, b, t),
                )
                subprocess.run(
                    f'msiexec /i "{msi_path}" /quiet', shell=True, check=True
                )
                os.remove(msi_path)
            elif system == "Linux":
                subprocess.run(
                    "sudo apt-get install -y wget apt-transport-https",
                    shell=True,
                    check=True,
                )
                subprocess.run(
                    "wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo apt-key add -",
                    shell=True,
                    check=True,
                )
                subprocess.run(
                    "echo \"deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print $2}' /etc/os-release) main\" | sudo tee /etc/apt/sources.list.d/adoptium.list",
                    shell=True,
                    check=True,
                )
                subprocess.run("sudo apt-get update -y", shell=True, check=True)
                subprocess.run(
                    "sudo apt-get install -y temurin-17-jdk", shell=True, check=True
                )
            elif system == "Darwin":
                subprocess.run(
                    '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                    shell=True,
                    check=True,
                )
                subprocess.run("brew tap adoptium/temurin", shell=True, check=True)
                subprocess.run("brew install --cask temurin17", shell=True, check=True)
            java_window.destroy()
            messagebox.showinfo("Успех :D", "Java 17 успешно установлена! ЗАПУСКАЙ!!!")
        except Exception as e:
            messagebox.showerror("АШЫПКА :D", f"Java 17 установлена. ЗАПУСКАЙ!!!!")
            sys.exit(1)

    if not check_java_version():
        threading.Thread(target=install_thread, daemon=True).start()
    else:
        java_window.destroy()


def install_java_windows(status_label, details_label):
    """Установка Java на Windows"""
    try:
        status_label.config(text="Скачивание установщика Java...")
        details_label.config(text="Это может занять несколько минут")

        url = get_java_installer_url()
        if not url:
            raise Exception("Не найден подходящий установщик для вашей системы")

        msi_path = os.path.join(os.environ["TEMP"], "OpenJDK17.msi")

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
            text=True,
        )

        # Очистка
        if os.path.exists(msi_path):
            os.remove(msi_path)

        if result.returncode != 0:
            raise Exception(f"Ошибка установки: {result.stderr}")

    except subprocess.TimeoutExpired:
        raise Exception(
            "Установка заняла слишком много времени. Попробуйте установить Java вручную."
        )
    except Exception as e:
        raise Exception(f"Ошибка установки на Windows: {str(e)}")


def install_java_linux(status_label, details_label):
    """Установка Java на Linux"""
    try:
        status_label.config(text="Установка Java через пакетный менеджер...")

        # Проверяем какой пакетный менеджер доступен
        commands = [
            # Ubuntu/Debian
            ["sudo", "apt-get", "update", "-y"],
            [
                "sudo",
                "apt-get",
                "install",
                "-y",
                "wget",
                "apt-transport-https",
                "gnupg",
            ],
            [
                "wget",
                "-qO",
                "-",
                "https://packages.adoptium.net/artifactory/api/gpg/key/public",
            ],
            ["sudo", "apt-key", "add", "-"],
            [
                "echo",
                '"deb https://packages.adoptium.net/artifactory/deb $(lsb_release -cs) main"',
                "|",
                "sudo",
                "tee",
                "/etc/apt/sources.list.d/adoptium.list",
            ],
            ["sudo", "apt-get", "update", "-y"],
            ["sudo", "apt-get", "install", "-y", "temurin-17-jdk"],
        ]

        for cmd in commands:
            status_label.config(text=f"Выполнение: {' '.join(cmd[:2])}...")
            result = subprocess.run(
                " ".join(cmd) if isinstance(cmd, list) else cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                print(
                    f"Команда {' '.join(cmd) if isinstance(cmd, list) else cmd} завершилась с ошибкой: {result.stderr}"
                )

    except Exception as e:
        raise Exception(f"Ошибка установки на Linux: {str(e)}")


def install_java_macos(status_label, details_label):
    """Установка Java на macOS"""
    try:
        status_label.config(text="Установка через Homebrew...")

        # Проверяем установлен ли Homebrew
        result = subprocess.run(["which", "brew"], capture_output=True)
        if result.returncode != 0:
            status_label.config(text="Установка Homebrew...")
            subprocess.run(
                '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                shell=True,
                check=True,
                timeout=300,
            )

        status_label.config(text="Установка Java...")
        subprocess.run(["brew", "tap", "adoptium/temurin"], check=True)
        subprocess.run(["brew", "install", "--cask", "temurin17"], check=True)

    except Exception as e:
        raise Exception(f"Ошибка установки на macOS: {str(e)}")


def show_java_install_error(error_msg):
    """Показывает детальную информацию об ошибке установки Java"""
    error_window = tk.Toplevel(win)
    error_window.title("Ошибка установки Java")
    error_window.geometry("500x300")

    tk.Label(
        error_window,
        text="❌ Ошибка установки Java 17",
        font=("Comfortaa", 12, "bold"),
        foreground="red",
    ).pack(pady=10)

    tk.Label(
        error_window,
        text="Не удалось автоматически установить Java 17",
        font=("Comfortaa", 10),
    ).pack(pady=5)

    # Детали ошибки
    details_text = tk.Text(error_window, height=8, width=60, font=("Consolas", 8))
    details_text.pack(pady=10, padx=10, fill="both", expand=True)
    details_text.insert("1.0", f"Детали ошибки:\n{error_msg}")
    details_text.config(state="disabled")

    # Рекомендации
    tk.Label(error_window, text="Рекомендации:", font=("Comfortaa", 9, "bold")).pack()
    tk.Label(
        error_window,
        text="1. Установите Java 17 вручную с adoptium.net\n2. Перезапустите лаунчер",
        font=("Comfortaa", 8),
    ).pack()

    tk.Button(error_window, text="Закрыть", command=error_window.destroy).pack(pady=10)

def skip_java_check():
    """Пропустить проверку Java (для опытных пользователей)"""
    result = messagebox.askyesno(
        "Пропустить проверку Java",
        "Вы уверены, что хотите пропустить проверку Java?\n\n"
        "Игра может не запуститься если Java 17 не установлена.\n"
        "Продолжить на свой страх и риск?",
        icon="warning",
    )
    return result


# Инициализация звука
mixer.init()
mixer.music.set_volume(0.1)

# Создание главного окна
win = ThemedTk(theme="arc")
win.geometry("1920x1080")
set_window_icon(win)
win.title("YamPixel")

# === ПЕРЕМЕЩАЕМ СЮДА ВСЁ ОТНОСИТЕЛЬНО СЕССИИ ===
LAST_SESSION_FILE = os.path.expanduser("~/YamalPixel/last_session.json")


def load_last_session():
    """Загружает последние настройки"""
    try:
        if os.path.exists(LAST_SESSION_FILE):
            with open(LAST_SESSION_FILE, "r", encoding="utf-8") as f:
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
        if "username" in globals() and hasattr(username, "text_value"):
            current_username = username.text_value.get()
            if current_username and current_username != "Введите никнейм":
                session_data["username"] = current_username

        # Сохраняем выбранную версию
        if "version_selector" in globals() and hasattr(
            version_selector, "current_value"
        ):
            current_version = version_selector.current_value.get()
            if current_version:
                session_data["version"] = current_version

        # Сохраняем настройки памяти
        session_data["memory"] = CONFIG.get("jvm_memory", "4G")

        # Сохраняем настройки полноэкранного режима
        if "enabled" in globals():
            session_data["fullscreen"] = bool(enabled.get())

        # Сохраняем настройки музыки
        if "enabled1" in globals():
            session_data["music"] = bool(enabled1.get())

        # Добавляем временную метку
        session_data["launcher_version"] = CURRENT_VERSION

        # Сохраняем только если есть что сохранять
        if session_data:
            # Создаем папку если не существует
            os.makedirs(os.path.dirname(LAST_SESSION_FILE), exist_ok=True)

            with open(LAST_SESSION_FILE, "w", encoding="utf-8") as f:
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
        if "username" in globals() and session.get("username"):
            username.text_value.set(session["username"])
            username.entry.configure(fg="#2b2b2b")
            print(f"👤 Восстановлен ник: {session['username']}")
            applied_count += 1

        # Восстанавливаем версию
        if "version_selector" in globals() and session.get("version"):
            try:
                target_version = session["version"]
                # Устанавливаем значение напрямую
                version_selector.current_value.set(target_version)
                version_selector.draw_selector()
                print(f"🎯 Восстановлена версия: {target_version}")
                applied_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка восстановления версии: {e}")

        # Восстанавливаем память
        if session.get("memory"):
            CONFIG["jvm_memory"] = session["memory"]
            print(f"💾 Восстановлена память: {session['memory']}")
            applied_count += 1

        # Восстанавливаем полноэкранный режим
        if "enabled" in globals() and session.get("fullscreen"):
            enabled.set(True)
            fullsc()
            print("🖥️ Восстановлен полноэкранный режим")
            applied_count += 1

        # Восстанавливаем музыку
        if "enabled1" in globals() and session.get("music"):
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
            print(
                f"🔄 Восстанавливаем сессию от {session.get('timestamp', 'неизвестно')}"
            )
            # Даем время на создание всех элементов интерфейса
            win.after(3000, lambda: apply_session_settings(session)) # noqa
        else:
            print("🔰 Сессия не найдена, используем настройки по умолчанию")
    except Exception as e:
        print(f"❌ Ошибка загрузки сессии: {e}")


# Запускаем загрузку сессии после полной инициализации
win.after(3500, load_session_on_start)  # noqa

win.after(200, check_for_updates)  # noqa

# Вызываем перед созданием главного окна
setup_environment()

# Модифицируем блок инициализации звука:
mixer.init()
mixer.music.load(str(RESOURCE_DIR / "menu_song.mp3"))
mixer.music.set_volume(0.1)

# Модифицируем блок GUI элементов:
bag = None
img = ttk.Label(win)
img.place(x=0, y=-1, relwidth=1, relheight=1)


def setup_adaptive_background():
    """Автоматический подбор фона под разрешение экрана"""
    try:
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        print(f"🖥️ Обнаружено разрешение: {screen_width}x{screen_height}")

        # Прямое соответствие
        bg_file = RESOLUTION_MAP.get((screen_width, screen_height))

        if bg_file:
            print(f"✅ Найдено точное соответствие: {bg_file}")
            load_custom_background(bg_file)
        else:
            # Используем стандартный
            print("🔧 Используем стандартный фон")
            load_default_background()

    except Exception as e:
        print(f"❌ Ошибка в setup_adaptive_background: {e}")
        load_default_background()


def load_custom_background(filename):
    """Загружает кастомный фон"""
    try:
        bg_path = RESOURCE_DIR / filename
        if bg_path.exists():
            global bag, img
            bag = tk.PhotoImage(file=str(bg_path))
            img.configure(image=bag)
            print(f"🎨 Успешно загружен фон: {filename}")
        else:
            print(f"⚠️ Фон {filename} не найден")
            load_default_background()

    except Exception as e:
        print(f"❌ Ошибка загрузки фона {filename}: {e}")
        load_default_background()


def load_default_background():
    """Загружает стандартный фон"""
    try:
        global bag, img
        default_bg = RESOURCE_DIR / "logo.png"
        if default_bg.exists():
            bag = tk.PhotoImage(file=str(default_bg))
            img.configure(image=bag)
            print("🔧 Используем стандартный фон logo.png")
    except Exception as e:
        print(f"💥 Критическая ошибка загрузки фона: {e}")


def create_background_selector():
    """Создает кнопку для ручного выбора фона"""
    try:
        selector_btn = ModernButton(
            win,
            text="🎨 Сменить фон",
            width=160,
            height=32,
            gradient=("#667eea", "#764ba2"),
            command=show_background_menu,
            font_size=10,
        )
        selector_btn.place(relx=0.5, rely=0.68, anchor="center")
        return selector_btn
    except Exception as e:
        print(f"❌ Ошибка создания кнопки фона: {e}")


def show_background_menu():
    """Показывает меню выбора фона"""
    try:
        menu = tk.Menu(win, tearoff=0, bg="#2b2b2b", fg="white", font=("Comfortaa", 9))

        for name, file in backgrounds:
            menu.add_command(
                label=name, command=lambda f=file: load_custom_background(f)
            )

        # Показываем меню под курсором
        menu.tk_popup(win.winfo_pointerx(), win.winfo_pointery())
    except Exception as e:
        print(f"❌ Ошибка показа меню фонов: {e}")


# Функции для управления окном
def fullsc():
    win.attributes("-fullscreen", True)


def outscrn():
    win.attributes("-fullscreen", False)


def open_game_folder():
    minecraft_dir = CONFIG["minecraft_dir"]
    try:
        if os.path.exists(minecraft_dir):
            if os.name == "nt":  # Windows
                os.startfile(minecraft_dir)
            elif os.name == "posix":  # Linux/MacOS
                subprocess.Popen(["xdg-open", minecraft_dir])
            print(f"Открыта папка с игрой: {minecraft_dir}")
        else:
            messagebox.showwarning(
                "Папка не найдена", f"Папка {minecraft_dir} не существует!"
            )
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")


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
        backup_dir = os.path.join(CONFIG["minecraft_dir"], "backups")
        os.makedirs(backup_dir, exist_ok=True)

        backup_filename = f"{backup_type}_backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)

        print(f"📦 Создаем архив: {backup_path}")

        created_files = []
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
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
    backup_dir = os.path.join(CONFIG["minecraft_dir"], "backups")
    print(f"🔍 Поиск бэкапов в: {backup_dir}")

    if not os.path.exists(backup_dir):
        print("❌ Папка бэкапов не существует")
        return []

    # Получаем все файлы бэкапов
    backup_files = []
    for filename in os.listdir(backup_dir):
        if filename.endswith(".zip"):
            file_path = os.path.join(backup_dir, filename)
            time_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path))

            # ПРАВИЛЬНО определяем тип бэкапа - используем startswith вместо in
            if filename.startswith("mods_backup_"):
                timestamp = filename.replace("mods_backup_", "").replace(".zip", "")
                backup_type = "mods"
            elif filename.startswith("versions_backup_"):
                timestamp = filename.replace("versions_backup_", "").replace(".zip", "")
                backup_type = "versions"
            elif filename.startswith("world_backup_"):
                timestamp = filename.replace("world_backup_", "").replace(".zip", "")
                backup_type = "world"
            else:
                continue  # Пропускаем файлы с другими именами

            backup_files.append(
                {
                    "filename": filename,
                    "path": file_path,
                    "type": backup_type,
                    "date": time_created.strftime("%d.%m.%Y %H:%M"),
                    "timestamp": timestamp,
                }
            )

    print(f"📁 Найдено файлов бэкапов: {len(backup_files)}")
    for bf in backup_files:
        print(f"   - {bf['filename']} (тип: {bf['type']})")

    if not backup_files:
        return []

    # Группируем по timestamp
    backup_groups = {}
    for backup in backup_files:
        ts = backup["timestamp"]
        if ts not in backup_groups:
            backup_groups[ts] = {"timestamp": ts, "date": backup["date"]}

        # Добавляем моды, версии или мир в группу
        backup_groups[ts][backup["type"]] = backup

    # Преобразуем в список и сортируем
    result = list(backup_groups.values())
    result.sort(key=lambda x: x["timestamp"], reverse=True)

    print(f"🎯 Сформировано групп бэкапов: {len(result)}")
    for item in result:
        components = []
        if "mods" in item:
            components.append("Моды")
        if "versions" in item:
            components.append("Версии")
        if "world" in item:
            components.append("Мир")
        print(f"   - {item['date']}: {', '.join(components)}")

    return result

def create_manual_backup():
    """Создает бэкап вручную по кнопке с автоматическими тестовыми файлами"""
    print("💾 Запуск создания бэкапа...")
    minecraft_dir = CONFIG["minecraft_dir"]
    mods_dir = os.path.join(minecraft_dir, "mods")
    versions_dir = os.path.join(minecraft_dir, "versions")
    world_dir = os.path.join(minecraft_dir, "world")

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
            test_mod = os.path.join(mods_dir, "auto_created_mod.jar")
            with open(test_mod, "w", encoding="utf-8") as f:
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
            test_version = os.path.join(versions_dir, "version_info.txt")
            with open(test_version, "w", encoding="utf-8") as f:
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
            test_world = os.path.join(world_dir, "level.dat")
            with open(test_world, "w", encoding="utf-8") as f:
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
        backup_info = "Созданы бэкапы:\n" + "\n".join(
            [f"• {os.path.basename(b)}" for b in backups_created]
        )
        messagebox.showinfo("Бэкапы созданы", backup_info)
    else:
        messagebox.showinfo("Бэкапы", "Не удалось создать бэкапы (папки не найдены)")


def show_backup_info():
    """Показывает информацию о бэкапах"""
    backup_dir = os.path.join(CONFIG["minecraft_dir"], "backups")
    if not os.path.exists(backup_dir):
        messagebox.showinfo("Бэкапы", "Бэкапы не создавались")
        return

    backups = []
    total_size = 0
    for filename in os.listdir(backup_dir):
        if filename.endswith(".zip"):
            file_path = os.path.join(backup_dir, filename)
            size = os.path.getsize(file_path) / (1024 * 1024)  # Размер в МБ
            total_size += size
            time_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path))

            # Определяем тип бэкапа
            if filename.startswith("mods_backup_"):
                backup_type = "Моды"
            elif filename.startswith("versions_backup_"):
                backup_type = "Версии"
            elif filename.startswith("world_backup_"):
                backup_type = "Мир"
            else:
                backup_type = "Другой"

            backups.append(
                (
                    filename,
                    f"{size:.1f} МБ",
                    time_created.strftime("%d.%m.%Y %H:%M"),
                    backup_type,
                )
            )

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
    backup_dir = os.path.join(CONFIG["minecraft_dir"], "backups")
    if not os.path.exists(backup_dir):
        messagebox.showinfo("Бэкапы", "Папка бэкапов не существует")
        return

    # Подсчитываем количество бэкапов
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".zip")]
    if not backup_files:
        messagebox.showinfo("Бэкапы", "Бэкапов не найдено")
        return

    # Подтверждение удаления
    result = messagebox.askyesno(
        "Удаление бэкапов",
        f"Вы уверены, что хотите удалить ВСЕ бэкапы?\n\n"
        f"Будет удалено: {len(backup_files)} файлов\n"
        f"Это действие нельзя отменить!",
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
    backup_frame = ttk.LabelFrame(
        parent_frame, text="🔄 Управление бэкапами", padding=10
    )
    backup_frame.pack(fill="x", padx=10, pady=5)

    # Кнопки в ряд
    button_row1 = ttk.Frame(backup_frame)
    button_row1.pack(fill="x", pady=5)

    ttk.Button(
        button_row1, text="💾 Создать бэкап", command=create_manual_backup, width=15
    ).pack(side="left", padx=5)

    # Второй ряд кнопок
    button_row2 = ttk.Frame(backup_frame)
    button_row2.pack(fill="x", pady=5)

    ttk.Button(
        button_row2, text="📊 Информация о бэкапах", command=show_backup_info, width=20
    ).pack(side="left", padx=5)
    ttk.Button(
        button_row2, text="🗑️ Удалить все бэкапы", command=delete_all_backups, width=18
    ).pack(side="left", padx=5)


def repair_missing_mods_with_progress():
    """Загрузка отсутствующих модов с прогресс-баром"""
    # Создаем окно прогресса (аналогично checker1)
    progress_window = tk.Toplevel(win)
    set_window_icon(progress_window)
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
    main_frame.pack(fill="both", expand=True)

    title_label = ttk.Label(
        main_frame, text="🔧 Починка модов", font=("Comfortaa", 14, "bold")
    )
    title_label.pack(pady=(0, 15))

    total_progress_label = ttk.Label(main_frame, text="Общий прогресс: 0%")
    total_progress_label.pack()

    total_progress = ttk.Progressbar(
        main_frame, orient="horizontal", length=400, mode="determinate"
    )
    total_progress.pack(pady=5)

    current_mod_label = ttk.Label(main_frame, text="Подготовка к загрузке...")
    current_mod_label.pack()

    status_label = ttk.Label(
        main_frame, text="Инициализация...", font=("Comfortaa", 9), foreground="blue"
    )
    status_label.pack(pady=10)

    def update_progress(current, total, mod_name="", status=""):
        """Обновляет прогресс в UI"""
        try:
            total_percent = (current * 100) // total if total > 0 else 0
            total_progress["value"] = total_percent
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
            mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
            base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"

            # Определяем какие моды нужно скачать
            mods_to_download = []
            for mod in CONFIG["mods"]:
                mod_path = os.path.join(mods_dir, mod["file"])
                if not os.path.exists(mod_path):
                    mods_to_download.append(mod)

            total_mods = len(mods_to_download)
            success_count = 0

            if total_mods == 0:
                win.after(0, lambda: progress_window.destroy()) # noqa
                return

            win.after(0, lambda: update_progress(0, total_mods, "Подготовка...")) # noqa

            for i, mod in enumerate(mods_to_download):
                try:
                    win.after(0,lambda idx=i, m=mod: update_progress( idx, total_mods, m["file"], "Получение ссылки..."),) # noqa

                    # Получаем прямую ссылку
                    params = {"public_key": mod["url"]}
                    response = requests.get(base_url, params=params, timeout=30)
                    response.raise_for_status()
                    download_url = response.json().get("href")

                    if not download_url:
                        continue

                    # Загружаем файл
                    mod_path = os.path.join(mods_dir, mod["file"])

                    with requests.get(
                        download_url, stream=True, timeout=60
                    ) as dl_response:
                        dl_response.raise_for_status()

                        total_size = int(dl_response.headers.get("content-length", 0))
                        downloaded_size = 0

                        with open(mod_path, "wb") as f:
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)

                                    # Обновляем прогресс
                                    win.after(
                                        0,
                                        lambda: update_progress(
                                            i,
                                            total_mods,
                                            mod["file"],
                                            f"Загружено: {downloaded_size / (1024 * 1024):.1f}MB",),) # noqa

                        if os.path.exists(mod_path) and os.path.getsize(mod_path) > 0:
                            success_count += 1
                            win.after(
                                0,
                                lambda: update_progress(
                                    i + 1, total_mods, mod["file"], "✅ Успешно"),) # noqa
                        else:
                            win.after(
                                0,
                                lambda: update_progress(
                                    i + 1, total_mods, mod["file"], "❌ Ошибка"),) # noqa

                except Exception as e:
                    win.after(
                        0,
                        lambda: update_progress(
                            i + 1, total_mods, mod["file"], f"❌ Ошибка: {str(e)[:30]}"
                        ),
                    ) # noqa

            # Закрываем окно
            win.after(1000, lambda: progress_window.destroy()) # noqa

        except Exception as e:
            win.after(0, lambda: progress_window.destroy()) # noqa

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
        icon="question",
    )

    if not result:
        return

    minecraft_dir = CONFIG["minecraft_dir"]
    mods_dir = os.path.join(minecraft_dir, "mods")
    disabled_dir = os.path.join(minecraft_dir, "mods_disabled_temp")

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
            if filename.endswith(".jar"):
                try:
                    shutil.move(
                        os.path.join(mods_dir, filename),
                        os.path.join(disabled_dir, filename),
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
            f"Моды находятся в: {disabled_dir}",
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
        icon="warning",
    )

    if not result:
        return

    minecraft_dir = CONFIG["minecraft_dir"]

    # Создаем полные бэкапы
    backups_created = []

    # Бэкап модов
    mods_dir = os.path.join(minecraft_dir, "mods")
    if os.path.exists(mods_dir) and os.listdir(mods_dir):
        backup_path = create_backup(mods_dir, "mods_full_backup")
        if backup_path:
            backups_created.append(f"Моды: {os.path.basename(backup_path)}")

    # Бэкап мира
    world_dir = os.path.join(minecraft_dir, "world")
    if os.path.exists(world_dir) and os.listdir(world_dir):
        backup_path = create_backup(world_dir, "world_full_backup")
        if backup_path:
            backups_created.append(f"Мир: {os.path.basename(backup_path)}")

    # Бэкап конфигов
    config_dir = os.path.join(minecraft_dir, "config")
    if os.path.exists(config_dir) and os.listdir(config_dir):
        backup_path = create_backup(config_dir, "config_full_backup")
        if backup_path:
            backups_created.append(f"Настройки: {os.path.basename(backup_path)}")

    # Полностью удаляем папку Minecraft
    progress_window = tk.Toplevel(win)
    progress_window.title("Переустановка")
    set_window_icon(progress_window)
    progress_window.geometry("400x150")

    progress_label = ttk.Label(progress_window, text="Удаление старых файлов...")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(
        progress_window, orient="horizontal", length=300, mode="indeterminate"
    )
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
            os.makedirs(os.path.join(minecraft_dir, "mods"), exist_ok=True)
            os.makedirs(os.path.join(minecraft_dir, "config"), exist_ok=True)
            os.makedirs(os.path.join(minecraft_dir, "shaderpacks"), exist_ok=True)

            progress_label.config(text="Установка Minecraft...")

            # Чистая установка Minecraft
            minecraft_launcher_lib.install.install_minecraft_version(
                versionid=CONFIG["version"], minecraft_directory=minecraft_dir
            )

            progress_label.config(text="Установка Fabric...")

            # Чистая установка Fabric
            minecraft_launcher_lib.fabric.install_fabric(
                minecraft_version=CONFIG["version"],
                loader_version=CONFIG["fabric_loader"],
                minecraft_directory=minecraft_dir,
            )

            progress_label.config(text="Установка модов...")

            # Скачиваем только ОСНОВНЫЕ моды (без проблемных)
            base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"



            for mod in essential_mods:
                try:
                    mods_dir_path = os.path.join(minecraft_dir, "mods")
                    mod_path = os.path.join(mods_dir_path, mod["file"])

                    params = {"public_key": mod["url"]}
                    response = requests.get(base_url, params=params)
                    response.raise_for_status()
                    download_url = response.json().get("href")

                    if download_url:
                        with open(mod_path, "wb") as f:
                            dl_response = requests.get(download_url, stream=True)
                            dl_response.raise_for_status()
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        # Распаковываем ZIP если нужно
                        if mod["file"].endswith(".zip"):
                            try:
                                with zipfile.ZipFile(mod_path, "r") as zip_file:
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
                report += (
                    "📦 Созданы бэкапы:\n"
                    + "\n".join([f"• {b}" for b in backups_created])
                    + "\n\n"
                )

            report += "🔄 Установлено:\n"
            report += "• Чистая версия Minecraft 1.20.1\n"
            report += "• Fabric Loader 0.17.2\n"
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
    set_window_icon(diag_window)
    diag_window.title("Диагностика проблем")
    diag_window.geometry("700x550")
    diag_window.configure(bg="#2b2b2b")  # Темный фон окна

    # Заголовок
    header_frame = ttk.Frame(diag_window)
    header_frame.pack(fill="x", padx=20, pady=15)

    ttk.Label(
        header_frame,
        text="Диагностика проблем",
        font=("Comfortaa", 16, "bold"),
        foreground="white",
        background="#2b2b2b",
    ).pack()

    ttk.Label(
        header_frame,
        text="Автоматическая проверка и решение проблем",
        font=("Comfortaa", 10),
        foreground="#cccccc",
        background="#2b2b2b",
    ).pack(pady=(5, 0))

    # Прогресс-бар
    progress_frame = ttk.Frame(diag_window)
    progress_frame.pack(fill="x", padx=20, pady=10)

    progress_label = ttk.Label(
        progress_frame,
        text="Проводим диагностику...",
        foreground="white",
        background="#2b2b2b",
    )
    progress_label.pack()

    progress_bar = ttk.Progressbar(
        progress_frame, orient="horizontal", length=650, mode="indeterminate"
    )
    progress_bar.pack(pady=5)
    progress_bar.start()

    # Окно результатов - ЧЕРНОЕ с цветным текстом
    results_frame = ttk.Frame(diag_window)
    results_frame.pack(fill="both", expand=True, padx=20, pady=10)

    results_text = tk.Text(
        results_frame,
        height=12,
        wrap="word",
        font=("Consolas", 9),
        bg="#1a1a1a",  # Черный фон
        fg="#00ff88",  # Зеленый текст по умолчанию
        relief="solid",
        borderwidth=1,
        padx=10,
        pady=10,
    )

    scrollbar = ttk.Scrollbar(
        results_frame, orient="vertical", command=results_text.yview
    )
    results_text.configure(yscrollcommand=scrollbar.set)

    results_text.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Статус
    status_frame = ttk.Frame(diag_window)
    status_frame.pack(fill="x", padx=20, pady=5)

    status_label = ttk.Label(
        status_frame,
        text="Начинаем проверку...",
        foreground="#ffaa00",
        background="#2b2b2b",
    )
    status_label.pack()

    # Кнопки
    button_frame = ttk.Frame(diag_window)
    button_frame.pack(fill="x", padx=20, pady=15)

    # Первый ряд
    row1 = ttk.Frame(button_frame)
    row1.pack(fill="x", pady=5)

    ttk.Button(
        row1, text="Запуск без модов", command=launch_without_mods, width=18
    ).pack(side="left", padx=5)

    # Второй ряд
    row2 = ttk.Frame(button_frame)
    row2.pack(fill="x", pady=5)

    ttk.Button(
        row2, text="Полная переустановка", command=complete_reinstall, width=18
    ).pack(side="left", padx=5)

    ttk.Button(
        row2,
        text="Создать отчет",
        command=lambda: create_debug_report(results_text),
        width=15,
    ).pack(side="left", padx=5)

    ttk.Button(row2, text="Закрыть", command=diag_window.destroy, width=12).pack(
        side="right", padx=5
    )

    # Функции диагностики с цветным текстом
    def add_result(text, color="#00ff88"):  # Зеленый по умолчанию
        results_text.insert("end", f"{text}\n", color)
        results_text.see("end")
        diag_window.update()

    def run_diagnostic():
        try:
            problems_found = []
            minecraft_dir = CONFIG["minecraft_dir"]

            # Проверка структуры - зеленый
            for folder in ["mods", "versions", "config"]:
                path = os.path.join(minecraft_dir, folder)
                if os.path.exists(path):
                    add_result(f"✅ Папка {folder} найдена", "#00ff88")
                else:
                    problems_found.append(f"Отсутствует папка {folder}")
                    add_result(
                        f"❌ Папка {folder} не найдена", "#ff4444"
                    )  # Красный для ошибок

            # Проверка модов - голубой
            mods_dir = os.path.join(minecraft_dir, "mods")
            if os.path.exists(mods_dir):
                mod_files = [f for f in os.listdir(mods_dir) if f.endswith(".jar")]
                add_result(f"📦 Найдено модов: {len(mod_files)}", "#00ccff")  # Голубой

                if len(mod_files) == 0:
                    problems_found.append("Папка модов пустая")
                    add_result(
                        "⚠️ Папка модов пуста", "#ffaa00"
                    )  # Желтый для предупреждений

            # Проверка ресурсов - зеленый/желтый
            memory = psutil.virtual_memory()
            if memory.available < 3 * 1024 * 1024 * 1024:
                problems_found.append("Мало оперативной памяти")
                add_result(
                    f"⚠️ Мало ОЗУ: {memory.available // 1024 // 1024}MB свободно",
                    "#ffaa00",
                )
            else:
                add_result(
                    f"✅ ОЗУ: {memory.available // 1024 // 1024}MB свободно", "#00ff88"
                )

            disk = psutil.disk_usage(minecraft_dir)
            if disk.free < 2 * 1024 * 1024 * 1024:
                problems_found.append("Мало места на диске")
                add_result(
                    f"⚠️ Мало места: {disk.free // 1024 // 1024}MB свободно", "#ffaa00"
                )
            else:
                add_result(
                    f"✅ Диск: {disk.free // 1024 // 1024}MB свободно", "#00ff88"
                )

            # Java - зеленый/красный
            java_ok = check_java_version()
            if java_ok:
                add_result("✅ Java установлена и работает", "#00ff88")
            else:
                problems_found.append("Проблемы с Java")
                add_result("❌ Java не найдена", "#ff4444")

            # Финальный отчет
            progress_bar.stop()

            if problems_found:
                add_result(f"\n🚨 Найдено проблем: {len(problems_found)}", "#ff4444")
                for problem in problems_found:
                    add_result(f"• {problem}", "#ffaa00")
                status_label.config(
                    text=f"Обнаружено {len(problems_found)} проблем",
                    foreground="#ff4444",
                )
            else:
                add_result("\n🎉 Все системы в норме!", "#00ff88")
                add_result("Игра должна запускаться без проблем", "#00ccff")
                status_label.config(text="Проблем не обнаружено", foreground="#00ff88")

        except Exception as e:
            add_result(f"❌ Ошибка диагностики: {str(e)}", "#ff4444")
            status_label.config(text="Ошибка при диагностике", foreground="#ff4444")

    # Настройка цветов для текста
    results_text.tag_configure("#00ff88", foreground="#00ff88")  # Зеленый
    results_text.tag_configure("#ff4444", foreground="#ff4444")  # Красный
    results_text.tag_configure("#ffaa00", foreground="#ffaa00")  # Желтый
    results_text.tag_configure("#00ccff", foreground="#00ccff")  # Голубой

    # Запускаем диагностику
    diag_window.after(500, run_diagnostic)
    diag_window.focus_force()


def create_debug_report(text_widget):
    """Создает отчет"""
    report_path = os.path.join(CONFIG["minecraft_dir"], "diagnostic_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text_widget.get("1.0", "end"))

    messagebox.showinfo("Отчет создан", f"Отчет сохранен в:\n{report_path}")


def show_version_info():
    """Показывает информацию о версии лаунчера"""
    messagebox.showinfo(
        "О лаунчере",
        f"YamalPixel Launcher\nВерсия: {CURRENT_VERSION}\n\n"
        f"Разработано с ❤️ для комьюнити",
    )





def format_changelog(changelog):
    """Форматирует changelog для красивого отображения"""
    if not changelog:
        return "Нет описания изменений"

    # Убираем Markdown-разметку
    changelog = re.sub(r"#{2,}", "", changelog)  # Убираем заголовки
    changelog = re.sub(r"\- ", "• ", changelog) # noqa
    changelog = re.sub(r"\*\*(.*?)\*\*", r"▸ \1", changelog)
    changelog = re.sub(r"\*(.*?)\*", r"\1", changelog)
    changelog = re.sub(r"`(.*?)`", r"\1", changelog)

    # Ограничиваем длину
    if len(changelog) > 1000:
        changelog = (
            changelog[:1000] + "...\n\n[Описание обрезано, полная версия на GitHub]"
        )

    return changelog.strip()


def is_latest_version():
    """Проверяет, является ли текущая версия последней"""
    try:
        response = requests.get(
            "https://api.github.com/repos/XxMoonmenxX/YamalPixel/releases/latest",
            timeout=5,
        )
        response.raise_for_status()

        latest_release = response.json()
        latest_version = latest_release["tag_name"].lstrip("v")

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

    else:

        launch_btn.config(state="normal")  # Разблокируем кастомную кнопку

def is_launch_timeout():
    """Проверяет, не завис ли запуск"""
    if LAUNCH_START_TIME and time.time() - LAUNCH_START_TIME > 120:  # 2 минуты таймаут
        return True
    return False


def is_game_process_running():
    """Проверяет, запущен ли уже процесс Minecraft"""
    try:
        if os.name == "nt":  # Windows
            result = subprocess.run(
                ["tasklist", "/fi", "imagename eq javaw.exe", "/fo", "csv"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            # Если есть процессы javaw.exe, считаем что игра может быть запущена
            return "javaw.exe" in result.stdout
        else:  # Linux/MacOS
            result = subprocess.run(
                ["pgrep", "-f", "minecraft"], capture_output=True, text=True
            )
            return result.returncode == 0
    except:
        return False


def create_progress_window():
    """Создает окно прогресса с защитой от множественного создания и корректной отменой запуска"""
    progress_window = tk.Toplevel(win)
    set_window_icon(progress_window)
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
    main_frame.pack(fill="both", expand=True)

    # Заголовок
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 20))
    ttk.Label(
        header_frame, text="🚀 Запуск YamalPixel", font=("Comfortaa", 16, "bold")
    ).pack()
    ttk.Label(
        header_frame,
        text="Подготовка к запуску игры...",
        font=("Comfortaa", 11),
        foreground="gray",
    ).pack(pady=(5, 0))

    # Прогресс-бар
    progress_frame = ttk.Frame(main_frame)
    progress_frame.pack(fill="x", pady=10)
    progress = ttk.Progressbar(
        progress_frame, orient="horizontal", length=400, mode="indeterminate"
    )
    progress.pack(pady=5)
    progress.start()

    # Статус запуска
    status_label = ttk.Label(
        progress_frame, text="Инициализация запуска...", font=("Comfortaa", 10)
    )
    status_label.pack()




def monitor_game_process(process):
    """Мониторит процесс игры и разблокирует интерфейс при завершении"""
    process.wait()
    # Если процесс завершился, разблокируем интерфейс
    win.after(0, lambda: set_launch_state(False))


# ДОБАВЬ ЭТО ПРЯМО ПЕРЕД СОЗДАНИЕМ menu_bar:


def show_simple_background_selector():
    """Простой выбор фона через отдельное окно"""
    try:
        selector_window = tk.Toplevel(win)
        set_window_icon(selector_window)
        selector_window.title("Выбор фона для лаунчера")
        selector_window.geometry("400x500")
        selector_window.configure(bg="#2b2b2b")
        selector_window.resizable(False, False)
        selector_window.transient(win)
        selector_window.grab_set()

        # Центрируем окно
        selector_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (400 // 2)
        y = (win.winfo_screenheight() // 2) - (500 // 2)
        selector_window.geometry(f"400x500+{x}+{y}")

        main_frame = ttk.Frame(selector_window, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(
            main_frame,
            text="🎨 Выбор фона",
            font=("Comfortaa", 16, "bold"),
            foreground="white",
            background="#2b2b2b",
        ).pack(pady=(0, 20))

        # Описание
        ttk.Label(
            main_frame,
            text="Выберите фон для своего разрешения экрана:",
            font=("Comfortaa", 10),
            foreground="#cccccc",
            background="#2b2b2b",
        ).pack(pady=(0, 15))

        # Список фонов


        # Создаем кнопки выбора
        for name, filename in backgrounds:
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x", pady=4)

            btn = ModernButton(
                btn_frame,
                text=name,
                width=320,
                height=36,
                gradient=("#4A5568", "#2D3748"),
                command=lambda f=filename: apply_background_and_close(
                    f, selector_window
                ),
                font_size=10,
                corner_radius=8,
            )
            btn.pack(pady=2)

        # Разделитель
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.pack(fill="x", pady=15)

        # Кнопка автоопределения
        auto_btn = ModernButton(
            main_frame,
            text="🔧 Автоопределение (рекомендуется)",
            width=320,
            height=36,
            gradient=("#667eea", "#764ba2"),
            command=lambda: (setup_adaptive_background(), selector_window.destroy()),
            font_size=10,
            corner_radius=8,
        )
        auto_btn.pack(pady=5)

        # Кнопка закрытия
        close_btn = ModernButton(
            main_frame,
            text="❌ Закрыть",
            width=200,
            height=32,
            gradient=("#718096", "#4A5568"),
            command=selector_window.destroy,
            font_size=10,
            corner_radius=6,
        )
        close_btn.pack(pady=10)

    except Exception as e:
        print(f"❌ Ошибка открытия селектора фонов: {e}")
        messagebox.showerror("Ошибка", "Не удалось открыть выбор фона")


def apply_background_and_close(filename, window):
    """Применяет фон и закрывает окно"""
    load_custom_background(filename)
    window.destroy()
    messagebox.showinfo("Успех", f"Фон {filename} применен!")


# А вот теперь создаем меню
menu_bar = tk.Menu(win)
win.config(menu=menu_bar)
settings_menu = tk.Menu(menu_bar, tearoff=0)

# И добавляем нашу команду
settings_menu.add_command(
    label="🎨 Выбрать фон вручную", command=show_simple_background_selector
)

menu_bar = tk.Menu(win)
win.config(menu=menu_bar)
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_separator(background="#FFB6C1")

settings_menu.configure(
    tearoffcommand=lambda: None,
    postcommand=lambda: settings_menu.configure(bg="#FFB6C1"),
)
menu_bar.add_cascade(label="Инструменты", menu=settings_menu)


# ОБНОВЛЕННЫЕ ПУНКТЫ МЕНЮ:
settings_menu.add_command(
    label="🎨 Скачать шейдеры", command=download_shaders
)  # НОВАЯ КНОПКА
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
settings_menu.add_command(label="🎨 Выбрать фон вручную", command=show_simple_background_selector)


# Или если хотите в выпадающем меню "Справка":
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="О лаунчере", command=show_version_info)
help_menu.add_separator()
help_menu.add_command(label="Проверить обновления", command=lambda: check_for_updates_local(win))
menu_bar.add_cascade(label="Справка", menu=help_menu)




def setup_adaptive_background():
    """Автоматический подбор фона под разрешение экрана"""

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    print(f"🖥️ Обнаружено разрешение: {screen_width}x{screen_height}")

    # Прямое соответствие
    bg_file = RESOLUTION_MAP.get((screen_width, screen_height))

    if bg_file:
        print(f"✅ Найдено точное соответствие: {bg_file}")
        load_custom_background(bg_file)
    else:
        # Ищем ближайшее по соотношению сторон
        bg_file = find_closest_resolution(screen_width, screen_height)
        print(f"🔄 Используем ближайшее: {bg_file}")
        load_custom_background(bg_file)

def find_closest_resolution(width, height):
    """Находит ближайшее разрешение по соотношению сторон"""
    aspect_ratio = width / height

    # Ближайшие соотношения сторон


    # Ищем с наименьшей разницей в соотношении
    best_match = "logo1.png"  # дефолт
    min_diff = float("inf")

    for res, target_ratio in ratios.items():
        diff = abs(aspect_ratio - target_ratio)
        if diff < min_diff:
            min_diff = diff
            best_match = RESOLUTION_MAP[res]

    return best_match


def load_custom_background(filename):
    """Загружает кастомный фон"""
    try:
        bg_path = RESOURCE_DIR / filename
        if bg_path.exists():
            global bag, img
            bag = tk.PhotoImage(file=str(bg_path))
            img.configure(image=bag)
            print(f"🎨 Загружен фон: {filename}")
        else:
            print(f"⚠️ Фон {filename} не найден")
            # Грузим стандартный как запасной вариант
            load_default_background()
    except Exception as e:
        print(f"❌ Ошибка загрузки фона {filename}: {e}")
        load_default_background()


def load_default_background():
    """Загружает стандартный фон"""
    try:
        global bag, img
        default_bg = RESOURCE_DIR / "logo.png"
        if default_bg.exists():
            bag = tk.PhotoImage(file=str(default_bg))
            img.configure(image=bag)
            print("🔧 Используем стандартный фон")
    except Exception as e:
        print(f"💥 Критическая ошибка загрузки фона: {e}")


def setup_adaptive_background():
    """Автоматический подбор фона под разрешение экрана"""


    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    print(f"🖥️ Обнаружено разрешение: {screen_width}x{screen_height}")

    # Прямое соответствие
    bg_file = RESOLUTION_MAP.get((screen_width, screen_height))

    if bg_file:
        print(f"✅ Найдено точное соответствие: {bg_file}")
        load_custom_background(bg_file)
    else:
        # Ищем ближайшее по соотношению сторон
        bg_file = find_closest_resolution(screen_width, screen_height)
        print(f"🔄 Используем ближайшее: {bg_file}")
        load_custom_background(bg_file)


def find_closest_resolution(width, height):
    """Находит ближайшее разрешение по соотношению сторон"""
    if width == 0 or height == 0:
        return "logo.png"

    aspect_ratio = width / height

    # Соотношения сторон для каждого разрешения


    # Ищем с наименьшей разницей в соотношении
    best_match = "logo1.png"  # дефолт - самый популярный
    min_diff = float("inf")

    for file, target_ratio in resolution_ratios.items():
        diff = abs(aspect_ratio - target_ratio)
        if diff < min_diff:
            min_diff = diff
            best_match = file

    print(f"📐 Соотношение сторон: {aspect_ratio:.2f}, выбрано: {best_match}")
    return best_match


def load_custom_background(filename):
    """Загружает кастомный фон"""
    try:
        bg_path = RESOURCE_DIR / filename
        if bg_path.exists():
            global bag, img
            bag = tk.PhotoImage(file=str(bg_path))
            img.configure(image=bag)
            print(f"🎨 Успешно загружен фон: {filename}")

            # Сохраняем выбор в настройках
            save_background_preference(filename)
        else:
            print(f"⚠️ Фон {filename} не найден, пробуем скачать...")
            download_and_set_background(filename)

    except Exception as e:
        print(f"❌ Ошибка загрузки фона {filename}: {e}")
        load_default_background()


def download_and_set_background(filename):
    """Скачивает и устанавливает фон если его нет"""
    try:
        # Используем существующую систему загрузки ресурсов
        setup_environment()  # Перезагружаем ресурсы

        # Проверяем снова после загрузки
        bg_path = RESOURCE_DIR / filename
        if bg_path.exists():
            load_custom_background(filename)
        else:
            print(f"💥 Не удалось скачать {filename}, используем стандартный")
            load_default_background()
    except Exception as e:
        print(f"💥 Ошибка при скачивании фона: {e}")
        load_default_background()


def load_default_background():
    """Загружает стандартный фон"""
    try:
        global bag, img
        default_bg = RESOURCE_DIR / "logo.png"
        if default_bg.exists():
            bag = tk.PhotoImage(file=str(default_bg))
            img.configure(image=bag)
            print("🔧 Используем стандартный фон logo.png")
        else:
            print("💥 Стандартный фон также недоступен!")
    except Exception as e:
        print(f"💥 Критическая ошибка загрузки фона: {e}")


def save_background_preference(filename):
    """Сохраняет выбор фона для будущих запусков"""
    try:
        session = load_last_session() or {}
        session["background"] = filename
        session["screen_resolution"] = (
            f"{win.winfo_screenwidth()}x{win.winfo_screenheight()}"
        )

        with open(LAST_SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить настройки фона: {e}")


def show_background_menu():
    """Показывает меню выбора фона"""
    menu = tk.Menu(win, tearoff=0, bg="#2b2b2b", fg="white", font=("Comfortaa", 9))

    for name, file in backgrounds:
        menu.add_command(label=name, command=lambda f=file: load_custom_background(f))

    # Показываем меню под курсором
    menu.tk_popup(win.winfo_pointerx(), win.winfo_pointery())


def show_simple_background_selector():
    """Простой и надежный выбор фона через отдельное окно"""
    try:
        selector_window = tk.Toplevel(win)
        selector_window.title("Выбор фона для лаунчера")
        selector_window.geometry("400x500")
        selector_window.configure(bg="#2b2b2b")
        selector_window.resizable(False, False)
        selector_window.transient(win)
        selector_window.grab_set()

        # Центрируем окно
        selector_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (400 // 2)
        y = (win.winfo_screenheight() // 2) - (500 // 2)
        selector_window.geometry(f"400x500+{x}+{y}")

        main_frame = ttk.Frame(selector_window, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(
            main_frame,
            text="🎨 Выбор фона",
            font=("Comfortaa", 16, "bold"),
            foreground="white",
            background="#2b2b2b",
        ).pack(pady=(0, 20))

        # Описание
        ttk.Label(
            main_frame,
            text="Выберите фон для своего разрешения экрана:",
            font=("Comfortaa", 10),
            foreground="#cccccc",
            background="#2b2b2b",
        ).pack(pady=(0, 15))

        # Создаем кнопки выбора
        for name, filename in backgrounds:
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x", pady=4)

            btn = ModernButton(
                btn_frame,
                text=name,
                width=320,
                height=36,
                gradient=("#4A5568", "#2D3748"),
                command=lambda f=filename: apply_background_and_close(
                    f, selector_window
                ),
                font_size=10,
                corner_radius=8,
            )
            btn.pack(pady=2)

        # Разделитель
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.pack(fill="x", pady=15)

        # Кнопка автоопределения
        auto_btn = ModernButton(
            main_frame,
            text="🔧 Автоопределение (рекомендуется)",
            width=320,
            height=36,
            gradient=("#667eea", "#764ba2"),
            command=lambda: (setup_adaptive_background(), selector_window.destroy()),
            font_size=10,
            corner_radius=8,
        )
        auto_btn.pack(pady=5)

        # Кнопка закрытия
        close_btn = ModernButton(
            main_frame,
            text="❌ Закрыть",
            width=200,
            height=32,
            gradient=("#718096", "#4A5568"),
            command=selector_window.destroy,
            font_size=10,
            corner_radius=6,
        )
        close_btn.pack(pady=10)

    except Exception as e:
        print(f"❌ Ошибка открытия селектора фонов: {e}")
        messagebox.showerror("Ошибка", "Не удалось открыть выбор фона")


def apply_background_and_close(filename, window):
    """Применяет фон и закрывает окно"""
    load_custom_background(filename)
    window.destroy()
    messagebox.showinfo("Успех", f"Фон {filename} применен!")


# Функция для открытия настроек
def open_settings():
    settings_window = tk.Toplevel(win)
    set_window_icon(settings_window)
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
        validatecommand=(
            settings_window.register(lambda p: p.isdigit() or p == ""),
            "%P",
        ),
    )
    memory_spinbox.grid(row=0, column=1)

    def save_settings():
        if not memory_var.get().isdigit():
            messagebox.showerror("Ошибка", "Введите число!")
            return

        memory_gb = int(memory_var.get())
        new_memory = f"-Xmx{memory_gb}G"
        CONFIG["jvm_memory"] = new_memory
        messagebox.showinfo("Сохранено", f"Память установлена: {memory_gb} ГБ")
        settings_window.destroy()

    ttk.Button(settings_window, text="Сохранить", command=save_settings).grid(
        row=1, columnspan=2
    )


# Добавление в меню
settings_menu.add_command(label="Настройки", command=open_settings)
settings_menu.add_separator()


# Функция для проверки и загрузки модов


# Функция для проверки установки Minecraft и Fabric
def check_minecraft_and_fabric_installed():
    minecraft_versions_dir = os.path.join(CONFIG["minecraft_dir"], "versions")
    fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
    fabric_version_dir = os.path.join(minecraft_versions_dir, fabric_version)
    if os.path.exists(fabric_version_dir):
        print("Fabric уже установлен.")
        return True
    else:
        print("Fabric не установлен.")
        return False


def is_modloader_needed(selected_version):
    """Проверяет нужен ли модлоадер (Fabric/NeoForge)"""


    if selected_version in fabric_supported_versions:
        return "fabric"
    elif selected_version in neoforge_supported_versions:
        return "neoforge"
    else:
        return None


def install_minecraft_version(version, progress_callback=None):
    """
    Устанавливает указанную версию Minecraft, если она отсутствует.
    """
    versions_dir = os.path.join(CONFIG["minecraft_dir"], "versions")
    version_dir = os.path.join(versions_dir, version)

    if not os.path.exists(version_dir):
        print(f"Версия {version} не найдена. Начинаем установку...")
        try:
            # ИСПРАВЛЕНО: правильное имя параметра 'version' вместо 'versionid'
            minecraft_launcher_lib.install.install_minecraft_version(
                version=version,  # ПРАВИЛЬНОЕ имя параметра
                minecraft_directory=CONFIG["minecraft_dir"],
                callback=progress_callback
            )
            print(f"✅ Версия {version} успешно установлена")
            return True
        except Exception as e:
            print(f"❌ Ошибка установки версии {version}: {e}")
            return False
    else:
        print(f"Версия {version} уже установлена.")
        return True


def clear_auth_cache():
    """Очищает кэш аутентификации Minecraft"""
    minecraft_dir = CONFIG["minecraft_dir"]
    cache_files = [
        os.path.join(minecraft_dir, "usercache.json"),
        os.path.join(minecraft_dir, "launcher_profiles.json"),
        os.path.join(minecraft_dir, "launcher_accounts.json"),
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
        "Сервак запущен, а ты - опущен",
    ]
    return random.choice(messages)


def check_and_download_missing_mods():
    """Проверяет и загружает отсутствующие моды перед запуском"""
    minecraft_dir = CONFIG["minecraft_dir"]
    mods_dir = os.path.join(minecraft_dir, "mods")

    # Проверяем какие моды отсутствуют
    missing_mods = []
    for mod in CONFIG["mods"]:
        mod_path = os.path.join(mods_dir, mod["file"])
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


def validate_username(username):
    """Проверяет корректность имени пользователя"""
    if not username or username == "Введите никнейм":
        return False, "Имя пользователя не может быть пустым"

    if len(username) < 3 or len(username) > 16:
        return False, "Длина имени должна быть от 3 до 16 символов"

    # Проверка разрешенных символов
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Имя может содержать только буквы, цифры и _"

    return True, "OK"
# ЗАГРУЗКА МОДОВ ТОЛЬКО ДЛЯ YamalPixel

def set_launch_state(launching=False):
    """Управляет состоянием кнопок во время запуска"""
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME

    LAUNCH_IN_PROGRESS = launching
    if launching:
        LAUNCH_START_TIME = time.time()
        # Блокируем только основные кнопки
        launch_btn.config(state="disabled")  # Блокируем кастомную кнопку

        # Для кастомных кнопок меняем текст через их собственные методы

    else:
        # Разблокируем кнопки
        launch_btn.config(state="normal")  # Разблокируем кастомную кнопку


def runn():
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME
    import uuid
    import random

    username_text = username.get().strip()
    is_valid, error_msg = validate_username(username_text)

    if not is_valid:
        messagebox.showerror("Ошибка", f"❌ Некорректное имя пользователя!\n\n{error_msg}")
        return
    try:
        if not username.get().strip() or username.get().strip() == "Введите никнейм":
            messagebox.showerror("Ошибка", "❌ Введите имя пользователя!")
            return

        selected_version = version_selector.get()

        def start_game_launch_wrapper():
            """Обертка для запуска игры после подготовки"""
            # Для версий, отличных от YamalPixel, устанавливаем Minecraft
            if selected_version != "YamalPixel":
                install_required_components(selected_version)

            # Запускаем основной процесс (включая установку модлоадеров)
            start_game_launch()

        # Если выбрана версия YamalPixel - сначала проверяем моды
        if selected_version == "YamalPixel":
            def on_mods_check_complete():
                """Запускается после завершения проверки модов"""
                start_game_launch_wrapper()

            checker1_with_callback(on_mods_check_complete)
        else:
            # Для других версий сразу запускаем подготовку и запуск
            start_game_launch_wrapper()

    except Exception as e:
        set_launch_state(False)
        messagebox.showerror(
            "Критическая ошибка", f"❌ Не удалось подготовить запуск:\n\n{str(e)}"
        )


def install_required_components(version_name):
    """Упрощенная функция установки компонентов - только для версий, отличных от YamalPixel"""
    try:
        # Создаем окно прогресса
        progress_window = tk.Toplevel(win)
        set_window_icon(progress_window)
        progress_window.title("Установка компонентов")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(win)
        progress_window.grab_set()

        # Центрируем окно
        progress_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (400 // 2)
        y = (win.winfo_screenheight() // 2) - (150 // 2)
        progress_window.geometry(f"400x150+{x}+{y}")

        progress_label = ttk.Label(progress_window, text="Подготовка компонентов...")
        progress_label.pack(pady=10)

        progress = ttk.Progressbar(
            progress_window, orient="horizontal", length=300, mode="indeterminate"
        )
        progress.pack(pady=10)
        progress.start()

        status_label = ttk.Label(progress_window, text="")
        status_label.pack()

        def install_thread():
            try:
                # Для версий, отличных от YamalPixel, просто устанавливаем Minecraft
                if version_name != "YamalPixel":
                    # Получаем версию Minecraft из названия
                    minecraft_version = get_minecraft_version(version_name)

                    win.after(0, lambda: status_label.config(text="Установка Minecraft...")) #noqa

                    # Устанавливаем чистый Minecraft
                    success = safe_install_minecraft_version(
                        version=minecraft_version,
                        minecraft_directory=CONFIG["minecraft_dir"]
                    )

                    if not success:
                        raise Exception(f"Не удалось установить Minecraft {minecraft_version}")

                    win.after(0, lambda: status_label.config(text="Minecraft установлен!"))

                # Модлоадеры (Fabric/NeoForge) будут установлены позже в execute_launch_process
                win.after(0, progress_window.destroy)

            except Exception as e:
                error_message = str(e)  # Сохраняем сообщение до вызова win.after
                win.after(0, lambda: progress_window.destroy())
                win.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось установить компоненты: {error_message}"))

        threading.Thread(target=install_thread, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось начать установку компонентов: {str(e)}")


def checker1_with_callback(completion_callback=None):
    """Версия checker1 с колбэком для последовательного выполнения"""
    if version_selector.get() != "YamalPixel":
        print("Выбрана версия, отличная от YamalPixel. Загрузка модов пропущена.")
        if completion_callback:
            completion_callback()
        return

    # Создаем окно прогресса
    progress_window = tk.Toplevel(win)
    set_window_icon(progress_window)
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
    main_frame.pack(fill="both", expand=True)

    # Заголовок
    title_label = ttk.Label(
        main_frame, text="📥 Загрузка модов", font=("Comfortaa", 14, "bold")
    )
    title_label.pack(pady=(0, 15))

    # Общий прогресс-бар
    total_progress_label = ttk.Label(main_frame, text="Общий прогресс: 0%")
    total_progress_label.pack()

    total_progress = ttk.Progressbar(
        main_frame, orient="horizontal", length=400, mode="determinate"
    )
    total_progress.pack(pady=5)

    # Прогресс текущего мода
    current_mod_label = ttk.Label(main_frame, text="Подготовка к загрузке...")
    current_mod_label.pack()

    current_progress = ttk.Progressbar(
        main_frame, orient="horizontal", length=400, mode="determinate"
    )
    current_progress.pack(pady=5)

    # Счетчик
    counter_label = ttk.Label(main_frame, text="Мод 0/0")
    counter_label.pack()

    # Статус
    status_label = ttk.Label(
        main_frame, text="Инициализация...", font=("Comfortaa", 9), foreground="blue"
    )
    status_label.pack(pady=10)

    def update_progress(current, total, mod_name="", file_progress=0, file_total=1):
        """Обновляет прогресс в UI - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ РЕКУРСИИ"""
        try:
            # Общий прогресс
            total_percent = (current * 100) // total if total > 0 else 0
            total_progress["value"] = total_percent
            total_progress_label.config(text=f"Общий прогресс: {total_percent}%")

            # Прогресс текущего файла
            file_percent = (file_progress * 100) // file_total if file_total > 0 else 0
            current_progress["value"] = file_percent

            # Тексты
            current_mod_label.config(text=f"Текущий мод: {mod_name}")
            counter_label.config(text=f"Мод {current}/{total}")

            if file_total > 0:
                status_text = f"Загрузка: {file_progress / (1024 * 1024):.1f}MB / {file_total / (1024 * 1024):.1f}MB"
            else:
                status_text = "Подготовка..."

            status_label.config(text=status_text)

            progress_window.update()
        except Exception as e:
            print(f"Ошибка обновления прогресса: {e}")

    def download_thread():
        """Поток загрузки модов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        nonlocal progress_window

        try:
            mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
            os.makedirs(mods_dir, exist_ok=True)
            base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"

            # Определяем какие моды нужно скачать
            mods_to_download = []
            for mod in CONFIG["mods"]:
                mod_path = os.path.join(mods_dir, mod["file"])
                if not os.path.exists(mod_path):
                    mods_to_download.append(mod)

            total_mods = len(mods_to_download)
            success_count = 0

            if total_mods == 0:
                win.after(
                    0, lambda: show_completion_result(progress_window, 0, 0, True, completion_callback)
                ) # noqa
                return

            win.after(0, lambda: update_progress(0, total_mods, "Подготовка...")) # noqa

            for i, mod in enumerate(mods_to_download):
                try:
                    mod_path = os.path.join(mods_dir, mod["file"])

                    win.after(
                        0,
                        lambda idx=i, m=mod: update_progress(idx, total_mods, m["file"], 0, 1),) # noqa

                    print(f"⬇️  Загружаем мод ({i + 1}/{total_mods}): {mod['file']}")

                    # Получаем ссылку для скачивания
                    params = {"public_key": mod["url"]}
                    response = requests.get(base_url, params=params, timeout=30)
                    response.raise_for_status()
                    download_url = response.json().get("href")

                    if not download_url:
                        print(f"❌ Не удалось получить ссылку для {mod['file']}")
                        continue

                    # Загружаем файл с прогрессом
                    with requests.get(
                            download_url, stream=True, timeout=60
                    ) as dl_response:
                        dl_response.raise_for_status()

                        total_size = int(dl_response.headers.get("content-length", 0))
                        downloaded_size = 0

                        with open(mod_path, "wb") as f:
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)

                                    # Обновляем прогресс текущего файла - БЕЗ РЕКУРСИИ
                                    if downloaded_size % (1024 * 1024) == 0:  # Обновляем каждые 1MB
                                        win.after(
                                            0,
                                            lambda ds=downloaded_size, ts=total_size: update_progress(
                                                i, total_mods, mod["file"], ds, ts
                                            ),
                                        )

                        # Финальное обновление прогресса
                        win.after(
                            0,
                            lambda: update_progress(
                                i, total_mods, mod["file"], total_size, total_size
                            ),
                        )

                        print(f"✅ Мод {mod['file']} успешно установлен")
                        success_count += 1

                except Exception as e:
                    print(f"❌ Ошибка загрузки мода {mod['file']}: {str(e)}")
                    win.after(
                        0, lambda: status_label.config(text=f"Ошибка: {str(e)[:50]}...")
                    )

            # Распаковываем ZIP-файлы
            win.after(0, lambda: status_label.config(text="Распаковка архивов..."))
            zip_count = 0
            for mod in mods_to_download:
                if mod["file"].endswith(".zip"):
                    zip_path = os.path.join(mods_dir, mod["file"])
                    if os.path.exists(zip_path):
                        try:
                            with zipfile.ZipFile(zip_path, "r") as zip_file:
                                zip_file.extractall(path=mods_dir)
                            print(
                                f"📦 Содержимое архива {mod['file']} успешно извлечено"
                            )
                            zip_count += 1
                        except Exception as e:
                            print(
                                f"❌ Ошибка распаковки архива {mod['file']}: {str(e)}"
                            )

            # ПОСЛЕ ПОЛНОЙ ЗАГРУЗКИ ВСЕХ МОДОВ - закрываем окно
            win.after(
                0,
                lambda: show_completion_result(
                    progress_window, success_count, total_mods, False, completion_callback
                ),
            )

        except Exception as e:
            print(f"💥 Критическая ошибка в потоке загрузки: {e}")
            win.after(0, lambda: show_completion_result(progress_window, 0, 0, True, completion_callback))

    def show_completion_result(window, success, total, all_exist, callback=None):
        """Показывает результат загрузки и ЗАКРЫВАЕТ окно"""
        try:
            window.destroy()
        except:
            pass

        if all_exist:
            messagebox.showinfo("Загрузка модов", "✅ Все моды уже установлены!")
            # Вызываем колбэк для запуска игры
            if callback:
                win.after(100, callback)
        elif success == total:
            messagebox.showinfo(
                "Загрузка модов",
                f"🎉 Все моды успешно загружены!\n\n"
                f"• Загружено: {success} модов\n"
                f"Запускайте игру!",
            )
            # Вызываем колбэк для запуска игры
            if callback:
                win.after(100, callback)
        elif success > 0:
            result = messagebox.askyesno(
                "Загрузка модов",
                f"📊 Загрузка завершена с ошибками\n\n"
                f"• Успешно: {success} модов\n"
                f"• Всего: {total} модов\n"
                f"• Не загружено: {total - success} модов\n\n"
                f"Запустить игру с доступными модами?",
            )
            if result and callback:
                # Вызываем колбэк для запуска игры
                win.after(100, callback)
        else:
            messagebox.showerror(
                "Ошибка загрузки",
                "❌ Не удалось загрузить ни одного мода!\n\n"
                "Возможные причины:\n"
                "• Проблемы с интернет-соединением\n"
                "• Яндекс.Диск блокирует загрузки\n"
                "• Антивирус блокирует загрузки",
            )
            # Даже при ошибке вызываем колбэк, если пользователь хочет продолжить
            if callback:
                result = messagebox.askyesno(
                    "Продолжить",
                    "Запустить игру без модов?"
                )
                if result:
                    win.after(100, callback)

    # Запускаем загрузку в отдельном потоке
    threading.Thread(target=download_thread, daemon=True).start()


def start_game_launch():
    """Основной процесс запуска игры (вынесен из runn)"""
    global LAUNCH_IN_PROGRESS, LAUNCH_START_TIME, progress_window, status_label, details_label, timer_label, log_label

    # НЕМЕДЛЕННО блокируем интерфейс
    set_launch_state(True)

    # Создаем окно прогресса запуска
    progress_window = tk.Toplevel(win)
    set_window_icon(progress_window)
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
    main_frame.pack(fill="both", expand=True)

    # Заголовок
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 20))
    ttk.Label(
        header_frame, text="🚀 Запуск YamalPixel", font=("Comfortaa", 16, "bold")
    ).pack()
    ttk.Label(
        header_frame,
        text="Подготовка к запуску игры...",
        font=("Comfortaa", 11),
        foreground="gray",
    ).pack(pady=(5, 0))

    # Прогресс-бар
    progress_frame = ttk.Frame(main_frame)
    progress_frame.pack(fill="x", pady=10)
    progress_bar = ttk.Progressbar(
        progress_frame, orient="horizontal", length=400, mode="indeterminate"
    )
    progress_bar.pack(pady=5)
    progress_bar.start()

    # Статус запуска
    status_label = ttk.Label(
        progress_frame, text="Инициализация запуска...", font=("Comfortaa", 10)
    )
    status_label.pack()

    # Таймер
    timer_frame = ttk.Frame(main_frame)
    timer_frame.pack(fill="x", pady=10)
    timer_label = ttk.Label(
        timer_frame, text="⏱️ Прошло времени: 0 сек", font=("Comfortaa", 9)
    )
    timer_label.pack()

    # Детали запуска
    details_label = ttk.Label(
        main_frame, text="", font=("Comfortaa", 8), foreground="blue"
    )
    details_label.pack()

    # Лог запуска
    log_frame = ttk.Frame(main_frame)
    log_frame.pack(fill="x", pady=5)
    log_label = ttk.Label(
        log_frame, text="", font=("Consolas", 7), foreground="green"
    )
    log_label.pack()

    # Флаг отмены
    cancelled = False

    def cancel_launch():
        nonlocal cancelled
        cancelled = True
        progress_window.destroy()
        set_launch_state(False)
        messagebox.showinfo("Отменено", "✅ Запуск игры отменен")

    # Кнопка отмены
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=20)
    cancel_btn = ttk.Button(button_frame, text="❌ Отменить запуск", command=cancel_launch)
    cancel_btn.pack()

    # Локальные функции для обновления UI
    def update_timer():
        """Обновляет таймер с минутами и секундами"""
        if LAUNCH_IN_PROGRESS and progress_window.winfo_exists():
            elapsed = int(time.time() - LAUNCH_START_TIME)
            minutes = elapsed // 60
            seconds = elapsed % 60

            if minutes > 0:
                timer_label.config(text=f"⏱️ Прошло времени: {minutes} мин {seconds} сек")
            else:
                timer_label.config(text=f"⏱️ Прошло времени: {seconds} сек")

            progress_window.after(1000, update_timer)

    # Запускаем обновление таймера
    update_timer()

    def update_ui_status(text="", detail=""):
        """Обновляет статус в UI"""
        try:
            if progress_window.winfo_exists():
                if text:
                    status_label.config(text=text)
                if detail:
                    details_label.config(text=detail)
        except Exception as e:
            print(f"[UI STATUS ERROR] {e}")

    def update_ui_log(message):
        """Обновляет лог в UI"""
        try:
            if progress_window.winfo_exists():
                log_label.config(text=message)
        except Exception as e:
            print(f"[UI LOG ERROR] {e}")

    # ГЛАВНЫЙ ПРОЦЕСС ЗАПУСКА
    def execute_launch_process():
        nonlocal cancelled  # Добавляем, чтобы можно было читать флаг

        try:
            selected_version = version_selector.get()
            update_ui_log(f"🔧 Выбрана версия: {selected_version}")

            #if selected_version == "Minecraft 1.21.1 + NeoForge":
                #messagebox.showwarning(
                    #"Проблемная версия",
                    #"Версия временно недоступна из-за проблем с Neoforge.\n"
                    #"Пожалуйста, выберите другую версию Minecraft."
                #)
                #return

            # Шаг 0: Установка компонентов (кроме YamalPixel)
            if selected_version != "YamalPixel":
                update_ui_status("Установка компонентов", "Подготавливаем версию...")
                update_ui_log(f"🔧 Устанавливаем компоненты для: {selected_version}")

                if cancelled:
                    return

                install_required_components_sync(selected_version)
                update_ui_log("✅ Компоненты установлены")

            if cancelled:
                return

            # Шаг 1: Подготовка игры
            update_ui_status("Подготовка игры", "Очистка и проверка...")
            cleanup_before_launch()
            clear_auth_cache()
            update_ui_log("✅ Файлы подготовлены")

            if cancelled:
                return

            # Шаг 2: Проверка и установка модлоадеров
            loader_type = is_modloader_needed(selected_version)
            if loader_type:
                minecraft_version = get_minecraft_version(selected_version)
                update_ui_status(f"Проверка {loader_type.capitalize()}", "Проверяем установку...")

                if cancelled:
                    return

                def check_modloader_installed():
                    try:
                        versions_dir = os.path.join(CONFIG["minecraft_dir"], "versions")

                        if loader_type == "fabric":
                            fabric_loader = "0.17.2"
                            fabric_version = f"fabric-loader-{fabric_loader}-{minecraft_version}"
                            return os.path.exists(os.path.join(versions_dir, fabric_version))

                        elif loader_type == "neoforge":
                            neoforge_versions = minecraft_launcher_lib.neoforge.get_versions(minecraft_version)
                            if neoforge_versions:
                                latest = neoforge_versions[0]
                                version_dir = os.path.join(versions_dir, f"neoforge-{latest}")
                                return os.path.exists(version_dir)
                            return False
                    except:
                        return False

                if not check_modloader_installed():
                    update_ui_log(f"🔧 Устанавливаем {loader_type.capitalize()}...")
                    try:
                        if loader_type == "fabric":
                            minecraft_launcher_lib.fabric.install_fabric(
                                minecraft_version=minecraft_version,
                                loader_version="0.17.2",
                                minecraft_directory=CONFIG["minecraft_dir"],
                            )
                            update_ui_log(f"✅ Fabric установлен для {minecraft_version}")
                        elif loader_type == "neoforge":
                            neoforge_versions = minecraft_launcher_lib.neoforge.get_versions(minecraft_version)
                            if not neoforge_versions:
                                raise Exception(f"Не найдены версии NeoForge для {minecraft_version}")
                            latest = neoforge_versions[0]
                            minecraft_launcher_lib.neoforge.install(
                                minecraft_version=minecraft_version,
                                loader_version=latest,
                                minecraft_directory=CONFIG["minecraft_dir"],
                            )
                            update_ui_log(f"✅ NeoForge {latest} установлен")
                    except Exception as e:
                        update_ui_log(f"❌ Ошибка установки {loader_type.capitalize()}: {e}")
                        raise

                if cancelled:
                    return

            # Шаг 3: Запуск игры
            update_ui_status("Запуск Minecraft", "Формируем команду...")

            import uuid
            import hashlib

            # Генерируем UUID на основе имени пользователя (стандартный метод для оффлайн-режима)
            username_text = username.get().strip()
            namespace = uuid.UUID('6ba7b811-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
            offline_uuid = str(uuid.uuid5(namespace, "OfflinePlayer:" + username_text))

            selected_memory = CONFIG.get("jvm_memory", "4G").replace("-Xmx", "")
            jvm_args = [
                f"-Xmx{selected_memory}",
                f"-Xms{selected_memory}",
                "-XX:+UseG1GC",
                "-Duser.language=ru",
                "-Duser.country=RU",
            ]

            # ИСПРАВЛЕННЫЕ ОПЦИИ ЗАПУСКА
            options = {
                "username": username_text,
                "uuid": offline_uuid,  # Важно: передаем сгенерированный UUID
                "token": "",
                "jvmArguments": jvm_args,
                "gameDirectory": CONFIG["minecraft_dir"],
                "gameLocale": "ru_RU"
            }
            if not options["username"] or options["username"] == "Введите никнейм":
                raise Exception("Введите корректное имя пользователя!")
            # Определяем версию для запуска
            if loader_type == "fabric":
                mc_ver = get_minecraft_version_for_fabric(selected_version)
                launch_version = f"fabric-loader-0.17.2-{mc_ver}"
            elif loader_type == "neoforge":
                mc_ver = get_minecraft_version(selected_version)
                neoforge_versions = minecraft_launcher_lib.neoforge.get_versions(mc_ver)
                if neoforge_versions:
                    latest = neoforge_versions[0]
                    launch_version = f"neoforge-{latest}"
                else:
                    raise Exception(f"Не найдено версий NeoForge для {mc_ver}")
            else:
                launch_version = get_minecraft_version(selected_version)

            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=launch_version,
                minecraft_directory=CONFIG["minecraft_dir"],
                options=options,
            )
            update_ui_log(f"⚡ Запускаем: {launch_version}")

            if cancelled:
                return

            process = launch_minecraft_process(command)
            if not process:
                raise Exception("Не удалось создать процесс")

            update_ui_status("Игра запущена", "Minecraft загружается...")
            update_ui_log("✅ Процесс запущен")

            time.sleep(3)
            if is_minecraft_process_running(process):
                win.after(2000, lambda: progress_window.destroy() if progress_window.winfo_exists() else None)
                win.after(
                    100,
                    lambda: messagebox.showinfo(
                        "Успешный запуск",
                        f"✅ Игра успешно запущена!\n\n• Игрок: {username.get()}\n• Версия: {selected_version}\n• Память: {selected_memory}"
                    ),
                )
                threading.Thread(target=monitor_game_process, args=(process,), daemon=True).start()
            else:
                raise Exception("Процесс Minecraft завершился сразу")

        except Exception as exc:
            error_msg = str(exc)
            print(f"[LAUNCH ERROR] {error_msg}")
            if progress_window.winfo_exists():
                progress_window.destroy()
            set_launch_state(False)
            win.after(0, lambda e=exc: messagebox.showerror("Ошибка", f"❌ Не удалось запустить игру:\n\n{e}"))

    # Запускаем основной процесс в потоке
    threading.Thread(target=execute_launch_process, daemon=True).start()


def update_system_certificates():
    """Пытается обновить системные сертификаты (для Windows)"""
    if os.name != 'nt':
        return False

    try:
        # Запускаем обновление сертификатов через PowerShell
        import subprocess
        result = subprocess.run([
            'powershell', '-Command',
            'Update-ScriptExecutionPolicy -Scope CurrentUser -Force;' +
            'Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force;' +
            'Install-Module -Name PSWindowsUpdate -Force;' +
            'Get-WUInstall -AcceptAll -AutoReboot'
        ], capture_output=True, text=True, timeout=300)

        return "успех" in result.stdout.lower()
    except:
        return False

def repair_version_file():
    """Исправление поврежденного файла версии Minecraft"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        versions_dir = os.path.join(minecraft_dir, "versions")
        problem_version = "1.18.2"

        # Путь к проблемному файлу
        version_json_path = os.path.join(versions_dir, problem_version, f"{problem_version}.json")

        print(f"🔧 Исправляем файл версии: {version_json_path}")

        # Проверяем существует ли файл
        if not os.path.exists(version_json_path):
            print(f"❌ Файл {version_json_path} не существует")
            return False

        # Создаем бэкап поврежденного файла
        backup_path = version_json_path + ".backup"
        shutil.copy2(version_json_path, backup_path)
        print(f"📂 Создан бэкап: {backup_path}")

        # Переустанавливаем версию Minecraft
        print("🔄 Переустанавливаем версию Minecraft...")
        minecraft_launcher_lib.install.install_minecraft_version(
            versionid=problem_version,
            minecraft_directory=minecraft_dir
        )

        print("✅ Файл версии успешно исправлен!")

        # Удаляем бэкап если все успешно
        if os.path.exists(backup_path):
            os.remove(backup_path)

        return True

    except Exception as e:
        print(f"❌ Ошибка при исправлении файла версии: {e}")

        # Восстанавливаем из бэкапа при ошибке
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, version_json_path)
            print("🔄 Восстановлен файл из бэкапа")

        return False


def auto_fix_version_files():
    """Автоматическое исправление всех поврежденных файлов версий"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        versions_dir = os.path.join(minecraft_dir, "versions")

        if not os.path.exists(versions_dir):
            print("❌ Папка versions не существует")
            return False

        fixed_count = 0
        problematic_versions = []

        # Проверяем все версии
        for version_folder in os.listdir(versions_dir):
            version_path = os.path.join(versions_dir, version_folder)
            json_path = os.path.join(version_path, f"{version_folder}.json")

            if os.path.exists(json_path):
                try:
                    # Пробуем загрузить JSON для проверки целостности
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except Exception as e:
                    print(f"❌ Обнаружен поврежденный файл: {version_folder}")
                    problematic_versions.append(version_folder)

        # Исправляем проблемные версии
        for version in problematic_versions:
            if repair_single_version(version):
                fixed_count += 1

        if fixed_count > 0:
            messagebox.showinfo(
                "Исправление завершено",
                f"✅ Успешно исправлено {fixed_count} версий Minecraft!"
            )
        else:
            messagebox.showinfo(
                "Проверка завершена",
                "✅ Все файлы версий в порядке, проблем не обнаружено."
            )

        return True

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось проверить версии: {e}")
        return False


def repair_single_version(version_name):
    """Исправляет одну конкретную версию"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]

        print(f"🔄 Исправляем версию: {version_name}")

        # Переустанавливаем версию
        minecraft_launcher_lib.install.install_minecraft_version(
            versionid=version_name,
            minecraft_directory=minecraft_dir
        )

        print(f"✅ Версия {version_name} успешно исправлена")
        return True

    except Exception as e:
        print(f"❌ Ошибка исправления версии {version_name}: {e}")
        return False

def install_required_components_sync(version_name):

    """Синхронная установка компонентов (без отдельного окна)"""

    try:
        if version_name in version_configs:
            config = version_configs[version_name]

            # ЗАЩИТА: проверяем количество значений
            if len(config) == 2:
                # Если 2 значения, добавляем третье (None)
                minecraft_version, loader_type = config
                loader_version = None
            elif len(config) == 3:
                # Если 3 значения, распаковываем нормально
                minecraft_version, loader_type, loader_version = config
            else:
                raise ValueError(f"Неверная конфигурация для {version_name}")
    except Exception as e:
        print(f"❌ Ошибка в install_required_components_sync: {e}")
    if version_name in version_configs:
        config = version_configs[version_name]
        # Безопасная распаковка
        if len(config) == 3:
            minecraft_version, loader_type, loader_version = config
        else:
            minecraft_version, loader_type = config
            loader_version = None

        # Устанавливаем Minecraft версию БЕЗОПАСНО
        print(f"Устанавливаем Minecraft {minecraft_version} для {version_name}")

        success = safe_install_minecraft_version(
            version=minecraft_version,
            minecraft_directory=CONFIG["minecraft_dir"]
        )

        if not success:
            raise Exception(f"Не удалось установить Minecraft {minecraft_version}")

        # Устанавливаем модлоадер если нужно
        if loader_type == "fabric" and loader_version:
            print(f"Устанавливаем Fabric {loader_version} для {minecraft_version}")
            minecraft_launcher_lib.fabric.install_fabric(
                minecraft_version=minecraft_version,
                loader_version=loader_version,
                minecraft_directory=CONFIG["minecraft_dir"]
            )
        elif loader_type == "neoforge":
            print(f"Устанавливаем NeoForge для {minecraft_version}")
            install_neoforge_sync(minecraft_version, CONFIG["minecraft_dir"])



def install_neoforge_sync(minecraft_version, minecraft_directory):
    """Синхронная установка NeoForge - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        print(f"🔧 Устанавливаем NeoForge для {minecraft_version}...")

        # Получаем NeoForge лоадер через правильный API
        neoforge_loader = get_mod_loader("neoforge")

        # Получаем доступные версии NeoForge
        neoforge_versions = neoforge_loader.get_loader_versions(
            minecraft_version,
            stable_only=True
        )

        if not neoforge_versions:
            raise Exception(f"Не найдены версии NeoForge для {minecraft_version}")

        # Берем последнюю стабильную версию
        latest_neoforge = neoforge_versions[0]
        print(f"📦 Используем NeoForge {latest_neoforge}")

        # Устанавливаем NeoForge
        neoforge_loader.install(
            minecraft_version=minecraft_version,
            minecraft_directory=minecraft_directory,
            loader_version=latest_neoforge
        )

        print(f"✅ NeoForge успешно установлен!")
        return True

    except Exception as e:
        print(f"❌ Ошибка установки NeoForge: {e}")
        return False

def check_network_connectivity():
    """Проверяет доступность серверов Minecraft"""
    import urllib.request
    import ssl

    test_urls = [
        "https://libraries.minecraft.net",
        "https://launcher.mojang.com",
        "https://piston-meta.mojang.com"
    ]

    for url in test_urls:
        try:
            # Создаем контекст без проверки SSL для теста
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(url, timeout=10, context=context) as response:
                if response.status == 200:
                    print(f"✅ {url} доступен")
                else:
                    print(f"⚠️ {url} недоступен (статус: {response.status})")

        except Exception as e:
            print(f"❌ {url} недоступен: {e}")
            return False

    return True


def repair_minecraft_installation(version):
    """Восстанавливает установку Minecraft для проблемных версий"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        versions_dir = os.path.join(minecraft_dir, "versions")
        version_dir = os.path.join(versions_dir, version)

        # Удаляем проблемную версию
        if os.path.exists(version_dir):
            import shutil
            shutil.rmtree(version_dir)
            print(f"🗑️ Удалена проблемная версия: {version}")

        # Пробуем установить заново
        print(f"🔄 Переустанавливаем {version}...")
        return safe_install_minecraft_version(version, minecraft_dir)

    except Exception as e:
        print(f"❌ Не удалось восстановить {version}: {e}")
        return False



def get_minecraft_version_for_fabric(version_name):
    """Получает версию Minecraft для Fabric"""
    return get_minecraft_version(version_name)


def safe_install_minecraft_version(version, minecraft_directory, progress_callback=None):
    """Безопасная установка версии Minecraft с обработкой ошибок"""
    try:
        # Устанавливаем таймауты и повторные попытки
        import socket
        socket.setdefaulttimeout(30)

        # Пробуем установить с обработкой SSL ошибок
        minecraft_launcher_lib.install.install_minecraft_version(
            version=version,
            minecraft_directory=minecraft_directory,
            callback=progress_callback
        )
        return True

    except Exception as e:
        print(f"❌ Ошибка установки Minecraft {version}: {e}")

        # Пробуем альтернативный метод для проблемных версий
        if "SSL" in str(e) or "certificate" in str(e).lower():
            return install_with_ssl_bypass(version, minecraft_directory)

        return False


def install_with_ssl_bypass(version, minecraft_directory):
    """Установка с обходом SSL проверок (только для проблемных версий)"""
    try:
        print(f"🔄 Пробуем альтернативный метод установки {version}...")

        # Используем настройки без строгой SSL проверки
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl._create_default_https_context = ssl._create_unverified_context
        # Здесь должен быть код для установки с кастомным SSL контекстом
        # К сожалению, minecraft-launcher-lib не поддерживает это напрямую

        print(f"⚠️ SSL ошибка для версии {version}. Требуется ручная установка.")
        return False

    except Exception as e:
        print(f"❌ Альтернативный метод также не сработал: {e}")
        return False


def safe_destroy_window(window):
    """Безопасно уничтожает окно с проверкой существования"""
    try:
        if window and window.winfo_exists():
            window.destroy()
    except Exception as e:
        print(f"Ошибка при закрытии окна: {e}")


def launch_minecraft_process(command, log_callback=None):
    """Запускает процесс Minecraft БЕЗ перехвата вывода"""
    try:
        if log_callback:
            log_callback("Запускаем Minecraft...")

        # ЗАПУСКАЕМ БЕЗ ПЕРЕХВАТА ВЫВОДА - это убирает белое окно
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,  # Игнорируем stdout
            stderr=subprocess.DEVNULL,  # Игнорируем stderr
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        if log_callback:
            log_callback("✅ Minecraft запущен в фоновом режиме")
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
        "Loading Minecraft",
        "Loading mods",
        "WARN",
        "ERROR",
        "INFO",
        "Shaders",
        "OpenGL",
        "Sound engine",
        "Setting user",
        "Failed to",
    ]

    # Пропускаем менее важные сообщения
    skip_patterns = [
        "FabricLoader",
        "SpongePowered",
        "Backend library",
        "Reloading ResourceManager",
        "Created:",
        "Successfully reloaded",
    ]

    # Проверяем, содержит ли строка важные паттерны
    if any(pattern in line for pattern in important_patterns):
        # Укорачиваем слишком длинные строки
        if len(line) > 100:
            line = line[:100] + "..."

        # Добавляем эмодзи для разных типов сообщений
        if "ERROR" in line or "Failed to" in line:
            return f"❌ {line}"
        elif "WARN" in line:
            return f"⚠️ {line}"
        elif "Loading Minecraft" in line:
            return f"🎮 {line}"
        elif "Loading mods" in line:
            return f"📦 {line}"
        elif "Setting user" in line:
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
        if process and process.poll() is None:
            return True

        # Дополнительная проверка через tasklist для Windows
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/fi", "imagename eq javaw.exe", "/fo", "csv"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return "javaw.exe" in result.stdout
        else:
            result = subprocess.run(
                ["pgrep", "-f", "minecraft"], capture_output=True, text=True
            )
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
    # Переменная для хранения ID таймера
    timer_id = None

    def update_timer():
        global timer_id
        if LAUNCH_IN_PROGRESS and progress_window.winfo_exists():
            elapsed = int(time.time() - LAUNCH_START_TIME)
            minutes = elapsed // 60
            seconds = elapsed % 60

            if minutes > 0:
                timer_label.config(text=f"⏱️ Прошло времени: {minutes} мин {seconds} сек")
            else:
                timer_label.config(text=f"⏱️ Прошло времени: {seconds} сек")

            # Сохраняем ID для возможной отмены
            timer_id = progress_window.after(1000, update_timer)
        else:
            # Останавливаем таймер если окно закрыто
            if timer_id:
                progress_window.after_cancel(timer_id)

    # Запускаем обновление таймера
    update_timer()


def format_minecraft_output(line):
    """Форматирует вывод Minecraft для отображения в лаунчере"""
    if not line:
        return None

    # Фильтруем только важные сообщения
    important_patterns = [
        "Loading Minecraft",
        "Loading mods",
        "WARN",
        "ERROR",
        "INFO",
        "Shaders",
        "OpenGL",
        "Sound engine",
        "Setting user",
        "Failed to",
    ]

    # Пропускаем менее важные сообщения
    skip_patterns = [
        "FabricLoader",
        "SpongePowered",
        "Backend library",
        "Reloading ResourceManager",
        "Created:",
        "Successfully reloaded",
    ]

    # Проверяем, содержит ли строка важные паттерны
    if any(pattern in line for pattern in important_patterns):
        # Укорачиваем слишком длинные строки
        if len(line) > 100:
            line = line[:100] + "..."

        # Добавляем эмодзи для разных типов сообщений
        if "ERROR" in line or "Failed to" in line:
            return f"❌ {line}"
        elif "WARN" in line:
            return f"⚠️ {line}"
        elif "Loading Minecraft" in line:
            return f"🎮 {line}"
        elif "Loading mods" in line:
            return f"📦 {line}"
        elif "Setting user" in line:
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
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/fi", "imagename eq javaw.exe", "/fo", "csv"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return "javaw.exe" in result.stdout
        else:
            result = subprocess.run(
                ["pgrep", "-f", "minecraft"], capture_output=True, text=True
            )
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
    corner_radius=20,
)
launch_btn.place(relx=0.5, rely=0.5, anchor="center")

# Запускаем анимацию
launch_btn.start_animation()



# Стили
style = ttk.Style()
style.configure("BW.TLabel", background="pink")
app = ttk.Style()
style.configure("Accent.TButton", background="#0078D7", foreground="white")
app.configure("TLabel", font=("Comfortaa", 12))
app.configure("TButton", font=("Comfortaa", 12))


# Функции для управления музыкой
def mscon():
    mixer.music.play()


def mscoff():
    mixer.music.stop()


enabled1 = tk.IntVar()



# Использование для музыки
enabled1 = tk.IntVar()
music_checkbox = ModernCheckbutton(
    win,
    text="🎵 Включить музыку",
    variable=enabled1,
    command=lambda: mscon() if enabled1.get() else mscoff(),
    width=200,  # можно настроить ширину
    height=32,  # и высоту
)
music_checkbox.place(relx=1.0, x=-8, y=50, anchor=tk.NE)

# И для полноэкранного режима
enabled = tk.IntVar()
fullscreen_checkbox = ModernCheckbutton(
    win,
    text="🖥️ Полный экран",
    variable=enabled,
    command=lambda: fullsc() if enabled.get() else outscrn(),
    width=200,
    height=32,
)
fullscreen_checkbox.place(relx=1.0, x=-8, y=90, anchor=tk.NE)


def create_close_button():
    """Создает и размещает кнопку закрытия ПОД чекбоксом музыки"""
    close_btn = ModernCloseButton(
        win,
        text="❌ ЗАКРЫТЬ",
        width=120,
        height=35,
        gradient=("#ff6b6b", "#ff4757"),
        glow_color="#ff4757",
        command=on_closing,
        font_size=11,
        corner_radius=10,
    )

    # Размещаем точно под чекбоксом музыки
    # x=20 (отступ слева), y=80 (отступ сверху - настрой под свой интерфейс)
    close_btn.pack(padx=6, pady=6, anchor=tk.NE)

    return close_btn

# Создаем кнопку при запуске
close_button = create_close_button()


# Добавьте в интерфейс где-нибудь внизу
status_frame = ttk.Frame(win, relief="sunken", padding=5)
status_frame.place(relx=0.5, rely=0.95, anchor="center")

status_label = ttk.Label(
    status_frame, text="✅ Готов к запуску", font=("Comfortaa", 9), foreground="green"
)
status_label.pack()


# Создание поля ввода
username = ModernEntry(
    win,
    placeholder="Введите никнейм",
    width=300,
    height=50,
    gradient=("#667eea", "#764ba2"),
    corner_radius=15,
)
username.place(relx=0.5, rely=0.44, anchor="c")

# Улучшенная функция показа онлайн игроков
def show_online_players():
    """Красивое отображение онлайн игроков"""
    try:
        # Создаем красивое окно с информацией
        online_window = tk.Toplevel(win)
        set_window_icon(online_window)
        online_window.title("🌐 Статус сервера")
        online_window.geometry("300x200")
        online_window.resizable(False, False)
        online_window.configure(bg="#2b2b2b")
        online_window.transient(win)
        online_window.grab_set()

        # Центрируем окно
        online_window.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (300 // 2)
        y = (win.winfo_screenheight() // 2) - (200 // 2)
        online_window.geometry(f"300x200+{x}+{y}")

        # Основной фрейм
        main_frame = ttk.Frame(online_window, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="🌐 Статус сервера",
            font=("Comfortaa", 16, "bold"),
            foreground="white",
            background="#2b2b2b",
        )
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
        status_label = ttk.Label(
            main_frame,
            text=status_text,
            font=("Comfortaa", 12, "bold"),
            foreground=status_color,
            background="#2b2b2b",
        )
        status_label.pack(pady=5)

        # Количество игроков
        players_label = ttk.Label(
            main_frame,
            text=players_text,
            font=("Comfortaa", 11),
            foreground="#cccccc",
            background="#2b2b2b",
        )
        players_label.pack(pady=5)

        # Пинг
        ping_label = ttk.Label(
            main_frame,  # ИСПРАВЛЕНО: main_frame вместо main_server
            text=f"📡 Пинг: {status.latency:.1f} мс",
            font=("Comfortaa", 10),
            foreground="#888888",
            background="#2b2b2b",
        )
        ping_label.pack(pady=5)

        # Версия
        version_label = ttk.Label(
            main_frame,
            text=f"⚙️ Версия: {status.version.name}",
            font=("Comfortaa", 9),
            foreground="#666666",
            background="#2b2b2b",
        )
        version_label.pack(pady=5)

        # Кнопка закрытия
        close_btn = ttk.Button(
            main_frame, text="Закрыть", command=online_window.destroy, width=15
        )
        close_btn.pack(pady=15)

    except Exception as e:
        # Красивое окно ошибки
        error_window = tk.Toplevel(win)
        error_window.title("❌ Ошибка")
        error_window.geometry("250x150")
        error_window.configure(bg="#2b2b2b")

        ttk.Label(
            error_window,
            text="❌ Ошибка подключения",
            font=("Comfortaa", 12, "bold"),
            foreground="#f44336",
            background="#2b2b2b",
        ).pack(pady=20)

        ttk.Label(
            error_window,
            text="Сервер недоступен",
            font=("Comfortaa", 10),
            foreground="#cccccc",
            background="#2b2b2b",
        ).pack(pady=5)

        ttk.Button(error_window, text="Закрыть", command=error_window.destroy).pack(
            pady=15
        )


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
    corner_radius=15,
)

# Размещаем кнопку
online_btn.place(relx=0.5, rely=0.61, anchor="c") # noqa

# Запускаем анимацию
online_btn.start_animation()

# Создаем красивый селектор версий
version_selector = ModernVersionSelector(
    win,
    width=320,
    height=48,
    gradient=("#667eea", "#764ba2"),
    corner_radius=20,
    versions_list=versions,
)
version_selector.place(relx=0.5, rely=0.4, anchor="c")  # noqa


# Функция выбора версии
def select_version(event):
    selected_version = version_selector.get()

    # Обновляем конфигурацию в зависимости от выбранной версии


    if selected_version in version_configs:
        config = version_configs[selected_version]
        CONFIG["minecraft_version"] = config[0]
        CONFIG["loader_type"] = config[1]
        CONFIG["loader_version"] = config[2]
        show_version_change_message(selected_version)


def show_version_change_message(version_name):
    """Показывает красивое сообщение об изменении версии"""
    message_window = tk.Toplevel(win)
    message_window.title("Версия изменена")
    message_window.geometry("300x150")
    message_window.resizable(False, False)
    message_window.configure(bg="#2b2b2b")
    message_window.transient(win)
    message_window.grab_set()

    # Центрируем окно
    message_window.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (300 // 2)
    y = (win.winfo_screenheight() // 2) - (150 // 2)
    message_window.geometry(f"300x150+{x}+{y}")

    # Содержимое окна
    main_frame = ttk.Frame(message_window, padding=20)
    main_frame.pack(fill="both", expand=True)

    # Иконка
    icon = "🎮" if "YamalPixel" in version_name else "⚙️"
    ttk.Label(main_frame, text=icon, font=("Comfortaa", 24), background="#2b2b2b").pack(
        pady=(0, 10)
    )

    # Текст
    ttk.Label(
        main_frame,
        text="Версия изменена",
        font=("Comfortaa", 14, "bold"),
        foreground="white",
        background="#2b2b2b",
    ).pack()

    ttk.Label(
        main_frame,
        text=version_name,
        font=("Comfortaa", 12),
        foreground="#4ECDC4",
        background="#2b2b2b",
    ).pack(pady=(5, 15))

    # Кнопка
    ttk.Button(main_frame, text="OK", command=message_window.destroy, width=10).pack()

    # Автоматическое закрытие через 2 секунды
    message_window.after(2000, message_window.destroy)  # noqa


# Вызываем функцию обновления статуса Discord после создания окна
win.after(300, update_discord_status)  # noqa





# Функция создания новой сборки с выбором модов
# === Глобальные переменные для сортировки ===
current_sort_col = "downloads"
current_sort_reverse = False


def create_new_collection():
    """Создаёт окно для создания новой сборки модов"""
    global current_sort_col, current_sort_reverse
    collection_window = tk.Toplevel(win)
    collection_window.title("Создать сборку")
    collection_window.geometry("900x1080")
    collection_window.transient(win)
    collection_window.grab_set()

    main_frame = ttk.Frame(collection_window, padding=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame, text="📦 Новая сборка модов", font=("Comfortaa", 16, "bold")
    ).pack(pady=(0, 20))

    # === Основные настройки ===
    settings_frame = ttk.Frame(main_frame)
    settings_frame.pack(fill="x", pady=(0, 20))

    ttk.Label(settings_frame, text="Название:").pack(anchor="w")
    name_var = tk.StringVar()
    ttk.Entry(settings_frame, textvariable=name_var, width=50).pack(
        fill="x", pady=(0, 10)
    )

    meta_frame = ttk.Frame(settings_frame)
    meta_frame.pack(fill="x")

    ttk.Label(meta_frame, text="Версия:").pack(side="left")
    version_var = tk.StringVar(value="1.20.1")



    version_combo = ttk.Combobox(
        meta_frame,
        textvariable=version_var,
        values=all_versions,
        state="readonly",
        width=12,
    )
    version_combo.pack(side="left", padx=(5, 20))

    ttk.Label(meta_frame, text="Загрузчик:").pack(side="left")
    loader_var = tk.StringVar(value="fabric")

    api = ModrinthAPI()

    def update_loaders(*args):
        """Обновляет список загрузчиков при смене версии"""
        selected_version = version_var.get()
        available_loaders = api.get_supported_loaders(selected_version)

        loader_combo['values'] = available_loaders
        if loader_var.get() not in available_loaders and available_loaders:
            loader_var.set(available_loaders[0])

    version_var.trace_add('write', update_loaders)

    loader_combo = ttk.Combobox(
        meta_frame,
        textvariable=loader_var,
        values=api.get_supported_loaders(version_var.get()),
        state="readonly",
        width=12,
    )
    loader_combo.pack(side="left", padx=5)

    update_loaders()

    # === Вкладки модов ===
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, pady=(0, 20))

    # --- Локальные моды ---
    local_frame = ttk.Frame(notebook, padding=10)
    notebook.add(local_frame, text="📁 Мои моды")

    local_search_frame = ttk.Frame(local_frame)
    local_search_frame.pack(fill="x", pady=(0, 10))

    ttk.Label(local_search_frame, text="Поиск:").pack(side="left")
    local_search_var = tk.StringVar()
    local_search_entry = ttk.Entry(
        local_search_frame, textvariable=local_search_var, width=30
    )
    local_search_entry.pack(side="left", padx=(5, 10))

    def search_local_mods():
        query = local_search_var.get().lower()
        load_local_mods(query)

    ttk.Button(local_search_frame, text="🔍 Поиск", command=search_local_mods).pack(
        side="left", padx=(0, 10)
    )
    ttk.Button(
        local_search_frame, text="🔄 Обновить", command=lambda: load_local_mods()
    ).pack(side="left")

    local_tree_frame = ttk.Frame(local_frame)
    local_tree_frame.pack(fill="both", expand=True)

    local_mods_tree = ttk.Treeview(
        local_tree_frame, columns=("name", "file", "size"), show="headings", height=10
    )
    local_mods_tree.heading("name", text="Название")
    local_mods_tree.heading("file", text="Файл")
    local_mods_tree.heading("size", text="Размер")

    local_mods_tree.column("name", width=250)
    local_mods_tree.column("file", width=200)
    local_mods_tree.column("size", width=80)

    def load_local_mods(search_query=None):
        local_mods_tree.delete(*local_mods_tree.get_children())
        mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")

        if not os.path.exists(mods_dir):
            return

        for file in os.listdir(mods_dir):
            if file.endswith(".jar"):
                if search_query and search_query not in file.lower():
                    continue

                file_path = os.path.join(mods_dir, file)
                try:
                    size = os.path.getsize(file_path) / 1024 / 1024
                    name = " ".join(
                        [
                            word.capitalize()
                            for word in file.replace(".jar", "")
                            .replace("_", " ")
                            .replace("-", " ")
                            .split()
                        ]
                    )
                    local_mods_tree.insert(
                        "", "end", values=(name, file, f"{size:.1f} MB"), tags=(file,)
                    )
                except (OSError, FileNotFoundError) as e:
                    print(f"⚠️ Не удалось прочитать файл {file}: {e}")

    local_scrollbar = ttk.Scrollbar(
        local_tree_frame, orient="vertical", command=local_mods_tree.yview
    )
    local_mods_tree.configure(yscrollcommand=local_scrollbar.set)

    local_mods_tree.pack(side="left", fill="both", expand=True)
    local_scrollbar.pack(side="right", fill="y")

    load_local_mods()

    # --- Modrinth ---
    modrinth_frame = ttk.Frame(notebook, padding=10)
    notebook.add(modrinth_frame, text="🌐 Modrinth")

    search_frame = ttk.Frame(modrinth_frame)
    search_frame.pack(fill="x", pady=(0, 10))

    ttk.Label(search_frame, text="Поиск модов:").pack(side="left")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", padx=(5, 10))

    def search_modrinth():
        """Поиск модов: сначала ищем, потом помечаем совместимость"""
        query = search_var.get().strip()
        if not query:
            messagebox.showwarning("Поиск", "Введите название мода")
            return

        # Текущие настройки
        minecraft_version = version_var.get()
        loader_type = loader_var.get().lower()

        progress_window = tk.Toplevel(collection_window)
        set_window_icon(progress_window)
        progress_window.title("Поиск")
        progress_window.geometry("300x100")
        progress_window.transient(collection_window)
        progress_window.grab_set()

        ttk.Label(progress_window, text="🔍 Ищем моды...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        def do_search():
            try:
                # 1. Ищем до 30 модов
                results = api.search_mods(query, limit=30)
                collection_window.after(0, progress_window.destroy)

                if not results or "hits" not in results:
                    collection_window.after(0, lambda: messagebox.showinfo("Результат", "Ничего не найдено"))
                    return

                mods = results["hits"]

                # 2. Прогресс-бар: анализ совместимости
                compatibility_window = tk.Toplevel(collection_window)
                set_window_icon(compatibility_window)
                compatibility_window.title("Анализ совместимости")
                compatibility_window.geometry("400x120")
                compatibility_window.transient(collection_window)
                compatibility_window.grab_set()

                ttk.Label(compatibility_window, text="🔍 Анализ совместимости...").pack(pady=10)
                compat_progress = ttk.Progressbar(
                    compatibility_window, orient="horizontal", mode="determinate", length=300
                )
                compat_progress.pack(pady=5)
                compat_progress.config(maximum=len(mods))

                compat_status = tk.StringVar(value="Анализ 1 из ...")
                ttk.Label(compatibility_window, textvariable=compat_status).pack(pady=5)

                # 3. Помечаем каждый мод: совместим или нет
                for idx, mod in enumerate(mods):
                    collection_window.after(0, lambda i=idx + 1, t=len(mods): compat_status.set(f"Анализ {i} из {t}"))  # noqa
                    collection_window.after(0, lambda i=idx: compat_progress.config(value=i))  # noqa

                    # Проверяем совместимость
                    versions = api.get_mod_versions(
                        mod_id=mod["project_id"],
                        minecraft_version=minecraft_version,
                        loader=loader_type
                    )

                    if versions:
                        mod["compatible"] = True
                        mod["compatible_version"] = versions[0]["version_number"]
                        mod["filename"] = versions[0]["files"][0]["filename"]
                    else:
                        mod["compatible"] = False
                        mod["compatible_version"] = "❌ Нет версии"
                        mod["filename"] = "N/A"

                collection_window.after(0, compatibility_window.destroy) # noqa

                # 4. Сортируем: совместимые — вверх
                mods.sort(key=lambda m: (not m["compatible"], -m.get("downloads", 0)))

                collection_window.after(0, lambda: display_modrinth_results(mods)) # noqa

            except Exception as e:
                collection_window.after(0, progress_window.destroy) # noqa
                collection_window.after(0, lambda: messagebox.showerror("Ошибка", f"Поиск не удался: {e}")) # noqa

        threading.Thread(target=do_search, daemon=True).start()

    def display_modrinth_results(mods):
        """Отображает моды с корректными tags"""
        modrinth_tree.delete(*modrinth_tree.get_children())

        for mod in mods:
            downloads = f"{mod.get('downloads', 0):,}"
            version = mod.get("compatible_version", "❌")
            status = "✅" if mod.get("compatible") else "❌"
            description = mod.get("description", "")[:80] + "..." if len(mod.get("description", "")) > 80 else mod.get(
                "description", "")

            # Вставляем строку
            item_id = modrinth_tree.insert(
                "",
                "end",
                values=(f"{mod['title']} ({version})", mod["author"], downloads, description, status),
                tags=(mod["project_id"], mod["filename"])  # ✅ Только ID и имя файла
            )

            # Назначаем цвет отдельно
            if mod.get("compatible"):
                modrinth_tree.item(item_id, tags=(mod["project_id"], mod["filename"], "compatible"))
            else:
                modrinth_tree.item(item_id, tags=(mod["project_id"], mod["filename"], "incompatible"))

        # Конфигурируем цвета
        modrinth_tree.tag_configure("compatible", background="#0a3020", foreground="white")
        modrinth_tree.tag_configure("incompatible", background="#3a1010", foreground="#ffaaaa")

    def on_treeview_sort(col):
        global current_sort_col, current_sort_reverse
        items = [(modrinth_tree.set(item, col), item) for item in modrinth_tree.get_children("")]
        if col == "downloads":
            items = [(int(item[0].replace(",", "")), item[1]) for item in items]
        else:
            items = [(item[0].lower(), item[1]) for item in items]

        items.sort(reverse=current_sort_reverse)
        for index, (_, item) in enumerate(items):
            modrinth_tree.move(item, "", index)

        current_sort_reverse = not current_sort_reverse
        update_sort_indicators(col)

    def update_sort_indicators(sorted_col):
        for col in modrinth_tree["columns"]:
            clean_text = modrinth_tree.heading(col)["text"].replace(" ▲", "").replace(" ▼", "")
            if col == sorted_col:
                indicator = " ▼" if current_sort_reverse else " ▲"
                modrinth_tree.heading(col, text=clean_text + indicator)
            else:
                modrinth_tree.heading(col, text=clean_text)

    ttk.Button(search_frame, text="🔍 Поиск", command=search_modrinth).pack(
        side="left", padx=(0, 10)
    )

    modrinth_tree_frame = ttk.Frame(modrinth_frame)
    modrinth_tree_frame.pack(fill="both", expand=True)

    modrinth_tree = ttk.Treeview(
        modrinth_tree_frame,
        columns=("name", "author", "downloads", "description", "status"),
        show="headings",
        height=15,
    )

    modrinth_tree.heading("name", text="Название", command=lambda: on_treeview_sort("name"))
    modrinth_tree.heading("author", text="Автор", command=lambda: on_treeview_sort("author"))
    modrinth_tree.heading("downloads", text="Загрузки", command=lambda: on_treeview_sort("downloads"))
    modrinth_tree.heading("description", text="Описание", command=lambda: on_treeview_sort("description"))
    modrinth_tree.heading("status", text="Совместимость")

    modrinth_tree.column("name", width=220)
    modrinth_tree.column("author", width=120)
    modrinth_tree.column("downloads", width=100)
    modrinth_tree.column("description", width=200)
    modrinth_tree.column("status", width=80)

    modrinth_scrollbar = ttk.Scrollbar(
        modrinth_tree_frame, orient="vertical", command=modrinth_tree.yview
    )
    modrinth_tree.configure(yscrollcommand=modrinth_scrollbar.set)

    modrinth_tree.pack(side="left", fill="both", expand=True)
    modrinth_scrollbar.pack(side="right", fill="y")

    # === Выбранные моды ===
    selected_frame = ttk.LabelFrame(main_frame, text="✅ Выбранные моды", padding=10)
    selected_frame.pack(fill="x", pady=(0, 20))

    selected_tree = ttk.Treeview(
        selected_frame, columns=("source", "name", "file"), show="headings", height=4
    )
    selected_tree.heading("source", text="Источник")
    selected_tree.heading("name", text="Название")
    selected_tree.heading("file", text="Файл")

    selected_tree.column("source", width=80)
    selected_tree.column("name", width=250)
    selected_tree.column("file", width=200)

    selected_scrollbar = ttk.Scrollbar(
        selected_frame, orient="vertical", command=selected_tree.yview
    )
    selected_tree.configure(yscrollcommand=selected_scrollbar.set)

    selected_tree.pack(side="left", fill="both", expand=True)
    selected_scrollbar.pack(side="right", fill="y")

    # === Управление модами ===
    def on_mod_select(event):
        selection = modrinth_tree.selection()
        if not selection:
            return

        item = modrinth_tree.item(selection[0])
        tags = item["tags"]
        if not tags:
            return

        mod_id = tags[0]  # ✅ project_id
        mod_title = item["values"][0].split(" (")[0]

        if not hasattr(collection_window, "last_search_results"):
            return

        matching_mod = next((m for m in collection_window.last_search_results if m["title"] == mod_title), None)
        if not matching_mod:
            return

        if matching_mod.get("compatible"):
            return  # ✅ Не показываем, если совместим

        # Теперь можно безопасно использовать mod_id
        try:
            # Получаем ВСЕ версии мода, чтобы показать пользователю
            all_versions_response = api.session.get(
                f"https://api.modrinth.com/v2/project/{mod_id}/version",
                timeout=10
            )
            if not all_versions_response.ok:
                messagebox.showwarning("Ошибка", "Не удалось загрузить данные о моде", parent=collection_window)
                return

            all_versions = all_versions_response.json()

            # Собираем данные
            game_versions = set()
            loaders = set()
            latest_version = None

            for v in all_versions:
                if v.get("game_versions"):
                    game_versions.update(v["game_versions"])
                if v.get("loaders"):
                    loaders.update([l.lower() for l in v["loaders"]])
                if not latest_version and v.get("version_number"):
                    latest_version = v["version_number"]

            game_versions = sorted(game_versions, key=lambda x: [int(p) if p.isdigit() else p for p in x.split(".")],
                                   reverse=True)
            loaders = sorted(loaders)

            message = f"❌ Мод '{mod_title}' не совместим:\n\n"
            message += f"• Версия: {version_var.get()}\n"
            message += f"• Загрузчик: {loader_var.get()}\n\n"

            if latest_version:
                message += f"📦 Последняя версия: {latest_version}\n"
            if game_versions:
                message += f"🟢 Поддерживаемые MC: {', '.join(game_versions[:5])}...\n"
            if loaders:
                message += f"🔧 Поддерживаемые: {', '.join(loaders)}\n"

            messagebox.showinfo("Совместимость", message, parent=collection_window)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}", parent=collection_window)
    selected_buttons = ttk.Frame(selected_frame)
    selected_buttons.pack(fill="x", pady=(10, 0))
    modrinth_tree.bind("<<TreeviewSelect>>", on_mod_select)

    def add_selected_mods():

        current_tab = notebook.index(notebook.select())
        if current_tab == 1:  # Modrinth
            for item in modrinth_tree.selection():
                values = modrinth_tree.item(item)["values"]
                tags = modrinth_tree.item(item)["tags"]  # → (project_id, filename)

                if len(tags) < 2:
                    continue

                mod_id = tags[0]  # ✅ строка: project_id
                filename = tags[1]  # ✅ строка: filename

                mod_title = values[0].split(" (")[0]

                if not any(selected_tree.item(i)["values"][1] == mod_title for i in selected_tree.get_children()):
                    selected_tree.insert(
                        "", "end",
                        values=("Modrinth", mod_title, filename),
                        tags=("modrinth", mod_id, filename)
                    )
    def remove_selected_mods():
        for item in selected_tree.selection():
            selected_tree.delete(item)

    def clear_all_mods():
        if selected_tree.get_children() and messagebox.askyesno("Подтверждение", "Очистить все выбранные моды?"):
            selected_tree.delete(*selected_tree.get_children())

    ttk.Button(selected_buttons, text="➕ Добавить выбранные", command=add_selected_mods, width=18).pack(side="left", padx=5)
    ttk.Button(selected_buttons, text="🗑️ Удалить выбранные", command=remove_selected_mods, width=18).pack(side="left", padx=5)
    ttk.Button(selected_buttons, text="🗑️ Очистить все", command=clear_all_mods, width=15).pack(side="left", padx=5)

    # === Создание сборки ===
    def create_collection():
        name = name_var.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название сборки!")
            return

        mods = []
        failed_mods = []

        progress_window = tk.Toplevel(collection_window)
        set_window_icon(progress_window)
        progress_window.title("Обработка модов")
        progress_window.geometry("500x300")
        progress_window.transient(collection_window)
        progress_window.grab_set()

        ttk.Label(progress_window, text="Получение информации о модах...", font=("Comfortaa", 12)).pack(pady=10)
        progress = ttk.Progressbar(progress_window, orient="horizontal", mode="determinate")
        progress.pack(fill="x", padx=20, pady=10)

        status_var = tk.StringVar(value="Подготовка...")
        status_label = ttk.Label(progress_window, textvariable=status_var)
        status_label.pack()

        log_text = tk.Text(progress_window, height=10, width=60)
        log_text.pack(fill="both", expand=True, padx=20, pady=10)

        def process_mods_thread():
            total_mods = len(selected_tree.get_children())
            for i, item in enumerate(selected_tree.get_children()):
                values = selected_tree.item(item)["values"]
                tags = selected_tree.item(item)["tags"]

                progress_window.after(0, lambda idx=i: progress.config(value=(idx * 100) // total_mods))  # noqa
                progress_window.after(0, lambda v=values: status_var.set(f"Обработка: {v[1]}"))  # noqa

                mod_info = {"source": tags[0], "name": values[1], "filename": values[2]}

                if tags[0] == "local":
                    log_text.insert("end", f"🔍 Ищем на Modrinth: {values[1]}...\n")
                    log_text.see("end")
                    modrinth_info = find_mod_on_modrinth(api, values[1], version_var.get(), loader_var.get())
                    if modrinth_info:
                        mod_info.update({
                            "source": "modrinth",
                            "modrinth_id": modrinth_info["id"],
                            "modrinth_slug": modrinth_info["slug"],
                            "correct_filename": modrinth_info["filename"],
                        })
                        mods.append(mod_info)
                        log_text.insert("end", f"✅ Найден: {modrinth_info['title']}\n")
                    else:
                        failed_mods.append(values[1])
                        log_text.insert("end", f"❌ Не найден на Modrinth: {values[1]}\n")
                elif tags[0] == "modrinth":
                    mod_info["modrinth_id"] = tags[1]
                    mods.append(mod_info)
                    log_text.insert("end", f"✅ Modrinth мод: {values[1]}\n")

                log_text.see("end")

            progress_window.after(0, progress_window.destroy)
            progress_window.after(0, lambda: finalize_collection_creation(name, mods, failed_mods))

        def finalize_collection_creation(name, mods, failed_mods):
            if not mods:
                messagebox.showerror("Ошибка", "Не удалось найти ни одного мода на Modrinth!")
                return

            if failed_mods:
                messagebox.showwarning(
                    "Внимание",
                    f"Следующие моды не найдены на Modrinth и будут пропущены:\n" + "\n".join(failed_mods),
                )

            collection_data = {
                "name": name,
                "minecraft_version": version_var.get(),
                "loader": loader_var.get(),
                "created_at": dt.now().isoformat(),
                "mods": mods,
                "mod_count": len(mods),
            }

            safe_name = "".join(c for c in name if c not in '/\\:*?"<>|')
            filename = f"{safe_name}.json"
            collections_dir = COLLECTIONS_CONFIG["collections_dir"]
            filepath = os.path.join(collections_dir, filename)

            # ✅ Создаём папку, если её нет
            os.makedirs(collections_dir, exist_ok=True)

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(collection_data, f, indent=2, ensure_ascii=False)
                message = f"Сборка '{name}' создана!\n\n• Модов: {len(mods)}\n• Версия: {version_var.get()}\n• Загрузчик: {loader_var.get()}"
                if failed_mods:
                    message += f"\n• Пропущено: {len(failed_mods)}"
                messagebox.showinfo("Успех", message)
                collection_window.destroy()
                show_collection_manager()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать сборку: {e}")

        threading.Thread(target=process_mods_thread, daemon=True).start()

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x")
    ttk.Button(button_frame, text="✅ Создать сборку", command=create_collection).pack(side="left", padx=5)
    ttk.Button(button_frame, text="❌ Отмена", command=collection_window.destroy).pack(side="right", padx=5)

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
            if not query or len(query) < 10:
                continue

            print(f"🔎 Ищем: '{query}'")
            results = api.search_mods(query, limit=20)

            if not results or "hits" not in results or not results["hits"]:
                continue

            print(f"📦 Найдено результатов: {len(results['hits'])}")

            # Проверяем все результаты
            best_match = find_best_match(
                results["hits"], mod_name, clean_name, minecraft_version, loader, api
            )
            if best_match:
                return best_match

        # Последняя попытка: поиск по ключевым словам
        return try_keyword_search(api, mod_name, minecraft_version, loader)

    except Exception as e:
        print(f"💥 Ошибка поиска мода {mod_name}: {e}")
        return None





def generate_search_queries(original_name, clean_name):
    """Генерирует расширенный список поисковых запросов"""
    queries = set()

    # Добавляем различные варианты
    variants = [
        clean_name,
        original_name,
        clean_name.replace(" ", ""),
        clean_name.replace(" ", "-"),
        clean_name.replace(" ", "_"),
        extract_core_name(original_name),
        remove_version_info(original_name),
        get_acronym(clean_name),
    ]

    # Добавляем отдельные слова из названия
    words = clean_name.split()
    for word in words:
        if len(word) > 3 and not word.isdigit():
            queries.add(word)

    # Добавляем комбинации слов
    if len(words) > 1:
        queries.add(" ".join(words[:2]))  # Первые два слова
        queries.add(" ".join(words[-2:]))  # Последние два слова

    # Фильтруем и возвращаем
    return [q for q in variants if q and len(q) > 1]

def remove_version_info(mod_name):
    """Удаляет информацию о версии"""
    import re

    # Удаляем паттерны версий типа 1.2.3, 1.2.3+1.20.1 и т.д.
    cleaned = re.sub(r"[\d.\-_]+\+?[\d.\-_]*", "", mod_name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_acronym(mod_name):
    """Создает акроним из названия"""
    words = mod_name.split()
    if len(words) > 1:
        return "".join(word[0].upper() for word in words if word)
    return ""


def try_find_by_filename(api, filename, minecraft_version, loader):
    """Пытается найти мод по точному имени файла"""
    try:
        # Извлекаем название из имени файла (без .jar и версии)
        base_name = filename.replace(".jar", "")

        # Удаляем информацию о версии и загрузчике
        clean_file_name = re.sub(r"[\d.\-_]+(?:fabric|forge|quilt|neoforge).*$", "", base_name)
        clean_file_name = re.sub(r"\s+", " ", clean_file_name).strip()

        if len(clean_file_name) > 3:
            print(f"📁 Поиск по имени файла: '{clean_file_name}'")
            results = api.search_mods(clean_file_name, limit=10)

            if results and "hits" in results and results["hits"]:
                for mod in results["hits"]:
                    similarity = calculate_similarity(
                        mod["title"].lower(), clean_file_name.lower()
                    )
                    if similarity > 0.4:
                        versions = api.get_mod_versions(
                            mod["project_id"], minecraft_version, loader.lower()
                        )
                        if versions:
                            latest_version = versions[0]
                            file = latest_version["files"][0]
                            print(f"✅ Найден по имени файла: {mod['title']}")
                            return {
                                "id": mod["project_id"],
                                "slug": mod["slug"],
                                "title": mod["title"],
                                "filename": file["filename"],
                            }
    except Exception as e:
        print(f"⚠️ Ошибка поиска по файлу: {e}")

    return None


def find_best_match(mods, original_name, clean_name, minecraft_version, loader, api):
    """Находит лучший совпадающий мод"""
    best_similarity = 0
    best_mod = None

    for mod in mods:
        mod_title = mod["title"].lower()

        # Вычисляем несколько метрик схожести
        similarity1 = calculate_similarity(mod_title, original_name.lower())
        similarity2 = calculate_similarity(mod_title, clean_name)
        similarity3 = calculate_word_overlap(mod_title, clean_name)

        # Общая схожесть (максимум из всех метрик)
        total_similarity = max(similarity1, similarity2, similarity3)

        print(f"  📊 '{mod['title']}' - схожесть: {total_similarity:.2f}")

        if total_similarity > best_similarity:
            # Проверяем поддержку версии
            versions = api.get_mod_versions(
                mod["project_id"], minecraft_version, loader.lower()
            )
            if versions:
                best_similarity = total_similarity
                latest_version = versions[0]
                file = latest_version["files"][0]
                best_mod = {
                    "id": mod["project_id"],
                    "slug": mod["slug"],
                    "title": mod["title"],
                    "filename": file["filename"],
                }

    # Понижаем порог для принятия решения
    if best_mod and best_similarity > 0.2:  # Был 0.6
        print(
            f"✅ Лучшее совпадение: {best_mod['title']} (схожесть: {best_similarity:.2f})"
        )
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
        "appliedenergistics": "applied energistics 2",
        "xaeros": "xaero",
        "inventoryprofiles": "inventory profiles next",
        "travelersbackpack": "traveler backpack",
        "lambdynamiclights": "lamb dynamic lights",
        "fallingleaves": "falling leaves",
        "ironchests": "iron chests",
        "techreborn": "tech reborn",
        "reborncore": "reborn core",
        "mavapi": "more axolotl variants api",
        "mavm": "more axolotl variants mod",
        "noindium": "no indium",
    }

    # Проверяем по ключевым словам
    for key, search_term in keyword_map.items():
        if key in mod_name.lower():
            print(f"🔑 Используем ключевое слово: {search_term}")
            results = api.search_mods(search_term, limit=5)

            if results and "hits" in results and results["hits"]:
                mod = results["hits"][0]
                versions = api.get_mod_versions(
                    mod["project_id"], minecraft_version, loader.lower()
                )
                if versions:
                    latest_version = versions[0]
                    file = latest_version["files"][0]
                    print(f"✅ Найден по ключевому слову: {mod['title']}")
                    return {
                        "id": mod["project_id"],
                        "slug": mod["slug"],
                        "title": mod["title"],
                        "filename": file["filename"],
                    }

    return None


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
                        project_data["id"], minecraft_version, loader.lower()
                    )
                    if versions:
                        latest_version = versions[0]
                        file = latest_version["files"][0]
                        print(
                            f"✅ Найден через ручное сопоставление: {project_data['title']}"
                        )
                        return {
                            "id": project_data["id"],
                            "slug": project_data["slug"],
                            "title": project_data["title"],
                            "filename": file["filename"],
                        }
            except Exception as e:
                print(f"⚠️ Ошибка ручного сопоставления: {e}")

    return None


def clean_mod_name(mod_name):
    """Очищает название мода от версий и лишних частей"""
    # Удаляем версии типа 1.20.1, 1.19.2 и т.д.
    import re

    cleaned = re.sub(
        r"[\d.\-_]+(?:fabric|forge|quilt|neoforge)?", " ", mod_name, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\b(?:fabric|forge|quilt|neoforge|mc|minecraft|mod)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Если после очистки ничего не осталось, возвращаем оригинал
    return cleaned if cleaned else mod_name


def extract_main_words(mod_name):
    """Извлекает основные слова из названия"""
    words = mod_name.split()
    # Оставляем только слова длиной > 3 символов и не являющиеся версиями
    main_words = [
        word for word in words if len(word) > 3 and not re.match(r"^[\d.\-_]+$", word)
    ]
    return " ".join(main_words[:3])  # Берем до 3 слов



# Функция показа менеджера сборок
def show_collection_manager():
    manager_window = tk.Toplevel(win)
    set_window_icon(manager_window)
    manager_window.title("Менеджер сборок (Бета)")
    manager_window.geometry("1000x500")
    manager_window.transient(win)
    manager_window.grab_set()

    main_frame = ttk.Frame(manager_window, padding=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame, text="📦 Менеджер сборок модов", font=("Comfortaa", 16, "bold")
    ).pack(pady=(0, 20))

    # Информация о папке
    collections_dir = COLLECTIONS_CONFIG["collections_dir"]
    info_label = ttk.Label(
        main_frame, text=f"Папка: {collections_dir}", foreground="gray"
    )
    info_label.pack(pady=(0, 10))

    # Список сборок
    tree = ttk.Treeview(
        main_frame,
        columns=("name", "version", "loader", "mods", "created"),
        show="headings",
    )
    tree.heading("name", text="Название")
    tree.heading("version", text="Версия")
    tree.heading("loader", text="Загрузчик")
    tree.heading("mods", text="Модов")
    tree.heading("created", text="Создана")

    tree.column("name", width=200)
    tree.column("version", width=100)
    tree.column("loader", width=80)
    tree.column("mods", width=60)
    tree.column("created", width=100)

    # Статус сборок
    status_var = tk.StringVar(value="Загрузка...")
    status_label = ttk.Label(main_frame, textvariable=status_var, foreground="blue")
    status_label.pack(pady=5)

    def load_collections():
        tree.delete(*tree.get_children())
        collections_dir = COLLECTIONS_CONFIG["collections_dir"]

        if not os.path.exists(collections_dir):
            status_var.set("Папка сборок не существует!")
            return

        try:
            files = os.listdir(collections_dir)
            json_files = [f for f in files if f.endswith(".json")]
            status_var.set(f"Найдено сборок: {len(json_files)}")

            for file in json_files:
                filepath = os.path.join(collections_dir, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Проверяем структуру данных
                    if all(
                            field in data
                            for field in [
                                "name",
                                "minecraft_version",
                                "loader",
                                "mod_count",
                                "created_at",
                            ]
                    ):
                        created = datetime.datetime.fromisoformat(
                            data["created_at"]
                        ).strftime("%d.%m.%Y")
                        tree.insert(
                            "",
                            "end",
                            values=(
                                data["name"],
                                data["minecraft_version"],
                                data["loader"],
                                data["mod_count"],
                                created,
                            ),
                            tags=(file,),
                        )
                    else:
                        print(f"Неполные данные в файле {file}")

                except Exception as e:
                    print(f"Ошибка загрузки {file}: {e}")

        except Exception as e:
            status_var.set(f"Ошибка: {e}")

    tree.pack(fill="both", expand=True)
    load_collections()

    # Кнопки управления
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)

    def refresh_collections():
        status_var.set("Обновление...")
        load_collections()

    def open_collections_folder():
        os.makedirs(COLLECTIONS_CONFIG["collections_dir"], exist_ok=True)
        if os.name == "nt":
            os.startfile(COLLECTIONS_CONFIG["collections_dir"])
        else:
            subprocess.Popen(["xdg-open", COLLECTIONS_CONFIG["collections_dir"]])

    def load_to_game():
        selection = tree.selection()
        if selection:
            filename = tree.item(selection[0])["tags"][0]
            load_collection_to_game(filename)
        else:
            messagebox.showwarning("Выбор", "Выберите сборку для загрузки")

    def delete_collection():
        selection = tree.selection()
        if selection:
            filename = tree.item(selection[0])["tags"][0]
            filepath = os.path.join(COLLECTIONS_CONFIG["collections_dir"], filename)
            if messagebox.askyesno("Подтверждение", "Удалить сборку?"):
                try:
                    os.remove(filepath)
                    load_collections()
                    messagebox.showinfo("Успех", "Сборка удалена")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    ttk.Button(button_frame, text="🔄 Обновить", command=refresh_collections).pack(
        side="left", padx=5
    )
    ttk.Button(
        button_frame, text="📁 Открыть папку", command=open_collections_folder
    ).pack(side="left", padx=5)
    ttk.Button(button_frame, text="🎮 Загрузить в игру", command=load_to_game).pack(
        side="left", padx=5
    )
    ttk.Button(button_frame, text="🗑️ Удалить", command=delete_collection).pack(
        side="left", padx=5
    )
    ttk.Button(
        button_frame,
        text="➕ Новая сборка",
        command=lambda: (manager_window.destroy(), create_new_collection()),
    ).pack(side="right", padx=5)
    ttk.Button(button_frame, text="❌ Закрыть", command=manager_window.destroy).pack(
        side="right", padx=5
    )


# Функция загрузки сборки в игру
def load_collection_to_game(filename):
    filepath = os.path.join(COLLECTIONS_CONFIG["collections_dir"], filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            collection = json.load(f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить сборку: {e}")
        return

    # Создаем окно прогресса с логом
    progress_window = tk.Toplevel(win)
    set_window_icon(progress_window)
    progress_window.title(f"Загрузка сборки: {collection['name']}")
    progress_window.geometry("700x500")
    progress_window.transient(win)
    progress_window.grab_set()

    main_frame = ttk.Frame(progress_window, padding=15)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame,
        text=f"📦 Загрузка сборки: {collection['name']}",
        font=("Comfortaa", 14, "bold"),
    ).pack(pady=(0, 10))

    # Информация о сборке
    info_text = f"Версия: {collection['minecraft_version']} | Загрузчик: {collection['loader']} | Модов: {collection['mod_count']}"
    ttk.Label(main_frame, text=info_text).pack(pady=(0, 15))

    # Прогресс-бар
    progress = ttk.Progressbar(
        main_frame, orient="horizontal", length=600, mode="determinate"
    )
    progress.pack(fill="x", pady=5)

    # Статус и счетчик
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill="x", pady=5)

    status_var = tk.StringVar(value="Подготовка...")
    status_label = ttk.Label(
        status_frame, textvariable=status_var, font=("Comfortaa", 10)
    )
    status_label.pack(side="left")

    counter_var = tk.StringVar(value="0/0")
    counter_label = ttk.Label(
        status_frame, textvariable=counter_var, font=("Comfortaa", 10)
    )
    counter_label.pack(side="right")

    # Детальный лог
    log_frame = ttk.LabelFrame(main_frame, text="Детальный лог загрузки", padding=10)
    log_frame.pack(fill="both", expand=True, pady=(10, 0))

    log_text = tk.Text(log_frame, height=15, width=80, font=("Consolas", 9))
    log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    log_text.configure(yscrollcommand=log_scrollbar.set)

    log_text.pack(side="left", fill="both", expand=True)
    log_scrollbar.pack(side="right", fill="y")

    def log_message(message):
        win.after(0, lambda: log_text.insert("end", f"{message}\n"))
        win.after(0, lambda: log_text.see("end"))

    def download_thread():
        import concurrent.futures
        mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
        os.makedirs(mods_dir, exist_ok=True)

        log_message(f"📁 Папка модов: {mods_dir}")
        log_message(f"🔄 Начинаем загрузку {len(collection['mods'])} модов...")

        # Бэкап и очистка
        backup_path = create_mods_backup(collection["name"])
        if backup_path:
            log_message(f"📂 Создан бэкап: {os.path.basename(backup_path)}")

        cleared_count = clear_mods_directory(mods_dir)
        log_message(f"🗑️ Очищено модов: {cleared_count}")

        # Подготовка
        api = ModrinthAPI()
        total_mods = len(collection["mods"])
        success_count = 0

        # Прогресс
        progress["maximum"] = total_mods

        # Функция загрузки одного мода
        def download_single_mod(mod):
            nonlocal success_count
            try:
                log_message(f"\n🔍 Мод: {mod['name']}")

                if mod["source"] != "modrinth":
                    log_message(f"   ⚠️  Источник не поддерживается: {mod['source']}")
                    return False

                versions = api.get_mod_versions(
                    mod_id=mod["modrinth_id"],
                    minecraft_version=collection["minecraft_version"],
                    loader=collection["loader"].lower(),
                )

                if not versions:
                    log_message("   ❌ Не найдены совместимые версии")
                    return False

                latest_version = versions[0]
                version_id = latest_version["id"]
                project_slug = mod.get("modrinth_slug", mod["modrinth_id"])

                # Ищем JAR-файл
                target_file = next(
                    (f for f in latest_version["files"] if f["filename"].endswith(".jar")),
                    latest_version["files"][0] if latest_version["files"] else None
                )

                if not target_file:
                    log_message("   ❌ Нет файла для скачивания")
                    return False

                filename = target_file["filename"]
                filepath = os.path.join(mods_dir, filename)

                log_message(f"   ⬇️  {filename}")

                # Пробуем скачать
                if api.download_mod(project_slug, version_id, filename, mods_dir):
                    log_message(f"   ✅ Успешно: {filename}")
                    return True
                else:
                    log_message(f"   ❌ Ошибка: {filename}")
                    return False

            except Exception as e:
                log_message(f"   💥 Ошибка: {e}")
                return False

        # Параллельная загрузка
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(download_single_mod, mod) for mod in collection["mods"]]
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    success_count += 1
                win.after(0, lambda: progress.step(1))
                win.after(0, lambda s=success_count: counter_var.set(f"{s}/{total_mods}"))

        # Завершение
        log_message(f"\n🎉 ЗАВЕРШЕНО! Успешно: {success_count}/{total_mods}")
        win.after(0, lambda: finish_loading(progress_window, collection, success_count, total_mods, backup_path))

    threading.Thread(target=download_thread, daemon=True).start()

# Добавляем в меню
settings_menu.add_command(
    label="📦 Сборки модов (Бета)", command=show_collection_manager
)


def create_mods_backup(collection_name):
    """Создание бэкапа модов"""
    mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
    backup_dir = os.path.join(CONFIG["minecraft_dir"], "mods_backup")
    os.makedirs(backup_dir, exist_ok=True)

    if os.path.exists(mods_dir) and any(
            f.endswith(".jar") for f in os.listdir(mods_dir)
    ):
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
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
            if file.endswith(".jar"):
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
        os.path.join(CONFIG["minecraft_dir"], "mods", mod["filename"]),
        os.path.join(COLLECTIONS_CONFIG["collections_dir"], "mods", mod["filename"]),
        os.path.join(os.path.dirname(CONFIG["minecraft_dir"]), "mods", mod["filename"]),
    ]

    for src_path in possible_paths:
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, os.path.join(mods_dir, mod["filename"]))
                return True
            except Exception as e:
                print(f"Ошибка копирования {src_path}: {e}")

    print(f"Локальный файл не найден: {mod['filename']}")
    return False


def handle_modrinth_mod(mod, collection, api, mods_dir, minecraft_version, loader_type, log_callback):
    """Обработка мода с Modrinth с правильным скачиванием"""
    try:
        log_callback(f"🔍 Получаем информацию о {mod['name']}...")

        versions = api.get_mod_versions(
            mod_id=mod["project_id"],
            minecraft_version=minecraft_version,
            loader=loader_type
        )

        if not versions:
            log_callback(f"❌ Не найдены версии для {mod['name']}")
            return False

        # Выбираем последнюю версию
        latest_version = versions[0]
        version_id = latest_version["id"]

        if "files" not in latest_version or not latest_version["files"]:
            log_callback(f"❌ Нет информации о файлах для {mod['name']}")
            return False

        file_info = latest_version["files"][0]
        filename = file_info["filename"]

        # Получаем slug проекта для скачивания
        project_slug = mod.get("modrinth_slug") or mod["modrinth_id"]

        log_callback(f"📥 Скачиваем {filename}...")
        log_callback(f"🆔 Version ID: {version_id}")
        log_callback(f"🔗 Project: {project_slug}")

        # Скачиваем мод
        if api.download_mod(project_slug, version_id, filename, mods_dir):
            log_callback(f"✅ Успешно скачан: {filename}")
            return True
        else:
            # Пробуем через прямой URL из file_info
            if "url" in file_info and file_info["url"]:
                log_callback(f"🔄 Пробуем прямую ссылку...")
                direct_url = file_info["url"]
                try:
                    response = api.session.get(direct_url, timeout=30, stream=True)
                    response.raise_for_status()

                    filepath = os.path.join(mods_dir, filename)
                    with open(filepath, "wb") as f:
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

    message = (
        f"Сборка '{collection['name']}' загружена!\n\n"
        f"✅ Успешно: {success_count}/{total_mods} модов"
    )

    if backup_path:
        message += f"\n\n📂 Бэкап создан: {os.path.basename(backup_path)}"

    if success_count < total_mods:
        message += (
            "\n\n⚠️ Некоторые моды не удалось загрузить. Проверьте лог для деталей."
        )

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
win.after(100, lambda: setup_adaptive_background()) # noqa


def apply_background_and_close(filename, window):
    """Применяет фон и закрывает окно"""
    load_custom_background(filename)
    window.destroy()
    messagebox.showinfo("Успех", f"Фон {filename} применен!")


if __name__ == "__main__":
    safe_mainloop()