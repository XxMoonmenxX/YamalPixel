# Ui/DependencyAnalyzer.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QMessageBox,
    QApplication, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from Ui.BaseWindow import BaseDialog

import logging

logger = logging.getLogger("YamalPixel.DependencyAnalyzer")

from Network.DependencyManager import DependencyManager, ModDependency
from typing import List, Dict, Callable


class DependencyAnalyzerWorker(QThread):
    """Поток для анализа зависимостей"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, mods, minecraft_version, loader):
        super().__init__()
        self.mods = mods
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.dependency_manager = DependencyManager()

    def run(self):
        try:
            self.progress.emit("Анализ модов...")

            all_dependencies = []

            for i, mod in enumerate(self.mods):
                mod_name = mod.get('name', 'Unknown')
                mod_source = mod.get('source')
                mod_id = mod.get('mod_id') or mod.get('project_id')

                if not mod_source or not mod_id:
                    logger.warning(f"⚠️ Мод {mod_name} пропущен: нет source={mod_source} или id={mod_id}")
                    self.progress.emit(f"⚠️ {mod_name} - нет ID, пропускаем")
                    continue

                self.progress.emit(f"Анализ: {mod_name} ({i + 1}/{len(self.mods)})")

                dependencies = self.dependency_manager.resolve_dependencies_for_mod(
                    mod, self.minecraft_version, self.loader
                )

                logger.info(f"Для мода {mod_name} найдено {len(dependencies)} зависимостей")
                all_dependencies.extend(dependencies)

            # Разделяем на обязательные и опциональные
            required = []
            optional = []
            seen = set()

            for dep in all_dependencies:
                key = f"{dep.source}:{dep.mod_id or dep.project_id}"
                if key not in seen:
                    seen.add(key)
                    if dep.dependency_type == 'required':
                        required.append(dep)
                    elif dep.dependency_type == 'optional':
                        optional.append(dep)

            result = {
                'total_mods': len([m for m in self.mods if m.get('mod_id') or m.get('project_id')]),
                'required_dependencies': required,
                'optional_dependencies': optional,
                'all_dependencies': required + optional
            }

            logger.info(f"Анализ завершен: обязательных={len(required)}, опциональных={len(optional)}")
            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Ошибка анализа зависимостей: {e}", exc_info=True)
            self.error.emit(str(e))


class DependencyAnalyzerDialog(BaseDialog):
    """Диалог для отображения результатов анализа зависимостей"""

    def __init__(self, parent, result, tree_widget=None, on_add_callback=None):
        super().__init__(parent)
        self.result = result
        self.tree_widget = tree_widget
        self.on_add_callback = on_add_callback
        self._is_closing = False

        self.setWindowTitle("Результаты анализа зависимостей")
        self.setMinimumSize(800, 500)
        # Делаем окно НЕ модальным, чтобы можно было взаимодействовать с основным окном
        self.setModal(False)

        self.setup_ui()
        self.display_results()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("🔍 Результаты анализа зависимостей")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Информация
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.info_label)

        # Tree для отображения зависимостей
        self.deps_tree = QTreeWidget()
        self.deps_tree.setHeaderLabels(["Тип", "Название", "Источник", "Статус"])
        self.deps_tree.setColumnWidth(0, 120)
        self.deps_tree.setColumnWidth(1, 350)
        self.deps_tree.setColumnWidth(2, 100)
        self.deps_tree.setColumnWidth(3, 100)
        main_layout.addWidget(self.deps_tree)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.add_button = QPushButton("➕ Добавить обязательные зависимости")
        self.add_button.clicked.connect(self._add_required_dependencies)
        button_layout.addWidget(self.add_button)

        self.close_button = QPushButton("❌ Закрыть")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

    def display_results(self):
        self.deps_tree.clear()

        required_deps = self.result.get('required_dependencies', [])
        optional_deps = self.result.get('optional_dependencies', [])

        # Добавляем обязательные зависимости
        for dep in required_deps:
            item = QTreeWidgetItem()
            item.setText(0, "🔴 Обязательная")
            item.setText(1, dep.name)
            item.setText(2, dep.source.upper())
            item.setText(3, "❌ Не установлена")
            item.setData(0, Qt.ItemDataRole.UserRole, dep)
            # Подсветка
            item.setForeground(0, QColor("#ff6b6b"))
            item.setForeground(1, QColor("#ff6b6b"))
            self.deps_tree.addTopLevelItem(item)

        # Добавляем опциональные зависимости
        for dep in optional_deps:
            item = QTreeWidgetItem()
            item.setText(0, "🟡 Необязательная")
            item.setText(1, dep.name)
            item.setText(2, dep.source.upper())
            item.setText(3, "ℹ️ Опционально")
            item.setData(0, Qt.ItemDataRole.UserRole, dep)
            self.deps_tree.addTopLevelItem(item)

        total = self.result.get('total_mods', 0)
        required = len(required_deps)
        optional = len(optional_deps)

        self.info_label.setText(
            f"📊 Проанализировано модов: {total}. "
            f"Найдено зависимостей: {required + optional} "
            f"(обязательных: {required}, опциональных: {optional})"
        )

        self.add_button.setEnabled(required > 0)

    def _add_required_dependencies(self):
        if not self.tree_widget:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить зависимости")
            return

        # Собираем обязательные зависимости
        required_deps = []
        for i in range(self.deps_tree.topLevelItemCount()):
            item = self.deps_tree.topLevelItem(i)
            if "Обязательная" in item.text(0):
                dep = item.data(0, Qt.ItemDataRole.UserRole)
                if dep:
                    required_deps.append(dep)

        if not required_deps:
            QMessageBox.information(self, "Информация", "Нет обязательных зависимостей для добавления")
            return

        reply = QMessageBox.question(
            self,
            "Добавление зависимостей",
            f"Добавить {len(required_deps)} обязательных зависимостей в сборку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        added_count = 0
        for dep in required_deps:
            if self._add_dependency_to_tree(dep):
                added_count += 1

        if added_count > 0:
            QMessageBox.information(
                self,
                "Готово",
                f"✅ Добавлено {added_count} зависимостей в сборку."
            )
            # Обновляем список
            self.display_results()
            # Если есть callback
            if self.on_add_callback:
                self.on_add_callback(added_count)
        else:
            QMessageBox.information(
                self,
                "Информация",
                "Все зависимости уже есть в сборке."
            )

    def _add_dependency_to_tree(self, dep: ModDependency) -> bool:
        if not self.tree_widget:
            return False

        # Проверяем, нет ли уже этого мода
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.text(1) == dep.name:
                return False

        source_icon = "🌐" if dep.source == "modrinth" else "⚡"
        mod_data = {
            'source': dep.source,
            'name': dep.name,
            'filename': f"{dep.mod_id or dep.project_id}.jar",
            'mod_id': dep.mod_id,
            'project_id': dep.project_id
        }

        if dep.source == 'modrinth':
            mod_data['modrinth_id'] = dep.mod_id or dep.project_id
            mod_data['modrinth_slug'] = dep.mod_id or dep.project_id
        else:
            mod_data['curseforge_id'] = dep.mod_id or dep.project_id
            mod_data['curseforge_slug'] = dep.mod_id or dep.project_id

        # Добавляем в Treeview
        item = QTreeWidgetItem()
        item.setText(0, f"{source_icon} {dep.source.capitalize()}")
        item.setText(1, dep.name)
        item.setText(2, mod_data['filename'])
        item.setData(0, Qt.ItemDataRole.UserRole, mod_data)
        self.tree_widget.addTopLevelItem(item)

        # Добавляем в selected_mods родительского окна
        parent = self.parent()
        while parent:
            if hasattr(parent, 'selected_mods') and isinstance(parent.selected_mods, list):
                # Проверяем, нет ли уже
                exists = False
                for existing in parent.selected_mods:
                    if existing.get('name') == dep.name:
                        exists = True
                        break
                if not exists:
                    parent.selected_mods.append(mod_data)
                    if hasattr(parent, 'update_selected_list'):
                        parent.update_selected_list()
                    logger.info(f"✅ Добавлена зависимость: {dep.name}")
                return True
            parent = parent.parent()

        return True


class DependencyAnalyzerUI:
    """UI для анализа и отображения зависимостей"""

    def __init__(self, parent, minecraft_version: str, loader: str, tree_widget=None):
        self.parent = parent
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.dependency_manager = DependencyManager()
        self.tree_widget = tree_widget
        self.on_complete_callback = None
        self.analyzer_dialog = None
        self.progress_dialog = None

    def show_analyzer(self, mods: List[Dict], on_complete: Callable = None):
        """Показывает окно анализа зависимостей"""
        self.on_complete_callback = on_complete

        # Показываем диалог прогресса
        self.progress_dialog = QDialog(self.parent)
        self.progress_dialog.setWindowTitle("Анализ зависимостей")
        self.progress_dialog.setFixedSize(400, 150)
        self.progress_dialog.setModal(True)

        layout = QVBoxLayout(self.progress_dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        status_label = QLabel("⏳ Анализ зависимостей...")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(progress_bar)

        # Запускаем анализ
        self.worker = DependencyAnalyzerWorker(mods, self.minecraft_version, self.loader)
        self.worker.progress.connect(status_label.setText)
        self.worker.finished.connect(lambda r: self._on_analysis_finished(r, self.progress_dialog))
        self.worker.error.connect(lambda e: self._on_analysis_error(e, self.progress_dialog))
        self.worker.start()

        self.progress_dialog.exec()

    def _on_analysis_finished(self, result, progress_dialog):
        """Обработка завершения анализа"""
        progress_dialog.accept()

        # Показываем результаты в отдельном диалоге
        self.analyzer_dialog = DependencyAnalyzerDialog(
            self.parent,
            result,
            self.tree_widget,
            self._on_dependencies_added
        )
        self.analyzer_dialog.show()

        if self.on_complete_callback:
            self.on_complete_callback(result)

    def _on_analysis_error(self, error_msg, progress_dialog):
        """Обработка ошибки анализа"""
        progress_dialog.accept()
        QMessageBox.critical(self.parent, "Ошибка", f"Не удалось проанализировать зависимости:\n{error_msg}")

    def _on_dependencies_added(self, count):
        """Обработка добавления зависимостей"""
        if self.tree_widget and hasattr(self.parent, 'update_selected_list'):
            self.parent.update_selected_list()
