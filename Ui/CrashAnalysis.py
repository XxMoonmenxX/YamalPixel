"""Human-readable game failure reports, presented on the Qt GUI thread."""
import json
import logging
from pathlib import Path

from PyQt6.QtCore import QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QVBoxLayout, QProgressDialog, QMessageBox,
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

class DependencyInstallWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)
    def __init__(self, ids, minecraft_dir, minecraft_version=None, loader=None, parent=None, collection_name=None):
        super().__init__(parent); self.ids=ids; self.minecraft_dir=str(minecraft_dir); self.minecraft_version=minecraft_version or '1.20.1'; self.loader=loader or 'fabric'; self.cancelled=False; self.collection_name=collection_name
    def cancel(self): self.cancelled=True
    def run(self):
        try:
            from Network.Downloader import download_single_mod_turbo_sync
            results=[]; manifest_mods=[]
            for i, mod_id in enumerate(self.ids, 1):
                if self.cancelled: break
                self.progress.emit(i-1, f'Загрузка {mod_id}...')
                info={'source':'modrinth','modrinth_id':mod_id,'project_id':mod_id,'name':mod_id,'filename':mod_id+'.jar','minecraft_version':self.minecraft_version,'loader':self.loader}
                ok=download_single_mod_turbo_sync(info,self.minecraft_dir,source='modrinth',minecraft_version=self.minecraft_version,loader=self.loader)
                if not ok:
                    info['source']='curseforge'; info['curseforge_id']=mod_id
                    ok=download_single_mod_turbo_sync(info,self.minecraft_dir,source='curseforge',minecraft_version=self.minecraft_version,loader=self.loader)
                if ok:
                    manifest_mods.append({'source':info['source'],'name':info['name'],'modrinth_id':info.get('modrinth_id'),'curseforge_id':info.get('curseforge_id'),'project_id':mod_id,'filename':info['filename']})
                results.append({'id':mod_id,'success':bool(ok)})
            manifest_error=None
            if manifest_mods and self.collection_name:
                from Core.collection_loader import append_mods_to_collection
                saved, detail=append_mods_to_collection(self.collection_name,manifest_mods)
                manifest_error = None if saved else detail
                if manifest_error: self.progress.emit(len(self.ids),'Моды скачаны, манифест не изменён: '+str(manifest_error))
            self.progress.emit(len(self.ids), 'Готово'); self.finished.emit({'results':results,'cancelled':self.cancelled,'manifest_error':manifest_error})
        except Exception as exc: self.failed.emit(str(exc))


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
        self.action_row = QHBoxLayout(); layout.addLayout(self.action_row)
        self._action_buttons = []
        category = analysis.get('category')
        if category == 'mod_dependency': self._add_action('🛠️ Установить недостающие', self.install_dependencies)
        if category in ('mixin','api_mismatch'): self._add_action('🚫 Отключить подозреваемый мод', self.quarantine_suspect)
        if category == 'config_corrupt': self._add_action('📝 Переименовать конфиг', self.rename_config)
        self._add_action('⏪ Откатить все моды', self.rollback_last_ok)
        close = QPushButton('Закрыть')
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def _add_action(self, text, callback):
        button=QPushButton(text); button.clicked.connect(callback); self.action_row.addWidget(button); self._action_buttons.append(button)

    def _run_action(self, fn, label):
        self.progress=QProgressDialog(label, 'Отмена', 0, 0, self); self.progress.setWindowTitle('Починка'); self.progress.setAutoClose(False); self.progress.show(); QApplication.processEvents()
        try: fn()
        except Exception as exc: QMessageBox.critical(self,'Починка',str(exc))
        finally: self.progress.close()

    def quarantine_suspect(self):
        from Core.repair_quarantine import Quarantine
        suspect=str((self.analysis.get('suspects') or [''])[0]).lower(); mods=Path(self.minecraft_dir)/'mods'
        matches=[p for p in mods.glob('*.jar') if suspect and suspect in p.stem.lower()]
        if not matches: QMessageBox.warning(self,'Карантин','Подозрительный JAR не найден.'); return
        self._run_action(lambda: Quarantine(self.minecraft_dir).move(matches[0],'crash suspect'),'Перемещение мода в карантин...')

    def rename_config(self):
        config=Path(self.minecraft_dir)/'config'; suspect=str((self.analysis.get('suspects') or self.analysis.get('evidence') or [''])[0])
        matches=list(config.glob('*')) if config.is_dir() else []; match=next((p for p in matches if p.name in suspect),None)
        if not match: QMessageBox.warning(self,'Конфигурация','Битый конфиг не найден.'); return
        self._run_action(lambda: match.rename(match.with_name(match.name+'.broken')),'Переименование конфига...')

    def install_dependencies(self):
        ids=list(dict.fromkeys(self.analysis.get('missing_dependency_ids') or []))
        if not ids: QMessageBox.warning(self,'Зависимости','Точные ID недостающих зависимостей не найдены в логе.'); return
        self.progress=QProgressDialog('', 'Отмена', 0, len(ids), self); self.progress.setWindowTitle('Установка зависимостей'); self.progress.setAutoClose(False)
        from Core.run import get_current_collection
        self.dependency_worker=DependencyInstallWorker(ids,self.minecraft_dir,self.analysis.get('minecraft_version'),self.analysis.get('loader'),self,get_current_collection())
        self.dependency_worker.progress.connect(lambda value,text: (self.progress.setValue(value),self.progress.setLabelText(text)))
        self.dependency_worker.finished.connect(self._dependencies_finished); self.dependency_worker.failed.connect(self._dependencies_failed); self.progress.canceled.connect(self.dependency_worker.cancel); self.progress.show(); self._set_actions(False); self.dependency_worker.start()

    def _set_actions(self, enabled):
        for button in self._action_buttons: button.setEnabled(enabled)
    def _dependencies_finished(self, result):
        self.progress.close(); self._set_actions(True); ok=[x['id'] for x in result['results'] if x['success']]; bad=[x['id'] for x in result['results'] if not x['success']]
        extra = '\nМанифест обновлён.' if not result.get('manifest_error') else '\nМанифест не изменён: '+str(result['manifest_error'])
        QMessageBox.information(self,'Зависимости',f'Установлено: {len(ok)}\nНе удалось: {len(bad)}'+(f'\n\n{", ".join(bad)}' if bad else '')+extra)
    def _dependencies_failed(self, error):
        self.progress.close(); self._set_actions(True); QMessageBox.critical(self,'Зависимости',error)

    def rollback_last_ok(self):
        from Core.repair_engine import rollback_to_last_ok
        self._run_action(lambda: rollback_to_last_ok(self.minecraft_dir),'Восстановление последней рабочей сборки...')

    def copy_report(self):
        QApplication.clipboard().setText(self.details.toPlainText())

    def open_logs(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.minecraft_dir) / 'logs')))
