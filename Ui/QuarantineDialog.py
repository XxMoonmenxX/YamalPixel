from pathlib import Path
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QListWidget,QPushButton,QHBoxLayout,QLabel
from Core.repair_quarantine import Quarantine
class QuarantineDialog(QDialog):
    def __init__(self, instance_dir, parent=None):
        super().__init__(parent); self.instance_dir=Path(instance_dir); self.q=Quarantine(self.instance_dir); self.setWindowTitle('Карантин модов'); self.resize(650,400)
        self.items=QListWidget(); self.status=QLabel(); self.restore_btn=QPushButton('Восстановить'); self.delete_btn=QPushButton('Удалить'); close=QPushButton('Закрыть')
        lay=QVBoxLayout(self); lay.addWidget(self.items); lay.addWidget(self.status); row=QHBoxLayout(); row.addWidget(self.restore_btn); row.addWidget(self.delete_btn); row.addWidget(close); lay.addLayout(row)
        self.restore_btn.clicked.connect(self.restore); self.delete_btn.clicked.connect(self.delete); close.clicked.connect(self.close); self.refresh()
    def refresh(self):
        self.items.clear(); self.q.root.mkdir(parents=True,exist_ok=True)
        for p in sorted(self.q.root.glob('*/*.meta.json')): self.items.addItem(str(p))
    def restore(self):
        item=self.items.currentItem()
        if not item:return
        try: self.q.restore(Path(item.text())); self.status.setText('Мод восстановлен'); self.refresh()
        except Exception as e:self.status.setText(str(e))
    def delete(self):
        item=self.items.currentItem()
        if not item:return
        try:
            p=Path(item.text()); folder=p.parent
            for child in folder.iterdir(): child.unlink()
            folder.rmdir(); self.status.setText('Запись удалена'); self.refresh()
        except Exception as e:self.status.setText(str(e))
