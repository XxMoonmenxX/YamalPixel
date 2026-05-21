## Ui/collection_manager.py
import os
import json
import threading
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QWidget, QSplitter,
    QTextEdit, QFrame, QTabWidget, QLineEdit, QComboBox,
    QProgressBar, QApplication
)

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QColor

from Core.collection_loader import (
    load_all_collections, delete_collection, install_collection,
    get_collections_dir, get_collection_mods_info, save_collection
)
from ConfDir.Configs import COLLECTIONS_CONFIG
from ConfDir.Versions import CURRENT_VERSION, all_versions

from Ui.BaseWindow import BaseDialog

# Конфигурация сервера сообщества
COMMUNITY_SERVER_URL = "http://90.151.59.120:8000"
SERVER_API_KEY = "F9bK7pL2sR5wX8zQ3vN6yT1mC4eB7gH0jU"

try:
    from Ui.CollectionCreator import CollectionCreator
except ImportError:
    CollectionCreator = None
    print("⚠️ CollectionCreator не найден")


print("=== IMPORTING collection_manager.py ===")
import sys
sys.stdout.flush()

print("  Import 1: os")
import os
sys.stdout.flush()

print("  Import 2: json")
import json
sys.stdout.flush()

print("  Import 3: threading")
import threading
sys.stdout.flush()

print("  Import 4: requests")
import requests
sys.stdout.flush()

print("  Import 5: datetime")
from datetime import datetime
sys.stdout.flush()

print("  Import 6: PyQt6.QtWidgets")
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QWidget, QSplitter,
    QTextEdit, QFrame, QTabWidget, QLineEdit, QComboBox,
    QProgressBar, QApplication
)
sys.stdout.flush()

print("  Import 7: PyQt6.QtCore")
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, pyqtSlot
sys.stdout.flush()

print("  Import 8: PyQt6.QtGui")
from PyQt6.QtGui import QFont, QIcon, QColor
sys.stdout.flush()

print("  Import 9: Core.collection_loader")
from Core.collection_loader import (
    load_all_collections, delete_collection, install_collection,
    get_collections_dir, get_collection_mods_info, save_collection
)
sys.stdout.flush()

print("  Import 10: ConfDir.Configs")
from ConfDir.Configs import COLLECTIONS_CONFIG
sys.stdout.flush()

print("  Import 11: ConfDir.Versions")
from ConfDir.Versions import CURRENT_VERSION, all_versions
sys.stdout.flush()

print("=== collection_manager.py imports complete ===")
sys.stdout.flush()


class CommunityAPI:
    """API для работы с общедоступными сборками"""

    def __init__(self):
        self.base_url = COMMUNITY_SERVER_URL
        self.headers = {
            "X-API-Key": SERVER_API_KEY,
            "Content-Type": "application/json"
        }
        self.timeout = 30

    def test_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/community/ping", timeout=10, headers=self.headers)
            return response.status_code == 200
        except:
            return False

    def get_collections(self, page=1, limit=20, category="all"):
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/collections",
                params={"page": page, "limit": limit, "category": category, "sort_by": "downloads"},
                timeout=self.timeout,
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return {"success": False, "error": f"Ошибка сервера: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_collection_details(self, collection_id):
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/collection/{collection_id}",
                timeout=self.timeout,
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_collection(self, collection_id):
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/download/{collection_id}",
                timeout=self.timeout,
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def increment_downloads(self, collection_id):
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/community/stats/download/{collection_id}",
                timeout=10,
                headers=self.headers
            )
            return response.status_code == 200
        except:
            return False

    def search_collections(self, query, page=1, limit=20):
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/search",
                params={"q": query, "page": page, "limit": limit},
                timeout=self.timeout,
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return {"success": False, "error": f"Ошибка поиска: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_collection(self, collection_data, username="anonymous"):
        try:
            collection_data["uploader"] = username
            collection_data["upload_date"] = datetime.now().isoformat()
            collection_data["downloads"] = 0

            response = requests.post(
                f"{self.base_url}/api/v1/community/upload",
                json=collection_data,
                timeout=self.timeout,
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return {"success": False, "error": f"Ошибка загрузки: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_categories(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/community/categories", timeout=10, headers=self.headers)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"categories": ["Все", "Оптимизация", "Технологии", "Приключения", "Квесты", "Магия", "Биомы",
                               "Строительство", "Выживание", "PvP"]}


class CommunityCollectionsTab(QWidget):
    """Вкладка со сборками сообщества"""

    collection_selected = pyqtSignal(dict)
    display_collections_signal = pyqtSignal(dict)
    display_search_results_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.api = CommunityAPI()
        self.current_page = 1
        self.total_pages = 1

        self.display_collections_signal.connect(self._display_collections)
        self.display_search_results_signal.connect(self._display_search_results)

        self.setup_ui()
        self.load_categories()
        self.load_collections()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Панель поиска и фильтров
        filter_layout = QHBoxLayout()

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск сборок...")
        self.search_input.setMinimumWidth(250)
        filter_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("🔍 Поиск")
        self.search_btn.clicked.connect(self.search_collections)
        filter_layout.addWidget(self.search_btn)

        filter_layout.addSpacing(20)

        # Категории
        filter_layout.addWidget(QLabel("Категория:"))
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(150)
        self.category_combo.currentTextChanged.connect(self.load_collections)
        filter_layout.addWidget(self.category_combo)

        filter_layout.addStretch()

        # Кнопка обновления
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(lambda: self.load_collections(1))
        filter_layout.addWidget(self.refresh_btn)

        layout.addLayout(filter_layout)

        # Список сборок
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Название", "Автор", "Версия", "Модов", "Скачиваний", "Рейтинг", "Обновлено"])
        self.tree.setColumnWidth(0, 280)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 60)
        self.tree.setColumnWidth(4, 80)
        self.tree.setColumnWidth(5, 80)
        self.tree.setColumnWidth(6, 100)
        self.tree.itemDoubleClicked.connect(self.on_collection_double_click)
        layout.addWidget(self.tree)

        # Пагинация
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self.prev_btn = QPushButton("◀ Назад")
        self.prev_btn.clicked.connect(lambda: self.load_collections(self.current_page - 1))
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Страница 1 из 1")
        pagination_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Вперед ▶")
        self.next_btn.clicked.connect(lambda: self.load_collections(self.current_page + 1))
        pagination_layout.addWidget(self.next_btn)

        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        # Статус
        self.status_label = QLabel("Готов")
        self.status_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.status_label)

    def load_categories(self):
        try:
            data = self.api.get_categories()
            categories = data.get("categories",
                                  ["Все", "Оптимизация", "Технологии", "Приключения", "Квесты", "Магия", "Биомы",
                                   "Строительство", "Выживание", "PvP"])
            self.category_combo.clear()
            self.category_combo.addItems(categories)
        except:
            self.category_combo.addItems(
                ["Все", "Оптимизация", "Технологии", "Приключения", "Квесты", "Магия", "Биомы", "Строительство",
                 "Выживание", "PvP"])

    def load_collections(self, page=1):
        self.current_page = page
        self.status_label.setText("Загрузка сборок...")
        self.tree.clear()

        def load_thread():
            category = self.category_combo.currentText()
            category_param = "all" if category == "Все" else category.lower()

            result = self.api.get_collections(page=page, limit=20, category=category_param)
            # Используем сигнал вместо invokeMethod
            self.display_collections_signal.emit(result)

        threading.Thread(target=load_thread, daemon=True).start()

    def _display_collections(self, result):
        """Отображает сборки (вызывается через сигнал)"""
        if not result.get("success", False):
            self.status_label.setText(f"❌ {result.get('error', 'Ошибка загрузки')}")
            return

        collections = result.get("collections", [])
        self.total_pages = result.get("total_pages", 1)

        self.page_label.setText(f"Страница {self.current_page} из {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

        if not collections:
            item = QTreeWidgetItem(["Нет сборок", "", "", "", "", "", ""])
            self.tree.addTopLevelItem(item)
            self.status_label.setText("Сборок не найдено")
            return

        for col in collections:
            # Форматирование даты
            updated_date = col.get("updated_at", col.get("upload_date", ""))
            if updated_date:
                try:
                    dt = datetime.fromisoformat(updated_date.replace('Z', '+00:00'))
                    updated_str = dt.strftime("%d.%m.%Y")
                except:
                    updated_str = updated_date[:10]
            else:
                updated_str = "Неизвестно"

            # Рейтинг в звездах
            rating = col.get("rating", 0)
            rating_str = "★" * int(rating) + "☆" * (5 - int(rating)) if rating > 0 else "Нет оценок"

            item = QTreeWidgetItem()
            item.setText(0, col["name"])
            item.setText(1, col.get("uploader", "Неизвестно"))
            item.setText(2, col.get("minecraft_version", "1.20.1"))
            item.setText(3, str(col.get("mod_count", 0)))
            item.setText(4, f"{col.get('downloads', 0):,}")
            item.setText(5, rating_str)
            item.setText(6, updated_str)
            item.setData(0, Qt.ItemDataRole.UserRole, col["id"])
            item.setData(0, Qt.ItemDataRole.UserRole + 1, col)
            self.tree.addTopLevelItem(item)

        self.status_label.setText(f"✅ Загружено {len(collections)} сборок")

    def search_collections(self):
        query = self.search_input.text().strip()
        if not query:
            self.load_collections(1)
            return

        self.status_label.setText(f"Поиск: {query}...")
        self.tree.clear()

        def search_thread():
            result = self.api.search_collections(query, limit=50)
            # Используем сигнал вместо invokeMethod
            self.display_search_results_signal.emit(result)

        threading.Thread(target=search_thread, daemon=True).start()

    def _display_search_results(self, result):
        """Отображает результаты поиска (вызывается через сигнал)"""
        if not result.get("success", False):
            self.status_label.setText(f"❌ Ошибка поиска: {result.get('error', 'Неизвестная ошибка')}")
            return

        collections = result.get("collections", [])

        if not collections:
            item = QTreeWidgetItem(["Ничего не найдено", "", "", "", "", "", ""])
            self.tree.addTopLevelItem(item)
            self.status_label.setText("Ничего не найдено")
            return

        for col in collections:
            item = QTreeWidgetItem()
            item.setText(0, col["name"])
            item.setText(1, col.get("uploader", "Неизвестно"))
            item.setText(2, col.get("minecraft_version", "1.20.1"))
            item.setText(3, str(col.get("mod_count", 0)))
            item.setText(4, f"{col.get('downloads', 0):,}")
            item.setText(5, "Нет оценок")
            item.setText(6, col.get("upload_date", "Неизвестно")[:10])
            item.setData(0, Qt.ItemDataRole.UserRole, col["id"])
            item.setData(0, Qt.ItemDataRole.UserRole + 1, col)
            self.tree.addTopLevelItem(item)

        self.status_label.setText(f"✅ Найдено {len(collections)} сборок")
        self.page_label.setText("Результаты поиска")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

    def search_collections(self):
        query = self.search_input.text().strip()
        if not query:
            self.load_collections(1)
            return

        self.status_label.setText(f"Поиск: {query}...")
        self.tree.clear()

        def search_thread():
            result = self.api.search_collections(query, limit=50)
            from PyQt6.QtCore import QMetaObject, Q_ARG
            QMetaObject.invokeMethod(self, "display_search_results", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(dict, result))

        threading.Thread(target=search_thread, daemon=True).start()

    def display_search_results(self, result):
        if not result.get("success", False):
            self.status_label.setText(f"❌ Ошибка поиска: {result.get('error', 'Неизвестная ошибка')}")
            return

        collections = result.get("collections", [])

        if not collections:
            item = QTreeWidgetItem(["Ничего не найдено", "", "", "", "", "", ""])
            self.tree.addTopLevelItem(item)
            self.status_label.setText("Ничего не найдено")
            return

        for col in collections:
            item = QTreeWidgetItem()
            item.setText(0, col["name"])
            item.setText(1, col.get("uploader", "Неизвестно"))
            item.setText(2, col.get("minecraft_version", "1.20.1"))
            item.setText(3, str(col.get("mod_count", 0)))
            item.setText(4, f"{col.get('downloads', 0):,}")
            item.setText(5, "Нет оценок")
            item.setText(6, col.get("upload_date", "Неизвестно")[:10])
            item.setData(0, Qt.ItemDataRole.UserRole, col["id"])
            item.setData(0, Qt.ItemDataRole.UserRole + 1, col)
            self.tree.addTopLevelItem(item)

        self.status_label.setText(f"✅ Найдено {len(collections)} сборок")
        self.page_label.setText("Результаты поиска")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

    def on_collection_double_click(self, item, column):
        collection_id = item.data(0, Qt.ItemDataRole.UserRole)
        collection_data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        self.show_collection_details(collection_id, collection_data)

    def show_collection_details(self, collection_id, collection_data):
        dialog = CommunityCollectionDetailsDialog(self, collection_id, collection_data, self.api)
        dialog.collection_imported.connect(self.on_collection_imported)
        dialog.exec()

    def on_collection_imported(self):
        """Обновляем список после импорта"""
        self.load_collections(self.current_page)


class CommunityCollectionDetailsDialog(BaseDialog):
    """Диалог деталей сборки сообщества"""

    collection_imported = pyqtSignal()

    def __init__(self, parent, collection_id, collection_data, api):
        super().__init__(parent)
        self.collection_id = collection_id
        self.collection_data = collection_data
        self.api = api
        self.setWindowTitle(f"Детали сборки: {collection_data['name']}")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self.setup_ui()
        self.load_details()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Заголовок
        title_layout = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ECDC4;")
        title_layout.addWidget(self.title_label)

        self.id_label = QLabel()
        self.id_label.setStyleSheet("color: #888888; font-size: 10px;")
        title_layout.addWidget(self.id_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Метаданные
        self.meta_text = QTextEdit()
        self.meta_text.setReadOnly(True)
        self.meta_text.setMaximumHeight(120)
        layout.addWidget(self.meta_text)

        # Описание
        desc_label = QLabel("📝 Описание:")
        desc_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(desc_label)

        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(100)
        layout.addWidget(self.desc_text)

        # Моды
        mods_label = QLabel("📦 Моды в сборке:")
        mods_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(mods_label)

        self.mods_list = QTreeWidget()
        self.mods_list.setHeaderLabels(["#", "Источник", "Название"])
        self.mods_list.setColumnWidth(0, 40)
        self.mods_list.setColumnWidth(1, 80)
        self.mods_list.setColumnWidth(2, 300)
        layout.addWidget(self.mods_list)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.download_btn = QPushButton("⬇️ Скачать и импортировать")
        self.download_btn.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6B6B, stop:1 #4ECDC4);")
        self.download_btn.clicked.connect(self.download_and_import)
        buttons_layout.addWidget(self.download_btn)

        self.compatibility_btn = QPushButton("🔍 Проверить совместимость")
        self.compatibility_btn.clicked.connect(self.check_compatibility)
        buttons_layout.addWidget(self.compatibility_btn)

        self.copy_btn = QPushButton("📋 Копировать ID")
        self.copy_btn.clicked.connect(self.copy_id)
        buttons_layout.addWidget(self.copy_btn)

        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)

        layout.addLayout(buttons_layout)

    def load_details(self):
        self.title_label.setText(self.collection_data['name'])
        self.id_label.setText(f"ID: {self.collection_id[:8]}...")

        # Метаданные
        meta = f"""
        👤 Автор: {self.collection_data.get('uploader', 'Неизвестно')}
        🎮 Minecraft: {self.collection_data.get('minecraft_version', '1.20.1')}
        ⚙️ Загрузчик: {self.collection_data.get('loader', 'Fabric')}
        📦 Модов: {self.collection_data.get('mod_count', 0)}
        ⬇️ Скачиваний: {self.collection_data.get('downloads', 0)}
        """
        self.meta_text.setPlainText(meta)

        # Описание
        self.desc_text.setPlainText(self.collection_data.get('description', 'Нет описания'))

        # Моды
        for i, mod in enumerate(self.collection_data.get('mods', []), 1):
            source = mod.get('source', 'unknown')
            source_icon = "🌐" if source == "modrinth" else "⚡" if source == "curseforge" else "💾"
            item = QTreeWidgetItem()
            item.setText(0, str(i))
            item.setText(1, f"{source_icon} {source.capitalize()}")
            item.setText(2, mod.get('name', 'Unknown'))
            self.mods_list.addTopLevelItem(item)

    def download_and_import(self):
        """Скачать и импортировать сборку"""
        # Показываем диалог прогресса
        self.progress_dialog = ImportProgressDialog(self, self.collection_id, self.collection_data, self.api)
        self.progress_dialog.finished.connect(self.on_import_finished)
        self.progress_dialog.exec()

    def on_import_finished(self):
        """Обработка завершения импорта"""
        self.collection_imported.emit()
        QMessageBox.information(self, "Успех", f"Сборка '{self.collection_data['name']}' успешно импортирована!")
        self.accept()

    def check_compatibility(self):
        from ConfDir.Versions import all_versions

        mc_version = self.collection_data.get('minecraft_version', '1.20.1')
        loader_type = self.collection_data.get('loader', 'fabric')

        compatible = []
        for version in all_versions:
            if version.startswith("📦"):
                continue
            if mc_version in version and loader_type.lower() in version.lower():
                compatible.append(version)

        if compatible:
            versions_text = "\n".join([f"• {v}" for v in compatible[:10]])
            if len(compatible) > 10:
                versions_text += f"\n• ...и ещё {len(compatible) - 10} версий"
            QMessageBox.information(
                self,
                "Совместимость",
                f"Эта сборка совместима со следующими версиями:\n\n{versions_text}\n\n"
                f"Рекомендуемая версия: {mc_version} + {loader_type.capitalize()}"
            )
        else:
            QMessageBox.information(
                self,
                "Совместимость",
                f"Сборка создана для:\n"
                f"• Minecraft {mc_version}\n"
                f"• Загрузчик: {loader_type}\n\n"
                f"Убедитесь, что у вас установлена нужная версия."
            )

    def copy_id(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.collection_id)
        QMessageBox.information(self, "Скопировано", f"ID сборки скопирован: {self.collection_id}")


class ImportProgressDialog(BaseDialog):
    """Диалог прогресса импорта сборки"""

    finished = pyqtSignal()

    def __init__(self, parent, collection_id, collection_data, api):
        super().__init__(parent)
        self.collection_id = collection_id
        self.collection_data = collection_data
        self.api = api
        self.cancelled = False

        self.setWindowTitle(f"Импорт сборки: {collection_data['name']}")
        self.setFixedSize(450, 200)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        self.status_label = QLabel("Загрузка сборки...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.cancel_import)
        layout.addWidget(self.cancel_btn)

        # Запускаем импорт в отдельном потоке
        threading.Thread(target=self.import_thread, daemon=True).start()

    def import_thread(self):
        try:
            # Скачиваем сборку
            self.update_status("Скачивание сборки...")
            result = self.api.download_collection(self.collection_id)

            if not result.get("success", False):
                self.show_error(result.get("error", "Ошибка скачивания"))
                return

            # Сохраняем локально
            self.update_status("Сохранение сборки...")
            collections_dir = COLLECTIONS_CONFIG["collections_dir"]
            os.makedirs(collections_dir, exist_ok=True)

            # Создаем имя файла
            safe_name = "".join(
                c for c in self.collection_data["name"] if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            filename = f"{safe_name}.json"
            filepath = os.path.join(collections_dir, filename)

            # Добавляем суффикс если файл существует
            counter = 1
            while os.path.exists(filepath):
                filename = f"{safe_name}_{counter}.json"
                filepath = os.path.join(collections_dir, filename)
                counter += 1

            # Получаем данные сборки
            collection = result["collection"]
            collection["source"] = "community"
            collection["original_id"] = self.collection_id
            collection["imported_date"] = datetime.now().isoformat()

            # Сохраняем
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(collection, f, indent=2, ensure_ascii=False)

            # Увеличиваем счетчик (в фоне, не блокируем)
            self.update_status("Обновление статистики...")
            self.api.increment_downloads(self.collection_id)

            # Успешное завершение
            self.import_success()

        except Exception as e:
            self.show_error(str(e))

    def update_status(self, text):
        """Обновляет статус из потока"""
        from PyQt6.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(
            self.status_label, "setText",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, text)
        )

    def show_error(self, error_msg):
        """Показывает ошибку и закрывает диалог"""
        from PyQt6.QtCore import QMetaObject, Q_ARG

        def display_error():
            self.status_label.setText(f"❌ Ошибка: {error_msg}")
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.cancel_btn.setText("Закрыть")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.accept)

        QMetaObject.invokeMethod(
            self, "close_delayed",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, error_msg)
        )

    def import_success(self):
        """Успешное завершение импорта"""
        from PyQt6.QtCore import QMetaObject, Q_ARG

        def on_success():
            self.finished.emit()
            self.accept()

        QMetaObject.invokeMethod(
            self, "on_success",
            Qt.ConnectionType.QueuedConnection
        )

    @pyqtSlot()
    def on_success(self):
        """Слот для успешного завершения"""
        self.finished.emit()
        self.accept()

    @pyqtSlot(str)
    def close_delayed(self, error_msg):
        """Слот для закрытия с ошибкой"""
        self.status_label.setText(f"❌ Ошибка: {error_msg}")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.cancel_btn.setText("Закрыть")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)

    def cancel_import(self):
        """Отмена импорта"""
        self.cancelled = True
        self.accept()

    def start_import(self):
        def import_thread():
            # Скачиваем сборку
            result = self.api.download_collection(self.collection_id)

            if not result.get("success", False):
                self.show_error(result.get("error", "Ошибка скачивания"))
                return

            # Сохраняем локально
            collections_dir = COLLECTIONS_CONFIG["collections_dir"]
            os.makedirs(collections_dir, exist_ok=True)

            # Создаем имя файла
            safe_name = "".join(
                c for c in self.collection_data["name"] if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            filename = f"{safe_name}.json"
            filepath = os.path.join(collections_dir, filename)

            # Добавляем суффикс если файл существует
            counter = 1
            while os.path.exists(filepath):
                filename = f"{safe_name}_{counter}.json"
                filepath = os.path.join(collections_dir, filename)
                counter += 1

            # Получаем данные сборки
            collection = result["collection"]
            collection["source"] = "community"
            collection["original_id"] = self.collection_id
            collection["imported_date"] = datetime.now().isoformat()

            # Сохраняем
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(collection, f, indent=2, ensure_ascii=False)

            # Увеличиваем счетчик
            self.api.increment_downloads(self.collection_id)

            # Эмитим сигнал для завершения
            self.finished.emit()
            self.accept()

        threading.Thread(target=import_thread, daemon=True).start()

    def show_error(self, error_msg):
        self.status_label.setText(f"❌ Ошибка: {error_msg}")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.cancel_btn.setText("Закрыть")

    def cancel_import(self):
        self.cancelled = True
        self.accept()


class CollectionManager(BaseDialog):
    """Менеджер сборок с вкладками"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Менеджер сборок")
        self.setMinimumSize(1100, 700)
        self.setModal(True)

        self.setStyleSheet(self._get_stylesheet())

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("📦 Менеджер сборок модов")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Информация о папке
        info_layout = QHBoxLayout()
        info_label = QLabel(f"📁 Папка сборок: {get_collections_dir()}")
        info_label.setObjectName("info")
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Вкладки
        self.tab_widget = QTabWidget()

        # Вкладка локальных сборок
        self.local_tab = LocalCollectionsTab(self)
        self.tab_widget.addTab(self.local_tab, "💾 Локальные сборки")

        # Вкладка сборок сообщества
        self.community_tab = CommunityCollectionsTab(self)
        self.tab_widget.addTab(self.community_tab, "🌐 Сборки сообщества")

        layout.addWidget(self.tab_widget)

        # Кнопки внизу
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _get_stylesheet(self):
        return """
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel#title {
                color: #4ECDC4;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
            QLabel#info {
                color: #888888;
                font-size: 11px;
            }
            QTabWidget::pane {
                background-color: #1e1e2a;
                border: 1px solid #3a3a4a;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #2a2a3a;
                color: #e0e0e0;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #4ECDC4;
                color: #1a1a1a;
            }
            QTabBar::tab:hover {
                background-color: #3a3a4a;
            }
            QPushButton {
                background-color: #3a3a4a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a5a;
            }
        """


class LocalCollectionsTab(QWidget):
    """Вкладка локальных сборок"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_collection = None
        self.current_filename = None

        self.setup_ui()
        self.load_collections()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # Левая панель - список сборок
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.collections_tree = QTreeWidget()
        self.collections_tree.setHeaderLabels(["Название", "Версия", "Загрузчик", "Модов", "Создана"])
        self.collections_tree.setColumnWidth(0, 250)
        self.collections_tree.setColumnWidth(1, 100)
        self.collections_tree.setColumnWidth(2, 100)
        self.collections_tree.setColumnWidth(3, 60)
        self.collections_tree.setColumnWidth(4, 100)
        self.collections_tree.itemClicked.connect(self.on_collection_selected)
        left_layout.addWidget(self.collections_tree)

        # Кнопки управления списком
        list_buttons = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_collections)
        list_buttons.addWidget(self.refresh_btn)

        self.open_folder_btn = QPushButton("📁 Открыть папку")
        self.open_folder_btn.clicked.connect(self.open_collections_folder)
        list_buttons.addWidget(self.open_folder_btn)

        left_layout.addLayout(list_buttons)

        layout.addWidget(left_widget, 2)

        # Правая панель - детали
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        # Информация
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        right_layout.addWidget(self.info_text)

        # Список модов
        mods_label = QLabel("📦 Моды в сборке:")
        mods_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(mods_label)

        self.mods_list = QTreeWidget()
        self.mods_list.setHeaderLabels(["Источник", "Название", "Файл"])
        self.mods_list.setColumnWidth(0, 80)
        self.mods_list.setColumnWidth(1, 250)
        self.mods_list.setColumnWidth(2, 200)
        right_layout.addWidget(self.mods_list)

        # Кнопки действий
        action_layout = QHBoxLayout()

        self.install_btn = QPushButton("📥 Установить сборку")
        self.install_btn.clicked.connect(self.install_collection)
        self.install_btn.setEnabled(False)
        action_layout.addWidget(self.install_btn)

        self.delete_btn = QPushButton("🗑️ Удалить сборку")
        self.delete_btn.clicked.connect(self.delete_collection)
        self.delete_btn.setEnabled(False)
        action_layout.addWidget(self.delete_btn)

        action_layout.addStretch()

        self.new_btn = QPushButton("➕ Новая сборка")
        self.new_btn.clicked.connect(self.create_new_collection)
        action_layout.addWidget(self.new_btn)

        right_layout.addLayout(action_layout)

        layout.addWidget(right_widget, 3)

    def load_collections(self):
        self.collections_tree.clear()
        collections = load_all_collections()

        for col in collections:
            item = QTreeWidgetItem()
            item.setText(0, col['display_name'])
            item.setText(1, col['minecraft_version'])
            item.setText(2, col['loader'].capitalize())
            item.setText(3, str(col['mod_count']))
            item.setText(4, col['created_str'])
            item.setData(0, Qt.ItemDataRole.UserRole, col['filename'])
            item.setData(0, Qt.ItemDataRole.UserRole + 1, col)
            self.collections_tree.addTopLevelItem(item)

        if collections:
            self.collections_tree.setCurrentItem(self.collections_tree.topLevelItem(0))
            self.on_collection_selected(self.collections_tree.topLevelItem(0))

    def on_collection_selected(self, item):
        self.current_filename = item.data(0, Qt.ItemDataRole.UserRole)
        self.current_collection = item.data(0, Qt.ItemDataRole.UserRole + 1)

        self.install_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        # Информация
        info = f"""
<b>Название:</b> {self.current_collection['name']}
<b>Версия Minecraft:</b> {self.current_collection['minecraft_version']}
<b>Загрузчик:</b> {self.current_collection['loader'].capitalize()}
<b>Количество модов:</b> {self.current_collection['mod_count']}
<b>Создана:</b> {self.current_collection['created_str']}
"""
        if self.current_collection.get('description'):
            info += f"\n<b>Описание:</b>\n{self.current_collection['description']}"

        self.info_text.setHtml(info)

        # Моды
        self.mods_list.clear()
        mods_info = get_collection_mods_info(self.current_collection)

        for mod in mods_info:
            source_icon = "🌐" if mod['source'] == 'modrinth' else "⚡" if mod['source'] == 'curseforge' else "💾"
            item = QTreeWidgetItem()
            item.setText(0, f"{source_icon} {mod['source'].capitalize()}")
            item.setText(1, mod['name'])
            item.setText(2, mod['filename'])
            self.mods_list.addTopLevelItem(item)

    def install_collection(self):
        """Установка сборки"""
        if not self.current_collection:
            return

        print("=== install_collection button clicked ===")
        import sys
        sys.stdout.flush()

        reply = QMessageBox.question(
            self,
            "Установка сборки",
            f"Установить сборку '{self.current_collection['name']}'?\n\n"
            f"Будет установлено {self.current_collection['mod_count']} модов.\n"
            f"Существующие моды в папке mods будут заменены.\n\n"
            f"Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            print("User cancelled")
            return

        print("Creating CollectionInstallProgress...")
        sys.stdout.flush()

        try:
            progress = CollectionInstallProgress(self, self.current_collection)
            print("CollectionInstallProgress created, calling exec()...")
            sys.stdout.flush()

            progress.exec()
            print("CollectionInstallProgress.exec() finished")
            sys.stdout.flush()

        except Exception as e:
            print(f"ERROR in install_collection: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()



    def delete_collection(self):
        if not self.current_filename:
            return

        reply = QMessageBox.question(
            self,
            "Удаление сборки",
            f"Удалить сборку '{self.current_collection['name']}'?\n\n"
            f"Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if delete_collection(self.current_filename):
            QMessageBox.information(self, "Успех", f"Сборка '{self.current_collection['name']}' удалена!")
            self.load_collections()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить сборку")

    def open_collections_folder(self):
        import subprocess
        import os
        folder = get_collections_dir()
        os.makedirs(folder, exist_ok=True)
        if os.name == "nt":
            os.startfile(folder)
        else:
            subprocess.Popen(["xdg-open", folder])

    def create_new_collection(self):
        """Открывает диалог создания новой сборки"""
        try:
            from Ui.CollectionCreator import CollectionCreator

            # Правильно передаем parent - self (текущая вкладка) или self.window()
            # Используем self.window() чтобы получить главное окно менеджера
            creator = CollectionCreator(self.window())
            creator.exec()

            # После создания обновляем список сборок
            self.load_collections()

            # Обновляем селектор версий в главном окне
            main_window = self.window().parent() if self.window() else None
            if main_window and hasattr(main_window, 'refresh_versions'):
                main_window.refresh_versions()

        except ImportError as e:
            print(f"Ошибка импорта CollectionCreator: {e}")
            QMessageBox.information(
                self,
                "Создание сборки",
                "Функция создания сборок будет доступна в следующем обновлении."
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть создание сборки: {e}")


class CollectionInstallWorker(QThread):
    """Поток для установки сборки"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, int, int)
    log = pyqtSignal(str)

    def __init__(self, collection_data):
        print("=== CollectionInstallWorker.__init__ ===")
        import sys
        sys.stdout.flush()
        super().__init__()
        self.collection_data = collection_data
        self._cancelled = False
        print(f"collection_data name: {collection_data.get('name', 'Unknown')}")
        sys.stdout.flush()

    def cancel(self):
        """Отмена установки"""
        print("CollectionInstallWorker.cancel called")
        self._cancelled = True

    def run(self):
        print("=== CollectionInstallWorker.run START ===")
        import sys
        sys.stdout.flush()

        try:
            from Core.backup import ModsBackupManager

            # Создаем список для отслеживания
            installed_mods = []

            def callback(current, total, mod_name, status="loading", reason=None):
                if self._cancelled:
                    return
                print(f"CALLBACK: {current}/{total} - {mod_name} - status={status}")
                sys.stdout.flush()
                self.progress.emit(current, total, mod_name)
                if status == "skipped":
                    self.log.emit(f"⏭️ Пропущен {mod_name}: {reason}")
                elif status == "loading":
                    self.log.emit(f"📥 Загрузка: {mod_name} ({current + 1}/{total})")
                elif status == "success":
                    self.log.emit(f"✅ Установлен: {mod_name}")
                    installed_mods.append(mod_name)

            print("Calling install_collection...")
            sys.stdout.flush()

            success = install_collection(self.collection_data, callback, create_backup=True)

            print(f"install_collection returned: {success}")
            print(f"Installed mods count: {len(installed_mods)}")
            sys.stdout.flush()

            total = len(self.collection_data.get('mods', []))
            success_count = len(installed_mods)

            print(f"Success count: {success_count} / {total}")
            sys.stdout.flush()

            self.finished.emit(success, success_count, total)

        except Exception as e:
            print(f"ERROR in CollectionInstallWorker.run: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            self.finished.emit(False, 0, 0)

class CollectionInstallProgress(QDialog):
    """Диалог прогресса установки сборки"""

    def __init__(self, parent, collection_data):
        print("=== CollectionInstallProgress.__init__ START ===")
        import sys
        sys.stdout.flush()

        super().__init__(parent)
        self.collection_data = collection_data
        self.cancelled = False
        self.worker = None

        print(f"collection_data: {collection_data.get('name', 'Unknown')}")
        sys.stdout.flush()

        self.setWindowTitle(f"Установка сборки: {collection_data['name']}")
        self.setFixedSize(500, 300)
        self.setModal(True)
        print("Window setup complete")
        sys.stdout.flush()

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: white;
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
                background-color: #1e1e2a;
                color: #e0e0e0;
                border: 1px solid #4ECDC4;
                border-radius: 8px;
                font-family: monospace;
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
        """)
        print("Stylesheet applied")
        sys.stdout.flush()

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        print("Layout created")
        sys.stdout.flush()

        title = QLabel(f"📦 Установка сборки: {collection_data['name']}")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4ECDC4;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        print("Title added")
        sys.stdout.flush()

        info = QLabel(f"Модов: {len(collection_data.get('mods', []))}")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        print("Info added")
        sys.stdout.flush()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        print("Progress bar added")
        sys.stdout.flush()

        self.status_label = QLabel("Подготовка к установке...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        print("Status label added")
        sys.stdout.flush()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        layout.addWidget(self.log_text)
        print("Log text added")
        sys.stdout.flush()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.cancel_install)
        layout.addWidget(self.cancel_btn)
        print("Cancel button added")
        sys.stdout.flush()

        print("Creating CollectionInstallWorker...")
        sys.stdout.flush()

        self.worker = CollectionInstallWorker(collection_data)
        print("Worker created")
        sys.stdout.flush()

        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(self.on_finished)
        print("Signals connected")
        sys.stdout.flush()

        print("Starting worker...")
        sys.stdout.flush()
        self.worker.start()
        print("Worker started")
        sys.stdout.flush()

        print("=== CollectionInstallProgress.__init__ END ===")
        sys.stdout.flush()

    def add_log(self, message):
        """Добавляет сообщение в лог"""
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()

    def update_progress(self, current, total, mod_name):
        """Обновляет прогресс"""
        if total > 0:
            percent = int((current + 1) * 100 / total)
            self.progress_bar.setValue(percent)
            self.status_label.setText(f"Установка: {mod_name} ({current + 1}/{total})")

    def on_finished(self, success, success_count, total):
        """Обработка завершения установки"""
        if self.cancelled:
            return

        if success:
            self.status_label.setText("✅ Установка завершена!")
            self.progress_bar.setValue(100)
            self.add_log(f"\n✅ Успешно установлено {success_count} из {total} модов")

            QMessageBox.information(
                self,
                "Установка завершена",
                f"✅ Сборка '{self.collection_data['name']}' успешно установлена!\n\n"
                f"• Модов: {success_count}/{total}\n"
                f"• Версия: {self.collection_data['minecraft_version']}\n"
                f"• Загрузчик: {self.collection_data['loader']}\n\n"
                f"Теперь можно запустить игру!"
            )
        else:
            self.status_label.setText("❌ Ошибка при установке")
            self.add_log(f"\n❌ Установлено {success_count} из {total} модов")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"❌ Не удалось установить сборку '{self.collection_data['name']}'\n\n"
                f"Успешно установлено: {success_count} из {total} модов"
            )

        self.cancel_btn.setText("Закрыть")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)

    def cancel_install(self):
        """Отмена установки"""
        print("Cancel install called")
        self.cancelled = True
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)
        self.accept()