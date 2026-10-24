# Network/Downloader.py
import os
from Network.proxy_status import proxy_available, mark_proxy_unavailable
import time
import hashlib
import requests
import asyncio
import logging
import zipfile
from Core.mod_transaction import safe_target, validate_jar_or_zip
from pathlib import Path
from ConfDir.Configs import API_KEY
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Только PyQt6 импорты
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from ConfDir.Configs import CONFIG, CURSEFORGE_CONFIG

logger = logging.getLogger(__name__)

def _safe_print(message):
    """Keep diagnostic output from crashing on legacy Windows consoles."""
    try:
        print(message)
    except UnicodeEncodeError:
        try:
            print(str(message).encode("ascii", "backslashreplace").decode("ascii"))
        except Exception:
            logger.info("%s", message)


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
        cached = self.cache.get(public_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        link = await asyncio.to_thread(get_yandex_direct_link_sync, public_key)
        if link:
            self.cache[public_key] = (time.monotonic() + 60, link)
        return link

    async def download_file_async(self, url, file_path, progress_callback=None):
        return await asyncio.to_thread(download_file_sync, url, str(file_path), progress_callback)

    def download_file_sync(self, url, file_path, progress_callback=None):
        return download_file_sync(url, str(file_path), progress_callback)


def get_yandex_direct_link_sync(public_key):
    """Синхронное получение прямой ссылки с Яндекс.Диска"""
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    try:
        response = requests.get(api_url, params={"public_key": public_key}, timeout=30)
        response.raise_for_status()
        link = response.json().get("href")
        if not isinstance(link, str) or not link.startswith(('https://', 'http://')):
            raise ValueError('API Яндекс Диска не вернул ссылку на файл')
        return link
    except Exception as e:
        logger.error(f"Ошибка получения ссылки: {e}")
        return None


def download_file_sync(url, filepath, progress_callback=None):
    temporary = filepath + '.part'
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=60, headers={'Accept-Encoding': 'identity'}) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            # requests decodes HTTP compression; Content-Length describes encoded bytes.
            if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                total_size = 0
            downloaded = 0
            with open(temporary, 'wb') as output:
                for chunk in response.iter_content(8192):
                    if chunk:
                        output.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size:
                            progress_callback(downloaded, total_size)
            if downloaded == 0 or (total_size and downloaded != total_size):
                raise ValueError('Неполная загрузка')
        if filepath.lower().endswith(('.jar', '.zip')):
            if not validate_jar_or_zip(temporary):
                raise ValueError('Повреждённый архив')
        os.replace(temporary, filepath)
        return True
    except Exception as exc:
        logger.error('Ошибка скачивания %s: %s', url, exc)
        return False
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def download_yandex_file_sync(public_url, filepath, source='yandex', progress_callback=None):
    if proxy_available() and download_through_proxy(public_url, filepath, source, progress_callback):
        return True
    public_url = public_url.strip()
    for attempt in range(2):
        direct_link = get_yandex_direct_link_sync(public_url)
        success = (download_file_sync(direct_link, filepath, progress_callback) if progress_callback
                   else download_file_sync(direct_link, filepath)) if direct_link else False
        if success:
            return True
        if attempt == 0:
            logger.info('Повторная попытка Яндекс Диска со свежей ссылкой: %s', public_url)
            time.sleep(0.3)
    logger.error('Не удалось скачать файл Яндекс Диска: %s', public_url)
    return False


def download_single_mod_turbo_sync(mod_info, minecraft_dir, source="yandex", minecraft_version=None, loader=None):
    """
    Синхронная загрузка одного мода
    source: "yandex", "modrinth", "curseforge", "shader", "local"
    """
    import traceback
    logger.info(f"🚀 download_single_mod_turbo_sync: {mod_info.get('name', 'unknown')}")
    try:
        # Определяем имя файла - пробуем разные ключи
        filename = mod_info.get('file') or mod_info.get('filename') or mod_info.get('file_name')
        if not filename:
            # Если нет имени файла, генерируем из названия
            name = mod_info.get('name', 'mod')
            filename = f"{name}.jar"

        _safe_print(f"🔍 Начинаем загрузку мода: {filename} (источник: {source})")

        mods_dir = os.path.join(minecraft_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        file_path = safe_target(mods_dir, filename)

        # 1. Проверяем локальный кэш
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
            _safe_print(f"✅ Мод уже есть: {filename}")
            if not file_path.lower().endswith(('.jar', '.zip')) or validate_jar_or_zip(file_path):
                return True

        # 2. Пробуем через прокси
        use_proxy = proxy_available()

        if use_proxy and source == "local":
            url = mod_info.get('url') or mod_info.get('download_url') or mod_info.get('direct_link')

            if url:
                _safe_print(f"🌐 Прокси: пробуем {filename}")
                if download_through_proxy(url, file_path, source):
                    _safe_print(f"✅ Загружено через прокси: {filename}")
                    return True
                _safe_print(f"⚠️ Прокси не сработал, пробуем прямой метод")

        # 3. Прямая загрузка в зависимости от источника
        if source == "yandex":
            return _download_from_yandex(mod_info, file_path, mods_dir)
        elif source == "modrinth":
            # Передаём minecraft_version и loader дальше
            return _download_from_modrinth(mod_info, file_path, mods_dir, minecraft_version, loader)
        elif source == "curseforge":
            return _download_from_curseforge(mod_info, file_path, mods_dir)
        elif source == "shader":
            return _download_shader(mod_info, file_path)
        else:
            _safe_print(f"❌ Неизвестный источник: {source}")
            return False

    except Exception as e:
        _safe_print(f"❌ Ошибка загрузки мода: {e}")
        return False


def _download_from_yandex(mod_info, file_path, mods_dir):
    """Прямая загрузка с Яндекс.Диска"""
    try:
        url = mod_info.get('url')
        if not url:
            _safe_print(f"❌ Нет URL для Яндекс.Диска")
            return False

        success = download_yandex_file_sync(url, file_path, 'yandex')
        if success and file_path.lower().endswith(('.jar', '.zip')) and not validate_jar_or_zip(file_path):
            try: os.remove(file_path)
            except OSError: pass
            return False

        if success and file_path.endswith(".zip"):
            try:
                import zipfile
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    root = Path(mods_dir).resolve()
                    for member in zip_ref.infolist():
                        if member.is_dir():
                            continue
                        target = (root / member.filename).resolve()
                        if target.parent != root and root not in target.parents:
                            raise ValueError(f"Небезопасный путь в архиве: {member.filename}")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(member) as source, target.open("wb") as output:
                            import shutil
                            shutil.copyfileobj(source, output)
                _safe_print(f"📦 Распакован: {os.path.basename(file_path)}")
            except Exception as e:
                _safe_print(f"⚠️ Ошибка распаковки: {e}")

        return success

    except Exception as e:
        _safe_print(f"❌ Ошибка прямой загрузки Яндекс: {e}")
        return False


def _download_from_modrinth(mod_info, file_path, mods_dir, minecraft_version=None, loader=None):
    """Загрузка с Modrinth"""
    _safe_print(f"🔄 Загрузка Modrinth")
    try:
        from Network.ModrinthLoader import ModrinthAPI

        api = ModrinthAPI()
        mod_id = mod_info.get('modrinth_id') or mod_info.get('project_id')

        if not mod_id:
            _safe_print(f"❌ Нет ID мода для Modrinth")
            return False

        filename = mod_info.get('file') or mod_info.get('filename') or f"{mod_id}.jar"

        # Если minecraft_version и loader не переданы, берём из mod_info
        mc_version = minecraft_version or mod_info.get('minecraft_version', '1.20.1')
        loader_type = loader or mod_info.get('loader', 'fabric')

        _safe_print(f"🔄 Загрузка Modrinth: {mod_id} для {mc_version}/{loader_type}")

        # Передаём minecraft_version и loader в download_mod
        success = api.download_mod(
            project_slug=mod_id,
            version_id=mod_info.get('version_id'),  # может быть None
            filename=filename,
            mods_dir=mods_dir,
            minecraft_version=mc_version,
            loader=loader_type
        )

        if success:
            _safe_print(f"✅ Загрузка Modrinth успешна: {filename}")
            return True

        if mod_info.get("version_id"):
            return False
        # Пробуем альтернативный метод
        _safe_print(f"🔄 Пробуем альтернативную загрузку...")
        from Network.Downloader import download_file_sync
        cdn_url = f"https://cdn.modrinth.com/data/{mod_id}/versions/latest/{filename}"
        return download_file_sync(cdn_url, file_path)

    except Exception as e:
        _safe_print(f"❌ Ошибка прямой загрузки Modrinth: {e}")
        return False


def _download_from_curseforge(mod_info, file_path, mods_dir):
    """Загрузка с CurseForge"""
    try:
        from Network.CurseForgeLoader import CurseForgeAPI
        from ConfDir.Configs import CURSEFORGE_CONFIG

        proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://90.151.59.120:8000")
        api = CurseForgeAPI(proxy_url)

        mod_id = mod_info.get('curseforge_id') or mod_info.get('project_id')
        if not mod_id:
            _safe_print(f"❌ Нет ID мода для CurseForge")
            return False

        filename = mod_info.get('file') or mod_info.get('filename') or f"mod-{mod_id}.jar"
        minecraft_version = mod_info.get('minecraft_version', '1.20.1')
        loader = mod_info.get('loader', 'fabric')

        _safe_print(f"🔄 Загрузка CurseForge: {mod_id} для {minecraft_version}/{loader}")

        pinned = mod_info.get('version_id') or mod_info.get('file_id')
        if pinned:
            # The stored ID and filename are enough to use CurseForge's public CDN.
            version_id = pinned
        else:
            versions = api.get_mod_versions(str(mod_id), minecraft_version, loader)
            if not versions:
                return False
            version_id = versions[0]['id']

        # Скачиваем через метод CurseForgeAPI
        success = api.download_mod(str(mod_id), version_id, filename, mods_dir)

        if success:
            _safe_print(f"✅ Загрузка CurseForge успешна: {filename}")
            return True

        return False

    except Exception as e:
        _safe_print(f"❌ Ошибка прямой загрузки CurseForge: {e}")
        return False


def _download_shader(mod_info, file_path):
    url = mod_info.get('url')
    return bool(url and download_yandex_file_sync(url, file_path, 'shader'))


def download_single_mod_turbo(mod_info, minecraft_dir):
    """Compatibility entry point using the same route as the UI downloader."""
    return download_single_mod_turbo_sync(mod_info, minecraft_dir, source=mod_info.get('source', 'yandex'),
                                          minecraft_version=mod_info.get('minecraft_version'),
                                          loader=mod_info.get('loader'))


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
                self.worker.wait(5000)
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
            from Core.instances import ensure_game_directory
            shaders_dir = os.path.join(ensure_game_directory(), "shaderpacks")
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
                    shader_path = safe_target(shaders_dir, shader['file'])
                    success = download_yandex_file_sync(shader['url'], shader_path, 'shader')

                    if success:
                        success_count += 1
                        self.log.emit(f"✅ Успешно: {shader['name']}")

                        # Shader packs are loaded directly from their ZIP files.
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
                self.worker.wait(5000)
                self.add_log("❌ Загрузка отменена пользователем")
                self.current_label.setText("❌ Загрузка отменена")
                self.cancel_btn.setEnabled(False)
                self.close_btn.setEnabled(True)

    dialog = ShaderProgressDialog(parent, shaders_list)
    dialog.exec()


def download_through_proxy(url: str, filepath: str, source: str = "unknown", progress_callback=None) -> bool:
    """
    Универсальная загрузка файла через прокси-сервер
    source: "yandex", "curseforge", "modrinth", "shader", "unknown"
    """
    if not proxy_available():
        return False
    try:
        from ConfDir.Configs import CURSEFORGE_CONFIG
        import requests
        import os

        proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://90.151.59.120:8000")
        proxy_endpoint = f"{proxy_url}/api/v1/mirror/download"

        payload = {
            "url": url,
            "filename": os.path.basename(filepath),
            "source": source,
            "file_type": "shader" if source == "shader" else "mod"
        }

        # Для Modrinth добавляем дополнительную информацию
        if source == "modrinth":
            # Из URL можно извлечь project_id и version_id
            # https://cdn.modrinth.com/data/.../versions/.../file.jar
            pass

        # Для CurseForge добавляем ID
        if source == "curseforge":
            # Прокси сам разберётся
            pass

        _safe_print(f"🌐 Прокси: загрузка {os.path.basename(filepath)} через {source}")

        response = requests.post(
            proxy_endpoint,
            json=payload,
            timeout=60,
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY}
        )

        if response.status_code == 200:
            content = response.content
            if not content:
                raise ValueError('Прокси вернул пустой файл')
            temporary = filepath + '.proxy.part'
            try:
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                with open(temporary, 'wb') as stream:
                    stream.write(content)
                    if progress_callback:
                        progress_callback(len(content), len(content))
                if filepath.lower().endswith(('.jar', '.zip')):
                    with zipfile.ZipFile(temporary) as archive:
                        if archive.testzip() is not None:
                            raise ValueError('Прокси вернул повреждённый архив')
                elif response.headers.get('Content-Type', '').startswith(('text/html', 'application/json')):
                    raise ValueError('Прокси вернул страницу ошибки вместо файла')
                os.replace(temporary, filepath)
                return True
            finally:
                if os.path.exists(temporary):
                    os.remove(temporary)

        if response.status_code >= 500:
            mark_proxy_unavailable()
        return False

    except requests.RequestException as exc:
        mark_proxy_unavailable()
        logger.debug('Proxy unavailable: %s', exc)
        return False
    except (ValueError, zipfile.BadZipFile) as e:
        mark_proxy_unavailable()
        _safe_print(f"❌ Прокси: ошибка - {e}")
        return False
    except Exception as e:
        _safe_print(f"❌ Прокси: ошибка - {e}")
        return False
