# run.py - ФИНАЛЬНАЯ БОЕВАЯ ВЕРСИЯ
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ConfDir.Versions import CURRENT_VERSION
from launcher_paths import resource_path
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

try:
    from Network.Updates import apply_staged_update
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        apply_staged_update()
except Exception:
    logging.getLogger(__name__).debug('Staged update was not applied', exc_info=True)

# ============================================================
# ВОССТАНОВЛЕНИЕ STDOUT
# ============================================================
log_dir = Path.home() / 'YamalPixel' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(
    log_dir / 'launcher.log', maxBytes=2 * 1024 * 1024, backupCount=3, encoding='utf-8')],
    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
if sys.stdout is None:
    sys.stdout = open(log_dir / 'launcher-console.log', 'a', encoding='utf-8', buffering=1)
if sys.stderr is None:
    sys.stderr = sys.stdout
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='backslashreplace')



def log_uncaught_error(kind, value, traceback):
    logging.critical('Необработанная ошибка лаунчера', exc_info=(kind, value, traceback))
    sys.__excepthook__(kind, value, traceback)


sys.excepthook = log_uncaught_error


# ============================================================
# СПЛЕШ
# ============================================================
class SplashWithProgress(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(450, 250)
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:1 #0f3460);
            border-radius: 20px;
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        self.title = QLabel("🚀 YamalPixel Launcher")
        self.title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #4ECDC4;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)

        self.version = QLabel(CURRENT_VERSION)
        self.version.setFont(QFont("Segoe UI", 10))
        self.version.setStyleSheet("color: #666666;")
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.version)

        layout.addStretch()

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a3a;
                border: none;
                border-radius: 10px;
                height: 20px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #4ECDC4);
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.progress)

        self.status = QLabel("Загрузка...")
        self.status.setFont(QFont("Segoe UI", 10))
        self.status.setStyleSheet("color: #888888;")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def update_progress(self, value, text):
        self.progress.setValue(value)
        self.status.setText(text)


# ============================================================
# ГЛАВНЫЙ БЛОК
# ============================================================
# run.py - ПРАВИЛЬНЫЙ ПОРЯДОК
if __name__ == "__main__":
    if '--smoke-test' in sys.argv:
        from Core.build_smoke import main as smoke_main
        sys.exit(smoke_main())
    keep_mods = '--keep-mods' in sys.argv
    if keep_mods:
        sys.argv.remove('--keep-mods')
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))

    splash = SplashWithProgress()
    splash.show()
    app.processEvents()

    # Загружаем модули ДО создания окна
    from Ui.MainWindow import MainWindow

    # Закрываем сплеш
    splash.close()

    # СОЗДАЁМ ОКНО
    window = MainWindow()
    # Дублируем установку после создания окна для корректного значка
    # в заголовке и на панели задач Windows.
    window.setWindowIcon(QIcon(resource_path('icon.ico')))
    if keep_mods:
        from ConfDir.Configs import CONFIG
        CONFIG['launch_without_mods_next'] = True
    window.show()

    # ЗАПУСКАЕМ
    sys.exit(app.exec())
