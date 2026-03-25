# Ui/CollectionCreator.py
import os
import json
import threading
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QTextEdit, QMessageBox, QWidget, QFrame,
    QApplication, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from Core.collection_loader import save_collection
from Network.ModrinthLoader import ModrinthAPI
from Network.CurseForgeLoader import CurseForgeAPI
from ConfDir.Configs import CURSEFORGE_CONFIG
from ConfDir.Versions import all_versions
from Ui.DependencyAnalyzer import DependencyAnalyzerUI


class SearchWorker(QThread):
    finished = pyqtSignal(list, str)
    error = pyqtSignal(str, str)

    def __init__(self, source, query, minecraft_version, loader):
        super().__init__()
        self.source = source
        self.query = query
        self.minecraft_version = minecraft_version
        self.loader = loader

    def run(self):
        try:
            if self.source == "modrinth":
                api = ModrinthAPI()
                results = api.search_mods(self.query, limit=50)
                if results and "hits" in results:
                    self.finished.emit(results["hits"], "modrinth")
                else:
                    self.finished.emit([], "modrinth")

            elif self.source == "curseforge":
                # Создаем API с увеличенным таймаутом
                api = CurseForgeAPI()
                # Увеличиваем таймаут для сессии
                api.timeout = 60
                api.session.timeout = 60

                if not api.test_connection():
                    self.error.emit("Прокси-сервер недоступен", "curseforge")
                    return

                results = api.search_mods(
                    query=self.query,
                    minecraft_version=self.minecraft_version,
                    loader=self.loader,
                    limit=50
                )
                if results and results.get("success") and results.get("data"):
                    self.finished.emit(results["data"], "curseforge")
                else:
                    self.finished.emit([], "curseforge")

        except requests.exceptions.Timeout:
            self.error.emit("Таймаут подключения к серверу (попробуйте позже)", self.source)
        except Exception as e:
            self.error.emit(str(e), self.source)


class CollectionCreator(QDialog):
    """Диалог создания новой сборки"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создание новой сборки")
        self.setMinimumSize(1100, 700)
        self.setModal(True)

        self.selected_mods = []

        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("📦 Создание новой сборки")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Основные настройки
        settings_frame = QFrame()
        settings_frame.setObjectName("settings_frame")
        settings_layout = QHBoxLayout(settings_frame)
        settings_layout.setSpacing(20)

        # Название
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Название сборки:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите название")
        self.name_input.setMinimumWidth(250)
        name_layout.addWidget(self.name_input)
        settings_layout.addLayout(name_layout)

        # Версия Minecraft
        version_layout = QVBoxLayout()
        version_layout.addWidget(QLabel("Версия Minecraft:"))
        self.version_combo = QComboBox()
        self.version_combo.addItems(all_versions)
        self.version_combo.setCurrentText("1.20.1")
        version_layout.addWidget(self.version_combo)
        settings_layout.addLayout(version_layout)

        # Загрузчик
        loader_layout = QVBoxLayout()
        loader_layout.addWidget(QLabel("Загрузчик:"))
        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["fabric", "forge", "quilt", "neoforge"])
        loader_layout.addWidget(self.loader_combo)
        settings_layout.addLayout(loader_layout)

        settings_layout.addStretch()
        layout.addWidget(settings_frame)

        # Вкладки
        self.tab_widget = QTabWidget()

        # Modrinth
        self.modrinth_tab = self.create_search_tab("modrinth")
        self.tab_widget.addTab(self.modrinth_tab, "🌐 Modrinth")

        # CurseForge
        self.curseforge_tab = self.create_search_tab("curseforge")
        self.tab_widget.addTab(self.curseforge_tab, "⚡ CurseForge")

        layout.addWidget(self.tab_widget)

        # Выбранные моды
        selected_frame = QFrame()
        selected_frame.setObjectName("selected_frame")
        selected_layout = QVBoxLayout(selected_frame)

        selected_header = QHBoxLayout()
        selected_header.addWidget(QLabel("✅ Выбранные моды"))
        selected_header.addStretch()
        self.selected_count_label = QLabel("Всего: 0")
        selected_header.addWidget(self.selected_count_label)
        selected_layout.addLayout(selected_header)

        self.selected_tree = QTreeWidget()
        self.selected_tree.setHeaderLabels(["Источник", "Название", "Файл"])
        self.selected_tree.setColumnWidth(0, 100)
        self.selected_tree.setColumnWidth(1, 350)
        self.selected_tree.setColumnWidth(2, 250)
        self.selected_tree.setMaximumHeight(150)
        selected_layout.addWidget(self.selected_tree)

        # Кнопки
        buttons_row = QHBoxLayout()
        self.remove_btn = QPushButton("🗑️ Удалить выбранный")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("🗑️ Очистить все")
        self.clear_btn.clicked.connect(self.clear_all)
        buttons_row.addWidget(self.remove_btn)
        buttons_row.addWidget(self.clear_btn)
        buttons_row.addStretch()
        selected_layout.addLayout(buttons_row)

        layout.addWidget(selected_frame)

        # Кнопки сохранения
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        # Кнопка анализа зависимостей
        self.analyze_btn = QPushButton("🔍 Анализ зависимостей")
        self.analyze_btn.clicked.connect(self.analyze_dependencies)
        save_layout.addWidget(self.analyze_btn)

        self.save_btn = QPushButton("✅ Сохранить сборку")
        self.save_btn.clicked.connect(self.save_collection)
        self.save_btn.setMinimumWidth(150)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        save_layout.addWidget(self.save_btn)
        save_layout.addWidget(self.cancel_btn)
        layout.addLayout(save_layout)

    def analyze_dependencies(self):
        """Анализирует зависимости выбранных модов"""
        if not self.selected_mods:
            QMessageBox.warning(self, "Анализ", "Добавьте моды для анализа")
            return

        # Выводим информацию о модах для анализа
        print("=" * 60)
        print("🔍 Анализ зависимостей для модов:")
        for i, mod in enumerate(self.selected_mods, 1):
            source = mod.get('source', 'unknown')
            name = mod.get('name', 'Unknown')
            mod_id = mod.get('modrinth_id') or mod.get('curseforge_id')
            print(f"  {i}. [{source.upper()}] {name} (ID: {mod_id})")
        print("=" * 60)

        # Создаем анализатор
        analyzer = DependencyAnalyzerUI(
            parent=self,
            minecraft_version=self.version_combo.currentText(),
            loader=self.loader_combo.currentText(),
            tree_widget=self.selected_tree
        )

        def on_analysis_complete(result):
            required_count = len(result.get('required_dependencies', []))
            optional_count = len(result.get('optional_dependencies', []))

            print(f"\n📊 Результат анализа:")
            print(f"   - Обязательных зависимостей: {required_count}")
            print(f"   - Опциональных зависимостей: {optional_count}")

            for dep in result.get('required_dependencies', []):
                print(f"      🔴 Обязательная: {dep.name} ({dep.source})")
            for dep in result.get('optional_dependencies', []):
                print(f"      🟡 Опциональная: {dep.name} ({dep.source})")

            QMessageBox.information(
                self,
                "Анализ завершен",
                f"Найдено зависимостей:\n"
                f"• Обязательных: {required_count}\n"
                f"• Опциональных: {optional_count}\n\n"
                f"Проверьте консоль для деталей."
            )

        analyzer.show_analyzer(self.selected_mods, on_analysis_complete)

    def create_search_tab(self, source):
        """Создает вкладку поиска"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Поисковая строка
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))

        search_input = QLineEdit()
        search_input.setPlaceholderText("Введите название мода...")
        search_layout.addWidget(search_input)

        search_btn = QPushButton("🔍 Поиск")
        search_layout.addWidget(search_btn)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Результаты
        tree = QTreeWidget()
        tree.setHeaderLabels(["Название", "Автор", "Загрузки", "Совместимость"])
        tree.setColumnWidth(0, 320)
        tree.setColumnWidth(1, 150)
        tree.setColumnWidth(2, 100)
        tree.setColumnWidth(3, 100)
        tree.itemDoubleClicked.connect(lambda item, col: self.add_mod(item, source))
        layout.addWidget(tree)

        # Статус
        status_label = QLabel("Готов к поиску")
        status_label.setStyleSheet("color: #888888;")
        layout.addWidget(status_label)

        # Сохраняем виджеты
        if source == "modrinth":
            self.modrinth_search = search_input
            self.modrinth_btn = search_btn
            self.modrinth_tree = tree
            self.modrinth_status = status_label
            self.modrinth_btn.clicked.connect(lambda: self.search_mods("modrinth"))
        else:
            self.curseforge_search = search_input
            self.curseforge_btn = search_btn
            self.curseforge_tree = tree
            self.curseforge_status = status_label
            self.curseforge_btn.clicked.connect(lambda: self.search_mods("curseforge"))

        return tab

    def setup_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel#title {
                color: #4ECDC4;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
            QFrame#settings_frame, QFrame#selected_frame {
                background-color: #1e1e2a;
                border-radius: 10px;
                padding: 15px;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QComboBox {
                background-color: #2a2a3a;
                color: white;
                border: 1px solid #3a3a4a;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #4ECDC4;
            }
            QTreeWidget {
                background-color: #1a1a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a4a;
                border-radius: 8px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #4ECDC4;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #2a2a3a;
                color: #4ECDC4;
                padding: 5px;
                border: none;
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
            QPushButton:disabled {
                background-color: #2a2a3a;
                color: #666;
            }
        """)

    def search_mods(self, source):
        """Запускает поиск"""
        if source == "modrinth":
            query = self.modrinth_search.text().strip()
            if not query:
                self.modrinth_status.setText("Введите название для поиска")
                return
            self.modrinth_status.setText("Поиск на Modrinth...")
            self.modrinth_btn.setEnabled(False)
            self.modrinth_tree.clear()
            self.modrinth_status.setStyleSheet("color: #ffaa00;")
        else:
            query = self.curseforge_search.text().strip()
            if not query:
                self.curseforge_status.setText("Введите название для поиска")
                return
            self.curseforge_status.setText("Поиск на CurseForge... (может занять до 30 секунд)")
            self.curseforge_btn.setEnabled(False)
            self.curseforge_tree.clear()
            self.curseforge_status.setStyleSheet("color: #ffaa00;")

        self.worker = SearchWorker(
            source, query,
            self.version_combo.currentText(),
            self.loader_combo.currentText()
        )
        self.worker.finished.connect(lambda r, s: self.display_results(r, s))
        self.worker.error.connect(lambda e, s: self.show_error(e, s))
        self.worker.start()

    def display_results(self, results, source):
        """Отображает результаты поиска"""
        if source == "modrinth":
            self.modrinth_btn.setEnabled(True)
            self.modrinth_status.setStyleSheet("color: #888888;")
            if not results:
                self.modrinth_status.setText("Ничего не найдено")
                return
            self.modrinth_status.setText(f"Найдено {len(results)} модов")
            self.modrinth_tree.clear()

            for mod in results:
                item = QTreeWidgetItem()
                item.setText(0, mod.get("title", "Unknown"))
                item.setText(1, mod.get("author", "Unknown"))
                item.setText(2, f"{mod.get('downloads', 0):,}")
                item.setText(3, "✅")
                # Сохраняем project_id
                mod_data = {
                    "project_id": mod.get("project_id"),
                    "slug": mod.get("slug"),
                    "title": mod.get("title"),
                    "author": mod.get("author"),
                    "downloads": mod.get("downloads")
                }
                item.setData(0, Qt.ItemDataRole.UserRole, mod_data)
                self.modrinth_tree.addTopLevelItem(item)
        else:
            self.curseforge_btn.setEnabled(True)
            self.curseforge_status.setStyleSheet("color: #888888;")
            if not results:
                self.curseforge_status.setText("Ничего не найдено")
                return
            self.curseforge_status.setText(f"Найдено {len(results)} модов")
            self.curseforge_tree.clear()

            for mod in results:
                item = QTreeWidgetItem()
                item.setText(0, mod.get("title", "Unknown"))
                item.setText(1, mod.get("author", "Unknown"))
                item.setText(2, f"{mod.get('downloads', 0):,}")
                compatible = mod.get("compatible", True)
                item.setText(3, "✅" if compatible else "❌")
                # Сохраняем project_id как строку
                mod_data = {
                    "project_id": mod.get("project_id"),
                    "slug": mod.get("slug", ""),
                    "title": mod.get("title"),
                    "author": mod.get("author"),
                    "downloads": mod.get("downloads"),
                    "filename": mod.get("filename", f"{mod.get('slug', mod.get('project_id'))}.jar")
                }
                item.setData(0, Qt.ItemDataRole.UserRole, mod_data)
                self.curseforge_tree.addTopLevelItem(item)

    def show_error(self, error, source):
        """Показывает ошибку"""
        if source == "modrinth":
            self.modrinth_btn.setEnabled(True)
            self.modrinth_status.setText(f"❌ Ошибка: {error}")
            self.modrinth_status.setStyleSheet("color: #ff8888;")
        else:
            self.curseforge_btn.setEnabled(True)
            self.curseforge_status.setText(f"❌ Ошибка: {error}")
            self.curseforge_status.setStyleSheet("color: #ff8888;")

    def add_mod(self, item, source):
        """Добавляет мод в выбранные"""
        mod_data = item.data(0, Qt.ItemDataRole.UserRole)

        # Проверяем, не добавлен ли уже
        for existing in self.selected_mods:
            if source == "modrinth" and existing.get("modrinth_id") == mod_data.get("project_id"):
                QMessageBox.information(self, "Информация", f"Мод '{mod_data.get('title')}' уже добавлен")
                return
            if source == "curseforge" and existing.get("curseforge_id") == str(mod_data.get("project_id")):
                QMessageBox.information(self, "Информация", f"Мод '{mod_data.get('title')}' уже добавлен")
                return

        if source == "modrinth":
            mod_info = {
                "source": "modrinth",
                "modrinth_id": mod_data.get("project_id"),
                "modrinth_slug": mod_data.get("slug"),
                "name": mod_data.get("title"),
                "filename": f"{mod_data.get('slug', mod_data.get('project_id'))}.jar"
            }
        else:
            mod_info = {
                "source": "curseforge",
                "curseforge_id": str(mod_data.get("project_id")),
                "curseforge_slug": mod_data.get("slug", ""),
                "name": mod_data.get("title"),
                "filename": mod_data.get("filename", f"{mod_data.get('slug', mod_data.get('project_id'))}.jar")
            }

        self.selected_mods.append(mod_info)
        self.update_selected_list()

        # Показываем сообщение об успешном добавлении
        QMessageBox.information(
            self,
            "Мод добавлен",
            f"✅ Мод '{mod_info['name']}' добавлен в сборку.\n\n"
            f"Теперь вы можете проанализировать зависимости через кнопку 'Анализ зависимостей'."
        )

    def _analyze_and_add_dependencies(self, mod_info: Dict):
        """Анализирует зависимости добавленного мода и добавляет их в список"""
        from Network.DependencyManager import DependencyManager

        print(f"\n🔍 Анализ зависимостей для добавленного мода: {mod_info.get('name')}")

        # Создаем менеджер зависимостей
        dep_manager = DependencyManager()

        # Получаем зависимости
        dependencies = dep_manager.resolve_dependencies_for_mod(
            mod_info,
            self.version_combo.currentText(),
            self.loader_combo.currentText()
        )

        print(f"📊 Найдено зависимостей: {len(dependencies)}")

        # Добавляем обязательные зависимости в список
        added_count = 0
        for dep in dependencies:
            if dep.dependency_type == 'required':
                # Проверяем, нет ли уже такой зависимости
                exists = False
                for existing in self.selected_mods:
                    existing_id = existing.get('modrinth_id') or existing.get('curseforge_id')
                    dep_id = dep.mod_id or dep.project_id
                    if existing_id == dep_id or existing.get('name') == dep.name:
                        exists = True
                        break

                if not exists:
                    # Создаем данные для зависимости
                    dep_data = {
                        "source": dep.source,
                        "name": dep.name,
                        "filename": f"{dep.mod_id or dep.project_id}.jar"
                    }

                    if dep.source == "modrinth":
                        dep_data["modrinth_id"] = dep.project_id
                        dep_data["modrinth_slug"] = dep.mod_id or dep.project_id
                    else:
                        dep_data["curseforge_id"] = dep.project_id
                        dep_data["curseforge_slug"] = dep.mod_id or dep.project_id

                    self.selected_mods.append(dep_data)
                    added_count += 1
                    print(f"  ✅ Добавлена зависимость: {dep.name} ({dep.source})")

        if added_count > 0:
            self.update_selected_list()
            print(f"✅ Добавлено {added_count} зависимостей")
        else:
            print(f"ℹ️ Нет новых зависимостей для добавления")

    def remove_selected(self):
        """Удаляет выбранный мод"""
        current = self.selected_tree.currentItem()
        if current:
            index = self.selected_tree.indexOfTopLevelItem(current)
            if index >= 0:
                del self.selected_mods[index]
                self.update_selected_list()

    def clear_all(self):
        """Очищает все выбранные моды"""
        self.selected_mods.clear()
        self.update_selected_list()

    def update_selected_list(self):
        """Обновляет список выбранных модов"""
        self.selected_tree.clear()

        for mod in self.selected_mods:
            source_icon = "🌐" if mod["source"] == "modrinth" else "⚡"
            item = QTreeWidgetItem()
            item.setText(0, f"{source_icon} {mod['source'].capitalize()}")
            item.setText(1, mod["name"])
            item.setText(2, mod["filename"])
            self.selected_tree.addTopLevelItem(item)

        self.selected_count_label.setText(f"Всего: {len(self.selected_mods)}")

    def save_collection(self):
        """Сохраняет сборку"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название сборки!")
            return

        if not self.selected_mods:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один мод!")
            return

        # Собираем данные
        collection_data = {
            "name": name,
            "minecraft_version": self.version_combo.currentText(),
            "loader": self.loader_combo.currentText(),
            "created_at": datetime.now().isoformat(),
            "mods": self.selected_mods,
            "mod_count": len(self.selected_mods),
            "source": "local"
        }

        # Сохраняем
        success, result = save_collection(collection_data)  # из Core.collection_loader

        if success:
            QMessageBox.information(
                self,
                "Успех",
                f"Сборка '{name}' успешно создана!\n\n"
                f"• Модов: {len(self.selected_mods)}\n"
                f"• Версия: {self.version_combo.currentText()}\n"
                f"• Загрузчик: {self.loader_combo.currentText()}"
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить сборку:\n{result}")