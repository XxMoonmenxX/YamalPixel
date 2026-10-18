"""Java selection and portable runtime installation, with all work off the GUI thread."""
from __future__ import annotations

import threading

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from Core.java_manager import (
    JAVA_VERSIONS, JavaInstallCancelled, discover_java, install_java,
    load_java_selection, probe_java, required_java_major, save_java_selection,
)


class JavaManagerWorker(QThread):
    progress = pyqtSignal(int, str)
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, minecraft_dir, task="scan", value=None, parent=None):
        super().__init__(parent)
        self.minecraft_dir, self.task, self.value = minecraft_dir, task, value
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            selected = None
            if self.task == "install":
                selected = install_java(self.value, self.minecraft_dir, self.progress.emit, self.cancel_event)
            elif self.task == "probe":
                info = probe_java(self.value)
                if not info:
                    raise RuntimeError("Этот файл не запускается как Java. Выберите bin/java.exe из папки установленной Java.")
                selected = info["path"]
            runtimes = discover_java(self.minecraft_dir, self.cancel_event)
            if selected and not any(item["path"] == selected for item in runtimes):
                info = probe_java(selected)
                if info:
                    runtimes.append(info)
            if not self.cancel_event.is_set():
                self.result.emit({"runtimes": runtimes, "selected": selected, "task": self.task})
        except JavaInstallCancelled:
            self.error.emit("Операция отменена")
        except Exception as error:
            self.error.emit(str(error))


class JavaManagerDialog(QDialog):
    def __init__(self, parent=None, minecraft_dir=None, minecraft_version=None):
        super().__init__(parent)
        if minecraft_dir is None:
            from ConfDir.Configs import CONFIG
            minecraft_dir = CONFIG["minecraft_dir"]
        self.minecraft_dir = str(minecraft_dir)
        self.minecraft_version = minecraft_version or "1.20.1"
        try:
            self.required = required_java_major(self.minecraft_version, self.minecraft_dir)
        except ValueError:
            self.required = None
        self.selection = load_java_selection(self.minecraft_dir)
        self.worker = None
        self._closing = False
        self.setWindowTitle("Версия JAVA")
        self.setMinimumSize(740, 470)
        self.resize(860, 520)
        self.setStyleSheet("""
            QDialog { background: #171d2b; }
            QLabel { color: #e7edf5; background: transparent; }
            QTreeWidget { background: #21293a; color: #e7edf5; border: 1px solid #35435a;
                          border-radius: 8px; padding: 6px; outline: none; }
            QTreeWidget::item { padding: 7px 4px; }
            QTreeWidget::item:selected { background: #36556b; }
            QHeaderView::section { background: #283449; color: #8de4d8; border: none; padding: 8px; }
            QPushButton { color: #eef4fa; background: #344259; border: none; border-radius: 6px; padding: 9px 15px; }
            QPushButton:hover { background: #435572; }
            QPushButton:disabled { background: #272f3e; color: #788398; }
            QPushButton#applyJava { background: #268c81; }
            QPushButton#applyJava:hover { background: #30a295; }
            QProgressBar { background: #283449; border: none; border-radius: 5px; color: white; text-align: center; min-height: 20px; }
            QProgressBar::chunk { background: #3cae9e; border-radius: 5px; }
            QMessageBox { background: #21293a; color: white; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        title = QLabel("☕ Версии Java для Minecraft")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #8de4d8;")
        layout.addWidget(title)
        recommendation = (f"Для Minecraft {self.minecraft_version} рекомендуется Java {self.required}. " if self.required else "Точная версия Java берётся из установленного профиля Minecraft. ")
        description = QLabel(recommendation + "Зелёным отмечены найденные и проверенные версии. Автовыбор подбирает Java отдельно для каждой версии игры.")
        description.setWordWrap(True)
        layout.addWidget(description)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Версия", "Состояние", "Расположение Java"])
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 160)
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.itemDoubleClicked.connect(self._double_clicked)
        layout.addWidget(self.tree, 1)
        self.status = QLabel("Поиск установленных Java…")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)
        hint = QLabel("Установка скачивает официальный Temurin в папку игры. Java в системе, PATH и реестр не меняются. Java 16 — устаревшая версия для Minecraft 1.17.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a3b0c4; font-size: 11px;")
        layout.addWidget(hint)
        buttons = QHBoxLayout()
        self.refresh_btn = QPushButton("Обновить список")
        self.refresh_btn.clicked.connect(self.refresh)
        buttons.addWidget(self.refresh_btn)
        self.choose_btn = QPushButton("Выбрать java.exe…")
        self.choose_btn.clicked.connect(self.choose_file)
        buttons.addWidget(self.choose_btn)
        buttons.addStretch()
        self.install_btn = QPushButton("Установить")
        self.install_btn.clicked.connect(self.install_selected)
        buttons.addWidget(self.install_btn)
        self.apply_btn = QPushButton("Использовать")
        self.apply_btn.setObjectName("applyJava")
        self.apply_btn.clicked.connect(self.apply_selection)
        buttons.addWidget(self.apply_btn)
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.reject)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)
        self._busy(True)
        QTimer.singleShot(0, self.refresh)

    def _busy(self, active):
        self.refresh_btn.setEnabled(not active)
        self.choose_btn.setEnabled(not active)
        self.tree.setEnabled(not active)
        self.install_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)
        self.progress.setVisible(active)
        self.close_btn.setText("Отмена" if active else "Закрыть")
        if not active:
            self._selection_changed()

    def _start(self, task="scan", value=None):
        if self.worker is not None or self._closing:
            return
        self.progress.setRange(0, 0)
        self._busy(True)
        self.worker = JavaManagerWorker(self.minecraft_dir, task, value, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    @pyqtSlot()
    def refresh(self):
        self.status.setText("Поиск установленных Java…")
        self._start()

    @pyqtSlot(int, str)
    def _on_progress(self, percent, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(percent)
        self.status.setText(message)

    @pyqtSlot(object)
    def _on_result(self, result):
        if self._closing:
            return
        if result.get("selected"):
            self.selection = result["selected"]
        self.tree.clear()
        auto = QTreeWidgetItem(["Автоматически", "Рекомендуется", "Отдельная подходящая Java для каждой версии Minecraft"])
        auto.setData(0, Qt.ItemDataRole.UserRole, {"selection": "auto"})
        self.tree.addTopLevelItem(auto)
        if self.selection == "auto":
            self.tree.setCurrentItem(auto)
        runtimes = result["runtimes"]
        versions = sorted(set(JAVA_VERSIONS) | {item["major"] for item in runtimes})
        for major in versions:
            installed = [item for item in runtimes if item["major"] == major]
            label = f"Java {major}" + (" — для этой игры" if major == self.required else "")
            if installed:
                for runtime in installed:
                    item = QTreeWidgetItem([label, f"Установлена · {runtime['version']}", runtime["path"]])
                    item.setData(0, Qt.ItemDataRole.UserRole, {"selection": runtime["path"], "major": major})
                    for column in range(3):
                        item.setForeground(column, QColor("#7be2a2"))
                    item.setToolTip(2, runtime["path"])
                    self.tree.addTopLevelItem(item)
                    if self.selection.lower() == runtime["path"].lower():
                        self.tree.setCurrentItem(item)
            else:
                item = QTreeWidgetItem([label, "Можно установить", "Официальный Eclipse Temurin / Adoptium"])
                item.setData(0, Qt.ItemDataRole.UserRole, {"major": major})
                for column in range(3):
                    item.setForeground(column, QColor("#a3b0c4"))
                self.tree.addTopLevelItem(item)
        if not self.tree.currentItem():
            self.tree.setCurrentItem(auto)
        self.status.setText(f"Найдено установок Java: {len(runtimes)}. Выберите вариант и нажмите «Использовать».")

    @pyqtSlot(str)
    def _on_error(self, message):
        if not self._closing:
            self.status.setText("Ошибка: " + message)

    @pyqtSlot()
    def _on_finished(self):
        worker, self.worker = self.worker, None
        if worker:
            worker.deleteLater()
        self._busy(False)
        if self._closing:
            super().reject()

    @pyqtSlot()
    def _selection_changed(self):
        item = self.tree.currentItem()
        data = item.data(0, Qt.ItemDataRole.UserRole) if item else {}
        ready = self.worker is None and not self._closing
        self.apply_btn.setEnabled(ready and "selection" in data)
        self.install_btn.setEnabled(ready and "major" in data and "selection" not in data)
        self.install_btn.setText(f"Установить Java {data['major']}" if "major" in data and "selection" not in data else "Установить")

    def _double_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if "selection" in data:
            self.apply_selection()
        else:
            self.install_selected()

    @pyqtSlot()
    def install_selected(self):
        item = self.tree.currentItem()
        data = item.data(0, Qt.ItemDataRole.UserRole) if item else {}
        if "major" in data and "selection" not in data:
            self._start("install", data["major"])

    @pyqtSlot()
    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите bin/java.exe", "", "Java (java.exe javaw.exe java);;Все файлы (*)")
        if path:
            self.status.setText("Проверка выбранной Java…")
            self._start("probe", path)

    @pyqtSlot()
    def apply_selection(self):
        item = self.tree.currentItem()
        data = item.data(0, Qt.ItemDataRole.UserRole) if item else {}
        value = data.get("selection")
        if value is None or self.worker is not None:
            return
        try:
            save_java_selection(self.minecraft_dir, value)
        except Exception as error:
            self.status.setText(f"Не удалось сохранить выбор Java: {error}")
            return
        self.selection = value
        warning = ""
        if value != "auto" and self.required and data.get("major") != self.required:
            warning = f" Для этой игры рекомендуется Java {self.required}; другая версия может не подойти модам."
        self.status.setText("Выбор сохранён. Он применяется к следующему запуску игры." + warning)

    def reject(self):
        if self.worker is not None:
            self._closing = True
            self.worker.cancel()
            self.status.setText("Остановка операции… Текущий сетевой запрос завершится по таймауту.")
            self.close_btn.setEnabled(False)
            return
        self._closing = True
        super().reject()

    def closeEvent(self, event):
        if self.worker is not None:
            event.ignore()
            self.reject()
        else:
            self._closing = True
            super().closeEvent(event)
