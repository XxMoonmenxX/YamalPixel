"""Shader selection UI; downloads use the shared progress dialog."""
import os
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ConfDir.Configs import SHADERS_CONFIG
from Core.instances import ensure_game_directory
from Ui.BaseWindow import PlainDialog
from Ui.DownloadDialog import DownloadProgressDialog, ShaderDownloadWorker


class ShaderManagerDialog(PlainDialog):
    """Диалог выбора и загрузки шейдеров"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Менеджер шейдеров")
        self.setMinimumSize(900, 550)
        self.setModal(True)

        self.setup_ui()
        self.load_shaders()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("🎨 Менеджер шейдеров")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ECDC4;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Выберите шейдеры для установки")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888888;")
        layout.addWidget(subtitle)

        # Список шейдеров
        self.shaders_tree = QTreeWidget()
        self.shaders_tree.setHeaderLabels(["✓", "Название", "Размер", "Статус"])
        self.shaders_tree.setColumnWidth(0, 40)
        self.shaders_tree.setColumnWidth(1, 400)
        self.shaders_tree.setColumnWidth(2, 80)
        self.shaders_tree.setColumnWidth(3, 100)
        self.shaders_tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.shaders_tree)

        # Счетчик выбранных
        self.counter_label = QLabel("Выбрано: 0 шейдеров")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.download_btn.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6B6B, stop:1 #4ECDC4);")
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

        # Проверяем установленные шейдеры
        self.check_installed_shaders()

    def check_installed_shaders(self):
        """Проверяет какие шейдеры уже установлены"""
        shaders_dir = os.path.join(ensure_game_directory(), "shaderpacks")
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
            self.counter_label.setStyleSheet("color: #ffaa00;")
        else:
            self.counter_label.setStyleSheet("color: #ffffff;")

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
        shaders_dir = os.path.join(ensure_game_directory(), "shaderpacks")
        os.makedirs(shaders_dir, exist_ok=True)

        import subprocess
        if os.name == "nt":
            os.startfile(shaders_dir)
        else:
            subprocess.Popen(["xdg-open", shaders_dir])

class ShaderDownloadProgressDialog(DownloadProgressDialog):
    def __init__(self, parent, shaders):
        super().__init__(parent, shaders, kind='shaders')


def show_shader_manager(parent=None):
    ShaderManagerDialog(parent).exec()


def download_shaders_turbo_ui(shaders_list, parent=None):
    if shaders_list:
        ShaderDownloadProgressDialog(parent, shaders_list).exec()
