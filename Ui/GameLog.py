"""Live Minecraft console, kept bounded and rendered as plain text."""
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices, QTextCursor
from PyQt6.QtWidgets import QDialog, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout


class GameLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path = None
        self.setWindowTitle('Живой лог Minecraft')
        self.resize(950, 580)
        self.setStyleSheet('QDialog { background: #171d29; } QLabel {color: #a7ddda;} '
                           'QPlainTextEdit { background: #101621; color: #e8edf7; padding: 8px; font-family: Consolas; } '
                           'QPushButton { background: #344259; color: white; padding: 8px; border-radius: 5px; }')
        layout = QVBoxLayout(self)
        self.path_label = QLabel('Ожидание запуска Java…')
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(2000)
        layout.addWidget(self.console)
        button = QPushButton('Открыть папку лога')
        button.clicked.connect(self.open_folder)
        layout.addWidget(button)

    def start_session(self, path):
        self.path = Path(path)
        self.path_label.setText(str(self.path))
        self.console.clear()

    def append_text(self, text):
        scrollbar = self.console.verticalScrollBar()
        follow = scrollbar.value() >= scrollbar.maximum() - 3
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        if follow:
            scrollbar.setValue(scrollbar.maximum())

    def open_folder(self):
        if self.path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.path.parent)))
