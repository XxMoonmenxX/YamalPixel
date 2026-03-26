# Network/Downloader.py
import os
import time
import hashlib
import requests
import asyncio
import logging
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Только PyQt6 импорты
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from ConfDir.Configs import CONFIG

logger = logging.getLogger(__name__)


class LauncherCache:
    def __init__(self):
        self.cache_dir = Path.home() / ".yamalpixel_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def is_cache_fresh(self, cache_file, max_age_hours=24):
        if not cache_file.exists():
            return False
        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < (max_age_hours * 3600)

    def get_file_hash(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def download_and_cache(self, url, cache_file):
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            with open(cache_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192 * 4):
                    f.write(chunk)

            logger.info(f"Файл закэширован: {cache_file.name}")
        except Exception as e:
            logger.error(f"Ошибка кэширования {url}: {e}")
            raise

    def get_cached_file(self, url, force_refresh=False):
        file_hash = self.get_file_hash(url)
        cache_file = self.cache_dir / file_hash

        if cache_file.exists() and not force_refresh:
            if self.is_cache_fresh(cache_file):
                return cache_file

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
        if self._session:
            await self._session.close()
            self._session = None

    async def get_turbo_link(self, public_key):
        if public_key in self.cache:
            return self.cache[public_key]

        api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
        try:
            async with self.session.get(api_url, params={"public_key": public_key}) as response:
                if response.status == 200:
                    data = await response.json()
                    direct_link = data.get("href")
                    self.cache[public_key] = direct_link
                    return direct_link
                else:
                    logger.error(f"Ошибка API Яндекс: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error("Таймаут получения ссылки Яндекс")
            return None
        except Exception as e:
            logger.error(f"Ошибка получения ссылки: {e}")
            return None

    async def download_file_async(self, url, file_path, progress_callback=None):
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
            logger.error(f"Ошибка загрузки {url}: {e}")
            return False

    def download_file_sync(self, url, file_path, progress_callback=None):
        try:
            return asyncio.run(
                self.download_file_async(url, file_path, progress_callback)
            )
        finally:
            asyncio.run(self.cleanup())


def get_yandex_direct_link_sync(public_key):
    """Синхронное получение прямой ссылки с Яндекс.Диска"""
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    try:
        response = requests.get(api_url, params={"public_key": public_key}, timeout=30)
        response.raise_for_status()
        return response.json().get("href")
    except Exception as e:
        logger.error(f"Ошибка получения ссылки: {e}")
        return None


def download_file_sync(url, filepath, progress_callback=None):
    """Синхронное скачивание файла с прогрессом"""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(filepath, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded, total_size)

        if os.path.getsize(filepath) > 1000:
            return True
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
            return False

    except Exception as e:
        logger.error(f"Ошибка скачивания {url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


def download_single_mod_turbo_sync(mod_info, minecraft_dir):
    """Синхронная загрузка одного мода"""
    try:
        print(f"🔍 Начинаем загрузку мода: {mod_info['file']}")

        direct_link = get_yandex_direct_link_sync(mod_info["url"])

        if not direct_link:
            print(f"❌ Не удалось получить ссылку для {mod_info['file']}")
            return False

        mods_dir = os.path.join(minecraft_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        file_path = os.path.join(mods_dir, mod_info["file"])

        success = download_file_sync(direct_link, file_path)

        if success and mod_info["file"].endswith(".zip"):
            try:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(mods_dir)
                print(f"📦 Мод распакован: {mod_info['file']}")
            except Exception as e:
                print(f"⚠️ Ошибка распаковки {mod_info['file']}: {e}")

        return success

    except Exception as e:
        print(f"❌ Ошибка загрузки мода {mod_info['file']}: {e}")
        return False


def download_single_mod_turbo(mod_info, minecraft_dir):
    """Асинхронная версия (для совместимости)"""
    downloader = TurboDownloader()
    try:
        direct_link = asyncio.run(downloader.get_turbo_link(mod_info["url"]))
        if not direct_link:
            return False

        mods_dir = os.path.join(minecraft_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        file_path = os.path.join(mods_dir, mod_info["file"])

        success = downloader.download_file_sync(direct_link, file_path)

        if success and mod_info["file"].endswith(".zip"):
            try:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(mods_dir)
            except:
                pass

        asyncio.run(downloader.cleanup())
        return success

    except Exception as e:
        logger.error(f"Ошибка загрузки мода {mod_info['file']}: {e}")
        try:
            asyncio.run(downloader.cleanup())
        except:
            pass
        return False


class ModDownloadWorker(QThread):
    """Поток для загрузки модов (PyQt6)"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)
    log = pyqtSignal(str)

    def __init__(self, mods_list, minecraft_dir):
        super().__init__()
        self.mods_list = mods_list
        self.minecraft_dir = minecraft_dir
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        total = len(self.mods_list)
        success_count = 0

        for i, mod in enumerate(self.mods_list):
            if self.cancelled:
                self.log.emit("❌ Загрузка отменена")
                break

            self.progress.emit(i, total, mod["file"])
            self.log.emit(f"⬇️ Загрузка: {mod['file']}")

            try:
                success = download_single_mod_turbo_sync(mod, self.minecraft_dir)
                if success:
                    success_count += 1
                    self.log.emit(f"✅ Успешно: {mod['file']}")
                else:
                    self.log.emit(f"❌ Ошибка: {mod['file']}")
            except Exception as e:
                self.log.emit(f"💥 Ошибка {mod['file']}: {str(e)}")

        self.finished.emit(success_count, total)


def download_mods_turbo_ui(mods_list, parent=None):
    """PyQt6 версия загрузки модов с UI"""
    if not mods_list:
        return

    class DownloadProgressDialog(QDialog):
        def __init__(self, parent, mods):
            super().__init__(parent)
            self.mods = mods
            self.setWindowTitle("Загрузка модов")
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
                    background-color: #4a5568;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6b82;
                }
            """)

            layout = QVBoxLayout(self)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            title = QLabel("📥 Загрузка модов")
            title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            self.info_label = QLabel(f"Всего модов: {len(mods)}")
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.info_label)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            layout.addWidget(self.progress_bar)

            self.current_label = QLabel("Подготовка к загрузке...")
            self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.current_label)

            log_label = QLabel("📋 Лог загрузки:")
            log_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
            layout.addWidget(log_label)

            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setFont(QFont("Consolas", 9))
            self.log_text.setMinimumHeight(200)
            layout.addWidget(self.log_text)

            button_layout = QHBoxLayout()
            self.cancel_btn = QPushButton("Отмена")
            self.cancel_btn.clicked.connect(self.cancel_download)
            button_layout.addWidget(self.cancel_btn)

            button_layout.addStretch()

            self.close_btn = QPushButton("Закрыть")
            self.close_btn.clicked.connect(self.accept)
            self.close_btn.setEnabled(False)
            button_layout.addWidget(self.close_btn)

            layout.addLayout(button_layout)

            self.worker = None
            self.start_download()

        def start_download(self):
            self.worker = ModDownloadWorker(self.mods, CONFIG["minecraft_dir"])
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_download_finished)
            self.worker.log.connect(self.add_log)
            self.worker.start()

        def update_progress(self, current, total, mod_name):
            percent = int((current + 1) * 100 / total) if total > 0 else 0
            self.progress_bar.setValue(percent)
            self.current_label.setText(f"Загрузка: {mod_name} ({current + 1}/{total})")

        def add_log(self, message):
            self.log_text.append(message)
            self.log_text.moveCursor(QTextCursor.MoveOperation.End)

        def on_download_finished(self, success_count, total):
            self.progress_bar.setValue(100)
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)

            if success_count == total:
                self.current_label.setText("✅ Все моды успешно загружены!")
                self.add_log(f"\n✅ Успешно загружено {success_count} из {total} модов")
            else:
                self.current_label.setText(f"⚠️ Загружено {success_count} из {total} модов")
                self.add_log(f"\n⚠️ Загружено {success_count} из {total} модов")

        def cancel_download(self):
            if self.worker and self.worker.isRunning():
                self.worker.cancel()
                self.worker.terminate()
                self.worker.wait(1000)
                self.add_log("❌ Загрузка отменена пользователем")
                self.current_label.setText("❌ Загрузка отменена")
                self.cancel_btn.setEnabled(False)
                self.close_btn.setEnabled(True)

    dialog = DownloadProgressDialog(parent, mods_list)
    dialog.exec()


def download_shaders_turbo_ui(shaders_list, parent=None):
    """PyQt6 версия загрузки шейдеров с UI"""
    if not shaders_list:
        return

    class ShaderDownloadWorker(QThread):
        progress = pyqtSignal(int, int, str)
        finished = pyqtSignal(int, int)
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
                    direct_link = get_yandex_direct_link_sync(shader["url"])
                    if not direct_link:
                        self.log.emit(f"❌ Не удалось получить ссылку: {shader['name']}")
                        continue

                    shader_path = os.path.join(shaders_dir, shader["file"])
                    success = download_file_sync(direct_link, shader_path)

                    if success:
                        success_count += 1
                        self.log.emit(f"✅ Успешно: {shader['name']}")

                        if shader["file"].endswith(".zip"):
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
                    background-color: #4a5568;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6b82;
                }
            """)

            layout = QVBoxLayout(self)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            title = QLabel("📥 Загрузка шейдеров")
            title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            self.info_label = QLabel(f"Всего шейдеров: {len(shaders)}")
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.info_label)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            layout.addWidget(self.progress_bar)

            self.current_label = QLabel("Подготовка к загрузке...")
            self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.current_label)

            log_label = QLabel("📋 Лог загрузки:")
            log_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
            layout.addWidget(log_label)

            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setFont(QFont("Consolas", 9))
            self.log_text.setMinimumHeight(200)
            layout.addWidget(self.log_text)

            button_layout = QHBoxLayout()
            self.cancel_btn = QPushButton("Отмена")
            self.cancel_btn.clicked.connect(self.cancel_download)
            button_layout.addWidget(self.cancel_btn)

            button_layout.addStretch()

            self.close_btn = QPushButton("Закрыть")
            self.close_btn.clicked.connect(self.accept)
            self.close_btn.setEnabled(False)
            button_layout.addWidget(self.close_btn)

            layout.addLayout(button_layout)

            self.worker = None
            self.start_download()

        def start_download(self):
            self.worker = ShaderDownloadWorker(self.shaders)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_download_finished)
            self.worker.log.connect(self.add_log)
            self.worker.start()

        def update_progress(self, current, total, shader_name):
            percent = int((current + 1) * 100 / total) if total > 0 else 0
            self.progress_bar.setValue(percent)
            self.current_label.setText(f"Загрузка: {shader_name} ({current + 1}/{total})")

        def add_log(self, message):
            self.log_text.append(message)
            self.log_text.moveCursor(QTextCursor.MoveOperation.End)

        def on_download_finished(self, success_count, total):
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