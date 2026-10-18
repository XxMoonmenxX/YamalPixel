"""Offline checks executed inside the compiled launcher after a build."""
import argparse
import json
import tempfile
import traceback
import zipfile
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap
from launcher_paths import resource_path, launcher_executable


class ProbeWorker(QThread):
    value = pyqtSignal(str)

    def run(self):
        self.value.emit('worker-ok')


class ProbeReceiver(QObject):
    received = False
    gui_thread = False

    @pyqtSlot(str)
    def receive(self, value):
        self.received = value == 'worker-ok'
        self.gui_thread = QThread.currentThread() == QApplication.instance().thread()


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true')
    parser.add_argument('--smoke-report', type=Path, required=True)
    args = parser.parse_args(argv)
    report = {'ok': False, 'checks': [], 'executable': launcher_executable()}
    try:
        app = QApplication.instance() or QApplication([])
        app.setQuitOnLastWindowClosed(False)
        import MCLIB
        import certifi
        import aiohttp
        import pygame
        import mcstatus
        import pypresence
        import psutil
        from Ui.MainWindow import MainWindow
        from Ui.CollectionCreator import CollectionCreator
        from Ui.collection_manager import CollectionManager
        from Ui.LauncherGuide import LauncherGuide
        from Core.local_mods import import_local_mods, copy_local_mod
        check(bool(MCLIB.utils.get_library_version()), 'Не найден MCLIB/version.txt')
        check(Path(certifi.where()).is_file(), 'Не найдены CA-сертификаты')
        report['checks'].append('dependencies')
        check(not QIcon(resource_path('icon.ico')).isNull(), 'Не загружается иконка')
        check(Path(resource_path('Ui/assets/chevron-down.svg')).is_file(), 'Не найден SVG')
        check(not QPixmap(resource_path('YamalPixelRes/logo2.png')).isNull(), 'Не загружается фон')
        report['checks'].append('resources')
        from Core.game_log import loading_stage
        from Ui.GameLog import GameLogDialog
        log_dialog = GameLogDialog()
        log_dialog.append_text('Loading 57 mods\n')
        check('57 mods' in log_dialog.console.toPlainText(), 'Не работает живой лог Minecraft')
        check(loading_stage('Loading 57 mods') is not None, 'Не распознаются этапы запуска')
        log_dialog.close()
        report['checks'].append('minecraft-live-log')
        guide = LauncherGuide()
        guide.search.setText('Ctrl/Shift')
        check('Ctrl/Shift' in guide.browser.toPlainText(), 'Не работает поиск в гайде')
        guide.close()
        report['checks'].append('user-guide')
        dialog = CollectionCreator()
        dialog.mode_combo.setCurrentIndex(1)
        check(dialog.mode_combo.currentData() == 'custom', 'Недоступен режим кастомной сборки')
        dialog.show()
        app.processEvents()
        dialog.close()
        report['checks'].append('collection-gui')
        sample = {'name': 'Build edit check', 'minecraft_version': '1.20.1', 'loader': 'fabric',
                  'mods': [{'name': 'Remote', 'source': 'modrinth', 'filename': 'remote.jar'},
                           {'name': 'Local', 'source': 'local', 'filename': 'local.jar'}]}
        editor = CollectionCreator(collection_data=sample, original_filename='build-check.json')
        check(editor.mode_combo.currentData() == 'mixed', 'Не открывается смешанная сборка')
        check(editor.selected_tree.topLevelItemCount() == 2, 'Не загружается список модов редактора')
        editor.selected_tree.topLevelItem(0).setSelected(True)
        editor.remove_selected()
        check(len(editor.selected_mods) == 1 and len(sample['mods']) == 2, 'Редактор изменяет исходные данные')
        editor.reject()
        report['checks'].append('collection-editor')
        receiver = ProbeReceiver()
        worker = ProbeWorker()
        worker.value.connect(receiver.receive)
        timer = QTimer()
        timer.setInterval(20)
        timer.timeout.connect(lambda: app.quit() if receiver.received else None)
        timer.start()
        QTimer.singleShot(5000, app.quit)
        worker.start()
        app.exec()
        worker.wait(2000)
        timer.stop()
        check(receiver.received and receiver.gui_thread, 'Не работают сигналы QThread → GUI')
        report['checks'].append('qt-thread-signals')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'custom.jar'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('fabric.mod.json', '{"id":"build-check"}')
            mods = import_local_mods([source], root / 'collections')
            source.unlink()
            copy_local_mod(mods[0], root / 'collections', root / 'installed.jar')
            check((root / 'installed.jar').is_file(), 'Не работает установка локального мода')
        report['checks'].append('local-mods')
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    args.smoke_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1
