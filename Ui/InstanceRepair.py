"""Repair a selected instance without deleting worlds or launcher storage."""
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QProgressBar, QVBoxLayout


class RepairWorker(QThread):
    progress = pyqtSignal(str, str)
    result = pyqtSignal(bool, str)

    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.version = version

    def run(self):
        try:
            from Core.run import install_required_components_sync
            install_required_components_sync(self.version, self.progress.emit, raise_on_error=True)
            self.result.emit(True, 'Файлы проверены, моды сборки восстановлены. Миры и настройки сохранены.')
        except Exception as exc:
            self.result.emit(False, str(exc))


class InstanceRepairDialog(QDialog):
    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Восстановление: ' + version)
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        self.label = QLabel('Проверка файлов…')
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        layout.addWidget(self.bar)
        self.close_button = QPushButton('Закрыть')
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
        self.worker = RepairWorker(version, self)
        self.worker.progress.connect(self.update_progress)
        self.worker.result.connect(self.show_result)
        self.worker.finished.connect(lambda: self.close_button.setEnabled(True))
        self.worker.start()

    def update_progress(self, kind, value):
        if kind == 'progress':
            self.bar.setRange(0, 100)
            self.bar.setValue(int(value))
        else:
            self.label.setText(value)

    def show_result(self, success, message):
        self.bar.setRange(0, 100)
        self.bar.setValue(100 if success else 0)
        self.label.setText(message)

    def done(self, result):
        if not self.worker.isRunning():
            super().done(result)

    def closeEvent(self, event):
        if self.worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)
