"""Minimal PyQt6 UI example for :class:`Core.mrpack_handler.MrpackImporter`.

The widget can be embedded into an existing window or copied as a starting
point for a launcher page.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from Core.mrpack_handler import MrpackImporter


class MrpackImportWorker(QThread):
    """Run the blocking ZIP and download work outside the GUI thread."""

    progress = pyqtSignal(int, int, str)
    status = pyqtSignal(str)
    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, mrpack_path, instance_name, parent=None, instance_directory=None):
        super().__init__(parent)
        self.mrpack_path = mrpack_path
        self.instance_name = instance_name
        self.instance_directory = instance_directory
        self.persist_collection = False

    def run(self):
        try:
            def report(current, total, message):
                self.progress.emit(current, total, message)
                self.status.emit(message)

            metadata = MrpackImporter(
                self.mrpack_path,
                self.instance_name,
                progress_callback=report,
                instance_directory=self.instance_directory,
                persist_collection=self.persist_collection,
            ).import_pack()
            self.succeeded.emit(metadata)
        except Exception as exc:
            self.failed.emit(str(exc))


class MrpackImportWidget(QWidget):
    """A copy-ready button, progress bar and status label for mrpack import."""

    imported = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None

        self.import_button = QPushButton("Импорт .mrpack")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.status_label = QLabel("Готово к импорту")

        layout = QVBoxLayout(self)
        layout.addWidget(self.import_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        self.import_button.clicked.connect(self.choose_mrpack)

    def choose_mrpack(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Modrinth-сборку",
            "",
            "Modrinth pack (*.mrpack);;Все файлы (*)",
        )
        if not path:
            return

        default_name = path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if default_name.lower().endswith(".mrpack"):
            default_name = default_name[:-7]
        instance_name, accepted = QInputDialog.getText(
            self, "Новый инстанс", "Имя инстанса:", text=default_name
        )
        if not accepted or not instance_name.strip():
            return
        self.start_import(path, instance_name.strip())

    def start_import(self, path, instance_name):
        if self.worker is not None and self.worker.isRunning():
            return

        self.import_button.setEnabled(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.status_label.setText("Подготовка импорта...")

        self.worker = MrpackImportWorker(path, instance_name, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.status.connect(self.status_label.setText)
        self.worker.succeeded.connect(self._on_success)
        self.worker.failed.connect(self._on_error)
        self.worker.finished.connect(self._on_thread_finished)
        self.worker.start()

    def _on_progress(self, current, total, message):
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(min(current, max(total, 1)))
        self.status_label.setText(message)

    def _on_success(self, metadata):
        self.status_label.setText("Импорт завершён")
        self.imported.emit(metadata)
        QMessageBox.information(
            self,
            "Импорт .mrpack",
            f"Инстанс «{metadata['name']}» создан. "
            f"Файлов: {metadata['mod_count']}",
        )

    def _on_error(self, message):
        self.status_label.setText("Ошибка импорта")
        QMessageBox.critical(self, "Импорт .mrpack", message)

    def _on_thread_finished(self):
        self.import_button.setEnabled(True)
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None


__all__ = ["MrpackImportWorker", "MrpackImportWidget"]
