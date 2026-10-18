# Ui/BaseWindow.py
"""
Базовый класс для всех окон с единым фоном
"""
import os
from PyQt6.QtWidgets import QDialog, QMainWindow
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

from ConfDir.ScaleRes import (
    find_closest_resolution,
    get_background_path,
    ensure_backgrounds_folder,
    USER_YAMALPIXEL_RES
)


class BaseWindowMixin:
    """Миксин для добавления фона в окна"""

    _stylesheet_cache = None
    _current_background = None

    def setup_background(self):
        """Настраивает фон для окна"""
        # Делаем фон прозрачным для стилей
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Загружаем фон
        self.load_background()

    def get_base_stylesheet(self, background_path=None):
        """Возвращает полный стиль с фоном"""
        if background_path and os.path.exists(background_path):
            # Экранируем обратные слеши для Windows
            bg_path = background_path.replace('\\', '/')
            background_css = f"""
                QWidget {{
                    background-image: url("{bg_path}");
                    background-repeat: no-repeat;
                    background-position: center;
                    background-attachment: fixed;
                }}
            """
        else:
            # Градиентный фон по умолчанию
            background_css = """
                QDialog#backgroundDialog {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1a1a2e, stop:0.3 #16213e, stop:0.6 #0f3460, stop:1 #1a1a2e);
                }
            """

        return background_css + """
            QWidget { background-image: none; }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QPushButton {
                background-color: rgba(58, 58, 74, 0.85);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(74, 74, 90, 0.9);
            }
            QPushButton#close_btn {
                background-color: #ff4757;
            }
            QPushButton#close_btn:hover {
                background-color: #ff6b6b;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: rgba(42, 42, 58, 0.85);
                color: white;
                border: 1px solid rgba(78, 205, 196, 0.5);
                border-radius: 8px;
                padding: 8px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid rgba(78, 205, 196, 1);
            }
            QTreeWidget, QListWidget {
                background-color: rgba(26, 26, 42, 0.85);
                color: #e0e0e0;
                border: 1px solid rgba(58, 58, 74, 0.8);
                border-radius: 8px;
                outline: none;
            }
            QTreeWidget::item:selected, QListWidget::item:selected {
                background-color: rgba(78, 205, 196, 0.7);
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: rgba(42, 42, 58, 0.9);
                color: rgba(78, 205, 196, 1);
                padding: 8px;
                border: none;
            }
            QTabWidget::pane {
                background-color: rgba(30, 30, 42, 0.7);
                border: 1px solid rgba(58, 58, 74, 0.8);
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: rgba(42, 42, 58, 0.7);
                color: #e0e0e0;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: rgba(78, 205, 196, 0.8);
                color: #1a1a1a;
            }
            QTabBar::tab:hover {
                background-color: rgba(58, 58, 74, 0.9);
            }
            QProgressBar {
                background-color: rgba(58, 58, 74, 0.7);
                border: none;
                border-radius: 8px;
                height: 20px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 107, 107, 0.8), stop:1 rgba(78, 205, 196, 0.8));
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: rgba(42, 42, 58, 0.6);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(78, 205, 196, 0.7);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(78, 205, 196, 0.9);
            }
            QMenuBar {
                background-color: rgba(0, 0, 0, 0.5);
                color: white;
            }
            QMenuBar::item:selected {
                background-color: rgba(78, 205, 196, 0.7);
            }
            QMenu {
                background-color: rgba(43, 43, 43, 0.9);
                color: white;
                border: 1px solid rgba(78, 205, 196, 0.5);
            }
            QMenu::item:selected {
                background-color: rgba(78, 205, 196, 0.7);
            }
            QMessageBox {
                background-color: rgba(43, 43, 43, 0.95);
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: rgba(74, 85, 104, 0.9);
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: rgba(90, 107, 130, 0.9);
            }
            QFrame {
                background-color: transparent;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget {
                background-color: transparent;
            }
            QWidget#central_widget, QWidget#content_widget {
                background-color: transparent;
            }
        """

    def load_background(self):
        """Загружает фон для окна"""
        try:
            # Получаем размер окна
            window_width = self.width()
            window_height = self.height()

            # Если окно еще не отрисовано, пропускаем
            if window_width <= 0 or window_height <= 0:
                QTimer.singleShot(100, self.load_background)
                return

            # Создаем папку для фонов если её нет
            ensure_backgrounds_folder()

            # Выбираем фон под соотношение сторон
            bg_file = find_closest_resolution(window_width, window_height)

            # Получаем путь к файлу фона
            bg_path = get_background_path(bg_file)

            # Если конкретный файл не найден, пробуем найти любой PNG
            if not bg_path:
                if os.path.exists(USER_YAMALPIXEL_RES):
                    for file in os.listdir(USER_YAMALPIXEL_RES):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            bg_path = os.path.join(USER_YAMALPIXEL_RES, file)
                            break

            if bg_path and os.path.exists(bg_path):
                print(f"🎨 Устанавливаем фон: {bg_path}")
                # Устанавливаем фон через setStyleSheet
                self.setStyleSheet(self.get_base_stylesheet(bg_path))
                self._current_background = bg_path
                return True
            else:
                print(f"⚠️ Фон не найден, используем градиент")
                self.setStyleSheet(self.get_base_stylesheet())
                return False

        except Exception as e:
            print(f"❌ Ошибка загрузки фона: {e}")
            import traceback
            traceback.print_exc()
            self.setStyleSheet(self.get_base_stylesheet())
            return False

    def resizeEvent(self, event):
        """При изменении размера перезагружаем фон"""
        # Вызываем родительский метод, если он есть
        if hasattr(super(), 'resizeEvent'):
            super().resizeEvent(event)
        # Перезагружаем фон с задержкой
        QTimer.singleShot(100, self.load_background)

    def showEvent(self, event):
        """При показе окна обновляем фон"""
        if hasattr(super(), 'showEvent'):
            super().showEvent(event)
        QTimer.singleShot(50, self.load_background)


class BaseDialog(QDialog, BaseWindowMixin):
    """Базовый класс для всех диалогов с единым фоном"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("backgroundDialog")
        self.setup_background()


class BaseMainWindow(QMainWindow, BaseWindowMixin):
    """Базовый класс для главного окна с единым фоном"""

    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setup_background()