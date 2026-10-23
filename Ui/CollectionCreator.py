# Ui/CollectionCreator.py
import os
from copy import deepcopy
import logging
logger = logging.getLogger(__name__)
import json
import threading
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QTextEdit, QMessageBox, QWidget, QFrame,
    QApplication, QHeaderView, QScrollArea, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QRunnable, QThreadPool, QObject
from PyQt6.QtGui import QFont, QColor, QPixmap, QPalette, QDesktopServices

from Core.collection_loader import save_collection, get_collections_dir
from Core.local_mods import import_local_mods
from Core.mod_transaction import safe_filename
from Network.ModrinthLoader import ModrinthAPI
from Network.CurseForgeLoader import CurseForgeAPI
from ConfDir.Configs import CURSEFORGE_CONFIG
from ConfDir.Versions import all_versions
from Ui.DependencyAnalyzer import DependencyAnalyzerUI
from Ui.BaseWindow import BaseDialog


# ============================================================
# МОДЕЛЬ МОДА
# ============================================================
class ModProject:
    """Класс для хранения информации о моде"""

    def __init__(self, data: dict, source: str = "modrinth"):
        self.source = source
        self.project_id = data.get('project_id', '')
        self.slug = data.get('slug', '')
        self.title = data.get('title', 'Без названия')
        self.description = data.get('description', '')
        self.author = data.get('author', '')
        self.categories = data.get('categories', [])
        self.downloads = data.get('downloads', 0)
        self.follows = data.get('follows', 0)
        self.date = data.get('date', '')
        self.version = data.get('version', '')
        self.version_id = data.get('version_id')
        self.icon_pixmap = None
        self.download_url = None
        self.file_name = None

        # Для Modrinth - icon_url есть в ответе
        if source == "modrinth":
            self.icon_url = data.get('icon_url', '')
            self.project_id = data.get('project_id', '')

        # Для CurseForge - иконки нужно формировать отдельно
        elif source == "curseforge":
            self.project_id = str(data.get('project_id', ''))
            self.slug = data.get('slug', '')
            self.title = data.get('title', 'Без названия')
            self.author = data.get('author', '')
            self.downloads = data.get('downloads', 0)
            self.file_name = data.get('filename', f"{self.slug}.jar")

            # Формируем URL для иконки CurseForge
            # Используем ID для формирования ссылки на иконку
            cf_id = self.project_id
            if cf_id:
                # Популярный способ получения иконок CurseForge через CDN
                self.icon_url = f"https://media.forgecdn.net/avatars/thumbnails/{cf_id}/64/64.png"
                # Альтернативный вариант если не работает:
                # self.icon_url = f"https://static.wikia.nocookie.net/minecraft_gamepedia/images/8/80/No_image.png"


# ============================================================
# СИГНАЛЫ ДЛЯ РАБОЧИХ ПОТОКОВ
# ============================================================
class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    warning = pyqtSignal(str)
    result = pyqtSignal(list)
    progress = pyqtSignal(int)
    icon_loaded = pyqtSignal(int, QPixmap)


# ============================================================
# ПОИСКОВЫЙ РАБОЧИЙ ПОТОК
# ============================================================
class SearchWorker(QRunnable):
    def __init__(self, query, source="modrinth", minecraft_version="1.20.1", loader="fabric"):
        super().__init__()
        self.query = query
        self.source = source
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.signals = WorkerSignals()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ModPackCreator/1.0'})

    def run(self):
        try:
            sources = ('modrinth', 'curseforge') if self.source == 'both' else (self.source,)
            projects = []
            errors = []
            with ThreadPoolExecutor(max_workers=len(sources)) as pool:
                jobs = {source: pool.submit(self._search_modrinth if source == 'modrinth' else self._search_curseforge)
                        for source in sources}
                for source, job in jobs.items():
                    try:
                        projects.extend(ModProject(hit, source) for hit in job.result())
                    except Exception as exc:
                        errors.append(f'{source}: {exc}')
            if not projects:
                if errors:
                    self.signals.error.emit('; '.join(errors))
                else:
                    self.signals.result.emit([])
                return
            self._get_versions_fast(projects)
            self.signals.result.emit(projects)
            if errors:
                # Keep useful results if one marketplace is temporarily unavailable.
                self.signals.warning.emit('Часть источников недоступна: ' + '; '.join(errors))
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()

    def _search_modrinth(self):
        url = 'https://api.modrinth.com/v2/search'
        params = {'query': self.query, 'limit': 50,
                  'facets': json.dumps([[f'versions:{self.minecraft_version}'],
                                        [f'categories:{self.loader}'], ['project_type:mod']])}
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('hits', [])

    def _search_curseforge(self):
        api = CurseForgeAPI()
        api.timeout = 15

        if not api.test_connection():
            raise Exception("Прокси-сервер недоступен")

        results = api.search_mods(
            query=self.query,
            minecraft_version=self.minecraft_version,
            loader=self.loader,
            limit=50
        )
        if results and results.get("success") and results.get("data"):
            return results["data"]
        return []

    def _get_versions_fast(self, projects):
        max_workers = min(20, len(projects))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, project in enumerate(projects):
                future = executor.submit(self._get_version_and_download, project)
                futures[future] = i

            for completed, future in enumerate(as_completed(futures), 1):
                i = futures[future]
                try:
                    result = future.result(timeout=5)
                    if result:
                        version, download_url, file_name = result
                        projects[i].version = version
                        projects[i].download_url = download_url
                        projects[i].file_name = file_name
                except Exception as e:
                    print(f"⚠️ Ошибка для мода {i}: {e}")

                self.signals.progress.emit(int(completed / len(projects) * 100))

    def _get_version_and_download(self, project):
        try:
            if project.source == 'modrinth':
                versions = ModrinthAPI().get_mod_versions(project.project_id, self.minecraft_version, self.loader)
                if versions:
                    version = versions[0]
                    files = [f for f in version.get('files', []) if f['filename'].endswith('.jar')]
                    file = next((f for f in files if f.get('primary')), files[0] if files else None)
                    if file:
                        project.version_id = version['id']
                        return version.get('version_number', 'N/A'), file.get('url'), file['filename']
            else:
                versions = CurseForgeAPI().get_mod_versions(project.project_id, self.minecraft_version, self.loader)
                if versions:
                    version = versions[0]
                    project.version_id = version['id']
                    return version.get('displayName', 'N/A'), version.get('downloadUrl'), version.get('fileName') or version.get('filename')
        except Exception as exc:
            logger.warning('Не удалось получить версию мода: %s', exc)
        return 'N/A', None, None


# ============================================================
# ЗАГРУЗЧИК ИКОНОК
# ============================================================
class IconLoader(QThread):
    icon_loaded = pyqtSignal(int, QPixmap)

    def __init__(self, projects):
        super().__init__()
        self.projects = projects
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ModPackCreator/1.0'})

    def run(self):
        max_workers = min(20, len(self.projects))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, project in enumerate(self.projects):
                if project.icon_url:
                    future = executor.submit(self._load_icon, i, project.icon_url)
                    futures[future] = i

            for future in as_completed(futures):
                i = futures[future]
                try:
                    result = future.result(timeout=5)
                    if result:
                        index, pixmap = result
                        if pixmap and not pixmap.isNull():
                            self.icon_loaded.emit(index, pixmap)
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки иконки {i}: {e}")

    def _load_icon(self, index, url):
        try:
            # Добавляем заголовки для CurseForge
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.curseforge.com/'
            }

            response = self.session.get(url, timeout=5, headers=headers, allow_redirects=True)

            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    return (index, pixmap.scaled(
                        56, 56,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))

            # Если не загрузилось, пробуем альтернативный URL для CurseForge
            if "curseforge" in url or "forgecdn" in url:
                alt_urls = self._get_alternative_icon_urls(url)
                for alt_url in alt_urls:
                    try:
                        response = self.session.get(alt_url, timeout=3, headers=headers)
                        if response.status_code == 200:
                            pixmap = QPixmap()
                            pixmap.loadFromData(response.content)
                            if not pixmap.isNull():
                                return (index, pixmap.scaled(
                                    56, 56,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation
                                ))
                    except:
                        continue

            return None

        except Exception as e:
            print(f"⚠️ Ошибка загрузки иконки: {e}")
            return None

    def _get_alternative_icon_urls(self, original_url):
        """Генерирует альтернативные URL для иконок CurseForge"""
        alt_urls = []

        # Пытаемся извлечь ID из URL
        import re
        match = re.search(r'/avatars/thumbnails/(\d+)/', original_url)
        if match:
            cf_id = match.group(1)
            # Разные размеры и форматы
            alt_urls.append(f"https://media.forgecdn.net/avatars/thumbnails/{cf_id}/128/128.png")
            alt_urls.append(f"https://media.forgecdn.net/avatars/thumbnails/{cf_id}/256/256.png")
            alt_urls.append(f"https://media.forgecdn.net/avatars/{cf_id}.png")
            alt_urls.append(f"https://media.forgecdn.net/avatars/{cf_id}.jpg")

        # Заглушка
        alt_urls.append("https://static.wikia.nocookie.net/minecraft_gamepedia/images/8/80/No_image.png")

        return alt_urls


# ============================================================
# ГЛАВНЫЙ ДИАЛОГ СОЗДАНИЯ СБОРКИ
# ============================================================
class CollectionCreator(QDialog):
    """Диалог создания новой сборки с карточками модов"""

    def __init__(self, parent=None, collection_data=None, original_filename=None):
        super().__init__(parent)
        self.original_data = deepcopy(collection_data) if collection_data is not None else None
        self.original_filename = original_filename
        self.setWindowTitle("Создание новой сборки")
        self.setObjectName("collectionCreator")
        self.setMinimumSize(1100, 750)
        self.setModal(True)

        self.selected_mods = []
        self.projects = []
        self.card_widgets = {}
        self.is_loading = False
        self.threadpool = QThreadPool()
        self.worker = None
        self.icon_loader = None

        self.setup_ui()
        self.setup_styles()
        self.update_mode()
        if self.original_data is not None:
            self.load_for_editing()

    def load_for_editing(self):
        data = self.original_data
        self.setWindowTitle('Редактирование сборки')
        self.title_label.setText('📦 Редактирование сборки')
        self.save_btn.setText('✅ Сохранить изменения')
        self.name_input.setText(data['name'])
        if self.version_combo.findText(data['minecraft_version']) < 0:
            self.version_combo.addItem(data['minecraft_version'])
        self.version_combo.setCurrentText(data['minecraft_version'])
        if self.loader_combo.findText(data['loader']) < 0:
            self.loader_combo.addItem(data['loader'])
        self.loader_combo.setCurrentText(data['loader'])
        self.selected_mods = deepcopy(data.get('mods', []))
        for mod in self.selected_mods:
            mod.setdefault('filename', mod.get('file') or f'{mod.get("name", "mod")}.jar')
        sources = {mod.get('source') for mod in self.selected_mods}
        mode = 'mixed' if 'local' in sources and len(sources) > 1 else 'custom' if sources == {'local'} else 'catalog'
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(mode))
        self.source_combo.setCurrentIndex(self.source_combo.findData('both'))
        self.update_selected_list()
        self.update_mode()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("📦 Создание новой сборки")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = title
        main_layout.addWidget(title)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem('Сборка из каталога', 'catalog')
        self.mode_combo.addItem('Кастомная сборка — локальные моды', 'custom')
        self.mode_combo.addItem('Смешанная сборка — каталоги и локальные моды', 'mixed')
        main_layout.addWidget(self.mode_combo)

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
        self.version_combo.currentTextChanged.connect(self.update_available_loaders)
        self.update_available_loaders()
        loader_layout.addWidget(self.loader_combo)
        settings_layout.addLayout(loader_layout)

        # Источник
        source_layout = QVBoxLayout()
        source_layout.addWidget(QLabel("Источник:"))
        self.source_combo = QComboBox()
        self.source_combo.addItem('Modrinth', 'modrinth')
        self.source_combo.addItem('CurseForge', 'curseforge')
        self.source_combo.addItem('Modrinth + CurseForge', 'both')
        source_layout.addWidget(self.source_combo)
        settings_layout.addLayout(source_layout)

        settings_layout.addStretch()
        main_layout.addWidget(settings_frame)

        # Поисковая панель
        search_widget = QWidget()
        search_widget.setObjectName("searchWidget")
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 5, 0, 5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск модов...")
        self.search_input.setObjectName("searchInput")
        self.search_input.returnPressed.connect(self.search_mods)

        self.search_btn = QPushButton("🚀 Поиск")
        self.search_btn.setObjectName("searchBtn")
        self.search_btn.setFixedHeight(36)
        self.search_btn.setFixedWidth(120)
        self.search_btn.clicked.connect(self.search_mods)

        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_btn)

        # Индикатор загрузки
        self.loading_indicator = QProgressBar()
        self.loading_indicator.setObjectName("loadingIndicator")
        self.loading_indicator.setRange(0, 0)
        self.loading_indicator.setVisible(False)
        self.loading_indicator.setFixedWidth(150)
        search_layout.addWidget(self.loading_indicator)

        main_layout.addWidget(search_widget)
        self.search_widget = search_widget

        self.local_panel = QWidget()
        local_layout = QVBoxLayout(self.local_panel)
        local_help = QLabel('Выберите свои JAR-моды, папку mods / сборки или ZIP с модами. '
                            'Версию Minecraft и загрузчик укажите выше. '
                            'Настройки и ресурсы сборки из архива не импортируются.')
        local_help.setWordWrap(True)
        local_layout.addWidget(local_help)
        local_buttons = QHBoxLayout()
        for text, handler in [('Добавить JAR / ZIP', self.choose_local_files),
                              ('Выбрать папку сборки', self.choose_local_folder)]:
            button = QPushButton(text)
            button.clicked.connect(handler)
            local_buttons.addWidget(button)
        local_layout.addLayout(local_buttons)
        main_layout.addWidget(self.local_panel)
        self.local_panel.hide()

        # Результаты поиска
        scroll_area = QScrollArea()
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.results_container = QWidget()
        self.results_container.setObjectName("resultsContainer")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(10)
        self.results_layout.addStretch()

        scroll_area.setWidget(self.results_container)
        main_layout.addWidget(scroll_area, 1)
        self.search_results = scroll_area

        # Статус
        self.status_label = QLabel("Введите запрос для поиска модов")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

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
        self.selected_tree.setColumnWidth(0, 120)
        self.selected_tree.setColumnWidth(1, 350)
        self.selected_tree.setColumnWidth(2, 250)
        self.selected_tree.setMaximumHeight(120)
        self.selected_tree.setAlternatingRowColors(True)
        self.selected_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        selected_layout.addWidget(self.selected_tree)

        buttons_row = QHBoxLayout()
        self.remove_btn = QPushButton("🗑️ Удалить выбранные")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("🗑️ Очистить все")
        self.clear_btn.clicked.connect(self.clear_all)
        buttons_row.addWidget(self.remove_btn)
        buttons_row.addWidget(self.clear_btn)
        buttons_row.addStretch()
        selected_layout.addLayout(buttons_row)

        main_layout.addWidget(selected_frame)

        # Кнопки сохранения
        save_layout = QHBoxLayout()
        save_layout.addStretch()

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
        main_layout.addLayout(save_layout)
        self.mode_combo.currentIndexChanged.connect(self.update_mode)

    def update_mode(self):
        custom = self.mode_combo.currentData() == 'custom'
        self.local_panel.setVisible(True)
        self.search_widget.setVisible(not custom)
        self.search_results.setVisible(not custom)
        self.source_combo.setEnabled(not custom)
        self.analyze_btn.setEnabled(True)
        self.selected_tree.setMaximumHeight(350 if custom else 240 if self.original_data is not None else 160)
        self.status_label.setText('Добавьте локальные моды и сохраните сборку' if custom
                                  else 'Введите запрос для поиска модов')

    def choose_local_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Выберите моды или архив сборки', '', 'Моды и сборки (*.jar *.zip)')
        if paths:
            self.add_local_paths(paths)

    def choose_local_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Выберите папку сборки или mods')
        if folder:
            self.add_local_paths([folder])

    def add_local_paths(self, paths):
        try:
            mods = import_local_mods(paths, get_collections_dir())
            existing = {mod['filename'].casefold(): mod for mod in self.selected_mods}
            additions = []
            for mod in mods:
                previous = existing.get(mod['filename'].casefold())
                if previous:
                    if previous.get('sha256') == mod['sha256']:
                        continue
                    raise ValueError(f'Уже добавлен другой мод с именем {mod["filename"]}')
                additions.append(mod)
            self.selected_mods.extend(additions)
            self.update_selected_list()
            self.update_mode()
            self.status_label.setText(f'Добавлено локальных модов: {len(additions)}')
        except Exception as exc:
            QMessageBox.warning(self, 'Импорт модов', str(exc))

    def update_available_loaders(self):
        from ConfDir.Versions import get_version_config, version_configs
        mc = self.version_combo.currentText()
        current = self.loader_combo.currentText()
        available = [loader for loader in ('fabric', 'forge', 'quilt', 'neoforge')
                     if any(config[0] == mc and config[1] == loader for config in version_configs.values())]
        self.loader_combo.clear()
        self.loader_combo.addItems(available)
        if current in available:
            self.loader_combo.setCurrentText(current)

    def setup_styles(self):
        # Use the launcher's dark theme explicitly, regardless of Windows' palette.
        arrow = os.path.join(os.path.dirname(__file__), 'assets', 'chevron-down.svg').replace('\\', '/')
        palette = QPalette(self.palette())
        for role, color in ((QPalette.ColorRole.Window, '#102033'),
                            (QPalette.ColorRole.Base, '#0b192a'),
                            (QPalette.ColorRole.AlternateBase, '#102238'),
                            (QPalette.ColorRole.WindowText, '#dce8f5'),
                            (QPalette.ColorRole.Text, '#dce8f5'),
                            (QPalette.ColorRole.PlaceholderText, '#91a9bf'),
                            (QPalette.ColorRole.Button, '#203b53'),
                            (QPalette.ColorRole.ButtonText, '#eaf2fa'),
                            (QPalette.ColorRole.Highlight, '#28556a'),
                            (QPalette.ColorRole.HighlightedText, '#ffffff')):
            palette.setColor(role, QColor(color))
        self.setPalette(palette)
        self.setStyleSheet("""
            QWidget { background-image: none; background-color: transparent;
                      color: #dce8f5; font-family: 'Segoe UI'; font-size: 12px; }
            QDialog#collectionCreator {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0b182a, stop:0.48 #17283d, stop:1 #123f46);
            }
            QLabel { background: transparent; border: none; }
            QLabel#title { color: #f1f7ff; font-size: 24px; font-weight: 600; padding: 10px; }
            QFrame#settings_frame, QFrame#selected_frame {
                background: #102033; border: 1px solid #30475e; border-radius: 12px; padding: 8px;
            }
            QLineEdit, QComboBox {
                background: #0b192a; color: #eaf2fa; border: 1px solid #38516a;
                border-radius: 8px; padding: 8px 12px; min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #68e0cc; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow { image: url("@ARROW@"); width: 12px; height: 8px; }
            QComboBox QAbstractItemView {
                background: #172c42; color: #eaf2fa; border: 1px solid #48657e;
                selection-background-color: #28556a; selection-color: #ffffff; padding: 4px;
            }
            QLineEdit#searchInput { padding: 10px 16px; font-size: 14px; }
            QPushButton { background: #203b53; color: #eaf2fa; border: 1px solid #385971;
                          border-radius: 8px; padding: 8px 14px; font-weight: 500; }
            QPushButton:hover { background: #2b506a; border-color: #68e0cc; }
            QPushButton:pressed { background: #17334a; }
            QPushButton:disabled { color: #7f96aa; background: #17283a; border-color: #253b4e; }
            QPushButton#searchBtn { background: #24566a; color: #efffff; border-color: #397d86; }
            QPushButton#searchBtn:hover { background: #2d6a7c; }
            QScrollArea#scrollArea { background: #0b192a; border: 1px solid #30475e; border-radius: 12px; }
            QWidget#resultsContainer { background: #0b192a; }
            QLabel#statusLabel { color: #a8bdd0; padding: 6px; }
            QTreeWidget { background: #0b192a; alternate-background-color: #102238; color: #dce8f5;
                          border: 1px solid #30475e; border-radius: 8px; outline: none; }
            QTreeWidget::item { padding: 6px 3px; }
            QTreeWidget::item:selected { background: #28556a; color: #ffffff; }
            QTreeWidget::item:hover { background: #192f46; }
            QHeaderView::section { background: #1c3047; color: #b7d7d5; padding: 8px; border: none; }
            QWidget#modCard { background: #172c42; border: 1px solid #30475e; border-radius: 10px; }
            QWidget#modCard:hover { border-color: #5e9ea7; }
            QLabel#modTitle { color: #f1f7ff; font-size: 16px; font-weight: 600; }
            QLabel#modDescription { color: #b4c7d8; font-size: 13px; }
            QProgressBar { background: #172c42; border: 1px solid #30475e; border-radius: 6px; }
            QProgressBar::chunk { background: #4ea89c; border-radius: 5px; }
            QScrollBar:vertical { background: #102033; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #385971; border-radius: 5px; min-height: 24px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal { background: #102033; height: 10px; }
            QScrollBar::handle:horizontal { background: #385971; border-radius: 5px; min-width: 24px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """.replace('@ARROW@', arrow))

    def search_mods(self):
        if self.mode_combo.currentData() == 'custom':
            return
        if self.is_loading:
            return

        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите запрос для поиска")
            return

        self.is_loading = True
        self.projects.clear()
        self.card_widgets.clear()
        self.clear_results()
        self.loading_indicator.setVisible(True)
        self.search_btn.setEnabled(False)
        self.status_label.setText("⏳ Поиск...")

        source = self.source_combo.currentData()
        minecraft_version = self.version_combo.currentText()
        loader = self.loader_combo.currentText()

        self.worker = SearchWorker(query, source, minecraft_version, loader)
        self.worker.signals.result.connect(self.on_search_result)
        self.worker.signals.error.connect(self.on_search_error)
        self.worker.signals.warning.connect(self.on_search_warning)
        self.worker.signals.finished.connect(self.on_search_finished)
        self.worker.signals.progress.connect(self.on_search_progress)

        self.threadpool.start(self.worker)

    def on_search_result(self, projects):
        self.projects = projects
        self.display_results()
        self.load_icons_async()
        self.status_label.setText(f"✅ Найдено: {len(projects)} модов")
        self.loading_indicator.setRange(0, 100)
        self.loading_indicator.setValue(100)

    def on_search_warning(self, message):
        self.status_label.setText(f'Найдено: {len(self.projects)} модов. {message}')

    def on_search_error(self, error_msg):
        self.status_label.setText(f"❌ {error_msg}")
        QMessageBox.critical(self, "Ошибка", error_msg)

    def on_search_finished(self):
        self.is_loading = False
        self.loading_indicator.setVisible(False)
        self.search_btn.setEnabled(True)

        if not self.projects:
            self.status_label.setText("Ничего не найдено")

    def on_search_progress(self, value):
        self.loading_indicator.setRange(0, 100)
        self.loading_indicator.setValue(value)

    def load_icons_async(self):
        if self.icon_loader and self.icon_loader.isRunning():
            self.icon_loader.quit()
            self.icon_loader.wait()

        # Фильтруем проекты без иконок
        projects_with_icons = [p for p in self.projects if p.icon_url]

        if not projects_with_icons:
            return

        self.icon_loader = IconLoader(self.projects)
        self.icon_loader.icon_loaded.connect(self.on_icon_loaded)
        self.icon_loader.start()

    def on_icon_loaded(self, index, pixmap):
        if index < len(self.projects) and index in self.card_widgets:
            widget = self.card_widgets[index]
            for child in widget.findChildren(QLabel):
                if child.objectName() == "modIcon":
                    child.setPixmap(pixmap)
                    child.setStyleSheet("""
                        #modIcon {
                            border-radius: 8px;
                            background-color: transparent;
                        }
                    """)
                    break

    def clear_results(self):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.card_widgets.clear()

    def display_results(self):
        self.clear_results()

        for i, project in enumerate(self.projects):
            card = self.create_mod_card(project, i)
            self.results_layout.insertWidget(self.results_layout.count() - 1, card)

    def create_mod_card(self, project: ModProject, index: int) -> QWidget:
        card = QWidget()
        card.setObjectName("modCard")
        self.card_widgets[index] = card

        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Иконка
        icon_widget = QLabel()
        icon_widget.setFixedSize(56, 56)
        icon_widget.setObjectName("modIcon")
        icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Показываем заглушку в зависимости от источника
        if project.source == "modrinth":
            icon_widget.setText("🌐")
        else:
            icon_widget.setText("⚡")

        icon_widget.setStyleSheet("""
            #modIcon {
                background-color: #203b53;
                border-radius: 8px;
                font-size: 24px;
            }
        """)

        # Информация
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Название
        title_label = QLabel(project.title)
        title_label.setObjectName("modTitle")

        # Описание
        desc_text = project.description[:150] + ("..." if len(project.description) > 150 else "")
        desc_label = QLabel(desc_text)
        desc_label.setObjectName("modDescription")
        desc_label.setWordWrap(True)

        # Статистика
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)

        # Источник
        source_label = QLabel("🌐 Modrinth" if project.source == "modrinth" else "⚡ CurseForge")
        source_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(source_label)

        downloads_label = QLabel(f"⬇ {self.format_number(project.downloads)}")
        downloads_label.setStyleSheet("color: #4ECDC4; font-size: 12px;")

        if project.author:
            author_label = QLabel(f"👤 {project.author}")
            author_label.setStyleSheet("color: #a9bed1; font-size: 12px;")
            stats_layout.addWidget(author_label)

        stats_layout.addWidget(downloads_label)

        if project.version and project.version != 'N/A':
            version_label = QLabel(f"v{project.version}")
            version_label.setStyleSheet("color: #a9bed1; font-size: 11px;")
            stats_layout.addWidget(version_label)

        stats_layout.addStretch()

        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить")
        add_btn.setObjectName("addBtn")
        add_btn.setFixedSize(90, 30)
        add_btn.setStyleSheet("""
            #addBtn {
                background-color: #24566a;
                color: #efffff;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            #addBtn:hover {
                background-color: #2d6a7c;
            }
        """)
        add_btn.clicked.connect(lambda checked, idx=index: self.add_mod_from_card(idx))

        stats_layout.addWidget(add_btn)

        info_layout.addWidget(title_label)
        info_layout.addWidget(desc_label)
        info_layout.addLayout(stats_layout)

        layout.addWidget(icon_widget)
        layout.addWidget(info_widget)

        return card

    def add_mod_from_card(self, index):
        if index >= len(self.projects):
            return

        project = self.projects[index]
        source = project.source

        # Проверяем, не добавлен ли уже
        for existing in self.selected_mods:
            if source == "modrinth" and existing.get("modrinth_id") == project.project_id:
                QMessageBox.information(self, "Информация", f"Мод '{project.title}' уже добавлен")
                return
            if source == "curseforge" and existing.get("curseforge_id") == project.project_id:
                QMessageBox.information(self, "Информация", f"Мод '{project.title}' уже добавлен")
                return

        if source == "modrinth":
            mod_info = {
                "source": "modrinth",
                "modrinth_id": project.project_id,
                "modrinth_slug": project.slug,
                "name": project.title,
                "filename": project.file_name or f"{project.slug}.jar",
                "project_id": project.project_id,
                "version_id": project.version_id,
                "mod_id": project.project_id
            }
        else:
            mod_info = {
                "source": "curseforge",
                "curseforge_id": project.project_id,
                "curseforge_slug": project.slug,
                "name": project.title,
                "filename": project.file_name or f"{project.slug}.jar",
                "project_id": project.project_id,
                "version_id": project.version_id,
                "mod_id": project.project_id
            }

        self.selected_mods.append(mod_info)
        self.update_selected_list()

        QMessageBox.information(
            self,
            "Мод добавлен",
            f"✅ Мод '{mod_info['name']}' добавлен в сборку."
        )

    def format_number(self, n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    def remove_selected(self):
        indices = sorted((self.selected_tree.indexOfTopLevelItem(item)
                          for item in self.selected_tree.selectedItems()), reverse=True)
        for index in indices:
            if index >= 0:
                del self.selected_mods[index]
        self.update_selected_list()

    def clear_all(self):
        self.selected_mods.clear()
        self.update_selected_list()

    def update_selected_list(self):
        self.selected_tree.clear()

        for mod in self.selected_mods:
            source_icon = "🌐" if mod["source"] == "modrinth" else "💾" if mod["source"] == "local" else "⚡"
            item = QTreeWidgetItem()
            item.setText(0, f"{source_icon} {mod['source'].capitalize()}")
            item.setText(1, mod["name"])
            item.setText(2, mod["filename"])
            self.selected_tree.addTopLevelItem(item)

        self.selected_count_label.setText(f"Всего: {len(self.selected_mods)}")
        self.analyze_btn.setEnabled(True)

    def analyze_dependencies(self):
        if not self.selected_mods:
            QMessageBox.warning(self, "Анализ", "Добавьте моды для анализа")
            return

        analyzer = DependencyAnalyzerUI(
            parent=self,
            minecraft_version=self.version_combo.currentText(),
            loader=self.loader_combo.currentText(),
            tree_widget=self.selected_tree
        )

        def on_analysis_complete(result):
            required_count = len(result.get('required_dependencies', []))
            optional_count = len(result.get('optional_dependencies', []))

            QMessageBox.information(
                self,
                "Анализ завершен",
                f"Найдено зависимостей:\n"
                f"• Обязательных: {required_count}\n"
                f"• Опциональных: {optional_count}"
            )

        analyzer.show_analyzer(self.selected_mods, on_analysis_complete)

    def save_collection(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название сборки!")
            return

        if not self.selected_mods and self.original_data is None:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один мод!")
            return

        if not self.loader_combo.currentText():
            QMessageBox.warning(self, 'Ошибка', 'Выберите доступный загрузчик для этой версии Minecraft.')
            return

        try:
            filenames = [safe_filename(mod['filename']).casefold() for mod in self.selected_mods]
            if len(set(filenames)) != len(filenames):
                raise ValueError('В сборке есть моды с одинаковыми именами файлов. Удалите дубликаты.')
        except (ValueError, KeyError) as exc:
            QMessageBox.warning(self, 'Ошибка', str(exc))
            return

        collection_data = deepcopy(self.original_data or {})
        collection_data.update({
            "name": name,
            "minecraft_version": self.version_combo.currentText(),
            "loader": self.loader_combo.currentText(),
            "mods": deepcopy(self.selected_mods),
            "mod_count": len(self.selected_mods),
            "source": collection_data.get('source', 'local'),
            "collection_type": self.mode_combo.currentData()
        })
        sources = {mod.get('source') for mod in self.selected_mods}
        if 'local' in sources and len(sources) > 1:
            collection_data['collection_type'] = 'mixed'
        original = self.original_data or {}
        changed = any(collection_data.get(key) != original.get(key)
                      for key in ('minecraft_version', 'loader', 'mods'))
        if changed:
            collection_data['dependencies_analyzed'] = False
            collection_data.pop('dependency_info', None)
            for mod in collection_data['mods']:
                mod.pop('dependencies_resolved', None)
                mod.pop('last_dependency_check', None)
                mod.pop('resolved_dependencies', None)
        if any(collection_data.get(key) != original.get(key) for key in ('minecraft_version', 'loader')):
            collection_data.pop('loader_version', None)

        if self.original_filename:
            success, result = save_collection(collection_data, filename=self.original_filename)
        else:
            success, result = save_collection(collection_data)

        if success:
            QMessageBox.information(
                self,
                "Успех",
                f"Сборка '{name}' {'обновлена' if self.original_data is not None else 'создана'}!\n\n"
                f"• Модов: {len(self.selected_mods)}\n"
                f"• Версия: {self.version_combo.currentText()}\n"
                f"• Загрузчик: {self.loader_combo.currentText()}"
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить сборку:\n{result}")
