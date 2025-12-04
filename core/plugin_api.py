"""
API для плагинов YamalPixel
"""

import tkinter as tk
from typing import Dict, Any, Callable, List, Optional
from pathlib import Path


class PluginAPI:
    """Основной API для взаимодействия плагинов с лаунчером"""

    def __init__(self, launcher_window: tk.Tk, config: Dict[str, Any], launcher_dir: Path):
        self.window = launcher_window
        self.config = config
        self.launcher_dir = launcher_dir

        # Система хуков
        self.hooks: Dict[str, List[Callable]] = {
            'on_launch_start': [],
            'on_launch_complete': [],
            'on_mods_downloaded': [],
            'on_collection_loaded': [],
            'on_ui_ready': [],
            'on_plugin_enable': [],
            'on_plugin_disable': [],
        }

        # Храним виджеты плагинов
        self.plugin_widgets: Dict[str, List[tk.Widget]] = {}
        # Храним родительские контейнеры для виджетов
        self.widget_parents: Dict[str, Dict[str, tk.Widget]] = {}

    def add_button(self, plugin_id: str, text: str, command: Callable,
                   position: tuple = None, parent: tk.Widget = None, **kwargs) -> Optional[tk.Button]:
        """
        Добавляет кнопку в интерфейс лаунчера
        """
        try:
            from Ui.UiComponents import ModernButton

            # Используем указанный родитель или основной window
            target_parent = parent or self.window

            # Проверяем, не существует ли уже такая кнопка
            if plugin_id in self.plugin_widgets:
                for widget in self.plugin_widgets[plugin_id]:
                    if isinstance(widget, tk.Button) and widget.cget("text") == text:
                        return widget

            # Создаем кнопку
            btn = ModernButton(
                target_parent,
                text=text,
                command=command,
                **kwargs
            )

            # Запоминаем родителя
            widget_id = f"button_{text}_{id(btn)}"
            if plugin_id not in self.widget_parents:
                self.widget_parents[plugin_id] = {}
            self.widget_parents[plugin_id][widget_id] = target_parent

            # Универсальное позиционирование - используем place для гибкости
            if position == 'top':
                # Размещаем в верхней части окна
                btn.place(relx=0.5, rely=0.1, anchor="center", width=kwargs.get('width', 200))
            elif position == 'bottom':
                # Размещаем в нижней части окна, выше других элементов
                btn.place(relx=0.5, rely=0.9, anchor="center", width=kwargs.get('width', 200))
            elif isinstance(position, tuple) and len(position) == 2:
                # Абсолютные координаты
                btn.place(x=position[0], y=position[1])
            else:
                # По умолчанию - динамическое размещение снизу
                # Находим позицию для новой кнопки (выше всех существующих кнопок плагинов)
                y_position = 0.9
                for pid, widgets in self.plugin_widgets.items():
                    for widget in widgets:
                        try:
                            # Получаем текущую позицию виджета
                            info = widget.place_info()
                            if info:
                                current_y = float(info.get('rely', 0.9))
                                y_position = min(y_position, current_y - 0.05)
                        except:
                            pass

                btn.place(relx=0.5, rely=y_position, anchor="center", width=kwargs.get('width', 200))

            # Сохраняем виджет
            if plugin_id not in self.plugin_widgets:
                self.plugin_widgets[plugin_id] = []
            self.plugin_widgets[plugin_id].append(btn)

            return btn

        except Exception as e:
            print(f"[API] Ошибка добавления кнопки: {e}")
            import traceback
            traceback.print_exc()
            return None

    def remove_plugin_widgets(self, plugin_id: str):
        """Удаляет все виджеты, созданные плагином"""
        if plugin_id in self.plugin_widgets:
            for widget in self.plugin_widgets[plugin_id]:
                try:
                    # Убираем виджет с экрана
                    widget.place_forget()
                    widget.destroy()

                    # Удаляем из родительских записей
                    for widget_id, parent in list(self.widget_parents.get(plugin_id, {}).items()):
                        if widget in parent.winfo_children():
                            del self.widget_parents[plugin_id][widget_id]

                except Exception as e:
                    print(f"[API] Ошибка удаления виджета: {e}")

            # Очищаем списки
            del self.plugin_widgets[plugin_id]
            if plugin_id in self.widget_parents:
                del self.widget_parents[plugin_id]

    # === Система хуков ===
    def register_hook(self, hook_name: str, callback: Callable):
        """Регистрирует функцию как хук"""
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)
        else:
            # Создаем новый хук если его нет
            self.hooks[hook_name] = [callback]

    def unregister_hook(self, hook_name: str, callback: Callable):
        """Удаляет хук"""
        if hook_name in self.hooks and callback in self.hooks[hook_name]:
            self.hooks[hook_name].remove(callback)

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Вызывает все зарегистрированные хуки"""
        results = []
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"[API] Ошибка в хуке '{hook_name}': {e}")
        return results

    # === UI API ===
    # Метод add_button уже определён — больше не дублируем!

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Показывает уведомление"""
        try:
            import tkinter.messagebox as msgbox
            msgbox.showinfo(title, message)
        except Exception as e:
            print(f"[API] Ошибка показа уведомления: {e}")

    # === Конфигурация лаунчера ===
    def get_config_value(self, key: str, default=None):
        """Получает значение из конфига лаунчера"""
        return self.config.get(key, default)

    def set_config_value(self, key: str, value):
        """Устанавливает значение в конфиг лаунчера"""
        self.config[key] = value

    # === Файловая система ===
    def get_minecraft_dir(self) -> Path:
        """Возвращает путь к папке Minecraft"""
        return Path(self.config.get("minecraft_dir", "~/YamalPixel")).expanduser()

    def get_mods_dir(self) -> Path:
        """Возвращает путь к папке модов"""
        return self.get_minecraft_dir() / "mods"

    def get_plugin_dir(self, plugin_id: str) -> Path:
        """Возвращает путь к папке плагина"""
        return self.launcher_dir / "plugins_external" / plugin_id

    # === Утилиты ===
    def log(self, plugin_id: str, message: str, level: str = "INFO"):
        """Логирует сообщение от плагина"""
        print(f"[{plugin_id}][{level}] {message}")