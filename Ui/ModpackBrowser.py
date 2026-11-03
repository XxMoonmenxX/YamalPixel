"""Standalone Modrinth/CurseForge modpack catalog dialog."""

from pathlib import Path

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from Core.collection_loader import get_collections_dir
from Core.instances import collection_directory
from Core.mod_transaction import safe_target
from Core.modpack_catalog import ModpackCatalogService
from mrpack_import_example import MrpackImportWorker


class ModpackProject:
    """Normalized item shown in the catalog."""

    def __init__(self, data):
        self.source = data.get("source", "modrinth")
        self.project_id = str(data.get("project_id") or data.get("id") or "")
        self.title = data.get("name") or data.get("title") or "Без названия"
        self.description = data.get("description", "")
        self.downloads = int(data.get("downloads") or 0)
        self.minecraft_version = data.get("minecraft_version", "")
        self.loader = data.get("loader", "")
        self.raw = dict(data)


class ModpackSearchWorker(QThread):
    result = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, query, source, sort, parent=None):
        super().__init__(parent)
        self.query = query
        self.source = source
        self.sort = sort

    def run(self):
        try:
            self.progress.emit(10, "Поиск модпаков в каталоге…")
            entries = ModpackCatalogService().search(
                self.source, self.query, self.sort, limit=50
            )
            projects = [ModpackProject(entry) for entry in entries]
            self.progress.emit(100, f"Найдено модпаков: {len(projects)}")
            self.result.emit(projects)
        except Exception as exc:
            self.error.emit(str(exc))


class ModpackParseWorker(QThread):
    result = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project

    def run(self):
        try:
            def report(current, total, message):
                self.progress.emit(current, total, message)

            metadata = ModpackCatalogService().download_and_install(
                self.project.raw,
                self.project.source,
                progress_callback=report,
                persist_collection=True,
            )
            self.result.emit(metadata)
        except Exception as exc:
            self.error.emit(str(exc))


class ModpackBrowserDialog(QDialog):
    """Search, parse and save modpacks independently from CollectionCreator."""

    imported = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Каталог модпаков")
        self.setObjectName("modpackBrowser")
        self.setMinimumSize(900, 620)
        self.resize(1180, 760)
        self.setModal(True)

        self.projects = []
        self.search_worker = None
        self.parse_worker = None
        self.import_worker = None
        self.is_loading = False
        self.search_failed = False

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        title = QLabel("📦 Каталог модпаков")
        title.setObjectName("browserTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        controls = QHBoxLayout()
        self.import_button = QPushButton("📁 Импортировать свой .mrpack")
        self.import_button.clicked.connect(self.import_local_mrpack)
        controls.addWidget(self.import_button)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Поиск модпака или пустой запрос для популярных")
        self.query_input.returnPressed.connect(self.search)
        controls.addWidget(self.query_input, 1)

        self.source_combo = QComboBox()
        self.source_combo.addItem("Modrinth", "modrinth")
        self.source_combo.addItem("CurseForge", "curseforge")
        self.source_combo.addItem("Modrinth + CurseForge", "both")
        controls.addWidget(self.source_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("По популярности", "downloads")
        self.sort_combo.addItem("По дате обновления", "updated")
        self.sort_combo.addItem("По релевантности", "relevance")
        controls.addWidget(self.sort_combo)

        self.search_button = QPushButton("🔍 Найти")
        self.search_button.clicked.connect(self.search)
        controls.addWidget(self.search_button)
        root.addLayout(controls)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(8, 8, 8, 8)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch()
        self.scroll.setWidget(self.results_container)
        root.addWidget(self.scroll, 1)

        self.status_label = QLabel("Введите запрос или нажмите «Найти» для популярных модпаков")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog#modpackBrowser { background: #102033; color: #eaf2fa; }
            QLabel#browserTitle { color: #f1f7ff; font-size: 24px; font-weight: 600; padding: 8px; }
            QLineEdit, QComboBox { background: #0b192a; color: #eaf2fa;
                border: 1px solid #38516a; border-radius: 8px; padding: 8px 10px; }
            QPushButton { background: #203b53; color: #eaf2fa; border: 1px solid #385971;
                border-radius: 8px; padding: 8px 12px; }
            QPushButton:hover { background: #2b506a; border-color: #68e0cc; }
            QPushButton:disabled { color: #7f96aa; background: #17283a; }
            QScrollArea { background: #0b192a; border: 1px solid #30475e; border-radius: 10px; }
            QWidget#resultsContainer { background: #0b192a; }
            QWidget#modpackCard { background: #172c42; border: 1px solid #30475e; border-radius: 10px; }
            QLabel#packTitle { color: #f1f7ff; font-size: 16px; font-weight: 600; }
            QLabel#packDescription { color: #b4c7d8; }
            QProgressBar { background: #17283a; border: 1px solid #30475e; border-radius: 6px; }
            QProgressBar::chunk { background: #4ea89c; border-radius: 5px; }
        """)

    def search(self):
        if self.is_loading:
            return
        query = self.query_input.text().strip()
        sort = self.sort_combo.currentData() or "downloads"
        if not query and sort != "downloads":
            QMessageBox.warning(
                self,
                "Поиск модпаков",
                "Пустой запрос доступен только для сортировки по популярности.",
            )
            return

        self.is_loading = True
        self.search_failed = False
        self.search_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Поиск модпаков…")
        self.projects = []
        self.clear_results()

        self.search_worker = ModpackSearchWorker(
            query, self.source_combo.currentData(), sort, self
        )
        self.search_worker.result.connect(self.on_search_result)
        self.search_worker.error.connect(self.on_search_error)
        self.search_worker.progress.connect(self.on_search_progress)
        self.search_worker.finished.connect(self.on_search_finished)
        self.search_worker.start()

    def on_search_result(self, projects):
        self.projects = projects
        self.render_results()
        self.status_label.setText(f"Найдено модпаков: {len(projects)}")

    def on_search_error(self, message):
        self.search_failed = True
        self.status_label.setText(f"Ошибка: {message}")
        QMessageBox.critical(self, "Поиск модпаков", message)

    def on_search_progress(self, value, message):
        self.progress_bar.setValue(max(0, min(100, int(value))))
        self.status_label.setText(message)

    def on_search_finished(self):
        self.is_loading = False
        self.search_button.setEnabled(True)
        self.import_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        worker = self.search_worker
        if worker is not None:
            worker.deleteLater()
            self.search_worker = None
        if not self.projects and not self.search_failed:
            self.status_label.setText("Модпаки не найдены")

    def clear_results(self):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def render_results(self):
        self.clear_results()
        for index, project in enumerate(self.projects):
            self.results_layout.insertWidget(self.results_layout.count() - 1,
                                             self.create_modpack_card(project, index))

    @staticmethod
    def _format_number(value):
        value = int(value or 0)
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(value)

    def create_modpack_card(self, project, index):
        card = QWidget()
        card.setObjectName("modpackCard")
        card.setMinimumHeight(108)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)

        icon = QLabel("📦" if project.source == "modrinth" else "⚡")
        icon.setFixedSize(52, 52)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: #203b53; border-radius: 8px; font-size: 22px;")
        layout.addWidget(icon)

        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel(project.title)
        title.setObjectName("packTitle")
        description = project.description[:180] + ("…" if len(project.description) > 180 else "")
        desc = QLabel(description or "Модпак из каталога")
        desc.setObjectName("packDescription")
        desc.setWordWrap(True)
        stats = QLabel(
            f"{project.source.capitalize()} · "
            f"MC: {project.minecraft_version or 'из архива'} · "
            f"Загрузчик: {project.loader or 'из архива'} · "
            f"⬇ {self._format_number(project.downloads)}"
        )
        info_layout.addWidget(title)
        info_layout.addWidget(desc)
        info_layout.addWidget(stats)
        layout.addWidget(info, 1)

        install = QPushButton("Установить")
        install.setMinimumWidth(120)
        install.clicked.connect(lambda checked, i=index: self.install_project(i))
        layout.addWidget(install)
        return card

    def install_project(self, index):
        if index < 0 or index >= len(self.projects):
            return
        if self.parse_worker is not None and self.parse_worker.isRunning():
            return
        project = self.projects[index]
        self.is_loading = True
        self.search_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"Скачивание и разбор: {project.title}…")
        self.parse_worker = ModpackParseWorker(project, self)
        self.parse_worker.progress.connect(self.on_parse_progress)
        self.parse_worker.result.connect(self.on_parsed)
        self.parse_worker.error.connect(self.on_parse_error)
        self.parse_worker.finished.connect(self.on_parse_finished)
        self.parse_worker.start()

    def on_parse_progress(self, current, total, message):
        maximum = max(int(total), 1)
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(max(0, min(int(current), maximum)))
        self.status_label.setText(message)

    def on_parsed(self, metadata):
        self._on_saved(metadata)

    def on_parse_error(self, message):
        self.status_label.setText(f"Ошибка: {message}")
        QMessageBox.critical(self, "Разбор модпака", message)

    def on_parse_finished(self):
        self.is_loading = False
        self.search_button.setEnabled(True)
        self.import_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        worker = self.parse_worker
        if worker is not None:
            worker.deleteLater()
            self.parse_worker = None

    @staticmethod
    def _collection_directory(instance_name):
        safe_name = ''.join(char for char in instance_name
                            if char.isalnum() or char in (' ', '-', '_')).rstrip()[:50]
        filename = f"{safe_name}.json"
        return collection_directory({
            "name": instance_name,
            "filename": filename,
            "instance_id": "file:" + filename,
        })

    def import_local_mrpack(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите .mrpack", "", "Modrinth pack (*.mrpack);;Все файлы (*)"
        )
        if not path:
            return
        default_name = Path(path).stem
        name, accepted = QInputDialog.getText(
            self, "Новый инстанс", "Имя инстанса:", text=default_name
        )
        name = name.strip()
        if not accepted or not name:
            return

        safe_name = ''.join(char for char in name if char.isalnum() or char in (' ', '-', '_')).rstrip()[:50]
        try:
            if not safe_name:
                raise ValueError('Название не содержит допустимых символов')
            collection_file = Path(safe_target(get_collections_dir(), safe_name + '.json'))
            destination = self._collection_directory(name)
            if collection_file.exists() or destination.exists() or destination.is_symlink():
                raise ValueError('Сборка или инстанс с таким именем уже существуют')
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Импорт .mrpack', str(exc))
            return

        self.is_loading = True
        self.search_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Импорт .mrpack…")
        self.import_worker = MrpackImportWorker(path, name)
        self.import_worker.instance_directory = self._collection_directory(name)
        self.import_worker.persist_collection = True
        self.import_worker.progress.connect(self.on_import_progress)
        self.import_worker.succeeded.connect(self.on_local_imported)
        self.import_worker.failed.connect(self.on_import_error)
        self.import_worker.finished.connect(self.on_import_finished)
        self.import_worker.start()

    def _has_active_worker(self):
        return any(worker is not None and worker.isRunning()
                   for worker in (self.search_worker, self.parse_worker, self.import_worker))

    def reject(self):
        if self._has_active_worker():
            self.status_label.setText('Дождитесь завершения текущей операции')
            return
        super().reject()

    def closeEvent(self, event):
        if self._has_active_worker():
            self.status_label.setText('Дождитесь завершения текущей операции')
            event.ignore()
            return
        super().closeEvent(event)

    def on_import_progress(self, current, total, message):
        maximum = max(int(total), 1)
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(max(0, min(int(current), maximum)))
        self.status_label.setText(message)

    def on_local_imported(self, metadata):
        self._on_saved(metadata)

    def on_import_error(self, message):
        self.status_label.setText(f"Ошибка: {message}")
        QMessageBox.critical(self, "Импорт .mrpack", message)

    def on_import_finished(self):
        self.is_loading = False
        self.search_button.setEnabled(True)
        self.import_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        worker = self.import_worker
        if worker is not None:
            worker.deleteLater()
            self.import_worker = None

    def _on_saved(self, data):
        self.status_label.setText(f"Импортирован модпак «{data['name']}»")
        self.imported.emit(data)
        QMessageBox.information(self, "Модпак импортирован",
                                f"Сборка «{data['name']}» сохранена.")


__all__ = [
    "ModpackBrowserDialog",
    "ModpackProject",
    "ModpackSearchWorker",
    "ModpackParseWorker",
]
