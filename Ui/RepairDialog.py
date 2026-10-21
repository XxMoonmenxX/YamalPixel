from PyQt6.QtWidgets import QDialog,QVBoxLayout,QLabel,QListWidget,QPushButton,QHBoxLayout,QTextEdit
from Core.repair_engine import RepairSession
class RepairDialog(QDialog):
    def __init__(self, instance_dir, parent=None):
        super().__init__(parent); self.setWindowTitle('Проверка и починка игры'); self.resize(700,450); self.instance_dir=instance_dir
        self.list=QListWidget(); self.report=QTextEdit(); self.report.setReadOnly(True); self.status=QLabel('Нажмите «Проверить»'); self.run_btn=QPushButton('Проверить'); self.fix_btn=QPushButton('Применить исправления'); self.undo_btn=QPushButton('Откатить применённые фиксы'); self.fix_btn.setEnabled(False); self.undo_btn.setEnabled(False)
        lay=QVBoxLayout(self); lay.addWidget(self.status); lay.addWidget(self.list); lay.addWidget(self.report); row=QHBoxLayout(); row.addWidget(self.run_btn); row.addWidget(self.fix_btn); row.addWidget(self.undo_btn); lay.addLayout(row)
        self.run_btn.clicked.connect(self.inspect); self.fix_btn.clicked.connect(self.repair); self.undo_btn.clicked.connect(self.undo)
    def inspect(self):
        self.result=RepairSession(self.instance_dir).run(plan_only=True); self.list.clear()
        for issue in self.result['issues']: self.list.addItem(f'[{issue.severity.value}] {issue.title} — {issue.detail}')
        self.status.setText(f'Найдено проблем: {len(self.result["issues"])}'); self.fix_btn.setEnabled(bool(self.result['plan']))
    def repair(self):
        self.result=RepairSession(self.instance_dir, progress=lambda msg,res: self.status.setText(msg)).run(); self.status.setText('Починка завершена: '+self.result['outcome']); self.fix_btn.setEnabled(False); self.undo_btn.setEnabled(bool(self.result.get('applied'))); self.report.setPlainText('Отчёт: '+self.result.get('text_report_path',self.result.get('report_path','')))
    def undo(self):
        from Core.repair_engine import rollback
        count=0
        for result in reversed(self.result.get('applied', [])):
            if rollback(result): count += 1
        self.status.setText(f'Откат выполнен: {count}'); self.undo_btn.setEnabled(False)
