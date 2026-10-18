"""Human-readable game failure reports, presented on the Qt GUI thread."""
import json
import logging
from pathlib import Path

from PyQt6.QtCore import QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QVBoxLayout,
)

logger = logging.getLogger(__name__)


def format_analysis(analysis):
    confidence = {'high': 'высокая', 'medium': 'средняя', 'low': 'низкая'}
    lines = [analysis.get('title', 'Результат анализа'), '', analysis.get('summary', ''), '',
             'Уверенность: ' + confidence.get(analysis.get('confidence'), 'не определена')]
    if analysis.get('exit_code') is not None:
        lines.append('Код завершения: ' + str(analysis['exit_code']))
    suspects = [str(x) for x in analysis.get('suspects', [])
                if not str(x).removeprefix('knot//').startswith(('net.minecraft.', 'java.', 'jdk.', 'sun.'))]
    if suspects:
        lines.extend(['', 'Связанные объекты / компоненты (это ещё не доказательство вины):'] +
                     ['• ' + x.removeprefix('knot//') for x in suspects[:6]])
    if analysis.get('actions'):
        lines.extend(['', 'Что попробовать:'] + [f'{i}. {action}' for i, action in enumerate(analysis['actions'], 1)])
    if analysis.get('evidence'):
        lines.extend(['', 'На чём основан вывод:'] + list(analysis['evidence']))
    if analysis.get('limitations'):
        lines.extend(['', str(analysis['limitations'])])
    if analysis.get('report_error'):
        lines.extend(['', 'Разбор удалось получить, но файл отчёта не сохранился: ' + str(analysis['report_error'])])
    if analysis.get('log_files'):
        lines.extend(['', 'Изученные файлы:'] + list(analysis['log_files']))
    return '\n'.join(lines)


class CrashAnalysisWorker(QThread):
    ready = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, minecraft_dir, log_file=None, parent=None):
        super().__init__(parent)
        self.minecraft_dir = str(minecraft_dir)
        self.log_file = log_file

    def run(self):
        try:
            from Core.crash_analyzer import analyze_session, analyze_text, write_analysis
            if self.log_file:
                path = Path(self.log_file)
                # Limit the preview to the last 16 MiB; the original file is preserved.
                with path.open('rb') as source:
                    source.seek(max(0, path.stat().st_size - 16 * 1024 * 1024))
                    text = source.read().decode('utf-8-sig', 'replace')
                analysis = analyze_text(text)
                analysis['log_files'] = [str(path)]
            else:
                session_path = Path(self.minecraft_dir) / 'logs' / 'launch-session.json'
                try:
                    context = json.loads(session_path.read_text(encoding='utf-8'))
                    if not isinstance(context, dict):
                        context = {}
                except (OSError, ValueError):
                    context = {}
                analysis = analyze_session(self.minecraft_dir, context=context,
                                           exit_code=context.get('exit_code'))
            try:
                analysis['report_path'] = write_analysis(analysis, self.minecraft_dir)
            except OSError as exc:
                analysis['report_error'] = str(exc)
            analysis['minecraft_dir'] = self.minecraft_dir
            self.ready.emit(analysis)
        except Exception as exc:
            logger.exception('Анализ вылета Minecraft')
            self.failed.emit(str(exc))


class CrashAnalysisDialog(QDialog):
    java_requested = pyqtSignal()
    bugreport_requested = pyqtSignal()

    def __init__(self, analysis, minecraft_dir, parent=None):
        super().__init__(parent)
        self.analysis = analysis
        self.minecraft_dir = str(minecraft_dir)
        self.setWindowTitle('Почему завершился Minecraft')
        self.resize(820, 620)
        self.setStyleSheet('''
            QDialog { background: #171d29; color: #e9edf6; }
            QLabel { color: #e9edf6; background: transparent; }
            QTextEdit { background: #101621; color: #e9edf6; border: 1px solid #38465e;
                        border-radius: 8px; padding: 12px; font-size: 13px; }
            QPushButton { background: #2b3c50; color: #f1f5fb; border: 1px solid #4d637c;
                          border-radius: 6px; padding: 9px 13px; }
            QPushButton:hover { background: #3b526b; }
        ''')
        layout = QVBoxLayout(self)
        heading = QLabel('Разбор вылета' if analysis.get('crashed') else 'Результат проверки логов')
        heading.setStyleSheet('font-size: 19px; font-weight: bold; color: #6fdfcc; padding: 6px;')
        layout.addWidget(heading)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlainText(format_analysis(analysis))
        layout.addWidget(self.details, 1)
        row = QHBoxLayout()
        for text, callback in (
            ('Копировать', self.copy_report),
            ('Открыть логи', self.open_logs),
            ('Версия JAVA', self.java_requested.emit),
            ('Полный Bugreport.txt', self.bugreport_requested.emit),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addLayout(row)
        close = QPushButton('Закрыть')
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def copy_report(self):
        QApplication.clipboard().setText(self.details.toPlainText())

    def open_logs(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.minecraft_dir) / 'logs')))
