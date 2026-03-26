# downloader.py
import os
import time
import hashlib
import requests
import aiohttp
import asyncio
import logging
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk, messagebox
import threading

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

            with open(cache_file, "wb") as f:
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
        self._session = None

    @property
    def session(self):
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=300)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def cleanup(self):
        """Закрывает сессию при завершении"""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_turbo_link(self, public_key):
        """Быстрое получение ссылки через асинхронность"""
        if public_key in self.cache:
            return self.cache[public_key]

        api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
        try:
            async with self.session.get(
                api_url, params={"public_key": public_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    direct_link = data.get("href")
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
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                total_size = int(response.headers.get("content-length", 0))

                with open(file_path, "wb") as f:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(8192 * 8):
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
        try:
            return asyncio.run(
                self.download_file_async(url, file_path, progress_callback)
            )
        finally:
            asyncio.run(self.cleanup())


def download_single_mod_turbo(mod_info, minecraft_dir):
    """Турбо-загрузка одного мода с правильным закрытием ресурсов"""
    downloader = TurboDownloader()
    try:
        print(f"🔍 Начинаем загрузку мода: {mod_info['file']}")

        # Получаем прямую ссылку
        direct_link = asyncio.run(downloader.get_turbo_link(mod_info["url"]))
        print(f"🔗 Прямая ссылка получена: {direct_link is not None}")

        if not direct_link:
            logging.error(f"Не удалось получить ссылку для {mod_info['file']}")
            asyncio.run(downloader.cleanup())
            return False

        # Путь для сохранения
        mods_dir = os.path.join(minecraft_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        file_path = os.path.join(mods_dir, mod_info["file"])

        # Загружаем файл
        success = downloader.download_file_sync(direct_link, file_path)
        print(
            f"📥 Результат загрузки {mod_info['file']}: {'✅ Успех' if success else '❌ Ошибка'}"
        )

        if success and mod_info["file"].endswith(".zip"):
            # Распаковываем ZIP
            try:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(mods_dir)
                print(f"📦 Мод распакован: {mod_info['file']}")
            except Exception as e:
                logging.error(f"Ошибка распаковки {mod_info['file']}: {e}")

        # Явно закрываем загрузчик
        asyncio.run(downloader.cleanup())
        return success

    except Exception as e:
        logging.error(f"Ошибка загрузки мода {mod_info['file']}: {e}")
        try:
            asyncio.run(downloader.cleanup())
        except:
            pass
        return False


def download_mods_turbo_ui(mods_list, minecraft_dir, win):
    """Версия с UI для использования в лаунчере"""

    # Создаем окно прогресса
    progress_window = tk.Toplevel(win)
    progress_window.title("Загрузка модов")
    progress_window.geometry("400x150")

    progress_label = ttk.Label(progress_window, text="Подготовка к загрузке...")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(
        progress_window, orient="horizontal", length=300, mode="determinate"
    )
    progress.pack(pady=10)

    status_label = ttk.Label(progress_window, text=f"0/{len(mods_list)} модов")
    status_label.pack()

    def download_thread():
        total_mods = len(mods_list)
        success_count = 0

        def update_progress(current, total, mod_name=""):
            percent = (current * 100) // total
            progress["value"] = percent
            status_label.config(text=f"{current}/{total} модов - {mod_name}")
            progress_window.update()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []

            for i, mod in enumerate(mods_list):
                future = executor.submit(download_single_mod_turbo, mod, minecraft_dir)
                futures.append((future, mod["file"]))

            # Обновляем прогресс
            for i, (future, mod_name) in enumerate(futures):
                try:
                    win.after(0, lambda: update_progress(i, total_mods, mod_name))
                    success = future.result(timeout=180)
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
            messagebox.showinfo(
                "Загрузка завершена", f"✅ Все {success} модов успешно загружены!"
            )
        else:
            messagebox.showwarning(
                "Загрузка завершена",
                f"📊 Загружено {success} из {total} модов\n\n"
                f"Некоторые моды могли не загрузиться. Проверьте логи.",
            )

    threading.Thread(target=download_thread, daemon=True).start()

def download_shaders_turbo_ui(shaders_list, parent=None):
    """
    PyQt6 версия загрузки шейдеров с UI прогресса
    shaders_list: список шейдеров [{"name": "...", "url": "...", "file": "..."}, ...]
    parent: родительское окно PyQt6
    """
    import threading
    import logging
    import os
    import requests
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QProgressBar, QTextEdit, QMessageBox, QApplication
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QTextCursor

    from ConfDir.Configs import CONFIG

    class ShaderDownloadWorker(QThread):
        """Поток для загрузки шейдеров"""
        progress = pyqtSignal(int, int, str)  # current, total, shader_name
        finished = pyqtSignal(int, int)  # success_count, total
        log = pyqtSignal(str)

        def __init__(self, shaders):
            super().__init__()
            self.shaders = shaders
            self.cancelled = False

        def cancel(self):
            self.cancelled = True

        def run(self):
            shaders_dir = os.path.join(CONFIG["minecraft_dir"], "shaderpacks")
            os.makedirs(shaders_dir, exist_ok=True)

            total = len(self.shaders)
            success_count = 0

            for i, shader in enumerate(self.shaders):
                if self.cancelled:
                    self.log.emit("❌ Загрузка отменена")
                    break

                self.progress.emit(i, total, shader["name"])
                self.log.emit(f"⬇️ Загрузка: {shader['name']}")

                try:
                    shader_path = os.path.join(shaders_dir, shader["file"])
                    direct_url = _convert_to_direct_link(shader["url"])

                    if _download_file_simple(direct_url, shader_path):
                        success_count += 1
                        self.log.emit(f"✅ Успешно: {shader['name']}")

                        # Распаковываем ZIP если нужно
                        if shader["file"].endswith(".zip"):
                            import zipfile
                            try:
                                with zipfile.ZipFile(shader_path, "r") as zip_ref:
                                    zip_ref.extractall(shaders_dir)
                                self.log.emit(f"📦 Распакован: {shader['name']}")
                            except Exception as e:
                                self.log.emit(f"⚠️ Ошибка распаковки {shader['name']}: {e}")
                    else:
                        self.log.emit(f"❌ Ошибка: {shader['name']}")

                except Exception as e:
                    self.log.emit(f"💥 Ошибка {shader['name']}: {str(e)}")

            self.finished.emit(success_count, total)

    class ShaderProgressDialog(QDialog):
        """Диалог прогресса загрузки шейдеров"""

        def __init__(self, parent, shaders):
            super().__init__(parent)
            self.shaders = shaders
            self.setWindowTitle("Загрузка шейдеров")
            self.setFixedSize(550, 450)
            self.setModal(True)

            self.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    border-radius: 15px;
                }
                QLabel {
                    color: white;
                    font-family: 'Segoe UI';
                }
                QProgressBar {
                    background-color: #3a3a4a;
                    border: none;
                    border-radius: 8px;
                    height: 20px;
                    text-align: center;
                    color: white;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FF6B6B, stop:1 #4ECDC4);
                    border-radius: 8px;
                }
                QTextEdit {
                    background-color: #1a1a2a;
                    color: #e0e0e0;
                    border: 1px solid #4ECDC4;
                    border-radius: 8px;
                    font-family: 'Consolas', monospace;
                    font-size: 10px;
                }
                QPushButton {
                    background-color: #3a3a4a;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4a4a5a;
                }
                QPushButton#cancel {
                    background-color: #ff4757;
                }
                QPushButton#cancel:hover {
                    background-color: #ff6b6b;
                }
            """)

            layout = QVBoxLayout(self)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            # Заголовок
            title = QLabel("📥 Загрузка шейдеров")
            title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            # Информация
            self.info_label = QLabel(f"Всего шейдеров: {len(shaders)}")
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.info_label)

            # Прогресс
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            layout.addWidget(self.progress_bar)

            # Текущий шейдер
            self.current_label = QLabel("Подготовка к загрузке...")
            self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.current_label)

            # Лог
            log_label = QLabel("📋 Лог загрузки:")
            log_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
            layout.addWidget(log_label)

            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setFont(QFont("Consolas", 9))
            self.log_text.setMaximumHeight(180)
            layout.addWidget(self.log_text)

            # Кнопки
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            self.cancel_btn = QPushButton("Отмена")
            self.cancel_btn.setObjectName("cancel")
            self.cancel_btn.clicked.connect(self.cancel_download)
            button_layout.addWidget(self.cancel_btn)

            self.close_btn = QPushButton("Закрыть")
            self.close_btn.clicked.connect(self.accept)
            self.close_btn.setEnabled(False)
            button_layout.addWidget(self.close_btn)

            layout.addLayout(button_layout)

            self.worker = None
            self.start_download()

        def start_download(self):
            """Запускает загрузку"""
            self.worker = ShaderDownloadWorker(self.shaders)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_download_finished)
            self.worker.log.connect(self.add_log)
            self.worker.start()

        def update_progress(self, current, total, shader_name):
            """Обновляет прогресс"""
            percent = int((current + 1) * 100 / total) if total > 0 else 0
            self.progress_bar.setValue(percent)
            self.current_label.setText(f"Загрузка: {shader_name} ({current + 1}/{total})")

        def add_log(self, message):
            """Добавляет сообщение в лог"""
            self.log_text.append(message)
            self.log_text.moveCursor(QTextCursor.MoveOperation.End)

        def on_download_finished(self, success_count, total):
            """Обработка завершения загрузки"""
            self.progress_bar.setValue(100)
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)

            if success_count == total:
                self.current_label.setText("✅ Все шейдеры успешно загружены!")
                self.add_log(f"\n✅ Успешно загружено {success_count} из {total} шейдеров")
            else:
                self.current_label.setText(f"⚠️ Загружено {success_count} из {total} шейдеров")
                self.add_log(f"\n⚠️ Загружено {success_count} из {total} шейдеров")

        def cancel_download(self):
            """Отмена загрузки"""
            if self.worker and self.worker.isRunning():
                self.worker.cancel()
                self.worker.terminate()
                self.worker.wait(1000)
                self.add_log("❌ Загрузка отменена пользователем")
                self.current_label.setText("❌ Загрузка отменена")
                self.cancel_btn.setEnabled(False)
                self.close_btn.setEnabled(True)

    dialog = ShaderProgressDialog(parent, shaders_list)
    dialog.exec()


def _convert_to_direct_link(yandex_url: str) -> str:
    """Конвертирует ссылку Яндекс.Диска в прямую для скачивания"""
    try:
        if "disk.yandex.ru/d/" in yandex_url:
            api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={yandex_url}"
            response = requests.get(api_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'href' in data:
                    return data['href']
        return yandex_url
    except Exception as e:
        logging.error(f"Ошибка конвертации ссылки {yandex_url}: {e}")
        return yandex_url


def _download_file_simple(url: str, filepath: str) -> bool:
    """Простое скачивание файла"""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        if os.path.getsize(filepath) > 1000:
            return True
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
            return False

    except Exception as e:
        logging.error(f"Ошибка скачивания {url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False