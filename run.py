# run_pyqt.py
import sys
import os
import signal

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Ui.MainWindow import run_main_window

if __name__ == "__main__":
    # Инициализация ресурсов
    from ConfDir.Configs import setup_environment

    setup_environment()

    # Запуск
    sys.exit(run_main_window())