## Ui/DownloadProgress.py
import os
import threading
import asyncio
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMetaObject, Q_ARG
from PyQt6.QtGui import QFont, QTextCursor

from Network.Downloader import download_single_mod_turbo
from ConfDir.Configs import CONFIG

from Ui.BaseWindow import BaseDialog


class ModDownloadWorker(QThread):
    """Поток для загрузки модов"""
    progress = pyqtSignal(int, int, str)  # current, total, mod_name
    finished = pyqtSignal(int, int)  # success_count, total
    log = pyqtSignal(str)

    def __init__(self, mods_list):
        super().__init__()
        self.mods_list = mods_list
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
                result = download_single_mod_turbo(mod, CONFIG["minecraft_dir"])
                if result:
                    success_count += 1
                    self.log.emit(f"✅ Успешно: {mod['file']}")
                else:
                    self.log.emit(f"❌ Ошибка: {mod['file']}")
            except Exception as e:
                self.log.emit(f"💥 Ошибка {mod['file']}: {str(e)}")

        self.finished.emit(success_count, total)


class ModDownloadProgressDialog(BaseDialog):
    """Диалог прогресса загрузки модов"""

    def __init__(self, parent, mods_list, on_complete=None):
        super().__init__(parent)
        self.mods_list = mods_list
        self.on_complete = on_complete
        self.worker = None

        self.setWindowTitle("Загрузка модов")
        self.setFixedSize(500, 400)
        self.setModal(True)

        self.setup_ui()
        self.start_download()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("📥 Загрузка модов")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ECDC4;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Информация
        self.info_label = QLabel(f"Всего модов: {len(self.mods_list)}")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        # Общий прогресс
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        layout.addWidget(self.total_progress)

        # Текущий мод
        self.current_label = QLabel("Подготовка к загрузке...")
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_label)

        # Лог
        log_label = QLabel("📋 Лог загрузки:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_btn)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def start_download(self):
        """Запускает загрузку в отдельном потоке"""
        self.worker = ModDownloadWorker(self.mods_list)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.log.connect(self.add_log)
        self.worker.start()

    def update_progress(self, current, total, mod_name):
        """Обновляет прогресс"""
        percent = int((current + 1) * 100 / total) if total > 0 else 0
        self.total_progress.setValue(percent)
        self.current_label.setText(f"Загрузка: {mod_name} ({current + 1}/{total})")

    def add_log(self, message):
        """Добавляет сообщение в лог"""
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def on_download_finished(self, success_count, total):
        """Обработка завершения загрузки"""
        self.total_progress.setValue(100)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

        if success_count == total:
            self.current_label.setText("✅ Все моды успешно загружены!")
            self.add_log(f"\n✅ Успешно загружено {success_count} из {total} модов")
        else:
            self.current_label.setText(f"⚠️ Загружено {success_count} из {total} модов")
            self.add_log(f"\n⚠️ Загружено {success_count} из {total} модов")

        if self.on_complete:
            self.on_complete(success_count, total)

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


def download_mods_turbo_ui(mods_list, parent=None, on_complete=None):
    """
    PyQt6 версия функции загрузки модов
    mods_list: список модов [{"file": "...", "url": "..."}, ...]
    parent: родительское окно
    on_complete: callback при завершении (success_count, total)
    """
    dialog = ModDownloadProgressDialog(parent, mods_list, on_complete)
    dialog.exec()
    return dialog