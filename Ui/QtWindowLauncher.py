## Ui/QtWindowLauncher.py
"""
Менеджер для запуска PyQt6 окон из Tkinter
"""
import sys
import threading
from typing import Optional


class QtWindowLauncher:
    _qt_app = None

    @classmethod
    def ensure_qt_app(cls):
        from PyQt6.QtWidgets import QApplication
        if cls._qt_app is None:
            cls._qt_app = QApplication.instance()
            if cls._qt_app is None:
                cls._qt_app = QApplication([])  # Без sys.argv
        return cls._qt_app

    @classmethod
    def show_diagnostic_window(cls, parent=None, selected_version=None):
        from Ui.QtDiagnosticWindow import QtDiagnosticWindow

        app = cls.ensure_qt_app()
        window = QtDiagnosticWindow(selected_version=selected_version)
        window.show()
        app.exec()

def launch_without_mods(self):
    import __main__
    if hasattr(__main__, 'launch_without_mods'):
        __main__.launch_without_mods(self)  # Передаем self как родителя

def complete_reinstall(self):
    import __main__
    if hasattr(__main__, 'complete_reinstall'):
        __main__.complete_reinstall(self)  # Передаем self как родителя

def auto_repair(self):
    import __main__
    if hasattr(__main__, 'old_repair_with_ui'):
        self.close()
        threading.Thread(target=lambda: __main__.old_repair_with_ui(self), daemon=True).start()  # Передаем self как родителя