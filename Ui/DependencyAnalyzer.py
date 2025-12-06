# Ui/DependencyAnalyzer.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import List, Dict, Callable, Optional

from Network.DependencyManager import DependencyManager, ModDependency


class DependencyAnalyzerUI:
    """UI для анализа и отображения зависимостей"""

    def __init__(self, parent, minecraft_version: str, loader: str, tree_widget=None):
        self.parent = parent
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.dependency_manager = DependencyManager()
        self.tree_widget = tree_widget  # Treeview для добавления модов
        self.on_complete_callback = None

        # Окно анализа
        self.analyzer_window = None
        self.current_analysis = None
        self._is_window_open = False

    def show_analyzer(self, mods: List[Dict], on_complete: Callable = None):
        """Показывает окно анализа зависимостей"""
        # Проверяем, не открыто ли уже окно
        if self._is_window_open and self.analyzer_window and self.analyzer_window.winfo_exists():
            self.analyzer_window.lift()
            self.analyzer_window.focus_force()
            return

        self.on_complete_callback = on_complete
        self.analyzer_window = tk.Toplevel(self.parent)
        self.analyzer_window.title("Анализ зависимостей")
        self.analyzer_window.geometry("800x600")
        self.analyzer_window.resizable(True, True)

        # Делаем окно модальным
        self.analyzer_window.transient(self.parent)
        self.analyzer_window.grab_set()

        # Обработчик закрытия окна
        self.analyzer_window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._is_window_open = True

        # Центрируем окно
        self.analyzer_window.update_idletasks()
        x = (self.parent.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.parent.winfo_screenheight() // 2) - (600 // 2)
        self.analyzer_window.geometry(f"800x600+{x}+{y}")

        self._create_ui()
        self._start_analysis(mods)

    def _create_ui(self):
        """Создает интерфейс анализатора"""
        main_frame = ttk.Frame(self.analyzer_window, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(
            main_frame,
            text="🔍 Анализ зависимостей",
            font=("Comfortaa", 14, "bold")
        ).pack(pady=(0, 15))

        # Статус анализа
        self.status_label = ttk.Label(
            main_frame,
            text="Подготовка к анализу...",
            font=("Comfortaa", 10)
        )
        self.status_label.pack(pady=5)

        # Прогресс-бар
        self.progress_bar = ttk.Progressbar(
            main_frame,
            orient="horizontal",
            length=700,
            mode="indeterminate"
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        # Фрейм для результатов
        results_frame = ttk.LabelFrame(main_frame, text="Результаты анализа", padding=10)
        results_frame.pack(fill="both", expand=True, pady=(10, 0))

        # Treeview для отображения зависимостей
        columns = ("type", "name", "source", "status")
        self.deps_tree = ttk.Treeview(
            results_frame,
            columns=columns,
            show="headings",
            height=15
        )

        self.deps_tree.heading("type", text="Тип")
        self.deps_tree.heading("name", text="Название")
        self.deps_tree.heading("source", text="Источник")
        self.deps_tree.heading("status", text="Статус")

        self.deps_tree.column("type", width=80)
        self.deps_tree.column("name", width=300)
        self.deps_tree.column("source", width=100)
        self.deps_tree.column("status", width=100)

        # Скроллбар
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient="vertical",
            command=self.deps_tree.yview
        )
        self.deps_tree.configure(yscrollcommand=scrollbar.set)

        self.deps_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        self.add_button = ttk.Button(
            button_frame,
            text="➕ Добавить обязательные зависимости",
            state="disabled",
            command=self._add_required_dependencies
        )
        self.add_button.pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="❌ Закрыть",
            command=self._on_close
        ).pack(side="right", padx=5)

    def _start_analysis(self, mods: List[Dict]):
        """Запускает анализ в отдельном потоке"""

        def analyze_thread():
            try:
                self.parent.after(0, lambda: self.status_label.config(text="Анализируем моды..."))

                # Анализируем зависимости
                result = self.dependency_manager.analyze_collection_dependencies(
                    mods, self.minecraft_version, self.loader
                )

                self.parent.after(0, lambda: self._display_results(result))
                self.parent.after(0, lambda: self.progress_bar.stop())

                # Вызываем callback если он есть
                if self.on_complete_callback:
                    self.parent.after(0, lambda: self.on_complete_callback(result))

            except Exception as e:
                self.parent.after(0, lambda: self.status_label.config(
                    text=f"Ошибка анализа: {str(e)[:50]}..."
                ))
                self.parent.after(0, lambda: self.progress_bar.stop())
                self.parent.after(0, lambda: self._on_close())

        threading.Thread(target=analyze_thread, daemon=True).start()

    def _display_results(self, result: Dict):
        """Отображает результаты анализа"""
        self.current_analysis = result

        # Очищаем дерево
        for item in self.deps_tree.get_children():
            self.deps_tree.delete(item)

        # Добавляем обязательные зависимости
        for dep in result.get('required_dependencies', []):
            self.deps_tree.insert(
                "",
                "end",
                values=(
                    "🔴 Обязательная",
                    dep.name,
                    dep.source.upper(),
                    "Не установлена"
                ),
                tags=("required", dep)
            )

        # Добавляем необязательные зависимости
        for dep in result.get('optional_dependencies', []):
            self.deps_tree.insert(
                "",
                "end",
                values=(
                    "🟡 Необязательная",
                    dep.name,
                    dep.source.upper(),
                    "Опционально"
                ),
                tags=("optional", dep)
            )

        # Настраиваем цвета
        self.deps_tree.tag_configure("required", foreground="#ff6b6b")
        self.deps_tree.tag_configure("optional", foreground="#f39c12")

        # Обновляем статус
        total = result.get('total_mods', 0)
        required = len(result.get('required_dependencies', []))
        optional = len(result.get('optional_dependencies', []))

        self.status_label.config(
            text=f"Проанализировано модов: {total}. "
                 f"Найдено зависимостей: {required + optional} "
                 f"(обязательных: {required}, опциональных: {optional})"
        )

        # Активируем кнопку если есть обязательные зависимости
        if required > 0:
            self.add_button.config(state="normal")

    def _add_required_dependencies(self):
        """Добавляет обязательные зависимости в сборку"""
        if not self.current_analysis:
            return

        required_deps = self.current_analysis.get('required_dependencies', [])

        if not required_deps:
            messagebox.showinfo("Информация", "Нет обязательных зависимостей для добавления")
            return

        # Спрашиваем подтверждение
        confirm = messagebox.askyesno(
            "Добавление зависимостей",
            f"Добавить {len(required_deps)} обязательных зависимостей в сборку?\n\n"
            f"Рекомендуется проверить совместимость версий."
        )

        if not confirm:
            return

        # Добавляем зависимости
        added_count = 0
        for dep in required_deps:
            if self._add_dependency_to_tree(dep):
                added_count += 1

        # Показываем результат
        if added_count > 0:
            messagebox.showinfo(
                "Готово",
                f"Добавлено {added_count} зависимостей в сборку.\n"
                f"Проверьте список модов."
            )

            # Закрываем окно анализатора после добавления
            self._on_close()
        else:
            messagebox.showinfo(
                "Информация",
                "Все зависимости уже есть в сборке."
            )

    def _add_dependency_to_tree(self, dep: ModDependency) -> bool:
        """Добавляет зависимость в Treeview, если её там нет"""
        if not self.tree_widget:
            return False

        # Проверяем, нет ли уже этого мода
        for item in self.tree_widget.get_children():
            item_tags = self.tree_widget.item(item)["tags"]
            if len(item_tags) >= 2 and item_tags[1] == dep.project_id:
                return False  # Уже существует

        # Добавляем новый мод
        self.tree_widget.insert(
            "",
            "end",
            values=(
                dep.source.capitalize(),
                dep.name,
                f"{dep.mod_id or dep.project_id}.jar"
            ),
            tags=(dep.source, dep.project_id)
        )
        return True

    def _on_close(self):
        """Обработчик закрытия окна"""
        self._is_window_open = False
        if self.analyzer_window and self.analyzer_window.winfo_exists():
            self.analyzer_window.grab_release()
            self.analyzer_window.destroy()