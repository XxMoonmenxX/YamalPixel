"""Shared progress UI and worker lifecycle for mod and shader downloads."""
import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QTextEdit, QPushButton

from Core.instances import ensure_game_directory
from Core.mod_transaction import safe_target
from Ui.BaseWindow import PlainDialog


class BatchDownloadWorker(QThread):
    progress = pyqtSignal(int, int, str)
    result = pyqtSignal(int, int)
    log = pyqtSignal(str)

    def __init__(self, items, minecraft_dir=None, kind='mods'):
        super().__init__()
        self.items = list(items)
        self.minecraft_dir = minecraft_dir or ensure_game_directory()
        self.kind = kind
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        from Network.Downloader import download_single_mod_turbo, download_yandex_file_sync
        success_count = 0
        for index, item in enumerate(self.items):
            if self.cancelled:
                self.log.emit('❌ Загрузка отменена')
                break
            name = item.get('name') or item.get('file') or item.get('filename') or 'файл'
            self.progress.emit(index, len(self.items), name)
            self.log.emit(f'⬇️ Загрузка: {name}')
            try:
                if self.kind == 'shaders':
                    destination = safe_target(os.path.join(self.minecraft_dir, 'shaderpacks'), item['file'])
                    success = download_yandex_file_sync(item['url'], destination, 'shader')
                else:
                    success = download_single_mod_turbo(item, self.minecraft_dir)
                success_count += bool(success)
                self.log.emit(f'{"✅ Успешно" if success else "❌ Ошибка"}: {name}')
            except Exception as exc:
                self.log.emit(f'❌ {name}: {exc}')
        self.result.emit(success_count, len(self.items))


class ModDownloadWorker(BatchDownloadWorker):
    pass


class ShaderDownloadWorker(BatchDownloadWorker):
    def __init__(self, shaders, minecraft_dir=None):
        super().__init__(shaders, minecraft_dir, kind='shaders')


class DownloadProgressDialog(PlainDialog):
    def __init__(self, parent, items, kind='mods'):
        super().__init__(parent)
        self._close_when_finished = False
        noun = 'шейдеров' if kind == 'shaders' else 'модов'
        self.setWindowTitle('Загрузка ' + noun)
        self.setFixedSize(550, 450)
        self.setModal(True)
        layout = QVBoxLayout(self)
        title = QLabel('📥 Загрузка ' + noun)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(QLabel(f'Всего {noun}: {len(items)}'))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.current_label = QLabel('Подготовка к загрузке…')
        layout.addWidget(self.current_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        buttons = QHBoxLayout()
        self.cancel_btn = QPushButton('Отмена')
        self.cancel_btn.clicked.connect(self.cancel_download)
        buttons.addWidget(self.cancel_btn)
        self.close_btn = QPushButton('Закрыть')
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)
        self.worker = (ShaderDownloadWorker(items) if kind == 'shaders' else ModDownloadWorker(items))
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log_text.append)
        self.worker.result.connect(self.on_download_finished)
        self.worker.finished.connect(self._thread_finished)
        self.worker.start()

    def update_progress(self, current, total, name):
        self.progress_bar.setValue(int(current * 100 / total) if total else 0)
        self.current_label.setText(f'Загрузка: {name} ({current + 1}/{total})')

    def on_download_finished(self, success_count, total):
        if success_count == total:
            self.progress_bar.setValue(100)
        self.current_label.setText(f'Загружено: {success_count} из {total}')
        self.cancel_btn.setEnabled(False)

    def _thread_finished(self):
        self.close_btn.setEnabled(True)
        if self._close_when_finished:
            self.accept()

    def cancel_download(self):
        self.worker.cancel()
        self.cancel_btn.setEnabled(False)
        self.current_label.setText('Отмена после завершения текущей загрузки…')

    def done(self, result):
        if self.worker.isRunning():
            self._close_when_finished = True
            self.cancel_download()
            return
        super().done(result)

    def closeEvent(self, event):
        if self.worker.isRunning():
            self._close_when_finished = True
            self.cancel_download()
            event.ignore()
        else:
            event.accept()
