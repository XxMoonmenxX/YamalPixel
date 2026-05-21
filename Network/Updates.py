## Network/Updates.py
import logging
import requests
import re
import os
import sys
import subprocess
import tempfile
import stat
import webbrowser
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from ConfDir.Versions import CURRENT_VERSION
from ConfDir.Configs import resource_path

logger = logging.getLogger("YamalPixel.Updates")


def set_window_icon(window):
    """Set icon for all windows (PyQt6 version)"""
    try:
        from PyQt6.QtGui import QIcon
        icon_path = resource_path("icon.ico")

        if not os.path.exists(icon_path):
            home_icon_path = Path.home() / "YamalPixelRes" / "icon.ico"
            if os.path.exists(home_icon_path):
                icon_path = home_icon_path
            else:
                print(f"Icon not found: {icon_path}")
                return

        window.setWindowIcon(QIcon(icon_path))
        print(f"Icon loaded from: {icon_path}")

    except Exception as e:
        print(f"Icon error: {e}")


class UpdateDownloadWorker(QThread):
    """Поток для скачивания обновления"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)  # success, filepath
    error = pyqtSignal(str)

    def __init__(self, download_url, temp_exe):
        super().__init__()
        self.download_url = download_url
        self.temp_exe = temp_exe

    def run(self):
        try:
            with requests.get(self.download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))

                with open(self.temp_exe, "wb") as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = int((downloaded / total_size) * 100)
                                self.progress.emit(percent)

            # Делаем файл исполняемым (для Linux/MacOS)
            if os.name != "nt":
                os.chmod(self.temp_exe, os.stat(self.temp_exe).st_mode | stat.S_IEXEC)

            self.finished.emit("success", self.temp_exe)

        except Exception as e:
            self.error.emit(str(e))


# Network/Updates.py - исправленный UpdateDialog

class UpdateDialog(QDialog):
    """Диалог обновления лаунчера"""

    def __init__(self, parent=None, release_data=None):
        super().__init__(parent)
        self.release_data = release_data
        self.latest_version = release_data["tag_name"].lstrip("v") if release_data else CURRENT_VERSION
        self.changelog = self._format_changelog(
            release_data.get("body", "Нет описания изменений")) if release_data else ""

        self.setWindowTitle(f"YamalPixel - Обновление до v{self.latest_version}")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        # Устанавливаем стиль
        self.setStyleSheet(self._get_stylesheet())

        # Основной layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("✨ Доступно обновление! ✨")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Версия
        version_label = QLabel(f"Версия {self.latest_version}")
        version_label.setObjectName("version")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #4ECDC4; max-height: 2px;")
        layout.addWidget(line)

        # Что нового
        whats_new = QLabel("📋 Что нового:")
        whats_new.setObjectName("whatsnew")
        layout.addWidget(whats_new)

        # Текстовое поле с changelog
        self.changelog_text = QTextEdit()
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setPlainText(self.changelog)
        self.changelog_text.setMinimumHeight(200)
        layout.addWidget(self.changelog_text)

        layout.addSpacing(10)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.install_btn = QPushButton("🔄 Установить обновление")
        self.install_btn.setObjectName("install")
        self.install_btn.setFixedSize(200, 45)
        self.install_btn.clicked.connect(self.install_update)
        button_layout.addWidget(self.install_btn)

        self.skip_btn = QPushButton("⏭️ Пропустить")
        self.skip_btn.setObjectName("skip")
        self.skip_btn.setFixedSize(140, 45)
        self.skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.skip_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.set_window_icon()

    def _get_stylesheet(self):
        return """
            QDialog {
                background-color: #1e1e2f;
                border-radius: 15px;
            }
            QLabel#title {
                color: #4ECDC4;
                font-size: 22px;
                font-weight: bold;
                font-family: 'Segoe UI';
                padding: 10px;
            }
            QLabel#version {
                color: #a0a0a0;
                font-size: 14px;
                font-family: 'Segoe UI';
                padding-bottom: 10px;
            }
            QLabel#whatsnew {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI';
                margin-top: 10px;
            }
            QTextEdit {
                background-color: #2a2a3a;
                color: #e0e0e0;
                border: 1px solid #4ECDC4;
                border-radius: 12px;
                padding: 12px;
                font-size: 12px;
                font-family: 'Consolas', monospace;
            }
            QPushButton#install {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #4ECDC4);
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
            QPushButton#install:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff8585, stop:1 #6ad5cb);
            }
            QPushButton#skip {
                background-color: #3a3a4a;
                color: #cccccc;
                border: 1px solid #4ECDC4;
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
            QPushButton#skip:hover {
                background-color: #4a4a5a;
                color: white;
            }
            QScrollBar:vertical {
                background-color: #2a2a3a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4ECDC4;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6ad5cb;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    def _format_changelog(self, changelog):
        """Форматирует changelog для отображения"""
        if not changelog:
            return "✨ Нет описания изменений"

        # Убираем Markdown-разметку
        changelog = re.sub(r"#{2,}", "", changelog)
        changelog = re.sub(r"\- ", "• ", changelog)
        changelog = re.sub(r"\*\*(.*?)\*\*", r"▸ \1", changelog)
        changelog = re.sub(r"\*(.*?)\*", r"\1", changelog)

        # Добавляем эмодзи для разных типов изменений
        changelog = re.sub(r"fixed", "🔧 fixed", changelog, flags=re.IGNORECASE)
        changelog = re.sub(r"added", "✨ added", changelog, flags=re.IGNORECASE)
        changelog = re.sub(r"changed", "🔄 changed", changelog, flags=re.IGNORECASE)
        changelog = re.sub(r"removed", "🗑️ removed", changelog, flags=re.IGNORECASE)

        return changelog.strip()

    def set_window_icon(self):
        try:
            from PyQt6.QtGui import QIcon
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Icon error: {e}")

    def install_update(self):
        """Начинает установку обновления"""
        # Ищем EXE-файл в ассетах
        update_asset = None
        for asset in self.release_data.get("assets", []):
            if asset["name"].lower().endswith(".exe"):
                update_asset = asset
                break

        if not update_asset:
            available = "\n".join([f"• {a['name']}" for a in self.release_data.get("assets", [])])
            QMessageBox.warning(
                self,
                "Файл не найден",
                f"EXE-файл не найден в релизе.\n\nДоступные файлы:\n{available}"
            )
            return

        self.accept()  # Закрываем диалог обновления
        self.start_download_and_install(update_asset["browser_download_url"])

    def start_download_and_install(self, download_url):
        """Запускает скачивание и установку обновления"""
        self.progress_dialog = UpdateProgressDialog(self, download_url)
        self.progress_dialog.show()


class UpdateProgressDialog(QDialog):
    """Диалог прогресса скачивания обновления"""

    def __init__(self, parent=None, download_url=None):
        super().__init__(parent)
        self.download_url = download_url
        self.temp_exe = os.path.join(tempfile.gettempdir(), "YamalPixelLauncher_New.exe")

        self.setWindowTitle("Обновление")
        self.setFixedSize(450, 180)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2f;
                border-radius: 15px;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI';
                font-size: 12px;
            }
            QProgressBar {
                background-color: #2a2a3a;
                border: none;
                border-radius: 10px;
                height: 20px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #4ECDC4);
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        self.status_label = QLabel("📥 Скачивание обновления...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.percent_label)

        # Запускаем скачивание
        self.worker = UpdateDownloadWorker(download_url, self.temp_exe)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_download_error)
        self.worker.start()

    def on_progress(self, percent):
        self.progress_bar.setValue(percent)
        self.percent_label.setText(f"{percent}%")

    def on_download_finished(self, success, filepath):
        """Обработка завершения скачивания"""
        self.status_label.setText("⚙️ Подготовка к обновлению...")
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")

        # Запускаем установку
        self.perform_update(filepath)

    def on_download_error(self, error_msg):
        """Обработка ошибки скачивания"""
        self.close()
        QMessageBox.critical(
            self,
            "Ошибка",
            f"Не удалось скачать обновление:\n{error_msg}\n\n"
            f"Попробуйте скачать новую версию вручную с GitHub."
        )
        self.show_manual_update()

    def perform_update(self, temp_exe):
        """Выполняет установку обновления"""
        current_exe = os.path.abspath(sys.argv[0])
        backup_exe = os.path.join(os.path.dirname(current_exe), "YamalPixelLauncher_Backup.exe")
        temp_dir = tempfile.gettempdir()

        if os.name == "nt":  # Windows
            bat_path = os.path.join(temp_dir, "yamalpixel_update.bat")
            with open(bat_path, "w", encoding="utf-8") as bat_file:
                bat_file.write(f"""@echo off
chcp 65001 >nul
echo YamalPixel - Обновление
timeout /t 2 /nobreak >nul

:: Закрываем лаунчер
taskkill /f /im "{os.path.basename(current_exe)}" >nul 2>&1

:: Очистка временных файлов PyInstaller
del /q /f "%TEMP%\\_MEI*" >nul 2>&1
for /d %%i in ("%TEMP%\\_MEI*") do rd /s /q "%%i" >nul 2>&1
timeout /t 1 /nobreak >nul

:: Создаем бэкап
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

:: Очистка
del "{backup_exe}" >nul 2>&1
del "%~f0" >nul 2>&1
""")

            subprocess.Popen(
                [bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

        else:  # Linux/MacOS
            sh_path = os.path.join(temp_dir, "yamalpixel_update.sh")
            with open(sh_path, "w", encoding="utf-8") as sh_file:
                sh_file.write(f"""#!/bin/bash
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
""")
            os.chmod(sh_path, 0o755)
            subprocess.Popen(
                ["nohup", "bash", sh_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Закрываем текущий лаунчер
        QApplication.quit()
        sys.exit(0)

    def show_manual_update(self):
        """Показывает опцию ручного обновления"""
        reply = QMessageBox.question(
            self,
            "Ручное обновление",
            "Не удалось автоматически обновиться.\n\n"
            "Причины:\n"
            "• Недостаточно прав\n"
            "• Антивирус заблокировал обновление\n"
            "• Файл занят другим процессом\n\n"
            "Хотите скачать новую версию вручную?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(self.download_url)
            QMessageBox.information(
                self,
                "Ручное обновление",
                "Скачайте новую версию и замените текущий файл лаунчера.\n\n"
                "Текущий лаунчер будет закрыт."
            )
            QApplication.quit()
            sys.exit(0)


def can_update_launcher():
    """Проверяет, можно ли обновить лаунчер"""
    try:
        test_file = os.path.join(os.path.dirname(sys.argv[0]), "test_write.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except:
        return False


def check_for_updates_local(parent_window=None):
    """
    Проверка обновлений для PyQt6
    parent_window: главное окно лаунчера (QMainWindow)
    """
    try:
        logging.info("Проверка обновлений...")

        # Проверяем права доступа
        if not can_update_launcher():
            logging.warning("Недостаточно прав для автоматического обновления")
            QMessageBox.information(
                parent_window,
                "Обновление",
                "Недостаточно прав для автоматического обновления.\n\n"
                "Запустите лаунчер от имени администратора для автоматического обновления,\n"
                "или скачайте новую версию вручную с GitHub."
            )
            return

        response = requests.get(
            "https://api.github.com/repos/XxMoonmenxX/YamalPixel/releases/latest",
            timeout=10
        )
        response.raise_for_status()

        release_data = response.json()
        latest_version = release_data["tag_name"].lstrip("v")

        if latest_version != CURRENT_VERSION:
            logging.info(f"Найдена новая версия: {latest_version}")

            # Показываем диалог обновления
            dialog = UpdateDialog(parent_window, release_data)
            dialog.exec()

        else:
            QMessageBox.information(
                parent_window,
                "Обновление",
                f"Вы используете последнюю версию: {CURRENT_VERSION}"
            )

    except requests.exceptions.Timeout:
        logging.error("Таймаут при проверке обновлений")
        QMessageBox.warning(
            parent_window,
            "Ошибка",
            "Не удалось проверить обновления: превышен таймаут.\n\n"
            "Проверьте интернет-соединение и попробуйте позже."
        )
    except requests.exceptions.ConnectionError:
        logging.error("Ошибка подключения при проверке обновлений")
        QMessageBox.warning(
            parent_window,
            "Ошибка",
            "Не удалось подключиться к серверу обновлений.\n\n"
            "Проверьте интернет-соединение и попробуйте позже."
        )
    except Exception as e:
        logging.error(f"Ошибка проверки обновлений: {str(e)}")
        QMessageBox.critical(
            parent_window,
            "Ошибка",
            f"Не удалось проверить обновления: {str(e)}"
        )