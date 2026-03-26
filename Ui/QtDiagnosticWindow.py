# Ui/QtDiagnosticWindow.py
"""
Окно диагностики на PyQt6
"""
import sys
import os
import psutil
import subprocess
import json
import datetime
import threading
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar, QFrame,
    QMessageBox, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QPalette

from ConfDir.Configs import CONFIG, get_minecraft_version
from ConfDir.Versions import CURRENT_VERSION


class DiagnosticWorker(QThread):
    """Рабочий поток для диагностики"""

    status_updated = pyqtSignal(str)
    result_added = pyqtSignal(str, str)  # text, color
    finished = pyqtSignal(dict)

    def __init__(self, selected_version=None):
        super().__init__()
        self.problems_found = []
        self.selected_version = selected_version

    def run(self):
        """Выполняет диагностику в отдельном потоке"""
        try:
            minecraft_dir = CONFIG["minecraft_dir"]

            # Проверка папок
            for folder in ["mods", "versions", "config", "shaderpacks"]:
                path = os.path.join(minecraft_dir, folder)
                if os.path.exists(path):
                    self.result_added.emit(f"✅ Папка {folder} найдена", "green")
                else:
                    self.problems_found.append(f"Отсутствует папка {folder}")
                    self.result_added.emit(f"❌ Папка {folder} не найдена", "red")

            # Проверка модов
            mods_dir = os.path.join(minecraft_dir, "mods")
            if os.path.exists(mods_dir):
                mod_files = [f for f in os.listdir(mods_dir) if f.endswith(".jar")]
                self.result_added.emit(f"📦 Найдено модов: {len(mod_files)}", "cyan")

                if len(mod_files) == 0:
                    self.problems_found.append("Папка модов пустая")
                    self.result_added.emit("⚠️ Папка модов пуста", "orange")

            # Проверка конфигов
            config_dir = os.path.join(minecraft_dir, "config")
            if os.path.exists(config_dir):
                config_files = len([f for f in os.listdir(config_dir) if f.endswith(('.json', '.toml', '.properties'))])
                if config_files > 0:
                    self.result_added.emit(f"⚙️ Найдено конфигов: {config_files}", "cyan")

            # Проверка ОЗУ
            memory = psutil.virtual_memory()
            memory_gb_free = memory.available // (1024 * 1024 * 1024)

            if memory.available < 3 * 1024 * 1024 * 1024:
                self.problems_found.append(f"Мало оперативной памяти (свободно: {memory_gb_free}GB)")
                self.result_added.emit(
                    f"⚠️ Мало ОЗУ: {memory.available // (1024 * 1024)}MB свободно",
                    "orange"
                )
            else:
                self.result_added.emit(
                    f"✅ ОЗУ: {memory_gb_free}GB свободно из {memory.total // (1024 * 1024 * 1024)}GB",
                    "green"
                )

            # Проверка диска
            try:
                disk = psutil.disk_usage(minecraft_dir)
                disk_gb_free = disk.free // (1024 * 1024 * 1024)

                if disk.free < 2 * 1024 * 1024 * 1024:
                    self.problems_found.append(f"Мало места на диске (свободно: {disk_gb_free}GB)")
                    self.result_added.emit(
                        f"⚠️ Мало места: {disk_gb_free}GB свободно",
                        "orange"
                    )
                else:
                    self.result_added.emit(
                        f"✅ Диск: {disk_gb_free}GB свободно из {disk.total // (1024 * 1024 * 1024)}GB",
                        "green"
                    )
            except:
                self.result_added.emit("⚠️ Не удалось проверить место на диске", "orange")

            # Проверка Java
            java_ok = self._check_java()
            if java_ok:
                java_version = self._get_java_version()
                self.result_added.emit(f"✅ Java установлена: {java_version}", "green")
            else:
                self.problems_found.append("Java 17+ не найдена")
                self.result_added.emit("❌ Java 17+ не найдена", "red")

            # Проверка модлоадера для выбранной версии
            if self.selected_version:
                try:
                    from ConfDir.Versions import is_modloader_needed
                    loader_needed = is_modloader_needed(self.selected_version)

                    if loader_needed:
                        versions_dir = os.path.join(minecraft_dir, "versions")
                        if loader_needed == "fabric":
                            loader_installed = any("fabric-loader" in v for v in os.listdir(versions_dir) if
                                                   os.path.isdir(os.path.join(versions_dir, v)))
                            if loader_installed:
                                self.result_added.emit(f"✅ Fabric установлен", "green")
                            else:
                                self.problems_found.append("Fabric не установлен")
                                self.result_added.emit("⚠️ Fabric не установлен", "orange")
                        elif loader_needed == "forge":
                            loader_installed = any("forge" in v.lower() for v in os.listdir(versions_dir))
                            if loader_installed:
                                self.result_added.emit(f"✅ Forge установлен", "green")
                            else:
                                self.problems_found.append("Forge не установлен")
                                self.result_added.emit("⚠️ Forge не установлен", "orange")
                except Exception as e:
                    self.result_added.emit(f"⚠️ Не удалось проверить модлоадеры: {e}", "orange")

            # Финальный отчет
            self.finished.emit({
                "problems": self.problems_found,
                "problem_count": len(self.problems_found)
            })

        except Exception as e:
            self.result_added.emit(f"❌ Ошибка диагностики: {str(e)}", "red")
            self.finished.emit({
                "problems": [str(e)],
                "problem_count": 1,
                "error": str(e)
            })

    def _check_java(self) -> bool:
        """Проверяет наличие Java 17+"""
        try:
            result = subprocess.run(
                ["java", "-version"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                timeout=10
            )
            version_output = (result.stderr or result.stdout).lower()

            import re
            match = re.search(r'version "([0-9]+)\.', version_output)
            if match:
                major_version = int(match.group(1))
                return major_version >= 17

            match = re.search(r'version "1\.([0-9]+)\.', version_output)
            if match:
                major_version = int(match.group(1))
                return major_version >= 8 and major_version <= 21

            return "openjdk" in version_output or "java" in version_output
        except:
            return False

    def _get_java_version(self) -> str:
        """Возвращает версию Java"""
        try:
            result = subprocess.run(
                ["java", "-version"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                timeout=5
            )
            output = (result.stderr or result.stdout).strip()
            lines = output.split('\n')
            if lines:
                return lines[0].strip()
            return "Неизвестно"
        except:
            return "Не найдена"


from PyQt6.QtGui import QIcon
from ConfDir.Configs import resource_path


class QtDiagnosticWindow(QMainWindow):
    """Окно диагностики на PyQt6"""

    def __init__(self, parent=None, selected_version=None):
        super().__init__(parent)

        self.selected_version = selected_version or "YamalPixel"

        self.setWindowTitle("Диагностика проблем")
        self.setMinimumSize(900, 650)
        self.setStyleSheet(self._get_stylesheet())

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("🔧 Диагностика проблем")
        title.setFont(QFont("Comfortaa", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Автоматическая проверка и решение проблем")
        subtitle.setFont(QFont("Comfortaa", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(20)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Проводим диагностику...")
        self.status_label.setFont(QFont("Comfortaa", 10))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Результаты
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        self.results_text.setMinimumHeight(350)
        main_layout.addWidget(self.results_text)

        # Кнопки действий
        actions_label = QLabel("🔧 Действия")
        actions_label.setFont(QFont("Comfortaa", 12, QFont.Weight.Bold))
        main_layout.addWidget(actions_label)

        buttons_layout = QHBoxLayout()

        self.launch_btn = QPushButton("🎮 Запуск без модов")
        self.launch_btn.clicked.connect(self.launch_without_mods)
        buttons_layout.addWidget(self.launch_btn)

        self.reinstall_btn = QPushButton("🔄 Полная переустановка")
        self.reinstall_btn.clicked.connect(self.complete_reinstall)
        buttons_layout.addWidget(self.reinstall_btn)

        self.repair_btn = QPushButton("🔧 Автопочинка")
        self.repair_btn.clicked.connect(self.auto_repair)
        buttons_layout.addWidget(self.repair_btn)

        self.report_btn = QPushButton("📄 Создать отчет")
        self.report_btn.clicked.connect(self.create_report)
        buttons_layout.addWidget(self.report_btn)

        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_btn)

        main_layout.addLayout(buttons_layout)

        # Статус-бар
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Готов к работе")

        # Запускаем диагностику
        self.start_diagnostic()
        self.set_window_icon()

    def set_window_icon(self):
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"⚠️ Ошибка установки иконки: {e}")

    def _get_stylesheet(self) -> str:
        return """
            QMainWindow {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff88;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5568, stop:1 #2d3748);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Comfortaa', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6b82, stop:1 #3d4a5c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3a4458, stop:1 #1f2a36);
            }
            QProgressBar {
                border: 1px solid #4a5568;
                border-radius: 5px;
                text-align: center;
                background-color: #1a1a1a;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4ecdc4, stop:1 #667eea);
                border-radius: 4px;
            }
            QFrame[frameShape="4"] {
                color: #4a5568;
                background-color: #4a5568;
                max-height: 1px;
            }
            QStatusBar {
                background-color: #1a1a1a;
                color: #888888;
            }
        """

    def start_diagnostic(self):
        self.worker = DiagnosticWorker(selected_version=self.selected_version)
        self.worker.result_added.connect(self.add_result)
        self.worker.finished.connect(self.on_diagnostic_finished)
        self.worker.start()

    def add_result(self, text: str, color: str):
        color_map = {
            "green": "#00ff88",
            "red": "#ff4444",
            "orange": "#ffaa00",
            "cyan": "#00ccff",
            "default": "#ffffff"
        }

        hex_color = color_map.get(color, "#ffffff")

        self.results_text.moveCursor(QTextCursor.MoveOperation.End)
        self.results_text.setTextColor(QColor(hex_color))
        self.results_text.insertPlainText(text + "\n")
        self.results_text.moveCursor(QTextCursor.MoveOperation.End)

    def on_diagnostic_finished(self, result: dict):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        problem_count = result.get("problem_count", 0)

        if problem_count > 0:
            self.status_label.setText(f"⚠️ Обнаружено {problem_count} проблем")
            self.status_label.setStyleSheet("color: #ffaa00")
            self.status_bar.showMessage(f"Найдено {problem_count} проблем, используйте кнопки действий для исправления")
        else:
            self.status_label.setText("✅ Проблем не обнаружено!")
            self.status_label.setStyleSheet("color: #00ff88")
            self.status_bar.showMessage("Все системы в норме")

            self.add_result("\n🎉 Все системы в норме!", "green")
            self.add_result("Игра должна запускаться без проблем", "cyan")

    def launch_without_mods(self):
        """Запуск без модов"""
        reply = QMessageBox.question(
            self,
            "Запуск без модов",
            "Запустить игру БЕЗ ВСЕХ модов?\n\n"
            "Это поможет определить:\n"
            "• Проблема в модах или в игре\n"
            "• Конфликтующие моды\n\n"
            "После проверки можно включить моды обратно.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Находим главное окно
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'launch_without_mods'):
                self.close()  # Закрываем диагностику
                main_window.launch_without_mods()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти главное окно")

    def complete_reinstall(self):
        """Полная переустановка"""
        reply = QMessageBox.question(
            self,
            "Полная переустановка",
            "⚠️ ВНИМАНИЕ! Это удалит ВСЕ файлы игры и настроек.\n\n"
            "Будет выполнено:\n"
            "• Удаление папки YamalPixel\n"
            "• Удаление всех модов и конфигов\n"
            "• Удаление миров и сохранений\n"
            "• Создание чистых бэкапов\n\n"
            "Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'complete_reinstall'):
                self.close()
                main_window.complete_reinstall()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти главное окно")

    def auto_repair(self):
        """Автопочинка"""
        reply = QMessageBox.question(
            self,
            "Автопочинка",
            "🔧 Запустить автоматическую починку файлов игры?\n\n"
            "Будет выполнено:\n"
            "• Проверка и создание недостающих папок\n"
            "• Проверка и загрузка отсутствующих модов\n"
            "• Проверка и установка Fabric/Forge\n"
            "• Восстановление поврежденных файлов\n\n"
            "Это может занять несколько минут.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Находим главное окно
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'old_repair_with_ui'):
                # Закрываем диагностику ПЕРЕД запуском автопочинки
                self.close()
                # Запускаем автопочинку
                main_window.old_repair_with_ui()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти главное окно")

    def create_report(self):
        """Создает отчет"""
        report_path = os.path.join(CONFIG["minecraft_dir"], "diagnostic_report.txt")

        try:
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("YamalPixel Launcher - Диагностический отчет\n")
                f.write(f"Дата: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Версия лаунчера: {CURRENT_VERSION}\n")
                f.write(f"Выбранная версия: {self.selected_version}\n")
                f.write("=" * 60 + "\n\n")
                f.write(self.results_text.toPlainText())
                f.write("\n\n" + "=" * 60 + "\n")
                f.write("Конец отчета\n")

            QMessageBox.information(
                self,
                "Отчет создан",
                f"📄 Отчет сохранен в:\n{report_path}\n\n"
                f"Вы можете отправить этот файл разработчику для помощи в решении проблем."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось сохранить отчет:\n{str(e)}"
            )

    def _find_main_window(self):
        """Находит главное окно лаунчера"""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "MainWindow":
                return parent
            parent = parent.parent()

        # Если не нашли через parent, ищем среди всех окон
        for widget in QApplication.topLevelWidgets():
            if widget.__class__.__name__ == "MainWindow":
                return widget

        return None

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)
        event.accept()