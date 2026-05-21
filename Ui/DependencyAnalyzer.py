# Ui/DependencyAnalyzer.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QMessageBox,
    QApplication, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from Ui.BaseWindow import BaseDialog

import logging

logger = logging.getLogger("YamalPixel.DependencyAnalyzer")

from Network.DependencyManager import DependencyManager, ModDependency


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

                # Критическая проверка: если нет ID, пропускаем
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


class DependencyAnalyzerUI:
    """UI для анализа и отображения зависимостей (PyQt6 версия)"""

    def __init__(self, parent, minecraft_version: str, loader: str, tree_widget=None):
        self.parent = parent
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.dependency_manager = DependencyManager()
        self.tree_widget = tree_widget
        self.on_complete_callback = None
        self.analyzer_window = None
        self._is_window_open = False

    def show_analyzer(self, mods: List[Dict], on_complete: Callable = None):
        """Показывает окно анализа зависимостей"""
        if self._is_window_open and self.analyzer_window and self.analyzer_window.isVisible():
            self.analyzer_window.raise_()
            self.analyzer_window.activateWindow()
            return

        self.on_complete_callback = on_complete
        self.analyzer_window = BaseDialog(self.parent)
        self.analyzer_window.setWindowTitle("Анализ зависимостей")
        self.analyzer_window.setMinimumSize(800, 600)
        self.analyzer_window.setModal(True)
        self._is_window_open = True

        self.analyzer_window.finished.connect(self._on_close)
        self._create_ui()
        self._start_analysis(mods)
        self.analyzer_window.exec()

    def _create_ui(self):
        """Создает интерфейс анализатора"""
        main_layout = QVBoxLayout(self.analyzer_window)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("🔍 Анализ зависимостей")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Статус
        self.status_label = QLabel("Подготовка к анализу...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        main_layout.addWidget(self.progress_bar)

        # Результаты
        results_label = QLabel("Результаты анализа:")
        results_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        main_layout.addWidget(results_label)

        # Tree для отображения зависимостей
        self.deps_tree = QTreeWidget()
        self.deps_tree.setHeaderLabels(["Тип", "Название", "Источник", "Статус"])
        self.deps_tree.setColumnWidth(0, 100)
        self.deps_tree.setColumnWidth(1, 350)
        self.deps_tree.setColumnWidth(2, 100)
        self.deps_tree.setColumnWidth(3, 100)
        main_layout.addWidget(self.deps_tree)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.add_button = QPushButton("➕ Добавить обязательные зависимости")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self._add_required_dependencies)
        button_layout.addWidget(self.add_button)

        self.close_button = QPushButton("❌ Закрыть")
        self.close_button.clicked.connect(self.analyzer_window.close)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

    def _start_analysis(self, mods: List[Dict]):
        """Запускает анализ в отдельном потоке"""
        self.worker = DependencyAnalyzerWorker(mods, self.minecraft_version, self.loader)
        self.worker.progress.connect(self.status_label.setText)
        self.worker.finished.connect(self._display_results)
        self.worker.error.connect(lambda e: self._show_error(e))
        self.worker.start()

    def _display_results(self, result: Dict):
        """Отображает результаты анализа"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        self.deps_tree.clear()

        # Добавляем обязательные зависимости
        required_deps = result.get('required_dependencies', [])
        logger.info(f"Найдено обязательных зависимостей: {len(required_deps)}")

        for dep in required_deps:
            item = QTreeWidgetItem()
            item.setText(0, "🔴 Обязательная")
            item.setText(1, dep.name)
            item.setText(2, dep.source.upper())
            item.setText(3, "Не установлена")
            item.setData(0, Qt.ItemDataRole.UserRole, dep)
            self.deps_tree.addTopLevelItem(item)

        # Добавляем необязательные зависимости
        optional_deps = result.get('optional_dependencies', [])
        logger.info(f"Найдено опциональных зависимостей: {len(optional_deps)}")

        for dep in optional_deps:
            item = QTreeWidgetItem()
            item.setText(0, "🟡 Необязательная")
            item.setText(1, dep.name)
            item.setText(2, dep.source.upper())
            item.setText(3, "Опционально")
            item.setData(0, Qt.ItemDataRole.UserRole, dep)
            self.deps_tree.addTopLevelItem(item)

        # Подсвечиваем обязательные зависимости
        for i in range(self.deps_tree.topLevelItemCount()):
            item = self.deps_tree.topLevelItem(i)
            if "Обязательная" in item.text(0):
                item.setForeground(0, QColor("#ff6b6b"))
                item.setForeground(1, QColor("#ff6b6b"))

        total = result.get('total_mods', 0)
        required = len(required_deps)
        optional = len(optional_deps)

        status_text = (
            f"✅ Проанализировано модов: {total}. "
            f"Найдено зависимостей: {required + optional} "
            f"(обязательных: {required}, опциональных: {optional})"
        )
        self.status_label.setText(status_text)
        logger.info(status_text)

        self.add_button.setEnabled(required > 0)

        if self.on_complete_callback:
            self.on_complete_callback(result)

    def _show_error(self, error_msg: str):
        """Показывает ошибку"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"❌ Ошибка: {error_msg}")
        QMessageBox.critical(self.analyzer_window, "Ошибка", f"Не удалось проанализировать зависимости:\n{error_msg}")

    def _add_required_dependencies(self):
        """Добавляет обязательные зависимости в сборку"""
        if not self.tree_widget:
            QMessageBox.warning(self.analyzer_window, "Ошибка", "Не удалось добавить зависимости")
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
            QMessageBox.information(self.analyzer_window, "Информация", "Нет обязательных зависимостей для добавления")
            return

        reply = QMessageBox.question(
            self.analyzer_window,
            "Добавление зависимостей",
            f"Добавить {len(required_deps)} обязательных зависимостей в сборку?\n\n"
            f"Рекомендуется проверить совместимость версий.\n\n"
            f"Зависимости будут добавлены к существующим модам.",
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
                self.analyzer_window,
                "Готово",
                f"✅ Добавлено {added_count} зависимостей в сборку.\n\n"
                f"Теперь в сборке {self.tree_widget.topLevelItemCount()} модов."
            )
            self.analyzer_window.close()
        else:
            QMessageBox.information(
                self.analyzer_window,
                "Информация",
                "Все зависимости уже есть в сборке."
            )

    def _add_dependency_to_tree(self, dep: ModDependency) -> bool:
        """Добавляет зависимость в Treeview И В selected_mods родительского окна"""
        if not self.tree_widget:
            return False

        # Проверяем, нет ли уже этого мода в tree_widget
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.text(1) == dep.name:
                return False

        source_icon = "🌐" if dep.source == "modrinth" else "⚡"
        mod_data = {
            'source': dep.source,
            'name': dep.name,
            'filename': f"{dep.mod_id or dep.project_id}.jar",
            # Важно: сохраняем ID для последующего анализа
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
        parent = self.analyzer_window.parent() or self.parent
        while parent:
            if hasattr(parent, 'selected_mods') and isinstance(parent.selected_mods, list):
                parent.selected_mods.append(mod_data)
                if hasattr(parent, 'update_selected_list'):
                    parent.update_selected_list()
                logger.info(f"✅ Добавлена зависимость в selected_mods: {dep.name} (ID: {dep.mod_id or dep.project_id})")
                break
            parent = parent.parent()

        return True

    def _on_close(self):
        """Обработчик закрытия окна"""
        self._is_window_open = False
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)