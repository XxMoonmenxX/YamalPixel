# core/java_checker.py
"""
Модуль для проверки и установки Java
"""
import os
import sys
import subprocess
import platform
import urllib.request
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple
import re

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger("YamalPixel.JavaChecker")


def extract_major_version(version_str: str) -> int:
    """
    Извлекает мажорную версию из строки версии Java
    Обрабатывает разные форматы: 1.8.0, 9.0.1, 11.0.2, 17.0.1 и т.д.
    """
    try:
        # Убираем возможные префиксы и суффиксы
        clean_version = version_str.split("_")[0]

        parts = clean_version.split(".")

        # Новый формат версий (9+): первое число - мажорная версия
        if len(parts) >= 1:
            major = int(parts[0])
            # Старый формат версий (1.8.x): второе число - мажорная версия
            if major == 1 and len(parts) >= 2:
                return int(parts[1])
            return major

    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка парсинга версии Java '{version_str}': {e}")

    return 0


def check_java_version() -> Tuple[bool, Optional[str]]:
    """
    Проверяет наличие Java 17+.
    Возвращает (установлена_ли, версия_или_сообщение)
    """
    java_versions = []

    # Метод 1: Проверка через java -version
    try:
        result = subprocess.run(
            ["java", "-version"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        version_output = result.stderr or result.stdout

        patterns = [
            r'version "([1-9]\d*\.\d+\.\d+[_\d]*)',
            r'java version "([1-9]\d*\.\d+\.\d+[_\d]*)',
            r'openjdk version "([1-9]\d*\.\d+\.\d+[_\d]*)',
            r'"([1-9]\d*\.\d+\.\d+[_\d]*)',
        ]

        for pattern in patterns:
            version_match = re.search(pattern, version_output)
            if version_match:
                version_str = version_match.group(1)
                major_version = extract_major_version(version_str)
                java_versions.append(major_version)
                logger.info(f"Найдена Java версия: {version_str} (major: {major_version})")
                break

    except (subprocess.CalledProcessError, FileNotFoundError, TimeoutError) as e:
        logger.debug(f"Метод java -version не сработал: {e}")

    # Метод 2: Проверка через where/java (поиск в PATH)
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["where", "java"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            result = subprocess.run(
                ["which", "java"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )

        if result.returncode == 0:
            java_path = result.stdout.strip().split("\n")[0]
            logger.info(f"Java найдена по пути: {java_path}")

            version_result = subprocess.run(
                [java_path, "-version"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                timeout=5,
            )

            version_output = version_result.stderr or version_result.stdout
            version_match = re.search(r'version "([1-9]\d*\.\d+\.\d+[_\d]*)', version_output)
            if version_match:
                version_str = version_match.group(1)
                major_version = extract_major_version(version_str)
                java_versions.append(major_version)
                logger.info(f"Java из PATH: {version_str} (major: {major_version})")

    except Exception as e:
        logger.debug(f"Метод поиска в PATH не сработал: {e}")

    # Метод 3: Проверка переменной JAVA_HOME
    try:
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java_exe = os.path.join(java_home, "bin", "java.exe" if os.name == "nt" else "java")
            if os.path.exists(java_exe):
                version_result = subprocess.run(
                    [java_exe, "-version"],
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                    timeout=5,
                )

                version_output = version_result.stderr or version_result.stdout
                version_match = re.search(r'version "([1-9]\d*\.\d+\.\d+[_\d]*)', version_output)
                if version_match:
                    version_str = version_match.group(1)
                    major_version = extract_major_version(version_str)
                    java_versions.append(major_version)
                    logger.info(f"Java из JAVA_HOME: {version_str} (major: {major_version})")

    except Exception as e:
        logger.debug(f"Метод JAVA_HOME не сработал: {e}")

    # Анализ результатов
    if java_versions:
        max_version = max(java_versions)
        logger.info(f"Максимальная найденная версия Java: {max_version}")
        if max_version >= 17:
            return True, f"Java {max_version} установлена"
        else:
            return False, f"Найдена Java {max_version}, требуется Java 17+"
    else:
        logger.warning("Java не найдена ни одним из методов")
        return False, "Java не найдена"


def get_java_installer_url() -> Optional[str]:
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


class JavaInstallWorker(QThread):
    """Поток для установки Java"""
    progress = pyqtSignal(int, str)  # percent, status
    finished = pyqtSignal(bool, str)  # success, message
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            system = platform.system()

            if system == "Windows":
                self._install_windows()
            elif system == "Linux":
                self._install_linux()
            elif system == "Darwin":
                self._install_macos()
            else:
                self.error.emit(f"Неподдерживаемая ОС: {system}")

        except Exception as e:
            self.error.emit(str(e))

    def _install_windows(self):
        """Установка Java на Windows"""
        url = get_java_installer_url()
        if not url:
            self.error.emit("Не найден подходящий установщик для вашей системы")
            return

        import tempfile
        msi_path = os.path.join(tempfile.gettempdir(), "OpenJDK17.msi")

        self.progress.emit(0, "Скачивание установщика Java...")

        # Скачиваем с прогрессом
        def report_hook(count, block_size, total_size):
            if self._is_cancelled:
                raise Exception("Отменено пользователем")
            if total_size > 0:
                percent = int(min(count * block_size * 100 / total_size, 100))
                self.progress.emit(percent, f"Скачивание: {percent}%")

        try:
            urllib.request.urlretrieve(url, msi_path, reporthook=report_hook)
        except Exception as e:
            if "Отменено" in str(e):
                self.error.emit("Установка отменена")
                return
            raise

        self.progress.emit(100, "Установка Java...")

        result = subprocess.run(
            f'msiexec /i "{msi_path}" /quiet /norestart',
            shell=True,
            timeout=300,
            capture_output=True,
            text=True,
        )

        # Очистка
        if os.path.exists(msi_path):
            os.remove(msi_path)

        if result.returncode != 0:
            raise Exception(f"Ошибка установки: {result.stderr}")

        self.finished.emit(True, "Java 17 успешно установлена!")

    def _install_linux(self):
        """Установка Java на Linux"""
        self.progress.emit(10, "Обновление списка пакетов...")

        commands = [
            ["sudo", "apt-get", "update", "-y"],
            ["sudo", "apt-get", "install", "-y", "wget", "apt-transport-https", "gnupg"],
            ["wget", "-qO", "-", "https://packages.adoptium.net/artifactory/api/gpg/key/public"],
            ["sudo", "apt-key", "add", "-"],
            ["echo", '"deb https://packages.adoptium.net/artifactory/deb $(lsb_release -cs) main"', "|", "sudo", "tee", "/etc/apt/sources.list.d/adoptium.list"],
            ["sudo", "apt-get", "update", "-y"],
            ["sudo", "apt-get", "install", "-y", "temurin-17-jdk"],
        ]

        for i, cmd in enumerate(commands):
            if self._is_cancelled:
                self.error.emit("Установка отменена")
                return

            self.progress.emit(10 + i * 12, f"Выполнение: {cmd[0]}...")

            result = subprocess.run(
                " ".join(cmd) if isinstance(cmd, list) else cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0 and "add" not in str(cmd):
                logger.warning(f"Команда {' '.join(cmd)} завершилась с ошибкой: {result.stderr}")

        self.finished.emit(True, "Java 17 успешно установлена!")

    def _install_macos(self):
        """Установка Java на macOS"""
        self.progress.emit(10, "Проверка Homebrew...")

        # Проверяем установлен ли Homebrew
        result = subprocess.run(["which", "brew"], capture_output=True)
        if result.returncode != 0:
            self.progress.emit(20, "Установка Homebrew...")
            subprocess.run(
                '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                shell=True,
                timeout=300,
            )

        self.progress.emit(50, "Установка Java...")
        subprocess.run(["brew", "tap", "adoptium/temurin"], capture_output=True)
        subprocess.run(["brew", "install", "--cask", "temurin17"], capture_output=True)

        self.finished.emit(True, "Java 17 успешно установлена!")


class JavaCheckDialog(QDialog):
    """Диалог проверки и установки Java"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Проверка Java")
        self.setFixedSize(450, 200)
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
            QPushButton {
                background-color: #4a5568;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6b82;
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
        layout.setContentsMargins(25, 25, 25, 25)

        # Заголовок
        self.title_label = QLabel("☕ Проверка Java")
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Статус
        self.status_label = QLabel("Проверка установки Java...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Прогресс-бар (изначально скрыт)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.install_btn = QPushButton("Установить Java 17")
        self.install_btn.clicked.connect(self.install_java)
        button_layout.addWidget(self.install_btn)

        self.skip_btn = QPushButton("Пропустить")
        self.skip_btn.setObjectName("cancel")
        self.skip_btn.clicked.connect(self.skip)
        button_layout.addWidget(self.skip_btn)

        layout.addLayout(button_layout)

        self.worker = None
        self.java_ok = False
        self.java_message = ""

        # Запускаем проверку
        self.check_java()

    def check_java(self):
        """Проверяет Java в отдельном потоке"""
        import threading

        def check_thread():
            ok, message = check_java_version()
            self.java_ok = ok
            self.java_message = message

            from PyQt6.QtCore import QMetaObject, Q_ARG
            QMetaObject.invokeMethod(
                self, "_on_check_complete",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, ok),
                Q_ARG(str, message)
            )

        threading.Thread(target=check_thread, daemon=True).start()

    def _on_check_complete(self, ok: bool, message: str):
        """Обработка завершения проверки"""
        if ok:
            self.title_label.setText("✅ Java установлена")
            self.status_label.setText(message)
            self.install_btn.setEnabled(False)
            self.skip_btn.setText("Продолжить")
            self.skip_btn.clicked.disconnect()
            self.skip_btn.clicked.connect(self.accept)
        else:
            self.title_label.setText("⚠️ Java не найдена")
            self.status_label.setText(message)

    def install_java(self):
        """Запускает установку Java"""
        self.install_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.status_label.setText("Подготовка к установке...")
        self.title_label.setText("📥 Установка Java 17")

        self.worker = JavaInstallWorker()
        self.worker.progress.connect(self._on_install_progress)
        self.worker.finished.connect(self._on_install_finished)
        self.worker.error.connect(self._on_install_error)
        self.worker.start()

    def _on_install_progress(self, percent: int, status: str):
        """Обновление прогресса установки"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(status)

    def _on_install_finished(self, success: bool, message: str):
        """Завершение установки"""
        self.progress_bar.setVisible(False)

        if success:
            self.title_label.setText("✅ Java установлена")
            self.status_label.setText(message)
            self.skip_btn.setText("Продолжить")
            self.skip_btn.setEnabled(True)
            self.skip_btn.clicked.disconnect()
            self.skip_btn.clicked.connect(self.accept)
        else:
            self.title_label.setText("❌ Ошибка установки")
            self.status_label.setText(message)
            self.skip_btn.setText("Пропустить")
            self.skip_btn.setEnabled(True)
            self.skip_btn.clicked.disconnect()
            self.skip_btn.clicked.connect(self.skip)

    def _on_install_error(self, error_msg: str):
        """Ошибка установки"""
        self.progress_bar.setVisible(False)
        self.title_label.setText("❌ Ошибка установки")
        self.status_label.setText(error_msg)
        self.skip_btn.setText("Пропустить")
        self.skip_btn.setEnabled(True)
        self.skip_btn.clicked.disconnect()
        self.skip_btn.clicked.connect(self.skip)

    def skip(self):
        """Пропустить проверку Java"""
        reply = QMessageBox.question(
            self,
            "Пропустить проверку",
            "Вы уверены, что хотите пропустить проверку Java?\n\n"
            "Игра может не запуститься, если Java 17 не установлена.\n"
            "Продолжить на свой страх и риск?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()


def check_java_on_startup(parent=None) -> bool:
    """
    Проверяет Java при запуске. Если Java 17+ не найдена,
    показывает диалог установки.
    Возвращает True, если Java есть или пользователь пропустил.
    """
    ok, message = check_java_version()

    if ok:
        logger.info(f"Java проверена: {message}")
        return True

    # Показываем диалог установки
    logger.warning(f"Java не найдена: {message}")
    dialog = JavaCheckDialog(parent)
    result = dialog.exec()

    # После закрытия диалога проверяем еще раз
    ok, _ = check_java_version()
    return ok