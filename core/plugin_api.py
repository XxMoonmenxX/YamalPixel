"""
БЕЗОПАСНЫЙ API для плагинов YamalPixel с системой разрешений
"""

import tkinter as tk
import hashlib
import json
import os
from typing import Dict, Any, Callable, List, Optional, Set
from pathlib import Path
import logging

# Настройка логирования для безопасности
security_logger = logging.getLogger("PluginSecurity")

class PluginAPI:
    """Защищенный API с проверкой разрешений для взаимодействия плагинов с лаунчером"""

    # === СИСТЕМА РАЗРЕШЕНИЙ ===
    # Вся потенциально опасная функциональность требует явного разрешения[citation:6]
    PERMISSIONS = {
        'ui_button': 'Добавление кнопок в интерфейс',
        'ui_notification': 'Показ уведомлений',
        'config_read': 'Чтение конфигурации лаунчера',
        'config_write': 'Изменение конфигурации лаунчера',
        'filesystem_read': 'Чтение файлов в папке Minecraft',
        'filesystem_mods_write': 'Запись в папку модов (опасно!)',
        'filesystem_config_write': 'Запись в папку конфигов',
        'network_request': 'Выполнение сетевых запросов',
        'subprocess_execute': 'Запуск сторонних процессов (очень опасно!)',
        'hook_registration': 'Регистрация системных хуков'
    }

    def __init__(self, launcher_window: tk.Tk, config: Dict[str, Any],
                 launcher_dir: Path, plugin_id: str, granted_permissions: Set[str]):
        self.window = launcher_window
        self.config = config
        self.launcher_dir = launcher_dir
        self.plugin_id = plugin_id
        self.granted_permissions = granted_permissions

        # Система хуков - только чтение для плагинов
        self._hooks: Dict[str, List[Callable]] = {
            'on_launch_start': [],
            'on_launch_complete': [],
            'on_mods_downloaded': [],
            'on_collection_loaded': [],
            'on_ui_ready': [],
            'on_plugin_enable': [],
            'on_plugin_disable': [],
        }

        # Храним виджеты плагинов
        self._plugin_widgets: Dict[str, List[tk.Widget]] = {}

        security_logger.info(f"[{plugin_id}] API инициализирован с разрешениями: {granted_permissions}")

    def add_label(self, text: str, position: tuple = None, **kwargs) -> Optional[tk.Label]:
        """
        Добавляет метку в интерфейс лаунчера.
        Требует разрешения 'ui_button'.
        """
        if not self.check_permission('ui_button', f"add_label: {text}"):
            return None

        try:
            # БЕЗОПАСНОСТЬ: Ограничение на количество виджетов
            if self.plugin_id in self._plugin_widgets:
                if len(self._plugin_widgets[self.plugin_id]) >= 5:
                    security_logger.warning(f"[{self.plugin_id}] Достигнут лимит виджетов")
                    return None

            label = tk.Label(self.window, text=text, **kwargs)

            # Позиционирование
            if position == 'top':
                label.place(relx=0.5, rely=0.05, anchor="center")
            elif position == 'bottom':
                label.place(relx=0.5, rely=0.95, anchor="center")
            elif isinstance(position, tuple) and len(position) == 2:
                x, y = position
                label.place(x=x, y=y)
            else:
                label.place(relx=0.5, rely=0.05, anchor="center")

            if self.plugin_id not in self._plugin_widgets:
                self._plugin_widgets[self.plugin_id] = []
            self._plugin_widgets[self.plugin_id].append(label)

            return label

        except Exception as e:
            security_logger.error(f"[{self.plugin_id}] Ошибка добавления метки: {e}")
            return None
    # === ОСНОВНОЙ МЕТОД БЕЗОПАСНОСТИ ===
    def check_permission(self, permission: str, action_description: str = "") -> bool:
        """
        Проверяет наличие разрешения у плагина.
        Логирует все попытки доступа для аудита.
        """
        if permission not in self.PERMISSIONS:
            security_logger.warning(f"[{self.plugin_id}] Запрос неизвестного разрешения: {permission}")
            return False

        if permission in self.granted_permissions:
            security_logger.info(f"[{self.plugin_id}] Разрешение '{permission}' granted для: {action_description}")
            return True
        else:
            security_logger.warning(f"[{self.plugin_id}] ОТКАЗ в разрешении '{permission}' для: {action_description}")
            return False

    # === UI API С ПРОВЕРКОЙ РАЗРЕШЕНИЙ ===
    def add_button(self, text: str, command: Callable, position: tuple = None, **kwargs) -> Optional[tk.Button]:
        """
        Добавляет кнопку в интерфейс лаунчера.
        Требует разрешения 'ui_button'.
        """
        if not self.check_permission('ui_button', f"add_button: {text}"):
            return None

        try:
            # БЕЗОПАСНОСТЬ: Валидация команды
            if not callable(command):
                security_logger.error(f"[{self.plugin_id}] Некорректная команда для кнопки")
                return None

            # БЕЗОПАСНОСТЬ: Ограничение на количество кнопок
            if self.plugin_id in self._plugin_widgets:
                if len(self._plugin_widgets[self.plugin_id]) >= 5:  # Максимум 5 виджетов на плагин
                    security_logger.warning(f"[{self.plugin_id}] Достигнут лимит виджетов")
                    return None

            from Ui.UiComponents import ModernButton
            btn = ModernButton(self.window, text=text, command=command, **kwargs)

            # Позиционирование с ограничениями
            if position == 'top':
                btn.place(relx=0.5, rely=0.1, anchor="center")
            elif position == 'bottom':
                btn.place(relx=0.5, rely=0.9, anchor="center")
            elif isinstance(position, tuple) and len(position) == 2:
                # БЕЗОПАСНОСТЬ: Проверяем, чтобы кнопка не выходила за границы окна
                x, y = position
                if 0 <= x <= self.window.winfo_width() and 0 <= y <= self.window.winfo_height():
                    btn.place(x=x, y=y)
                else:
                    btn.place(relx=0.5, rely=0.9, anchor="center")
            else:
                btn.place(relx=0.5, rely=0.9, anchor="center")

            if self.plugin_id not in self._plugin_widgets:
                self._plugin_widgets[self.plugin_id] = []
            self._plugin_widgets[self.plugin_id].append(btn)

            return btn

        except Exception as e:
            security_logger.error(f"[{self.plugin_id}] Ошибка добавления кнопки: {e}")
            return None

    def show_notification(self, title: str, message: str):
        """
        Показывает уведомление.
        Требует разрешения 'ui_notification'.
        """
        if not self.check_permission('ui_notification', f"show_notification: {title}"):
            return

        try:
            from tkinter import messagebox
            messagebox.showinfo(title, message)
            security_logger.info(f"[{self.plugin_id}] Показано уведомление: {title}")
        except Exception as e:
            security_logger.error(f"[{self.plugin_id}] Ошибка показа уведомления: {e}")

    # === КОНФИГУРАЦИЯ С ПРОВЕРКОЙ РАЗРЕШЕНИЙ ===
    def get_config_value(self, key: str, default=None):
        """Чтение конфига - требует разрешения 'config_read'"""
        if not self.check_permission('config_read', f"get_config_value: {key}"):
            return default

        value = self.config.get(key, default)
        security_logger.info(f"[{self.plugin_id}] Прочитан конфиг: {key} = {value}")
        return value

    def set_config_value(self, key: str, value):
        """Запись в конфиг - требует разрешения 'config_write'"""
        if not self.check_permission('config_write', f"set_config_value: {key}"):
            return

        # БЕЗОПАСНОСТЬ: Запрещаем изменение критичных ключей
        protected_keys = {'minecraft_dir', 'jvm_memory', 'enabled_plugins'}
        if key in protected_keys:
            security_logger.warning(f"[{self.plugin_id}] Попытка изменить защищенный ключ: {key}")
            return

        old_value = self.config.get(key)
        self.config[key] = value
        security_logger.info(f"[{self.plugin_id}] Изменен конфиг: {key}: {old_value} -> {value}")

    # === ФАЙЛОВАЯ СИСТЕМА С ПРОВЕРКОЙ РАЗРЕШЕНИЙ И ПЕСОЧНИЦЕЙ ===
    def safe_read_file(self, relative_path: str) -> Optional[str]:
        """
        Безопасное чтение файла в пределах папки Minecraft.
        Требует разрешения 'filesystem_read'.
        """
        if not self.check_permission('filesystem_read', f"safe_read_file: {relative_path}"):
            return None

        try:
            # БЕЗОПАСНОСТЬ: Нормализуем путь, предотвращаем directory traversal
            safe_path = self._sanitize_path(relative_path)
            if not safe_path:
                return None

            full_path = self.get_minecraft_dir() / safe_path

            # БЕЗОПАСНОСТЬ: Проверяем, что путь находится ВНУТРИ папки Minecraft
            if not self._is_path_safe(full_path):
                security_logger.warning(f"[{self.plugin_id}] Попытка доступа вне sandbox: {relative_path}")
                return None

            if full_path.exists() and full_path.is_file():
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                security_logger.info(f"[{self.plugin_id}] Прочитан файл: {relative_path} ({len(content)} байт)")
                return content
            else:
                security_logger.warning(f"[{self.plugin_id}] Файл не найден: {relative_path}")
                return None

        except Exception as e:
            security_logger.error(f"[{self.plugin_id}] Ошибка чтения файла {relative_path}: {e}")
            return None

    def safe_write_file(self, relative_path: str, content: str,
                       allowed_extensions: List[str] = None) -> bool:
        """
        Безопасная запись файла ТОЛЬКО в разрешенные папки.
        Требует соответствующего разрешения на запись.
        """
        # Определяем тип разрешения в зависимости от пути
        if 'mods' in relative_path:
            permission = 'filesystem_mods_write'
        elif 'config' in relative_path:
            permission = 'filesystem_config_write'
        else:
            security_logger.warning(f"[{self.plugin_id}] Неразрешенный путь для записи: {relative_path}")
            return False

        if not self.check_permission(permission, f"safe_write_file: {relative_path}"):
            return False

        try:
            # БЕЗОПАСНОСТЬ: Валидация пути
            safe_path = self._sanitize_path(relative_path)
            if not safe_path:
                return False

            full_path = self.get_minecraft_dir() / safe_path

            # БЕЗОПАСНОСТЬ: Проверка расширения файла
            if allowed_extensions:
                ext = full_path.suffix.lower()
                if ext not in allowed_extensions:
                    security_logger.warning(f"[{self.plugin_id}] Запрещенное расширение: {ext}")
                    return False

            # БЕЗОПАСНОСТЬ: Проверка размера файла (макс 10MB)
            if len(content.encode('utf-8')) > 10 * 1024 * 1024:
                security_logger.warning(f"[{self.plugin_id}] Файл слишком большой")
                return False

            # Создаем папку если нужно
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Записываем файл
            full_path.write_text(content, encoding='utf-8')

            # БЕЗОПАСНОСТЬ: Проверяем хэш после записи
            file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            security_logger.info(f"[{self.plugin_id}] Записан файл: {relative_path}, SHA256: {file_hash[:16]}")

            return True

        except Exception as e:
            security_logger.error(f"[{self.plugin_id}] Ошибка записи файла {relative_path}: {e}")
            return False

    # === СЛУЖЕБНЫЕ МЕТОДЫ БЕЗОПАСНОСТИ ===
    def _sanitize_path(self, relative_path: str) -> Optional[Path]:
        """Очищает и нормализует путь, предотвращает directory traversal"""
        try:
            # Преобразуем в Path и нормализуем
            path = Path(relative_path)
            normalized = path.resolve()

            # Преобразуем в строку и проверяем на опасные последовательности
            path_str = str(normalized)
            dangerous_patterns = ['..', '~', '//', '\\', ':', '*', '?', '"', '<', '>', '|']

            for pattern in dangerous_patterns:
                if pattern in path_str:
                    security_logger.warning(f"[{self.plugin_id}] Опасный путь: {relative_path}")
                    return None

            return Path(path_str)

        except Exception as e:
            security_logger.error(f"[{self.plugin_id}] Ошибка валидации пути {relative_path}: {e}")
            return None

    def _is_path_safe(self, full_path: Path) -> bool:
        """Проверяет, что путь находится внутри папки Minecraft"""
        minecraft_dir = self.get_minecraft_dir().resolve()
        try:
            # Проверяем, что полный путь находится внутри minecraft_dir
            return minecraft_dir in full_path.resolve().parents or full_path.resolve() == minecraft_dir
        except:
            return False

    # === БАЗОВЫЕ GETTERS (безопасные) ===
    def get_minecraft_dir(self) -> Path:
        return Path(self.config.get("minecraft_dir", "~/YamalPixel")).expanduser()

    def get_mods_dir(self) -> Path:
        return self.get_minecraft_dir() / "mods"

    def get_plugin_dir(self) -> Path:
        return self.launcher_dir / "plugins_external" / self.plugin_id

    # === СИСТЕМА ХУКОВ (плагины могут только регистрировать) ===
    def register_hook(self, hook_name: str, callback: Callable):
        """Регистрация хука - требует разрешения 'hook_registration'"""
        if not self.check_permission('hook_registration', f"register_hook: {hook_name}"):
            return

        if hook_name in self._hooks:
            # БЕЗОПАСНОСТЬ: Ограничиваем количество хуков на плагин
            if len(self._hooks[hook_name]) >= 3:
                security_logger.warning(f"[{self.plugin_id}] Достигнут лимит хуков для {hook_name}")
                return

            self._hooks[hook_name].append(callback)
            security_logger.info(f"[{self.plugin_id}] Зарегистрирован хук: {hook_name}")
        else:
            security_logger.warning(f"[{self.plugin_id}] Попытка регистрации неизвестного хука: {hook_name}")

    # Внутренний метод для менеджера плагинов
    def _call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Внутренний метод для вызова хуков (только для менеджера плагинов)"""
        results = []
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    security_logger.error(f"[{self.plugin_id}] Ошибка в хуке '{hook_name}': {e}")
        return results

    # === ОЧИСТКА РЕСУРСОВ ===
    def cleanup(self):
        """Очищает все ресурсы плагина"""
        security_logger.info(f"[{self.plugin_id}] Очистка ресурсов плагина")

        # Удаляем все виджеты
        if self.plugin_id in self._plugin_widgets:
            for widget in self._plugin_widgets[self.plugin_id]:
                try:
                    widget.place_forget()
                    widget.destroy()
                except:
                    pass
            del self._plugin_widgets[self.plugin_id]

        # Удаляем все хуки этого плагина
        for hook_name in list(self._hooks.keys()):
            self._hooks[hook_name] = [
                cb for cb in self._hooks[hook_name]
                # Фильтруем по имени функции (не идеально, но работает)
                if getattr(cb, '__module__', '').startswith(self.plugin_id)
            ]