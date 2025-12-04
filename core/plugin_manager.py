"""
Менеджер плагинов YamalPixel (упрощенная версия)
"""

import importlib.util
import sys
import json
import zipfile
import shutil
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import traceback

from .plugin_base import PluginBase, PluginManifest
from .plugin_api import PluginAPI


class PluginManager:
    """Основной менеджер плагинов"""

    def __init__(self, launcher_window, config: Dict, launcher_dir: Path):
        self.window = launcher_window
        self.config = config
        self.launcher_dir = Path(launcher_dir)

        # Пути
        self.plugins_dir = self.launcher_dir / "plugins_external"
        self.builtin_plugins_dir = self.launcher_dir / "plugins"

        # Хранилище плагинов
        self.plugins: Dict[str, 'LoadedPlugin'] = {}
        self.api: Optional[PluginAPI] = None

        # Создаем структуру папок
        self._setup_directories()

        # Инициализируем API
        self.api = PluginAPI(launcher_window, config, launcher_dir)

    def _setup_directories(self):
        """Создает необходимые папки"""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.builtin_plugins_dir.mkdir(parents=True, exist_ok=True)

    def discover_plugins(self) -> List[str]:
        """Обнаруживает все доступные плагины"""
        found_plugins = []

        # Ищем плагины в двух местах:
        search_dirs = [
            (self.builtin_plugins_dir, True),   # Встроенные
            (self.plugins_dir, False),          # Пользовательские
        ]

        for search_dir, is_builtin in search_dirs:
            if not search_dir.exists():
                continue

            for item in search_dir.iterdir():
                if item.is_dir():
                    manifest_path = item / "manifest.json"
                    init_path = item / "__init__.py"

                    if manifest_path.exists() and init_path.exists():
                        try:
                            manifest = PluginManifest(manifest_path)

                            if manifest.validate():
                                plugin_id = manifest.get('id')

                                # Проверяем, не загружен ли уже плагин
                                if plugin_id in self.plugins:
                                    continue

                                # Загружаем информацию о плагине
                                plugin = LoadedPlugin(
                                    plugin_id=plugin_id,
                                    name=manifest.get('name'),
                                    version=manifest.get('version'),
                                    author=manifest.get('author', 'Unknown'),
                                    description=manifest.get('description', ''),
                                    api_version=manifest.get('api_version', '1.0'),
                                    permissions=manifest.get('permissions', []),
                                    plugin_dir=item,
                                    enabled=False,  # По умолчанию выключены
                                    is_builtin=is_builtin
                                )

                                self.plugins[plugin_id] = plugin
                                found_plugins.append(plugin_id)

                                print(f"[PluginManager] Найден плагин: {plugin.name} v{plugin.version}")

                        except Exception as e:
                            print(f"[PluginManager] Ошибка загрузки плагина {item.name}: {e}")

        return found_plugins

    def load_plugin(self, plugin_id: str) -> bool:
        """Загружает плагин в память"""
        if plugin_id not in self.plugins:
            print(f"[PluginManager] Плагин {plugin_id} не найден")
            return False

        plugin = self.plugins[plugin_id]

        if plugin.loaded:
            print(f"[PluginManager] Плагин {plugin.name} уже загружен")
            return True

        try:
            # Динамически импортируем модуль
            spec = importlib.util.spec_from_file_location(
                plugin_id,
                plugin.plugin_dir / "__init__.py"
            )

            if spec is None or spec.loader is None:
                print(f"[PluginManager] Не удалось создать spec для {plugin_id}")
                return False

            module = importlib.util.module_from_spec(spec)

            # Выполняем код плагина
            spec.loader.exec_module(module)

            # Ищем класс Plugin
            if not hasattr(module, 'Plugin'):
                print(f"[PluginManager] Плагин {plugin_id} не имеет класса Plugin")
                return False

            # Создаем экземпляр плагина
            plugin_class = module.Plugin
            plugin.instance = plugin_class()

            # Устанавливаем основные поля
            plugin.instance.id = plugin_id
            plugin.instance.name = plugin.name
            plugin.instance.version = plugin.version
            plugin.instance.author = plugin.author
            plugin.instance.description = plugin.description
            plugin.instance.api_version = plugin.api_version
            plugin.instance.plugin_dir = plugin.plugin_dir

            if hasattr(plugin.instance, 'set_api'):
                plugin.instance.set_api(self.api)
            else:
                # Если метода нет, устанавливаем напрямую
                plugin.instance.api = self.api

            plugin.loaded = True
            print(f"[PluginManager] Плагин {plugin.name} загружен")

            return True

        except Exception as e:
            print(f"[PluginManager] Ошибка загрузки плагина {plugin_id}:")
            traceback.print_exc()
            return False

    def enable_plugin(self, plugin_id: str) -> bool:
        """Активирует плагин"""
        if plugin_id not in self.plugins:
            return False

        plugin = self.plugins[plugin_id]

        if plugin.enabled:
            print(f"[PluginManager] Плагин {plugin.name} уже активирован")
            return True

        # Загружаем плагин если еще не загружен
        if not plugin.loaded:
            if not self.load_plugin(plugin_id):
                return False

        try:
            # Перед активацией убедимся, что старые виджеты удалены
            if self.api:
                self.api.remove_plugin_widgets(plugin_id)

            # Активируем плагин
            plugin.instance.on_enable()
            plugin.enabled = True

            # Обновляем конфиг
            enabled_plugins = self.config.get("enabled_plugins", [])
            if plugin_id not in enabled_plugins:
                enabled_plugins.append(plugin_id)
                self.config["enabled_plugins"] = enabled_plugins

            # Вызываем хук
            self.api.call_hook('on_plugin_enable', plugin_id)

            print(f"[PluginManager] Плагин {plugin.name} активирован")
            return True

        except Exception as e:
            print(f"[PluginManager] Ошибка активации плагина {plugin_id}:")
            traceback.print_exc()
            return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """Деактивирует плагин"""
        if plugin_id not in self.plugins:
            return False

        plugin = self.plugins[plugin_id]

        if not plugin.enabled:
            print(f"[PluginManager] Плагин {plugin.name} уже деактивирован")
            return True

        try:
            # Деактивируем плагин
            if plugin.instance:
                plugin.instance.on_disable()

            # Удаляем ВСЕ виджеты плагина
            if self.api:
                self.api.remove_plugin_widgets(plugin_id)

            plugin.enabled = False

            # Обновляем конфиг
            enabled_plugins = self.config.get("enabled_plugins", [])
            if plugin_id in enabled_plugins:
                enabled_plugins.remove(plugin_id)
                self.config["enabled_plugins"] = enabled_plugins

            # Вызываем хук
            self.api.call_hook('on_plugin_disable', plugin_id)

            print(f"[PluginManager] Плагин {plugin.name} деактивирован")
            return True

        except Exception as e:
            print(f"[PluginManager] Ошибка деактивации плагина {plugin_id}:")
            traceback.print_exc()
            return False

    def initialize(self):
        """Инициализирует систему плагинов"""
        print("[PluginManager] Инициализация системы плагинов...")

        # Обнаруживаем плагины
        found = self.discover_plugins()
        print(f"[PluginManager] Найдено плагинов: {len(found)}")

        # Загружаем и активируем плагины из конфига
        enabled_plugins = self.config.get("enabled_plugins", [])

        for plugin_id in enabled_plugins:
            if plugin_id in self.plugins:
                self.enable_plugin(plugin_id)

        print("[PluginManager] Система плагинов готова")
        return True

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict]:
        """Возвращает информацию о плагине"""
        if plugin_id not in self.plugins:
            return None

        plugin = self.plugins[plugin_id]

        return {
            'id': plugin_id,
            'name': plugin.name,
            'version': plugin.version,
            'author': plugin.author,
            'description': plugin.description,
            'enabled': plugin.enabled,
            'loaded': plugin.loaded,
            'is_builtin': plugin.is_builtin,
            'api_version': plugin.api_version,
            'permissions': plugin.permissions,
            'path': str(plugin.plugin_dir),
        }

    def get_all_plugins(self) -> List[Dict]:
        """Возвращает список всех плагинов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        result = []

        for plugin_id, plugin in self.plugins.items():
            try:
                plugin_info = {
                    'id': plugin_id,
                    'name': getattr(plugin, 'name', 'Без названия'),
                    'version': getattr(plugin, 'version', '1.0.0'),
                    'author': getattr(plugin, 'author', 'Неизвестен'),
                    'description': getattr(plugin, 'description', ''),
                    'enabled': getattr(plugin, 'enabled', False),
                    'loaded': getattr(plugin, 'loaded', False),
                    'is_builtin': getattr(plugin, 'is_builtin', False),
                    'api_version': getattr(plugin, 'api_version', '1.0'),
                    'permissions': getattr(plugin, 'permissions', []),
                    'path': str(getattr(plugin, 'plugin_dir', ''))
                }

                # Если плагин загружен и имеет экземпляр, берем данные оттуда
                if plugin.loaded and plugin.instance:
                    instance = plugin.instance
                    plugin_info.update({
                        'name': getattr(instance, 'name', plugin_info['name']),
                        'version': getattr(instance, 'version', plugin_info['version']),
                        'author': getattr(instance, 'author', plugin_info['author']),
                        'description': getattr(instance, 'description', plugin_info['description']),
                    })

                result.append(plugin_info)

            except Exception as e:
                print(f"[PluginManager] Ошибка получения информации о плагине {plugin_id}: {e}")
                # Добавляем хотя бы базовую информацию
                result.append({
                    'id': plugin_id,
                    'name': 'Ошибка загрузки',
                    'version': '?',
                    'author': '?',
                    'description': f'Ошибка: {str(e)}',
                    'enabled': False,
                    'loaded': False,
                    'is_builtin': False,
                    'api_version': '1.0',
                    'permissions': [],
                    'path': ''
                })

        return result

    def install_from_zip(self, zip_path: Path) -> Tuple[bool, str]:
        """Устанавливает плагин из ZIP архива - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            import zipfile
            import json
            import tempfile
            import shutil

            print(f"[PluginManager] Начинаем установку из ZIP: {zip_path.name}")

            # Проверяем что это ZIP файл
            if not zipfile.is_zipfile(zip_path):
                return False, "Файл не является ZIP архивом"

            # Временная директория для распаковки
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)

                try:
                    # Открываем ZIP архив
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Получаем список файлов
                        file_list = zip_ref.namelist()
                        print(f"[PluginManager] Файлов в архиве: {len(file_list)}")

                        # Проверяем что есть manifest.json
                        manifest_files = []
                        for file_name in file_list:
                            if file_name.endswith('manifest.json'):
                                manifest_files.append(file_name)

                        if not manifest_files:
                            print("[PluginManager] Не найден manifest.json в архиве")
                            return False, "ZIP архив не содержит manifest.json"

                        # Распаковываем весь архив
                        zip_ref.extractall(temp_dir_path)

                        # Ищем manifest.json
                        manifest_path = None
                        for root, dirs, files in os.walk(temp_dir_path):
                            for file in files:
                                if file == 'manifest.json':
                                    manifest_path = Path(root) / file
                                    break
                            if manifest_path:
                                break

                        if not manifest_path or not manifest_path.exists():
                            return False, "Не найден manifest.json после распаковки"

                        print(f"[PluginManager] Найден manifest.json: {manifest_path}")

                        # Читаем манифест
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            try:
                                manifest_data = json.load(f)
                            except json.JSONDecodeError as e:
                                return False, f"Ошибка в формате JSON: {e}"

                        # Проверяем обязательные поля
                        required_fields = ['name', 'id', 'version', 'api_version']
                        missing_fields = []
                        for field in required_fields:
                            if field not in manifest_data:
                                missing_fields.append(field)

                        if missing_fields:
                            return False, f"Манифест не содержит поля: {', '.join(missing_fields)}"

                        plugin_id = manifest_data['id']
                        print(f"[PluginManager] ID плагина: {plugin_id}")

                        # Проверяем что ID содержит только разрешенные символы
                        if not all(c.isalnum() or c in '-_' for c in plugin_id):
                            return False, f"ID плагина '{plugin_id}' содержит недопустимые символы. Используйте только буквы, цифры, - и _"

                        # Определяем корневую папку плагина (там где manifest.json)
                        plugin_root = manifest_path.parent
                        print(f"[PluginManager] Корневая папка плагина: {plugin_root}")

                        # Проверяем наличие __init__.py
                        init_file = plugin_root / "__init__.py"
                        if not init_file.exists():
                            return False, "Плагин должен содержать __init__.py в той же папке что и manifest.json"

                        # Проверяем что плагин еще не установлен
                        target_dir = self.plugins_dir / plugin_id
                        if target_dir.exists():
                            # Предлагаем перезаписать
                            try:
                                import tkinter.messagebox as mb
                                from tkinter import Tk
                                root = Tk()
                                root.withdraw()

                                result = mb.askyesno(
                                    "Плагин уже установлен",
                                    f"Плагин '{manifest_data.get('name', plugin_id)}' уже установлен.\n"
                                    f"Хотите перезаписать его?"
                                )
                                root.destroy()

                                if not result:
                                    return False, "Установка отменена пользователем"

                                shutil.rmtree(target_dir)
                            except:
                                # Если не получилось спросить, перезаписываем
                                shutil.rmtree(target_dir)

                        # Копируем плагин в папку плагинов
                        shutil.copytree(plugin_root, target_dir)

                        # Проверяем валидность манифеста через PluginManifest
                        from .plugin_base import PluginManifest
                        manifest = PluginManifest(target_dir / "manifest.json")

                        if not manifest.validate():
                            # Подробная диагностика
                            print("[PluginManager] Детали манифеста:")
                            print(f"  name: {manifest.get('name')}")
                            print(f"  id: {manifest.get('id')}")
                            print(f"  version: {manifest.get('version')}")
                            print(f"  api_version: {manifest.get('api_version')}")
                            print(f"  Дополнительные поля: {list(manifest.data.keys())}")

                            # Проверяем что все поля правильного типа
                            if not isinstance(manifest.get('name'), str):
                                return False, "Поле 'name' должно быть строкой"
                            if not isinstance(manifest.get('id'), str):
                                return False, "Поле 'id' должно быть строкой"
                            if not isinstance(manifest.get('version'), str):
                                return False, "Поле 'version' должно быть строкой"

                            # Проверяем формат ID
                            plugin_id = manifest.get('id', '')
                            if not all(c.isalnum() or c in '-_' for c in plugin_id):
                                return False, f"ID '{plugin_id}' содержит недопустимые символы. Используйте только буквы, цифры, - и _"

                            return False, "Невалидный манифест плагина (проверьте структуру JSON)"

                        print(f"[PluginManager] Плагин {plugin_id} успешно установлен")

                        # Перезагружаем список плагинов
                        self.discover_plugins()

                        return True, plugin_id

                except Exception as e:
                    print(f"[PluginManager] Ошибка при распаковке: {e}")
                    import traceback
                    traceback.print_exc()
                    return False, f"Ошибка при распаковке: {str(e)}"

        except zipfile.BadZipFile:
            return False, "Некорректный ZIP архив (файл поврежден)"
        except Exception as e:
            print(f"[PluginManager] Общая ошибка установки: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Ошибка установки: {str(e)}"

    def reload_plugin_ui(self, plugin_id: str):
        """Перезагружает UI плагина (удаляет и создает заново)"""
        if plugin_id not in self.plugins:
            return False

        plugin = self.plugins[plugin_id]

        if not plugin.enabled or not plugin.loaded:
            return False

        try:
            # Временно деактивируем плагин
            if plugin.instance:
                plugin.instance.on_disable()

            # Удаляем все виджеты
            if self.api:
                self.api.remove_plugin_widgets(plugin_id)

            # Снова активируем плагин
            plugin.instance.on_enable()

            print(f"[PluginManager] UI плагина {plugin.name} перезагружен")
            return True

        except Exception as e:
            print(f"[PluginManager] Ошибка перезагрузки UI плагина {plugin_id}: {e}")
            return False


class LoadedPlugin:
    """Класс для хранения информации о загруженном плагине"""

    def __init__(self, plugin_id: str, name: str, version: str, author: str,
                 description: str, api_version: str, permissions: List[str],
                 plugin_dir: Path, enabled: bool = False, is_builtin: bool = False):
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.api_version = api_version
        self.permissions = permissions
        self.plugin_dir = plugin_dir
        self.enabled = enabled
        self.is_builtin = is_builtin

        self.loaded = False
        self.instance: Optional[PluginBase] = None

    def __repr__(self):
        return f"LoadedPlugin(id={self.plugin_id}, name={self.name}, enabled={self.enabled})"