"""
UI для управления плагинами (упрощенная версия)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from ConfDir.Configs import set_window_icon
import os
import threading

class PluginManagerUI:
    """Пользовательский интерфейс менеджера плагинов"""

    def __init__(self, parent_window, plugin_manager):
        self.parent = parent_window
        self.plugin_manager = plugin_manager
        self.window = None

    def show(self):
        """Показывает окно менеджера плагинов"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        set_window_icon(self.window)
        self.window.title("🔌 Менеджер плагинов")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()

        # Основной фрейм
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="🔌 Управление плагинами",
            font=("Comfortaa", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Фрейм для кнопок управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))

        # КНОПКА УСТАНОВКИ ИЗ ZIP
        ttk.Button(
            control_frame,
            text="📦 Установить из ZIP",
            command=self.install_from_zip,
            width=18
        ).pack(side="left", padx=5)

        ttk.Button(
            control_frame,
            text="🔄 Обновить список",
            command=self.refresh_plugins,
            width=15
        ).pack(side="left", padx=5)

        ttk.Button(
            control_frame,
            text="📁 Открыть папку плагинов",
            command=self.open_plugins_folder,
            width=22
        ).pack(side="left", padx=5)

        # Фрейм для списка плагинов
        plugins_frame = ttk.LabelFrame(main_frame, text="Доступные плагины", padding=10)
        plugins_frame.pack(fill="both", expand=True)

        # Создаем Treeview
        columns = ("name", "version", "author", "enabled", "builtin")
        self.tree = ttk.Treeview(plugins_frame, columns=columns, show="headings", height=15)

        # Настраиваем колонки
        self.tree.heading("name", text="Название")
        self.tree.heading("version", text="Версия")
        self.tree.heading("author", text="Автор")
        self.tree.heading("enabled", text="Статус")
        self.tree.heading("builtin", text="Тип")

        self.tree.column("name", width=200)
        self.tree.column("version", width=80)
        self.tree.column("author", width=150)
        self.tree.column("enabled", width=80)
        self.tree.column("builtin", width=80)

        # Скроллбар
        scrollbar = ttk.Scrollbar(plugins_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Фрейм для кнопок управления плагином
        plugin_buttons_frame = ttk.Frame(main_frame)
        plugin_buttons_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            plugin_buttons_frame,
            text="✅ Включить",
            command=self.enable_selected,
            width=12
        ).pack(side="left", padx=5)

        ttk.Button(
            plugin_buttons_frame,
            text="❌ Выключить",
            command=self.disable_selected,
            width=12
        ).pack(side="left", padx=5)

        ttk.Button(
            plugin_buttons_frame,
            text="🗑️ Удалить",
            command=self.delete_selected,
            width=12
        ).pack(side="left", padx=5)

        ttk.Button(
            plugin_buttons_frame,
            text="ℹ️ Информация",
            command=self.show_info,
            width=12
        ).pack(side="left", padx=5)

        # Кнопка закрытия
        ttk.Button(
            main_frame,
            text="Закрыть",
            command=self.window.destroy,
            width=12
        ).pack(side="right", pady=(10, 0))

        # Загружаем плагины
        self.refresh_plugins()

        # Двойной клик для включения/выключения
        self.tree.bind("<Double-1>", self.toggle_plugin)

    def install_from_zip(self):
        """Установка плагина из ZIP архива"""
        import tkinter.filedialog as filedialog

        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(
            title="Выберите ZIP архив плагина",
            filetypes=[
                ("ZIP архивы", "*.zip"),
                ("Все файлы", "*.*")
            ]
        )

        if not file_path:
            return

        # Проверяем размер файла (макс 100MB)
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > 100:
            messagebox.showerror(
                "Ошибка",
                f"Файл слишком большой ({file_size:.1f} MB).\n"
                f"Максимальный размер: 100 MB"
            )
            return

        # Создаем окно прогресса
        progress_window = tk.Toplevel(self.window)
        set_window_icon(progress_window)
        progress_window.title("Установка плагина")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self.window)
        progress_window.grab_set()

        ttk.Label(
            progress_window,
            text="📦 Установка плагина...",
            font=("Comfortaa", 12)
        ).pack(pady=10)

        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        status_label = ttk.Label(progress_window, text="")
        status_label.pack()

        def install_thread():
            try:
                from pathlib import Path
                zip_path = Path(file_path)

                status_label.config(text="Проверка архива...")
                progress_window.update()

                # Устанавливаем плагин через PluginManager
                success, result = self.plugin_manager.install_from_zip(zip_path)

                progress_window.destroy()

                if success:
                    messagebox.showinfo(
                        "Успех",
                        f"✅ Плагин успешно установлен!\n\n"
                        f"ID: {result}\n"
                        f"Файл: {zip_path.name}"
                    )
                    self.refresh_plugins()
                else:
                    messagebox.showerror(
                        "Ошибка установки",
                        f"❌ Не удалось установить плагин:\n\n{result}"
                    )

            except Exception as e:
                progress_window.destroy()
                messagebox.showerror(
                    "Ошибка",
                    f"❌ Произошла ошибка:\n\n{str(e)}"
                )

        # Запускаем установку в отдельном потоке
        threading.Thread(target=install_thread, daemon=True).start()

    def open_plugins_folder(self):
        """Открывает папку с плагинами"""
        plugins_dir = self.plugin_manager.plugins_dir
        os.makedirs(plugins_dir, exist_ok=True)

        if os.name == 'nt':
            os.startfile(plugins_dir)
        else:
            import subprocess
            subprocess.Popen(['xdg-open', str(plugins_dir)])

    def refresh_plugins(self):
        """Обновляет список плагинов в UI"""
        try:
            # Очищаем дерево
            self.tree.delete(*self.tree.get_children())

            # Получаем список плагинов через PluginManager
            plugins = self.plugin_manager.get_all_plugins()

            print(f"[UI] Загружено плагинов: {len(plugins)}")

            if not plugins:
                # Вставляем заглушку если нет плагинов
                self.tree.insert("", "end", values=("Нет плагинов", "", "", "", ""))
                return

            # Сортируем плагины: сначала включенные, потом по алфавиту
            sorted_plugins = sorted(
                plugins,
                key=lambda x: (not x.get('enabled', False), x.get('name', '').lower())
            )

            for plugin in sorted_plugins:
                plugin_id = plugin.get('id', 'unknown')
                plugin_name = plugin.get('name', 'Без названия')
                plugin_version = plugin.get('version', '1.0.0')
                plugin_author = plugin.get('author', 'Неизвестен')
                plugin_enabled = plugin.get('enabled', False)
                plugin_builtin = plugin.get('is_builtin', False)

                print(f"[UI] Загружаем плагин: {plugin_name} ({plugin_id})")

                # Определяем статус
                status = "✅ Включен" if plugin_enabled else "❌ Выключен"

                # Определяем тип
                plugin_type = "📦 Встроенный" if plugin_builtin else "🔌 Внешний"

                # Добавляем в дерево
                item_id = self.tree.insert(
                    "",
                    "end",
                    values=(
                        f"{plugin_name}",
                        f"{plugin_version}",
                        f"{plugin_author}",
                        f"{status}",
                        f"{plugin_type}"
                    ),
                    tags=(plugin_id,)
                )

                # Настраиваем цвета строк
                if plugin_enabled:
                    self.tree.tag_configure(plugin_id, background="#0a3020", foreground="white")
                else:
                    self.tree.tag_configure(plugin_id, background="#2b2b2b", foreground="#cccccc")

        except Exception as e:
            print(f"[UI] Ошибка обновления списка плагинов: {e}")
            import traceback
            traceback.print_exc()

    def get_selected_plugin_id(self):
        """Возвращает ID выбранного плагина"""
        selection = self.tree.selection()
        if selection:
            return self.tree.item(selection[0])['tags'][0]
        return None

    def enable_selected(self):
        """Включает выбранный плагин"""
        plugin_id = self.get_selected_plugin_id()
        if plugin_id:
            if self.plugin_manager.enable_plugin(plugin_id):
                self.refresh_plugins()

    def disable_selected(self):
        """Выключает выбранный плагин"""
        plugin_id = self.get_selected_plugin_id()
        if plugin_id:
            if self.plugin_manager.disable_plugin(plugin_id):
                self.refresh_plugins()

    def show_details(self):
        """Показывает подробности о плагине"""
        plugin_id = self.get_selected_plugin_id()
        if not plugin_id:
            return

        plugin_info = self.plugin_manager.get_plugin_info(plugin_id)
        if not plugin_info:
            return

        details = (
            f"📦 {plugin_info['name']} v{plugin_info['version']}\n\n"
            f"👤 Автор: {plugin_info['author']}\n"
            f"📝 Описание: {plugin_info['description']}\n"
            f"🔌 API версия: {plugin_info['api_version']}\n"
            f"📁 Путь: {plugin_info['path']}\n"
            f"✅ Статус: {'АКТИВЕН' if plugin_info['enabled'] else 'ОТКЛЮЧЕН'}"
        )

        messagebox.showinfo("Подробности плагина", details)