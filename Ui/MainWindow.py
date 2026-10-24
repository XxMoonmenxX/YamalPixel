## Ui/MainWindow.py - исправленная версия с работающим фоном

import os
import sys
import threading
import time
import json
import subprocess
import zipfile
import shutil
import logging
import re
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QApplication,
    QMessageBox, QProgressBar, QTextEdit, QFrame, QComboBox,
    QMenuBar, QMenu, QDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QSpinBox, QGroupBox, QScrollArea, QFileDialog
)

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QMetaObject, Q_ARG, pyqtSlot, QObject
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QBrush, QColor, QFontDatabase

# Импорты из проекта
from ConfDir.Configs import CONFIG, RESOURCE_DIR, RESOURCES, SHADERS_CONFIG, get_minecraft_version, \
    version_configs, messages, CURSEFORGE_CONFIG, set_window_icon, setup_environment, resource_path
from ConfDir.Versions import version_configs, fabric_supported_versions, neoforge_supported_versions, all_versions, \
    CURRENT_VERSION, quilt_supported_versions, forge_supported_versions, get_all_versions
from ConfDir.ScaleRes import RESOLUTION_MAP, ratios, resolution_ratios, backgrounds, find_closest_resolution
from ConfDir.utils import aggressive_clean_name, calculate_similarity, extract_core_name, MANUAL_MOD_MAPPINGS, \
    COLLECTIONS_CONFIG

from Core.run import is_game_running, set_current_collection, get_current_collection

from Network.proxy_status import start_proxy_probe
from Network.Updates import check_for_updates_local
from Network.Downloader import download_single_mod_turbo_sync, download_mods_turbo_ui, TurboDownloader, LauncherCache
from Network.ModrinthLoader import ModrinthAPI
from Network.CurseForgeLoader import CurseForgeAPI

from Network.shader_manager import show_shader_manager
from Network.Downloader import download_shaders_turbo_ui

from Ui.DependencyAnalyzer import DependencyAnalyzerUI
from Ui.BaseWindow import BaseMainWindow

import MCLIB
import requests

logger = logging.getLogger("YamalPixel.MainWindow")

# Глобальные переменные для состояния
LAUNCH_IN_PROGRESS = False
LAUNCH_START_TIME = None

from ConfDir.Versions import get_all_versions

ALL_VERSIONS = get_all_versions()


def create_backup(folder_path, backup_type):
    """Создает zip-бэкап указанной папки"""
    try:
        print(f"🔄 Создаем бэкап {backup_type} из: {folder_path}")

        if not os.path.exists(folder_path):
            print(f"❌ Папка {folder_path} не существует")
            return None

        files_in_folder = []
        if os.path.exists(folder_path):
            for root, dirs, files in os.walk(folder_path):
                files_in_folder.extend(files)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(CONFIG["minecraft_dir"], "backups")
        os.makedirs(backup_dir, exist_ok=True)

        backup_filename = f"{backup_type}_backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if os.path.exists(folder_path) and files_in_folder:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            arcname = os.path.relpath(file_path, folder_path)
                            zipf.write(file_path, arcname)

        print(f"✅ Создан бэкап {backup_type}: {backup_path}")
        return backup_path

    except Exception as e:
        print(f"❌ Ошибка создания бэкапа {backup_type}: {str(e)}")
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


def check_fabric_installed():
    """Проверяет установлен ли Fabric"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        versions_dir = os.path.join(minecraft_dir, "versions")
        fabric_version = f"fabric-loader-{CONFIG['fabric_loader']}-{CONFIG['version']}"
        fabric_version_dir = os.path.join(versions_dir, fabric_version)
        return os.path.exists(fabric_version_dir)
    except:
        return False


def check_quilt_installed():
    """Проверяет установлен ли Quilt"""
    try:
        minecraft_dir = CONFIG["minecraft_dir"]
        versions_dir = os.path.join(minecraft_dir, "versions")
        installed_versions = MCLIB.utils.get_installed_versions(minecraft_dir)
        for version in installed_versions:
            if version["id"].startswith("quilt-loader-"):
                return True
        return False
    except:
        return False


def install_fabric_silent():
    """Тихая установка Fabric"""
    try:
        print("🔧 Устанавливаем Fabric...")
        MCLIB.fabric.install_fabric(
            minecraft_version=CONFIG["version"],
            loader_version=CONFIG["fabric_loader"],
            minecraft_directory=CONFIG["minecraft_dir"],
        )
        print("✅ Fabric установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Fabric: {e}")
        return False


def install_quilt_silent():
    """Тихая установка Quilt"""
    try:
        print("🔧 Устанавливаем Quilt...")
        MCLIB.quilt.install_quilt(
            minecraft_version=CONFIG["version"],
            loader_version=None,
            minecraft_directory=CONFIG["minecraft_dir"],
        )
        print("✅ Quilt установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Quilt: {e}")
        return False


def check_forge_installed(minecraft_version, minecraft_directory):
    """Проверяет установлен ли Forge"""
    try:
        versions_dir = os.path.join(minecraft_directory, "versions")
        for folder in os.listdir(versions_dir):
            folder_lower = folder.lower()
            if ("forge" in folder_lower) and minecraft_version in folder_lower:
                json_path = os.path.join(versions_dir, folder, f"{folder}.json")
                if os.path.exists(json_path):
                    return True
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке Forge: {e}")
        return False


def download_single_mod_turbo_wrapper(self, mod):
    """Обертка для загрузки одного мода"""
    try:
        return download_single_mod_turbo_sync(mod, CONFIG["minecraft_dir"])
    except Exception as e:
        print(f"Ошибка загрузки мода {mod.get('file', 'unknown')}: {e}")
        return False


class ServerStatusWorker(QThread):
    """Поток для проверки статуса сервера"""

    finished = pyqtSignal(dict)  # результат
    error = pyqtSignal(str)  # ошибка

    def run(self):
        try:
            from mcstatus import JavaServer
            server = JavaServer.lookup("90.151.59.120:25565")
            status = server.status()

            result = {
                "online": status.players.online,
                "max": status.players.max,
                "latency": status.latency,
                "version": status.version.name,
                "success": True
            }
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class BugreportWorker(QThread):
    ready = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, parent=None, minecraft_dir=None):
        super().__init__(parent)
        self.minecraft_dir = minecraft_dir

    def run(self):
        try:
            from Core.bugreport import create_bugreport
            self.ready.emit(create_bugreport(minecraft_dir=self.minecraft_dir))
        except Exception as exc:
            logger.exception('Создание Bugreport.txt')
            self.failed.emit(str(exc))


class MessageDialog(QMessageBox):
    """Диалог с поддержкой русского текста"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Segoe UI", 10))

    @staticmethod
    def show_info(parent, title, text):
        dialog = MessageDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setText(text)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()

    @staticmethod
    def show_warning(parent, title, text):
        dialog = MessageDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setText(text)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.exec()

    @staticmethod
    def show_error(parent, title, text):
        dialog = MessageDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setText(text)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.exec()

    @staticmethod
    def show_question(parent, title, text):
        dialog = MessageDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setText(text)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return dialog.exec()


class LaunchWorker(QThread):
    progress = pyqtSignal(str, str)
    completed = pyqtSignal(bool)

    def __init__(self, version, username, parent=None):
        super().__init__(parent)
        self.version = version
        self.username = username

    def run(self):
        from Core.run import run_game_launch
        try:
            success = run_game_launch(self.version, self.username, self.progress.emit)
        except Exception as exc:
            self.progress.emit('error', str(exc))
            success = False
        self.completed.emit(success)


class VersionCatalogWorker(QObject):
    ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread = None
        self.cancelled = threading.Event()

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def isRunning(self):
        return self.thread is not None and self.thread.is_alive()

    def requestInterruption(self):
        self.cancelled.set()

    def run(self):
        from ConfDir.Versions import refresh_catalog
        try:
            result = refresh_catalog()
            if not self.cancelled.is_set():
                self.ready.emit(result)
        except Exception as exc:
            if not self.cancelled.is_set():
                self.error.emit(str(exc))


class MainWindow(QMainWindow):
    """Главное окно лаунчера на PyQt6"""

    def __init__(self):
        super().__init__()
        start_proxy_probe()

        # Загружаем шрифты, поддерживающие кириллицу
        self.load_fonts()

        # Настройка окна
        self.setWindowTitle(f"YamalPixel Launcher v{CURRENT_VERSION}")
        self.setMinimumSize(1200, 800)

        # ВАЖНО: Делаем фон окна прозрачным для отображения фонового изображения
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(self._get_stylesheet())

        # Центральный виджет - делаем прозрачным
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        central.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Верхняя панель - с полупрозрачным фоном
        top_panel = QWidget()
        top_panel.setFixedHeight(60)
        top_panel.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.6);
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 15px;
        """)
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(20, 10, 20, 10)

        # Логотип
        self.logo_label = QLabel("YamalPixel")
        self.logo_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.logo_label.setStyleSheet("color: #4ECDC4; background-color: transparent;")
        top_layout.addWidget(self.logo_label)

        top_layout.addStretch()

        # Чекбокс музыки
        self.music_checkbox = QCheckBox("Музыка")
        self.music_checkbox.setFont(QFont("Segoe UI", 11))
        self.music_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #4ECDC4;
                border: 1px solid #4ECDC4;
            }
            QCheckBox::indicator:unchecked {
                background-color: #555;
                border: 1px solid #666;
            }
        """)
        self.music_checkbox.toggled.connect(self.toggle_music)
        top_layout.addWidget(self.music_checkbox)

        # Чекбокс полноэкранного режима
        self.fullscreen_checkbox = QCheckBox("Полный экран")
        self.fullscreen_checkbox.setFont(QFont("Segoe UI", 11))
        self.fullscreen_checkbox.setStyleSheet(self.music_checkbox.styleSheet())
        self.fullscreen_checkbox.toggled.connect(self.toggle_fullscreen)
        top_layout.addWidget(self.fullscreen_checkbox)

        # Кнопка закрытия
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4757;
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        top_layout.addWidget(self.close_btn)

        main_layout.addWidget(top_panel)

        # Контентная область с фоном
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)

        # Карточка с формой - полупрозрачная
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.65);
                border-radius: 30px;
                padding: 30px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)

        # Приветствие
        welcome_label = QLabel("Добро пожаловать в YamalPixel!")
        welcome_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("background-color: transparent; color: #ffffff;")
        card_layout.addWidget(welcome_label)

        # Поле ввода ника
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите никнейм")
        self.username_input.setMaximumWidth(400)
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_input.setFont(QFont("Segoe UI", 12))
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 25px;
                padding: 12px 20px;
            }
            QLineEdit:focus {
                border: 2px solid #4ECDC4;
            }
        """)
        username_layout = QHBoxLayout()
        username_layout.addStretch()
        username_layout.addWidget(self.username_input)
        username_layout.addStretch()
        card_layout.addLayout(username_layout)

        # Селектор версий
        self.version_combo = QComboBox()
        self.version_combo.setMaximumWidth(400)
        self.version_combo.setFont(QFont("Segoe UI", 11))
        self.version_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 25px;
                padding: 12px 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: white;
                selection-background-color: #4ECDC4;
            }
        """)
        self.refresh_versions()
        self.version_combo.currentTextChanged.connect(self.on_version_changed)
        version_layout = QHBoxLayout()
        version_layout.addStretch()
        version_layout.addWidget(self.version_combo)
        version_layout.addStretch()
        card_layout.addLayout(version_layout)
        self.beta_checkbox = QCheckBox("Показывать бета версии")
        self.beta_checkbox.setChecked(CONFIG.get('show_beta_versions', False))
        self.beta_checkbox.setStyleSheet("color: #b5cadb; background: transparent;")
        self.beta_checkbox.toggled.connect(self.on_beta_changed)
        card_layout.addWidget(self.beta_checkbox, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Кнопка запуска
        self.launch_btn = QPushButton("ВОЙТИ В ИГРУ")
        self.launch_btn.setFixedSize(300, 60)
        self.launch_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.launch_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #4ECDC4);
                color: white;
                border: none;
                border-radius: 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff8585, stop:1 #6ad5cb);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e05555, stop:1 #3db5ab);
            }
        """)
        self.launch_btn.clicked.connect(self.launch_game)
        launch_layout = QHBoxLayout()
        launch_layout.addStretch()
        launch_layout.addWidget(self.launch_btn)
        launch_layout.addStretch()
        card_layout.addLayout(launch_layout)

        # Кнопка онлайна
        self.online_btn = QPushButton("Показать онлайн")
        self.online_btn.setFixedSize(250, 45)
        self.online_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.online_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A90E2, stop:1 #357ABD);
                color: white;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5aa0f2, stop:1 #458acd);
            }
        """)
        self.online_btn.clicked.connect(self.show_online_players)
        online_layout = QHBoxLayout()
        online_layout.addStretch()
        online_layout.addWidget(self.online_btn)
        online_layout.addStretch()
        card_layout.addLayout(online_layout)

        # Статус
        self.status_label = QLabel("Готов к запуску")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("background-color: transparent; color: #00ff88;")
        card_layout.addWidget(self.status_label)
        self.launch_progress = QProgressBar()
        self.launch_progress.setRange(0, 100)
        self.launch_progress.setStyleSheet('QProgressBar { background: #102033; color: white; border-radius: 7px; text-align: center; min-height: 18px; } QProgressBar::chunk { background: #4ecdc4; border-radius: 7px; }')
        self.launch_progress.hide()
        card_layout.addWidget(self.launch_progress)
        self.game_log_button = QPushButton('Лог запуска Minecraft')
        self.game_log_button.setEnabled(False)
        self.game_log_button.clicked.connect(self.show_game_log)
        card_layout.addWidget(self.game_log_button)
        self.game_log_reader = None
        self.game_log_dialog = None
        self.game_loading_started = None

        content_layout.addStretch()
        content_layout.addWidget(card)
        content_layout.addStretch()

        main_layout.addWidget(content_widget)

        # Меню
        self.create_menu()

        # Загрузка фона (после инициализации всех виджетов)
        self.load_background()

        # Загрузка сессии
        self.load_session()
        from Core.instances import select_instance
        select_instance(self.version_combo.currentText())
        self.version_combo.currentTextChanged.connect(select_instance)

        # Таймер для обновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)

        # Музыка (не включается автоматически)
        self.init_music()

        # Discord RPC
        self.init_discord_rpc()

        # Рабочий поток для сетевых операций
        self.worker_thread = None
        self.launch_worker = None
        self.crash_worker = None
        self.game_event_timer = QTimer(self)
        self.game_event_timer.timeout.connect(self.check_game_events)
        self.game_event_timer.start(700)
        self.catalog_worker = VersionCatalogWorker(self)
        self.catalog_worker.ready.connect(self.on_catalog_ready)
        self.catalog_worker.error.connect(self.on_catalog_error)
        self.catalog_worker.start()

        # Проверяем java
        self.check_java_on_startup()

    def check_java_on_startup(self):
        """Java is resolved for the selected game at launch, including bundled runtimes."""
        # A global Java 17 check misses bundled runtimes and other game versions.
        return

    @pyqtSlot(str, str)
    def _show_error_dialog(self, title: str, message: str):
        """Показывает диалог ошибки (вызывается из основного потока)"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)

    @pyqtSlot()
    def _show_java_dialog(self):
        """Показывает диалог установки Java (вызывается из основного потока)"""
        self.open_java_manager()

    def open_java_manager(self, checked=False, minecraft_version=None, minecraft_dir=None):
        from Ui.JavaManager import JavaManagerDialog
        from ConfDir.Versions import get_version_config
        config = get_version_config(self.version_combo.currentText())
        dialog = JavaManagerDialog(self, minecraft_dir or CONFIG['minecraft_dir'],
                                   minecraft_version or (config[0] if config else None))
        dialog.exec()

    def selected_game_directory(self, create=False):
        from Core.instances import ensure_game_directory, game_directory
        version = self.version_combo.currentText()
        return ensure_game_directory(version) if create else str(game_directory(version))

    def check_game_events(self):
        self.update_game_log()
        from Core.run import poll_game_events
        for analysis in poll_game_events():
            if analysis.get('crashed'):
                self.show_crash_result(analysis)

    def show_game_log(self):
        if self.game_log_dialog:
            self.game_log_dialog.show()
            self.game_log_dialog.raise_()
            self.game_log_dialog.activateWindow()

    def update_game_log(self):
        if self.game_log_reader is None:
            return
        from Core.game_log import loading_stage
        text = self.game_log_reader.read()
        if text:
            self.game_log_dialog.append_text(text)
            stage = loading_stage(text)
            if stage:
                self.status_label.setText('Minecraft: ' + stage)
        if is_game_running():
            elapsed = max(0, int(time.monotonic() - self.game_loading_started))
            self.launch_progress.setFormat(f'Minecraft работает · {elapsed // 60}:{elapsed % 60:02d} · подробности в логе')
        else:
            if not self.game_log_reader.at_end:
                return
            self.launch_progress.setRange(0, 100)
            self.launch_progress.setValue(100)
            self.launch_progress.setFormat('Процесс Minecraft завершён — лог сохранён')
            self.status_label.setText('Minecraft завершился; при вылете выполняется анализ логов')
            self.game_log_reader = None

    def show_crash_result(self, analysis):
        from Ui.CrashAnalysis import CrashAnalysisDialog
        self.crash_dialog = CrashAnalysisDialog(analysis, analysis.get('minecraft_dir', CONFIG['minecraft_dir']), self)
        self.crash_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.crash_dialog.java_requested.connect(lambda: self.open_java_manager(
            minecraft_version=analysis.get('minecraft'), minecraft_dir=analysis.get('shared_dir', CONFIG['minecraft_dir'])))
        self.crash_dialog.bugreport_requested.connect(
            lambda: self.save_bugreport(minecraft_dir=analysis.get('minecraft_dir')))
        self.crash_dialog.show()

    def analyze_last_crash(self, checked=False, log_file=None):
        if self.crash_worker and self.crash_worker.isRunning():
            return
        from Ui.CrashAnalysis import CrashAnalysisWorker
        self.crash_worker = CrashAnalysisWorker(self.selected_game_directory(), log_file, self)
        self.crash_action.setEnabled(False)
        self.crash_worker.ready.connect(self.show_crash_result)
        self.crash_worker.failed.connect(lambda error: MessageDialog.show_error(self, 'Анализ вылета', error))
        self.crash_worker.finished.connect(lambda: self.crash_action.setEnabled(True))
        self.crash_worker.start()

    def analyze_crash_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Выбрать лог или отчёт Minecraft',
                                            os.path.join(self.selected_game_directory(), 'logs'),
                                            'Логи и отчёты (*.log *.txt);;Все файлы (*)')
        if path:
            self.analyze_last_crash(log_file=path)

    def load_fonts(self):
        """Загружает шрифты, поддерживающие кириллицу"""
        font_families = [
            "Segoe UI",
            "Microsoft YaHei",
            "Arial",
            "Tahoma",
            "Verdana",
            "DejaVu Sans",
            "Liberation Sans"
        ]

        for family in font_families:
            if family in QFontDatabase.families():
                self.default_font_family = family
                break
        else:
            self.default_font_family = "Arial"

        print(f"Используется шрифт: {self.default_font_family}")

    def _get_stylesheet(self) -> str:
        """Стилизация главного окна - фон прозрачный, так как картинка будет через QPalette"""
        return """
            QMainWindow {
                background-color: transparent;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QMenuBar {
                background-color: rgba(0, 0, 0, 0.5);
                color: white;
            }
            QMenuBar::item {
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #4ECDC4;
            }
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #4ECDC4;
            }
            QMenu::item:selected {
                background-color: #4ECDC4;
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
                background-color: transparent;
            }
            QMessageBox QPushButton {
                background-color: #4a5568;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #5a6b82;
            }
        """

    def load_background(self):
        """Загружает фон из папки пользователя"""
        try:
            from ConfDir.ScaleRes import (
                find_closest_resolution,
                get_background_path,
                ensure_backgrounds_folder,
                USER_YAMALPIXEL_RES
            )

            # Создаем папку для фонов если её нет
            ensure_backgrounds_folder()

            # Получаем размер окна
            window_width = self.width()
            window_height = self.height()

            print(f"🎨 Загрузка фона для окна {window_width}x{window_height}")

            # Выбираем фон под соотношение сторон
            bg_file = find_closest_resolution(window_width, window_height)

            # Получаем путь к файлу фона
            bg_path = get_background_path(bg_file)

            # Если конкретный файл не найден, пробуем найти любой PNG в папке пользователя
            if not bg_path:
                print("🔍 Ищем любой доступный фон...")
                if os.path.exists(USER_YAMALPIXEL_RES):
                    for file in os.listdir(USER_YAMALPIXEL_RES):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            bg_path = os.path.join(USER_YAMALPIXEL_RES, file)
                            print(f"✅ Найден альтернативный фон: {file}")
                            break

            if bg_path and os.path.exists(bg_path):
                pixmap = QPixmap(bg_path)
                if not pixmap.isNull():
                    # Масштабируем под размер окна с сохранением пропорций
                    scaled_pixmap = pixmap.scaled(
                        window_width,
                        window_height,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )

                    # Устанавливаем фон для центрального виджета
                    palette = self.centralWidget().palette()
                    palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
                    self.centralWidget().setPalette(palette)
                    self.centralWidget().setAutoFillBackground(True)
                    print(f"✅ Фон успешно установлен!")
                    return
                else:
                    print(f"❌ Не удалось загрузить изображение: {bg_path}")
            else:
                print(f"❌ Фоновые изображения не найдены в: {USER_YAMALPIXEL_RES}")
                print(f"💡 Положите файлы PNG в папку: {USER_YAMALPIXEL_RES}")

            # Fallback - градиентный фон
            print("🎨 Устанавливаем градиентный фон (fallback)")
            self.centralWidget().setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1a1a2e, 
                        stop:0.3 #16213e, 
                        stop:0.6 #0f3460, 
                        stop:1 #1a1a2e);
                }
            """)

        except Exception as e:
            print(f"❌ Ошибка загрузки фона: {e}")
            import traceback
            traceback.print_exc()

            # Устанавливаем темный фон при ошибке
            self.centralWidget().setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1a1a2e, stop:1 #0f3460);
                }
            """)

    def resizeEvent(self, event):
        """При изменении размера окна перезагружаем фон"""
        super().resizeEvent(event)
        self.load_background()

    def refresh_versions(self):
        current = self.version_combo.currentText()
        selected = current or getattr(self, '_saved_version', '')
        items = get_all_versions(CONFIG.get('show_beta_versions', False))
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        self.version_combo.addItems(items)
        if selected in items:
            self.version_combo.setCurrentText(selected)
        self.version_combo.blockSignals(False)

    @pyqtSlot(bool)
    def on_beta_changed(self, checked):
        CONFIG['show_beta_versions'] = checked
        self.refresh_versions()

    @pyqtSlot(list)
    def on_catalog_ready(self, failed_loaders):
        self.refresh_versions()
        if failed_loaders:
            self.status_label.setText('Версии обновлены; временно недоступны: ' + ', '.join(failed_loaders))
        elif not (self.launch_worker and self.launch_worker.isRunning()):
            self.status_label.setText('Каталог версий обновлён')

    @pyqtSlot(str)
    def on_catalog_error(self, message):
        self.status_label.setText('Нет связи с каталогом — доступны сохранённые версии')
        logger.warning('Обновление каталога: %s', message)

    def on_version_changed(self, version):
        pass

    def launch_game(self):
        self.run_game_launch(self.version_combo.currentText(), self.username_input.text().strip())

    def run_game_launch(self, selected_version, username):
        if self.launch_worker and self.launch_worker.isRunning():
            return
        valid, message = self.validate_username(username)
        if not valid:
            MessageDialog.show_warning(self, 'Ошибка', message)
            return
        if is_game_running():
            MessageDialog.show_warning(self, 'Предупреждение', 'Игра уже запущена!')
            return
        self.launch_btn.setEnabled(False)
        self.launch_progress.setRange(0, 0)
        self.launch_progress.show()
        self.online_btn.setEnabled(False)
        self.version_combo.setEnabled(False)
        self.beta_checkbox.setEnabled(False)
        self.status_label.setText('Подготовка к запуску…')
        self.launch_worker = LaunchWorker(selected_version, username, self)
        self.launch_worker.progress.connect(self.on_launch_progress)
        self.launch_worker.completed.connect(self.on_launch_completed)
        self.launch_worker.start()

    @pyqtSlot(str, str)
    def on_launch_progress(self, kind, message):
        if kind == 'progress':
            self.launch_progress.setRange(0, 100)
            self.launch_progress.setValue(max(0, min(100, int(message))))
            return
        self.status_label.setText(message)
        color = '#ff7272' if kind == 'error' else '#65dec9' if kind == 'success' else '#f0c875'
        self.status_label.setStyleSheet(f'background: transparent; color: {color};')
        if kind == 'error':
            self._show_error_dialog('Ошибка запуска', message)

    @pyqtSlot(bool)
    def on_launch_completed(self, success):
        if success:
            from Core.run import GAME_PROCESS
            from Core.game_log import GameLogReader
            from Ui.GameLog import GameLogDialog
            context = getattr(GAME_PROCESS, '_yamal_context', {})
            path = context.get('java_console')
            if isinstance(path, str) and path:
                if self.game_log_dialog is None:
                    self.game_log_dialog = GameLogDialog(self)
                self.game_log_dialog.start_session(path)
                self.game_log_reader = GameLogReader(path)
                self.game_loading_started = time.monotonic()
                self.game_log_button.setEnabled(True)
                self.launch_progress.setRange(0, 0)
                self.launch_progress.setTextVisible(True)
                self.launch_progress.show()
                self.update_game_log()
        else:
            self.launch_progress.hide()
        self.launch_btn.setEnabled(True)
        self.online_btn.setEnabled(True)
        self.version_combo.setEnabled(True)
        self.beta_checkbox.setEnabled(True)

    @pyqtSlot(str, str)
    def _show_info_dialog(self, title, message):
        MessageDialog.show_info(self, title, message)

    def validate_username(self, username):
        """Проверяет корректность имени пользователя"""
        if not username or username == "Введите никнейм":
            return False, "Имя пользователя не может быть пустым"

        if len(username) < 3 or len(username) > 16:
            return False, "Длина имени должна быть от 3 до 16 символов"

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Имя может содержать только буквы, цифры и _"

        return True, "OK"

    def show_online_players(self):
        """Показывает онлайн игроков"""
        self.status_label.setText("Проверка статуса сервера...")
        self.status_label.setStyleSheet("background-color: transparent; color: #ffaa00;")
        self.online_btn.setEnabled(False)

        self.worker_thread = ServerStatusWorker()
        self.worker_thread.finished.connect(self.on_server_status_finished)
        self.worker_thread.error.connect(self.on_server_status_error)
        self.worker_thread.start()

    def on_server_status_finished(self, result):
        self.online_btn.setEnabled(True)
        self.status_label.setText("Готов к запуску")
        self.status_label.setStyleSheet("background-color: transparent; color: #00ff88;")

        players_online = result["online"]
        max_players = result["max"]

        msg = "Статус сервера\n\n"
        if players_online > 0:
            msg += "Сервер онлайн\n"
        else:
            msg += "Сервер пуст\n"
        msg += f"Игроков: {players_online}/{max_players}\n"
        msg += f"Пинг: {result['latency']:.1f} мс\n"
        msg += f"Версия: {result['version']}"

        MessageDialog.show_info(self, "Статус сервера", msg)

    def on_server_status_error(self, error_msg):
        self.online_btn.setEnabled(True)
        self.status_label.setText("Готов к запуску")
        self.status_label.setStyleSheet("background-color: transparent; color: #00ff88;")
        MessageDialog.show_warning(self, "Ошибка", f"Сервер недоступен: {error_msg}")

    def init_music(self):
        """Инициализация музыки"""
        try:
            from pygame import mixer
            mixer.init()
            music_path = RESOURCE_DIR / "menu_song.mp3"
            if not music_path.exists():
                music_path = Path(resource_path('YamalPixelRes/menu_song.mp3'))
            if music_path.exists():
                mixer.music.load(str(music_path))
                mixer.music.set_volume(0.1)
                self.mixer = mixer
                self.music_playing = False
            else:
                self.mixer = None
                self.music_playing = False
        except Exception as e:
            print(f"Ошибка инициализации музыки: {e}")
            self.mixer = None
            self.music_playing = False

    def toggle_music(self, checked):
        """Включение/выключение музыки"""
        if hasattr(self, 'mixer') and self.mixer:
            if checked:
                self.mixer.music.play(-1)
                self.music_playing = True
            else:
                self.mixer.music.stop()
                self.music_playing = False

    def toggle_fullscreen(self, checked):
        """Полноэкранный режим"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
        # После смены режима обновляем фон
        QTimer.singleShot(100, self.load_background)

    def init_discord_rpc(self):
        """Инициализация Discord RPC"""
        try:
            from pypresence import Presence
            self.rpc = Presence("1349070276327116890")
            self.rpc.connect()
            self.rpc.update(
                state="В меню",
                details=f"YamalPixel {CURRENT_VERSION}",
                large_image="logo",
                start=int(time.time())
            )
        except Exception as e:
            print(f"Discord RPC error: {e}")
            self.rpc = None

    def update_status(self):
        """Обновляет статус"""
        try:
            from Network.proxy_status import proxy_available
            if not proxy_available():
                self.status_label.setText('⚠️ Прокси-сервер недоступен. Загрузка идет напрямую (может быть медленнее).')
                self.status_label.setStyleSheet('background: transparent; color: #ffaa00;')
        except Exception:
            pass
        if hasattr(self, 'rpc') and self.rpc:
            try:
                self.rpc.update()
            except:
                pass

    def create_menu(self):
        """Создает меню"""
        menubar = self.menuBar()
        menubar.setFont(QFont("Segoe UI", 10))
        menubar.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")

        # Меню Инструменты
        tools_menu = menubar.addMenu("Инструменты")

        # Шейдеры
        shaders_action = tools_menu.addAction("Скачать шейдеры")
        shaders_action.triggered.connect(self.download_shaders)

        tools_menu.addSeparator()

        # Папка с игрой
        folder_action = tools_menu.addAction("Открыть папку с игрой")
        folder_action.triggered.connect(self.open_game_folder)

        # Запуск без модов
        no_mods_action = tools_menu.addAction("Запуск без модов")
        no_mods_action.triggered.connect(self.launch_without_mods)
        restore_mods_action = tools_menu.addAction("Вернуть отключённые моды")
        restore_mods_action.triggered.connect(self.restore_disabled_mods)

        tools_menu.addSeparator()

        # Бэкапы
        backup_action = tools_menu.addAction("Сделать бэкап")
        backup_action.triggered.connect(self.create_backup)

        backup_info_action = tools_menu.addAction("Показать бэкапы")
        backup_info_action.triggered.connect(self.show_backup_info)

        delete_backups_action = tools_menu.addAction("Удалить все бэкапы")
        delete_backups_action.triggered.connect(self.delete_all_backups)

        tools_menu.addSeparator()

        # Сборки модов
        collections_menu = tools_menu.addMenu("📦 Сборки модов")

        manager_action = collections_menu.addAction("Менеджер сборок")
        manager_action.triggered.connect(self.show_collection_manager)

        tools_menu.addSeparator()

        # Переустановка
        reinstall_action = tools_menu.addAction("Восстановить выбранную сборку")
        reinstall_action.triggered.connect(self.complete_reinstall)

        tools_menu.addSeparator()

        # Диагностика
        diagnostic_action = tools_menu.addAction("Диагностика проблем")
        diagnostic_action.triggered.connect(self.show_diagnostic)
        #self.crash_action = tools_menu.addAction('Разобрать последний вылет')
        #self.crash_action.triggered.connect(self.analyze_last_crash)
        #crash_file_action = tools_menu.addAction('Разобрать файл лога…')
        #crash_file_action.triggered.connect(self.analyze_crash_file)
        #self.bugreport_action = tools_menu.addAction("Сохранить полный Bugreport.txt")

        #self.bugreport_action.triggered.connect(self.save_bugreport)

        # Фон
        bg_action = tools_menu.addAction("Выбрать фон")
        bg_action.triggered.connect(self.select_background)

        # Настройки
        settings_action = tools_menu.addAction("Настройки")
        settings_action.triggered.connect(self.open_settings)

        # Меню Справка
        help_menu = menubar.addMenu("Справка")

        about_action = help_menu.addAction("О лаунчере")
        about_action.triggered.connect(self.show_about)

        update_action = help_menu.addAction("Проверить обновления")
        update_action.triggered.connect(self.check_updates)

        guide_menu = menubar.addMenu('Гайд')
        guide_action = guide_menu.addAction('Открыть гайд по лаунчеру')
        guide_action.setShortcut('F1')
        guide_action.triggered.connect(self.show_guide)

    def open_repair_dialog(self):
        from Ui.RepairDialog import RepairDialog
        dialog = RepairDialog(CONFIG.get('minecraft_dir', ''), self)
        dialog.exec()

    def show_guide(self):
        from Ui.LauncherGuide import LauncherGuide
        LauncherGuide(self).exec()

    def download_shaders(self):
        """Открывает менеджер шейдеров"""
        try:
            from Network.Downloader import download_shaders_turbo_ui
            from ConfDir.Configs import SHADERS_CONFIG

            dialog = QDialog(self)
            dialog.setWindowTitle("🎨 Выбор шейдеров")
            dialog.setMinimumSize(900, 550)
            dialog.setModal(True)

            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    border-radius: 15px;
                }
                QLabel {
                    color: white;
                    font-family: 'Segoe UI';
                }
                QListWidget {
                    background-color: #1a1a2a;
                    color: #e0e0e0;
                    border: 1px solid #4ECDC4;
                    border-radius: 8px;
                    outline: none;
                    font-family: 'Segoe UI';
                    font-size: 12px;
                }
                QListWidget::item {
                    padding: 8px;
                }
                QListWidget::item:selected {
                    background-color: #4ECDC4;
                    color: #1a1a1a;
                }
                QPushButton {
                    background-color: #3a3a4a;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-family: 'Segoe UI';
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #4a4a5a;
                }
                QPushButton#download {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FF6B6B, stop:1 #4ECDC4);
                }
                QPushButton#download:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff8585, stop:1 #6ad5cb);
                }
                QPushButton#select_all, QPushButton#clear_all {
                    background-color: #4a5568;
                }
            """)

            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            title = QLabel("🎨 Менеджер шейдеров")
            title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            subtitle = QLabel("Выберите шейдеры для установки")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setStyleSheet("color: #888888; font-size: 12px;")
            layout.addWidget(subtitle)

            list_widget = QListWidget()
            shader_names = [s["name"] for s in SHADERS_CONFIG["shaders"]]
            for name in shader_names:
                item = QListWidgetItem(name)
                item.setCheckState(Qt.CheckState.Unchecked)
                list_widget.addItem(item)

            layout.addWidget(list_widget)

            counter_label = QLabel("Выбрано: 0 шейдеров")
            counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            counter_label.setStyleSheet("color: #cccccc; font-size: 11px;")
            layout.addWidget(counter_label)

            def update_counter():
                count = 0
                for i in range(list_widget.count()):
                    if list_widget.item(i).checkState() == Qt.CheckState.Checked:
                        count += 1
                counter_label.setText(f"Выбрано: {count} шейдеров")
                if count > 5:
                    counter_label.setStyleSheet("color: #ffaa00; font-size: 11px;")
                else:
                    counter_label.setStyleSheet("color: #cccccc; font-size: 11px;")

            def select_all():
                for i in range(list_widget.count()):
                    list_widget.item(i).setCheckState(Qt.CheckState.Checked)
                update_counter()

            def clear_all():
                for i in range(list_widget.count()):
                    list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)
                update_counter()

            def on_item_changed(item):
                update_counter()

            list_widget.itemChanged.connect(on_item_changed)

            button_layout = QHBoxLayout()

            select_all_btn = QPushButton("✅ Выбрать все")
            select_all_btn.setObjectName("select_all")
            select_all_btn.clicked.connect(select_all)
            button_layout.addWidget(select_all_btn)

            clear_all_btn = QPushButton("❌ Снять все")
            clear_all_btn.setObjectName("clear_all")
            clear_all_btn.clicked.connect(clear_all)
            button_layout.addWidget(clear_all_btn)

            button_layout.addStretch()

            download_btn = QPushButton("📥 Скачать выбранные")
            download_btn.setObjectName("download")
            button_layout.addWidget(download_btn)

            open_folder_btn = QPushButton("📁 Открыть папку")
            open_folder_btn.clicked.connect(self.open_shaders_folder)
            button_layout.addWidget(open_folder_btn)

            cancel_btn = QPushButton("❌ Закрыть")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)

            layout.addLayout(button_layout)

            def download():
                selected = []
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.checkState() == Qt.CheckState.Checked:
                        selected.append(SHADERS_CONFIG["shaders"][i])

                if not selected:
                    MessageDialog.show_warning(self, "Выбор", "Выберите хотя бы один шейдер")
                    return

                total_size = len(selected) * 50
                reply = MessageDialog.show_question(
                    self,
                    "Подтверждение загрузки",
                    f"Начать загрузку {len(selected)} шейдеров?\n\n"
                    f"Примерный размер: ~{total_size} MB\n"
                    f"Время загрузки: 1-5 минут\n\n"
                    f"Шейдеры будут сохранены в папку shaderpacks"
                )

                if reply == QMessageBox.StandardButton.Yes:
                    dialog.accept()
                    download_shaders_turbo_ui(selected, self)

            download_btn.clicked.connect(download)

            dialog.move(
                self.x() + (self.width() - dialog.width()) // 2,
                self.y() + (self.height() - dialog.height()) // 2
            )

            dialog.exec()

        except Exception as e:
            MessageDialog.show_error(self, "Ошибка", f"Не удалось открыть менеджер шейдеров: {e}")

    def open_shaders_folder(self):
        """Открывает папку с шейдерами"""
        shaders_dir = os.path.join(self.selected_game_directory(create=True), "shaderpacks")
        os.makedirs(shaders_dir, exist_ok=True)

        if os.name == "nt":
            os.startfile(shaders_dir)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", shaders_dir])

    def open_game_folder(self):
        """Открывает папку с игрой"""
        minecraft_dir = self.selected_game_directory(create=True)
        if os.path.exists(minecraft_dir):
            if os.name == "nt":
                os.startfile(minecraft_dir)
            else:
                subprocess.Popen(["xdg-open", minecraft_dir])
        else:
            MessageDialog.show_warning(self, "Папка не найдена", f"Папка {minecraft_dir} не существует!")

    def create_backup(self):
        """Создает бэкап"""
        minecraft_dir = self.selected_game_directory(create=True)
        mods_dir = os.path.join(minecraft_dir, "mods")

        backups_created = []

        os.makedirs(mods_dir, exist_ok=True)

        if os.path.exists(mods_dir):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(minecraft_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)

            backup_path = os.path.join(backup_dir, f"mods_backup_{timestamp}.zip")
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(mods_dir):
                    for file in files:
                        if file.endswith(".jar"):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, mods_dir)
                            zipf.write(file_path, arcname)
            backups_created.append(backup_path)

        if backups_created:
            MessageDialog.show_info(self, "Бэкапы созданы",
                                    f"Созданы бэкапы:\n" + "\n".join(
                                        [f"• {os.path.basename(b)}" for b in backups_created]))
        else:
            MessageDialog.show_info(self, "Бэкапы", "Не удалось создать бэкапы")

    def show_backup_info(self):
        """Показывает информацию о бэкапах"""
        backup_dir = os.path.join(self.selected_game_directory(create=True), "backups")
        if not os.path.exists(backup_dir):
            MessageDialog.show_info(self, "Бэкапы", "Бэкапы не создавались")
            return

        backups = []
        total_size = 0
        for filename in os.listdir(backup_dir):
            if filename.endswith(".zip"):
                file_path = os.path.join(backup_dir, filename)
                size = os.path.getsize(file_path) / (1024 * 1024)
                total_size += size
                time_created = datetime.fromtimestamp(os.path.getctime(file_path))

                if filename.startswith("mods_backup_"):
                    backup_type = "Моды"
                elif filename.startswith("versions_backup_"):
                    backup_type = "Версии"
                elif filename.startswith("world_backup_"):
                    backup_type = "Мир"
                else:
                    backup_type = "Другой"

                backups.append((filename, f"{size:.1f} МБ", time_created.strftime("%d.%m.%Y %H:%M"), backup_type))

        if not backups:
            MessageDialog.show_info(self, "Бэкапы", "Бэкапы не найдены")
            return

        backups.sort(key=lambda x: x[2], reverse=True)

        info_text = f"Созданные бэкапы (всего: {len(backups)}, общий размер: {total_size:.1f} МБ):\n\n"
        for backup in backups:
            info_text += f"• {backup[0]}\n  Тип: {backup[3]}, Размер: {backup[1]}, Создан: {backup[2]}\n\n"

        MessageDialog.show_info(self, "Информация о бэкапах", info_text)

    def delete_all_backups(self):
        """Удаляет все бэкапы"""
        backup_dir = os.path.join(self.selected_game_directory(create=True), "backups")
        if not os.path.exists(backup_dir):
            MessageDialog.show_info(self, "Бэкапы", "Папка бэкапов не существует")
            return

        backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".zip")]
        if not backup_files:
            MessageDialog.show_info(self, "Бэкапы", "Бэкапов не найдено")
            return

        reply = MessageDialog.show_question(self, "Удаление бэкапов",
                                            f"Вы уверены, что хотите удалить ВСЕ бэкапы?\n\n"
                                            f"Будет удалено: {len(backup_files)} файлов\n"
                                            f"Это действие нельзя отменить!")

        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            for filename in backup_files:
                file_path = os.path.join(backup_dir, filename)
                os.remove(file_path)
                deleted_count += 1

            if not os.listdir(backup_dir):
                os.rmdir(backup_dir)

            MessageDialog.show_info(self, "Бэкапы", f"Удалено {deleted_count} бэкапов")

    def launch_without_mods(self):
        """Запуск игры полностью без модов"""
        reply = MessageDialog.show_question(self, "Запуск без модов",
                                            "Запустить игру БЕЗ ВСЕХ модов?\n\n"
                                            "Это поможет определить:\n"
                                            "• Проблема в модах или в игре\n"
                                            "• Конфликтующие моды\n\n"
                                            "После проверки можно включить моды обратно.")

        if reply != QMessageBox.StandardButton.Yes:
            return

        minecraft_dir = self.selected_game_directory(create=True)
        mods_dir = os.path.join(minecraft_dir, "mods")
        disabled_dir = os.path.join(minecraft_dir, "mods_disabled_temp")
        CONFIG["launch_without_mods_next"] = True
        CONFIG['launch_without_mods_version'] = self.version_combo.currentText()

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
            MessageDialog.show_info(self, "Моды отключены",
                                    f"Отключено {moved_count} модов.\n\n"
                                    f"Теперь запустите игру через основную кнопку 'Войти в игру'.\n\n"
                                    f"Моды находятся в: {disabled_dir}")
        else:
            MessageDialog.show_info(self, "Информация", "Модов для отключения не найдено")

    def restore_disabled_mods(self):
        minecraft_dir = self.selected_game_directory(create=True)
        mods_dir = os.path.join(minecraft_dir, 'mods')
        disabled_dir = os.path.join(minecraft_dir, 'mods_disabled_temp')
        if not os.path.isdir(disabled_dir):
            MessageDialog.show_info(self, 'Моды', 'Отключённых модов не найдено'); return
        os.makedirs(mods_dir, exist_ok=True); count=0
        for filename in os.listdir(disabled_dir):
            if filename.lower().endswith('.jar'):
                source=os.path.join(disabled_dir,filename); target=os.path.join(mods_dir,filename)
                if os.path.exists(target): continue
                shutil.move(source,target); count += 1
        if not os.listdir(disabled_dir): os.rmdir(disabled_dir)
        MessageDialog.show_info(self, 'Моды', f'Восстановлено модов: {count}')

    def complete_reinstall(self):
        if is_game_running() or (self.launch_worker and self.launch_worker.isRunning()):
            MessageDialog.show_info(self, 'Восстановление', 'Сначала закройте игру и дождитесь подготовки.')
            return
        selected = self.version_combo.currentText()
        reply = MessageDialog.show_question(self, 'Восстановить сборку',
            f'Проверить файлы и восстановить моды сборки «{selected}»? Миры, настройки и другие сборки сохранятся.')
        if reply == QMessageBox.StandardButton.Yes:
            from Ui.InstanceRepair import InstanceRepairDialog
            InstanceRepairDialog(selected, self).exec()

    def save_bugreport(self, checked=False, minecraft_dir=None):
        if getattr(self, 'bugreport_worker', None) and self.bugreport_worker.isRunning():
            return
        self.bugreport_action.setEnabled(False)
        self.bugreport_worker = BugreportWorker(self, minecraft_dir or self.selected_game_directory())
        self.bugreport_worker.ready.connect(lambda path: MessageDialog.show_info(
            self, 'Bugreport.txt', f'Полный отчёт сохранён:\n{path}'))
        self.bugreport_worker.failed.connect(lambda error: MessageDialog.show_error(self, 'Bugreport.txt', error))
        self.bugreport_worker.finished.connect(lambda: self.bugreport_action.setEnabled(True))
        self.bugreport_worker.start()

    def show_diagnostic(self):
        """Показывает окно диагностики"""
        from Ui.QtDiagnosticWindow import QtDiagnosticWindow
        selected_version = self.version_combo.currentText()
        self.diagnostic_window = QtDiagnosticWindow(self, selected_version)
        self.diagnostic_window.show()

    def select_background(self):
        """Выбор фона"""
        try:
            from ConfDir.ScaleRes import backgrounds

            dialog = QDialog(self)
            dialog.setWindowTitle("Выбор фона")
            dialog.setMinimumSize(400, 500)
            dialog.setModal(True)

            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Выберите фон:"))

            list_widget = QListWidget()
            for name, filename in backgrounds:
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, filename)
                list_widget.addItem(item)

            layout.addWidget(list_widget)

            def apply_background():
                item = list_widget.currentItem()
                if item:
                    filename = item.data(Qt.ItemDataRole.UserRole)
                    self.load_custom_background(filename)
                    dialog.accept()

            btn_layout = QHBoxLayout()
            apply_btn = QPushButton("Применить")
            apply_btn.clicked.connect(apply_background)
            cancel_btn = QPushButton("Отмена")
            cancel_btn.clicked.connect(dialog.reject)

            btn_layout.addStretch()
            btn_layout.addWidget(apply_btn)
            btn_layout.addWidget(cancel_btn)
            btn_layout.addStretch()

            layout.addLayout(btn_layout)
            dialog.exec()

        except Exception as e:
            MessageDialog.show_error(self, "Ошибка", f"Не удалось выбрать фон: {e}")

    def load_custom_background(self, filename, show_message=False):
        """Загружает выбранный фон"""
        try:
            from ConfDir.Configs import resource_path

            bg_path = None
            possible_paths = [
                os.path.join("YamalPixelRes", filename),
                resource_path(os.path.join("YamalPixelRes", filename)),
                filename
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    bg_path = path
                    break

            if bg_path and os.path.exists(bg_path):
                pixmap = QPixmap(bg_path)
                screen = QApplication.primaryScreen()
                screen_rect = screen.availableGeometry()
                scaled_pixmap = pixmap.scaled(
                    screen_rect.width(),
                    screen_rect.height(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                palette = self.centralWidget().palette()
                palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
                self.centralWidget().setPalette(palette)
                self.centralWidget().setAutoFillBackground(True)
                self.current_background = filename

                if show_message:
                    MessageDialog.show_info(self, "Успех", f"Фон {filename} применен!")
            else:
                print(f"⚠️ Файл фона не найден: {filename}")

        except Exception as e:
            print(f"Ошибка загрузки фона: {e}")

    def open_settings(self):
        """Открывает настройки"""
        from PyQt6.QtWidgets import QFormLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        dialog.setFixedSize(520, 430)
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border-radius: 15px;
            }
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QSpinBox {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #4ECDC4;
                border-radius: 8px;
                padding: 5px;
                font-size: 12px;
                min-width: 80px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #4a4a4a;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #4ECDC4;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #4ECDC4);
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff8585, stop:1 #6ad5cb);
            }
            QPushButton#cancel {
                background: #4a5568;
            }
            QPushButton#cancel:hover {
                background: #5a6b82;
            }
        """)

        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("⚙️ Память и Java")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ECDC4; margin-bottom: 10px;")
        main_layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        memory_label = QLabel("Выделено памяти (ГБ):")
        memory_label.setStyleSheet("color: #ffffff; font-size: 12px;")

        memory_spin = QSpinBox()
        memory_spin.setRange(1, 64)
        memory_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #4ECDC4;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """)

        current_mem = CONFIG.get("jvm_memory", "-Xmx4G")
        try:
            current_gb = int(current_mem.replace("-Xmx", "").replace("G", ""))
            memory_spin.setValue(current_gb)
        except:
            memory_spin.setValue(4)

        form_layout.addRow(memory_label, memory_spin)
        main_layout.addLayout(form_layout)

        info_label = QLabel("💡 Рекомендуется выделять 4-8 ГБ для сборки YamalPixel")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #888888; font-size: 10px; margin-top: 5px;")
        main_layout.addWidget(info_label)

        java_button = QPushButton('Версия JAVA')
        java_button.clicked.connect(self.open_java_manager)
        main_layout.addWidget(java_button)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #4ECDC4; max-height: 1px; margin: 10px 0;")
        main_layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        save_btn = QPushButton("💾 Сохранить")
        save_btn.setMinimumWidth(120)

        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setObjectName("cancel")
        cancel_btn.setMinimumWidth(100)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        def save_settings():
            memory_gb = memory_spin.value()
            CONFIG["jvm_memory"] = f"-Xmx{memory_gb}G"

            msg = QMessageBox(dialog)
            msg.setWindowTitle("Сохранено")
            msg.setText(f"✅ Память установлена: {memory_gb} ГБ")
            msg.setInformativeText(f"Новые настройки вступят в силу при следующем запуске игры.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

            dialog.accept()

        def cancel():
            dialog.reject()

        save_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(cancel)

        dialog.move(
            self.x() + (self.width() - dialog.width()) // 2,
            self.y() + (self.height() - dialog.height()) // 2
        )

        dialog.exec()

    def show_collection_manager(self):
        """Показывает менеджер сборок"""
        try:
            from Ui.collection_manager import CollectionManager
            manager = CollectionManager(self)
            manager.exec()
        except ImportError:
            MessageDialog.show_info(self, "Сборки модов",
                                    "Менеджер сборок будет доступен в следующем обновлении.\n\n"
                                    "Пока вы можете создавать сборки вручную в папке collections.")

    def create_new_collection(self):
        """Открывает диалог создания новой сборки"""
        try:
            from Ui.CollectionCreator import CollectionCreator
            creator = CollectionCreator(self)
            creator.exec()
            self.refresh_versions()
        except ImportError as e:
            print(f"Ошибка импорта CollectionCreator: {e}")
            MessageDialog.show_info(
                self,
                "Создание сборки",
                "Функция создания сборок будет доступна в следующем обновлении."
            )
        except Exception as e:
            MessageDialog.show_error(self, "Ошибка", f"Не удалось открыть создание сборки: {e}")

    def load_last_session(self):
        """Загружает последнюю сессию"""
        session_file = os.path.expanduser("~/YamalPixel/last_session.json")
        try:
            if os.path.exists(session_file):
                with open(session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки сессии: {e}")
        return None

    def save_session_data(self, data):
        """Сохраняет данные сессии"""
        session_file = os.path.expanduser("~/YamalPixel/last_session.json")
        try:
            os.makedirs(os.path.dirname(session_file), exist_ok=True)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")

    def show_about(self):
        """О программе"""
        MessageDialog.show_info(self, "О лаунчере",
                                f"YamalPixel Launcher\nВерсия: {CURRENT_VERSION}\n\n"
                                f"Разработано с любовью для комьюнити")

    def check_updates(self):
        """Проверка обновлений"""
        from Network.Updates import check_for_updates_local
        check_for_updates_local(self)

    def load_session(self):
        """Загружает все настройки из сессии"""
        data = self.load_last_session()
        if not data:
            return

        if "username" in data:
            self.username_input.setText(data["username"])

        if "show_beta_versions" in data:
            self.beta_checkbox.setChecked(data["show_beta_versions"])
        if "version" in data:
            self._saved_version = data["version"]
            idx = self.version_combo.findText(data["version"])
            if idx >= 0:
                self.version_combo.setCurrentIndex(idx)

        if "memory" in data:
            CONFIG["jvm_memory"] = data["memory"]

        if "fullscreen" in data and data["fullscreen"]:
            self.fullscreen_checkbox.setChecked(True)
            self.showFullScreen()

        if "music" in data and data["music"]:
            self.music_checkbox.setChecked(True)
            self.toggle_music(True)

        if "background" in data:
            self.load_custom_background(data["background"])

        print(f"✅ Загружены настройки: {list(data.keys())}")

    def save_session(self):
        """Сохраняет все настройки в сессию"""
        session_data = {}

        username = self.username_input.text().strip()
        if username and username != "Введите никнейм":
            session_data["username"] = username

        session_data["version"] = self.version_combo.currentText()
        session_data["show_beta_versions"] = self.beta_checkbox.isChecked()
        session_data["memory"] = CONFIG.get("jvm_memory", "-Xmx4G")
        session_data["fullscreen"] = self.fullscreen_checkbox.isChecked()
        session_data["music"] = self.music_checkbox.isChecked()

        if hasattr(self, 'current_background'):
            session_data["background"] = self.current_background

        screen = QApplication.primaryScreen()
        if screen:
            session_data["screen_resolution"] = f"{screen.size().width()}x{screen.size().height()}"

        session_data["launcher_version"] = CURRENT_VERSION
        session_data["timestamp"] = datetime.now().isoformat()

        try:
            from Core.run import get_current_collection
            current_collection = get_current_collection()
            if current_collection:
                session_data["active_collection"] = current_collection
        except Exception as e:
            print(f"Ошибка получения текущей сборки: {e}")

        session_data["discord_rpc"] = hasattr(self, 'rpc') and self.rpc is not None

        if "fabric_loader" in CONFIG:
            session_data["fabric_loader"] = CONFIG["fabric_loader"]
        if "loader_type" in CONFIG:
            session_data["loader_type"] = CONFIG["loader_type"]

        self.save_session_data(session_data)
        print(f"💾 Сохранены настройки: {list(session_data.keys())}")

    def closeEvent(self, event):
        """Закрытие окна - безопасная версия"""
        from Core.run import is_game_running, GAME_PROCESS
        for timer_name in ('update_timer', 'game_event_timer'):
            timer = getattr(self, timer_name, None)
            if timer is not None: timer.stop()
        for worker_name in ('catalog_worker', 'launch_worker', 'crash_worker', 'bugreport_worker'):
            worker = getattr(self, worker_name, None)
            if worker is not None and worker.isRunning():
                if hasattr(worker, 'requestInterruption'): worker.requestInterruption()
                if hasattr(worker, 'cancel'): worker.cancel()
                worker.wait(2000)
            if worker is not None and not worker.isRunning():
                setattr(self, worker_name, None)
        self.game_log_reader = None
        try:
            if is_game_running():
                reply = QMessageBox.question(
                    self,
                    "Игра запущена",
                    "Игра сейчас запущена. Закрыть лаунчер?\n\n"
                    "Игра продолжит работу в фоновом режиме.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
        except Exception as e:
            print(f"Ошибка проверки игры: {e}")

        try:
            self.save_session()
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")

        if hasattr(self, 'mixer') and self.mixer:
            try:
                if hasattr(self, 'music_playing') and self.music_playing:
                    self.mixer.music.stop()
                self.mixer.quit()
            except Exception as e:
                print(f"Ошибка остановки музыки: {e}")

        if hasattr(self, 'rpc') and self.rpc:
            try:
                self.rpc.close()
            except Exception as e:
                print(f"Ошибка закрытия Discord RPC: {e}")

        if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.isRunning():
            try:
                if hasattr(self.worker_thread, 'cancel'):
                    self.worker_thread.cancel()
                self.worker_thread.wait(5000)
                if not self.worker_thread.isRunning():
                    self.worker_thread = None
            except:
                pass

        event.accept()
        # QApplication quits when the last window closes; Minecraft stays alive.


def run_main_window():
    """Запускает главное окно"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_main_window())
