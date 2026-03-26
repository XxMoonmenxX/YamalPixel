# core/shader_manager.py
"""
Модуль для управления шейдерами
"""
import os
import threading
import asyncio
import logging
import zipfile
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QTextEdit,
    QMessageBox, QApplication, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ConfDir.Configs import CONFIG, SHADERS_CONFIG
from Network.Downloader import TurboDownloader

logger = logging.getLogger("YamalPixel.ShaderManager")


class ShaderDownloadWorker(QThread):
    """Поток для загрузки шейдеров"""
    progress = pyqtSignal(int, int, str)  # current, total, shader_name
    finished = pyqtSignal(int, int)  # success_count, total
    log = pyqtSignal(str)

    def __init__(self, shaders_list: List[Dict]):
        super().__init__()
        self.shaders_list = shaders_list
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        shaders_dir = os.path.join(CONFIG["minecraft_dir"], "shaderpacks")
        os.makedirs(shaders_dir, exist_ok=True)

        downloader = TurboDownloader()
        total = len(self.shaders_list)
        success_count = 0

        for i, shader in enumerate(self.shaders_list):
            if self.cancelled:
                self.log.emit("❌ Загрузка отменена")
                break

            self.progress.emit(i, total, shader["name"])
            self.log.emit(f"⬇️ Загрузка: {shader['name']}")

            try:
                # Получаем прямую ссылку
                direct_link = asyncio.run(downloader.get_turbo_link(shader["url"]))
                if not direct_link:
                    self.log.emit(f"❌ Не удалось получить ссылку: {shader['name']}")
                    continue

                shader_path = os.path.join(shaders_dir, shader["file"])
                success = downloader.download_file_sync(direct_link, shader_path)

                if success:
                    success_count += 1
                    self.log.emit(f"✅ Успешно: {shader['name']}")

                    # Распаковываем ZIP если нужно
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

        # Очистка
        try:
            asyncio.run(downloader.cleanup())
        except:
            pass

        self.finished.emit(success_count, total)


class ShaderManagerDialog(QDialog):
    """Диалог выбора и загрузки шейдеров"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 Менеджер шейдеров")
        self.setMinimumSize(900, 550)
        self.setModal(True)

        self.setStyleSheet(self._get_stylesheet())
        self.setup_ui()
        self.load_shaders()

    def _get_stylesheet(self) -> str:
        return """
            QDialog {
                background-color: #2b2b2b;
                border-radius: 15px;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI';
            }
            QTreeWidget {
                background-color: #1a1a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a4a;
                border-radius: 8px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 6px;
            }
            QTreeWidget::item:selected {
                background-color: #4ECDC4;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #2a2a3a;
                color: #4ECDC4;
                padding: 8px;
                border: none;
            }
            QPushButton {
                background-color: #3a3a4a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-family: 'Segoe UI';
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
            QScrollBar:vertical {
                background-color: #2a2a3a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #4ECDC4;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6ad5cb;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("🎨 Менеджер шейдеров")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Выберите шейдеры для установки")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(subtitle)

        # Список шейдеров
        self.shaders_tree = QTreeWidget()
        self.shaders_tree.setHeaderLabels(["✓", "Название", "Размер", "Статус"])
        self.shaders_tree.setColumnWidth(0, 50)
        self.shaders_tree.setColumnWidth(1, 400)
        self.shaders_tree.setColumnWidth(2, 100)
        self.shaders_tree.setColumnWidth(3, 120)
        self.shaders_tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.shaders_tree)

        # Счетчик выбранных
        self.counter_label = QLabel("Выбрано: 0 шейдеров")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counter_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        layout.addWidget(self.counter_label)

        # Кнопки
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("✅ Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("❌ Снять все")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(self.deselect_all_btn)

        button_layout.addStretch()

        self.download_btn = QPushButton("📥 Скачать выбранные")
        self.download_btn.setObjectName("download")
        self.download_btn.clicked.connect(self.download_selected)
        button_layout.addWidget(self.download_btn)

        self.open_folder_btn = QPushButton("📁 Открыть папку")
        self.open_folder_btn.clicked.connect(self.open_shaders_folder)
        button_layout.addWidget(self.open_folder_btn)

        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def load_shaders(self):
        """Загружает список шейдеров"""
        for shader in SHADERS_CONFIG["shaders"]:
            item = QTreeWidgetItem()
            item.setText(0, "☐")
            item.setText(1, shader["name"])
            item.setText(2, "~10-50MB")
            item.setText(3, "Не установлен")
            item.setData(0, Qt.ItemDataRole.UserRole, shader["url"])
            item.setData(0, Qt.ItemDataRole.UserRole + 1, shader["file"])
            self.shaders_tree.addTopLevelItem(item)

        self.check_installed_shaders()

    def check_installed_shaders(self):
        """Проверяет какие шейдеры уже установлены"""
        shaders_dir = os.path.join(CONFIG["minecraft_dir"], "shaderpacks")
        if not os.path.exists(shaders_dir):
            return

        installed = set()
        for file in os.listdir(shaders_dir):
            installed.add(file)

        for i in range(self.shaders_tree.topLevelItemCount()):
            item = self.shaders_tree.topLevelItem(i)
            shader_file = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if shader_file in installed or shader_file.replace(".zip", "") in installed:
                item.setText(3, "✅ Установлен")
                item.setForeground(3, QColor("#00ff88"))

    def on_item_clicked(self, item, column):
        """Обработка клика по элементу"""
        if column == 0:
            current = item.text(0)
            if current == "☐":
                item.setText(0, "☑")
                item.setForeground(0, QColor("#4ECDC4"))
            else:
                item.setText(0, "☐")
                item.setForeground(0, QColor("#ffffff"))
            self.update_counter()

    def update_counter(self):
        """Обновляет счетчик выбранных шейдеров"""
        count = 0
        for i in range(self.shaders_tree.topLevelItemCount()):
            item = self.shaders_tree.topLevelItem(i)
            if item.text(0) == "☑":
                count += 1

        self.counter_label.setText(f"Выбрано: {count} шейдеров")
        if count > 5:
            self.counter_label.setStyleSheet("color: #ffaa00; font-size: 11px;")
        else:
            self.counter_label.setStyleSheet("color: #cccccc; font-size: 11px;")

    def select_all(self):
        """Выбрать все шейдеры"""
        for i in range(self.shaders_tree.topLevelItemCount()):
            item = self.shaders_tree.topLevelItem(i)
            item.setText(0, "☑")
            item.setForeground(0, QColor("#4ECDC4"))
        self.update_counter()

    def deselect_all(self):
        """Снять все"""
        for i in range(self.shaders_tree.topLevelItemCount()):
            item = self.shaders_tree.topLevelItem(i)
            item.setText(0, "☐")
            item.setForeground(0, QColor("#ffffff"))
        self.update_counter()

    def download_selected(self):
        """Скачать выбранные шейдеры"""
        selected = []
        for i in range(self.shaders_tree.topLevelItemCount()):
            item = self.shaders_tree.topLevelItem(i)
            if item.text(0) == "☑":
                selected.append({
                    "name": item.text(1),
                    "url": item.data(0, Qt.ItemDataRole.UserRole),
                    "file": item.data(0, Qt.ItemDataRole.UserRole + 1)
                })

        if not selected:
            QMessageBox.warning(self, "Выбор", "Выберите хотя бы один шейдер")
            return

        total_size = len(selected) * 50
        reply = QMessageBox.question(
            self,
            "Подтверждение загрузки",
            f"Начать загрузку {len(selected)} шейдеров?\n\n"
            f"Примерный размер: ~{total_size} MB\n"
            f"Время загрузки: 1-5 минут\n\n"
            f"Шейдеры будут сохранены в папку shaderpacks",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            self.start_download(selected)

    def start_download(self, shaders):
        """Запускает загрузку шейдеров"""
        dialog = ShaderDownloadProgressDialog(self.parent(), shaders)
        dialog.exec()

    def open_shaders_folder(self):
        """Открывает папку с шейдерами"""
        shaders_dir = os.path.join(CONFIG["minecraft_dir"], "shaderpacks")
        os.makedirs(shaders_dir, exist_ok=True)

        import subprocess
        if os.name == "nt":
            os.startfile(shaders_dir)
        else:
            subprocess.Popen(["xdg-open", shaders_dir])


class ShaderDownloadProgressDialog(QDialog):
    """Диалог прогресса загрузки шейдеров"""

    def __init__(self, parent, shaders: List[Dict]):
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

        self.setup_ui()
        self.start_download()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("📥 Загрузка шейдеров")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Информация
        self.info_label = QLabel(f"Всего шейдеров: {len(self.shaders)}")
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
        self.log_text.ensureCursorVisible()

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


def show_shader_manager(parent=None):
    """
    Показывает менеджер шейдеров
    """
    dialog = ShaderManagerDialog(parent)
    dialog.exec()


def download_shaders_turbo_ui(shaders_list: List[Dict], parent=None):
    """
    Загружает шейдеры с UI прогресса
    """
    dialog = ShaderDownloadProgressDialog(parent, shaders_list)
    dialog.exec()