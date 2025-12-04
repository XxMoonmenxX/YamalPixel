"""
Менеджер плагинов YamalPixel
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
        self.launcher_dir = self._get_launcher_directory(launcher_dir)

        print(f"[PluginManager] Launcher directory: {self.launcher_dir}")
        print(f"[PluginManager] Is PyInstaller: {getattr(sys, 'frozen', False)}")

        # Пути - ВСЕГДА относительно директории лаунчера
        self.plugins_dir = self.launcher_dir / "plugins_external"
        self.builtin_plugins_dir = self.launcher_dir / "plugins"

        print(f"[PluginManager] Plugins dir: {self.plugins_dir}")
        print(f"[PluginManager] Builtin plugins dir: {self.builtin_plugins_dir}")

        # Хранилище плагинов
        self.plugins: Dict[str, 'LoadedPlugin'] = {}
        self.api: Optional[PluginAPI] = None

        # Создаем структуру папок
        self._setup_directories()

        # Инициализируем API
        self.api = PluginAPI(launcher_window, config, self.launcher_dir)

    def _get_launcher_directory(self, initial_dir: Path) -> Path:
        """
        Определяет правильную директорию лаунчера.
        Приоритеты:
        1. Директория исполняемого файла (если собран PyInstaller)
        2. Переданная директория
        3. Текущая рабочая директория
        """
        if getattr(sys, 'frozen', False):
            # Если собран PyInstaller - используем директорию исполняемого файла
            exe_path = Path(sys.executable).parent
            print(f"[PluginManager] Using PyInstaller directory: {exe_path}")
            return exe_path

        # Если переданный путь существует и является директорией - используем его
        if initial_dir and initial_dir.exists() and initial_dir.is_dir():
            print(f"[PluginManager] Using initial directory: {initial_dir}")
            return initial_dir

        # По умолчанию - директория файла plugin_manager.py
        default_dir = Path(__file__).parent.parent
        print(f"[PluginManager] Using default directory: {default_dir}")
        return default_dir

    def _setup_directories(self):
        """Создает необходимые папки"""
        print(f"[PluginManager] Creating directories...")
        print(f"[PluginManager] Plugins directory: {self.plugins_dir}")
        print(f"[PluginManager] Builtin plugins directory: {self.builtin_plugins_dir}")

        try:
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            self.builtin_plugins_dir.mkdir(parents=True, exist_ok=True)
            print(f"[PluginManager] Directories created successfully")
        except Exception as e:
            print(f"[PluginManager] Error creating directories: {e}")
            # Пробуем создать в текущей директории как запасной вариант
            try:
                current_dir = Path.cwd()
                self.plugins_dir = current_dir / "plugins_external"
                self.builtin_plugins_dir = current_dir / "plugins"
                self.plugins_dir.mkdir(parents=True, exist_ok=True)
                self.builtin_plugins_dir.mkdir(parents=True, exist_ok=True)
                print(f"[PluginManager] Created directories in current working directory")
            except Exception as e2:
                print(f"[PluginManager] Critical error: {e2}")

    def discover_plugins(self) -> List[str]:
        """Обнаруживает все доступные плагины"""
        found_plugins = []

        print(f"[PluginManager] Discovering plugins...")
        print(f"[PluginManager] Checking plugins dir: {self.plugins_dir}")
        print(f"[PluginManager] Checking builtin plugins dir: {self.builtin_plugins_dir}")

        # Ищем плагины в двух местах:
        search_dirs = [
            (self.builtin_plugins_dir, True),   # Встроенные
            (self.plugins_dir, False),          # Пользовательские
        ]

        for search_dir, is_builtin in search_dirs:
            if not search_dir.exists():
                print(f"[PluginManager] Directory does not exist: {search_dir}")
                continue

            print(f"[PluginManager] Searching in: {search_dir}")

            try:
                items = list(search_dir.iterdir())
                print(f"[PluginManager] Found {len(items)} items in {search_dir}")
            except Exception as e:
                print(f"[PluginManager] Error reading directory {search_dir}: {e}")
                continue

            for item in items:
                if item.is_dir():
                    manifest_path = item / "manifest.json"
                    init_path = item / "__init__.py"

                    if manifest_path.exists() and init_path.exists():
                        try:
                            print(f"[PluginManager] Found plugin candidate: {item.name}")
                            manifest = PluginManifest(manifest_path)

                            if manifest.validate():
                                plugin_id = manifest.get('id')
                                print(f"[PluginManager] Valid plugin found: {plugin_id}")

                                # Проверяем, не загружен ли уже плагин
                                if plugin_id in self.plugins:
                                    print(f"[PluginManager] Plugin {plugin_id} already loaded, skipping")
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

                                print(f"[PluginManager] Plugin registered: {plugin.name} v{plugin.version}")

                            else:
                                print(f"[PluginManager] Invalid manifest in: {item.name}")

                        except Exception as e:
                            print(f"[PluginManager] Error loading plugin {item.name}: {e}")
                            traceback.print_exc()
                    else:
                        if not manifest_path.exists():
                            print(f"[PluginManager] No manifest.json in: {item.name}")
                        if not init_path.exists():
                            print(f"[PluginManager] No __init__.py in: {item.name}")

        print(f"[PluginManager] Total plugins found: {len(found_plugins)}")
        return found_plugins

    def load_plugin(self, plugin_id: str) -> bool:
        """Загружает плагин в память"""
        if plugin_id not in self.plugins:
            print(f"[PluginManager] Plugin {plugin_id} not found")
            return False

        plugin = self.plugins[plugin_id]

        if plugin.loaded:
            print(f"[PluginManager] Plugin {plugin.name} already loaded")
            return True

        try:
            print(f"[PluginManager] Loading plugin: {plugin.name} from {plugin.plugin_dir}")

            # Добавляем директорию плагина в sys.path
            if str(plugin.plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin.plugin_dir))

            # Динамически импортируем модуль
            spec = importlib.util.spec_from_file_location(
                plugin_id,
                plugin.plugin_dir / "__init__.py"
            )

            if spec is None or spec.loader is None:
                print(f"[PluginManager] Failed to create spec for {plugin_id}")
                return False

            module = importlib.util.module_from_spec(spec)
            # Устанавливаем атрибуты для отладки
            module.__name__ = plugin_id
            module.__file__ = str(plugin.plugin_dir / "__init__.py")

            # Выполняем код плагина
            spec.loader.exec_module(module)

            # Ищем класс Plugin
            if not hasattr(module, 'Plugin'):
                print(f"[PluginManager] Plugin {plugin_id} doesn't have class Plugin")
                # Проверяем какие классы есть
                classes = [name for name in dir(module) if not name.startswith('_')]
                print(f"[PluginManager] Available in module: {classes}")
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
                print(f"[PluginManager] set_api called for {plugin.name}")
            else:
                # Если метода нет, устанавливаем напрямую
                plugin.instance.api = self.api
                print(f"[PluginManager] API set directly for {plugin.name}")

            plugin.loaded = True
            print(f"[PluginManager] Plugin {plugin.name} loaded successfully")

            return True

        except Exception as e:
            print(f"[PluginManager] Error loading plugin {plugin_id}:")
            traceback.print_exc()
            return False

    def enable_plugin(self, plugin_id: str) -> bool:
        """Активирует плагин"""
        if plugin_id not in self.plugins:
            print(f"[PluginManager] Cannot enable: plugin {plugin_id} not found")
            return False

        plugin = self.plugins[plugin_id]

        if plugin.enabled:
            print(f"[PluginManager] Plugin {plugin.name} already enabled")
            return True

        # Загружаем плагин если еще не загружен
        if not plugin.loaded:
            print(f"[PluginManager] Loading plugin {plugin.name} before enabling...")
            if not self.load_plugin(plugin_id):
                print(f"[PluginManager] Failed to load plugin {plugin.name}")
                return False

        try:
            print(f"[PluginManager] Enabling plugin: {plugin.name}")

            # Перед активацией убедимся, что старые виджеты удалены
            if self.api:
                self.api.remove_plugin_widgets(plugin_id)

            # Активируем плагин
            if hasattr(plugin.instance, 'on_enable'):
                plugin.instance.on_enable()
                print(f"[PluginManager] on_enable called for {plugin.name}")
            else:
                print(f"[PluginManager] Warning: {plugin.name} has no on_enable method")

            plugin.enabled = True

            # Обновляем конфиг
            enabled_plugins = self.config.get("enabled_plugins", [])
            if plugin_id not in enabled_plugins:
                enabled_plugins.append(plugin_id)
                self.config["enabled_plugins"] = enabled_plugins
                print(f"[PluginManager] Added {plugin_id} to enabled plugins config")

            # Вызываем хук
            self.api.call_hook('on_plugin_enable', plugin_id)

            print(f"[PluginManager] Plugin {plugin.name} enabled successfully")
            return True

        except Exception as e:
            print(f"[PluginManager] Error enabling plugin {plugin_id}:")
            traceback.print_exc()
            return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """Деактивирует плагин"""
        if plugin_id not in self.plugins:
            print(f"[PluginManager] Cannot disable: plugin {plugin_id} not found")
            return False

        plugin = self.plugins[plugin_id]

        if not plugin.enabled:
            print(f"[PluginManager] Plugin {plugin.name} already disabled")
            return True

        try:
            print(f"[PluginManager] Disabling plugin: {plugin.name}")

            # Деактивируем плагин
            if plugin.instance and hasattr(plugin.instance, 'on_disable'):
                plugin.instance.on_disable()
                print(f"[PluginManager] on_disable called for {plugin.name}")

            # Удаляем ВСЕ виджеты плагина
            if self.api:
                self.api.remove_plugin_widgets(plugin_id)
                print(f"[PluginManager] Widgets removed for {plugin.name}")

            plugin.enabled = False

            # Обновляем конфиг
            enabled_plugins = self.config.get("enabled_plugins", [])
            if plugin_id in enabled_plugins:
                enabled_plugins.remove(plugin_id)
                self.config["enabled_plugins"] = enabled_plugins
                print(f"[PluginManager] Removed {plugin_id} from enabled plugins config")

            # Вызываем хук
            self.api.call_hook('on_plugin_disable', plugin_id)

            print(f"[PluginManager] Plugin {plugin.name} disabled successfully")
            return True

        except Exception as e:
            print(f"[PluginManager] Error disabling plugin {plugin_id}:")
            traceback.print_exc()
            return False

    def initialize(self):
        """Инициализирует систему плагинов"""
        print("[PluginManager] ===== Initializing plugin system =====")
        print(f"[PluginManager] Working directory: {Path.cwd()}")
        print(f"[PluginManager] Launcher directory: {self.launcher_dir}")

        # Обнаруживаем плагины
        found = self.discover_plugins()
        print(f"[PluginManager] Found plugins: {len(found)}")

        # Загружаем и активируем плагины из конфига
        enabled_plugins = self.config.get("enabled_plugins", [])
        print(f"[PluginManager] Plugins to enable from config: {enabled_plugins}")

        success_count = 0
        for plugin_id in enabled_plugins:
            if plugin_id in self.plugins:
                print(f"[PluginManager] Enabling plugin from config: {plugin_id}")
                if self.enable_plugin(plugin_id):
                    success_count += 1
            else:
                print(f"[PluginManager] Warning: Plugin {plugin_id} from config not found")

        print(f"[PluginManager] Plugin system ready. Enabled: {success_count}/{len(enabled_plugins)}")
        print("[PluginManager] ===== Plugin system initialized =====")
        return True

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict]:
        """Возвращает информацию о плагине"""
        if plugin_id not in self.plugins:
            print(f"[PluginManager] Cannot get info: plugin {plugin_id} not found")
            return None

        plugin = self.plugins[plugin_id]

        info = {
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

        print(f"[PluginManager] Plugin info for {plugin_id}: {info.get('name', 'Unknown')}")
        return info

    def get_all_plugins(self) -> List[Dict]:
        """Возвращает список всех плагинов"""
        result = []
        print(f"[PluginManager] Getting all plugins (total: {len(self.plugins)})")

        for plugin_id, plugin in self.plugins.items():
            try:
                # Базовая информация из LoadedPlugin
                plugin_info = {
                    'id': plugin_id,
                    'name': plugin.name if hasattr(plugin, 'name') else 'Без названия',
                    'version': plugin.version if hasattr(plugin, 'version') else '1.0.0',
                    'author': plugin.author if hasattr(plugin, 'author') else 'Неизвестен',
                    'description': plugin.description if hasattr(plugin, 'description') else '',
                    'enabled': plugin.enabled if hasattr(plugin, 'enabled') else False,
                    'loaded': plugin.loaded if hasattr(plugin, 'loaded') else False,
                    'is_builtin': plugin.is_builtin if hasattr(plugin, 'is_builtin') else False,
                    'api_version': plugin.api_version if hasattr(plugin, 'api_version') else '1.0',
                    'permissions': plugin.permissions if hasattr(plugin, 'permissions') else [],
                    'path': str(plugin.plugin_dir) if hasattr(plugin, 'plugin_dir') else '',
                }

                # Если плагин загружен и имеет экземпляр, берем данные оттуда
                if plugin.loaded and plugin.instance:
                    instance = plugin.instance
                    if hasattr(instance, 'name'):
                        plugin_info['name'] = instance.name
                    if hasattr(instance, 'version'):
                        plugin_info['version'] = instance.version
                    if hasattr(instance, 'author'):
                        plugin_info['author'] = instance.author
                    if hasattr(instance, 'description'):
                        plugin_info['description'] = instance.description

                print(f"[PluginManager] Plugin {plugin_id}: {plugin_info['name']}")
                result.append(plugin_info)

            except Exception as e:
                print(f"[PluginManager] Error getting info for plugin {plugin_id}: {e}")
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
        """Устанавливает плагин из ZIP архива"""
        try:
            import zipfile
            import json
            import tempfile
            import shutil

            print(f"[PluginManager] Installing from ZIP: {zip_path.name}")
            print(f"[PluginManager] ZIP path: {zip_path}")
            print(f"[PluginManager] Target plugins dir: {self.plugins_dir}")

            # Проверяем что это ZIP файл
            if not zipfile.is_zipfile(zip_path):
                return False, "Файл не является ZIP архивом"

            # Проверяем что папка плагинов существует
            if not self.plugins_dir.exists():
                print(f"[PluginManager] Creating plugins directory: {self.plugins_dir}")
                self.plugins_dir.mkdir(parents=True, exist_ok=True)

            # Временная директория для распаковки
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)

                try:
                    # Открываем ZIP архив
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Получаем список файлов
                        file_list = zip_ref.namelist()
                        print(f"[PluginManager] Files in archive: {len(file_list)}")

                        # Проверяем что есть manifest.json
                        manifest_files = []
                        for file_name in file_list:
                            if 'manifest.json' in file_name:
                                manifest_files.append(file_name)

                        if not manifest_files:
                            print("[PluginManager] No manifest.json found in archive")
                            return False, "ZIP архив не содержит manifest.json"

                        # Распаковываем весь архив
                        print(f"[PluginManager] Extracting to temp directory: {temp_dir_path}")
                        zip_ref.extractall(temp_dir_path)

                        # Ищем manifest.json
                        manifest_path = None
                        for root, dirs, files in os.walk(temp_dir_path):
                            for file in files:
                                if file == 'manifest.json':
                                    manifest_path = Path(root) / file
                                    print(f"[PluginManager] Found manifest.json at: {manifest_path}")
                                    break
                            if manifest_path:
                                break

                        if not manifest_path or not manifest_path.exists():
                            return False, "Не найден manifest.json после распаковки"

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
                        print(f"[PluginManager] Plugin ID: {plugin_id}")

                        # Проверяем что ID содержит только разрешенные символы
                        if not all(c.isalnum() or c in '-_' for c in plugin_id):
                            return False, f"ID плагина '{plugin_id}' содержит недопустимые символы. Используйте только буквы, цифры, - и _"

                        # Определяем корневую папку плагина (там где manifest.json)
                        plugin_root = manifest_path.parent
                        print(f"[PluginManager] Plugin root directory: {plugin_root}")

                        # Проверяем наличие __init__.py
                        init_file = plugin_root / "__init__.py"
                        if not init_file.exists():
                            return False, "Плагин должен содержать __init__.py в той же папке что и manifest.json"

                        # Проверяем что плагин еще не установлен
                        target_dir = self.plugins_dir / plugin_id
                        if target_dir.exists():
                            print(f"[PluginManager] Plugin already exists at: {target_dir}")
                            # В UI уже спросили подтверждение, просто удаляем
                            shutil.rmtree(target_dir)
                            print(f"[PluginManager] Removed existing plugin directory")

                        # Копируем плагин в папку плагинов
                        print(f"[PluginManager] Copying plugin to: {target_dir}")
                        shutil.copytree(plugin_root, target_dir)

                        # Проверяем валидность манифеста через PluginManifest
                        from .plugin_base import PluginManifest
                        manifest = PluginManifest(target_dir / "manifest.json")

                        if not manifest.validate():
                            print("[PluginManager] Manifest validation failed")
                            return False, "Невалидный манифест плагина"

                        print(f"[PluginManager] Plugin {plugin_id} successfully installed")

                        # Перезагружаем список плагинов
                        self.discover_plugins()

                        return True, plugin_id

                except Exception as e:
                    print(f"[PluginManager] Error during extraction: {e}")
                    traceback.print_exc()
                    return False, f"Ошибка при распаковке: {str(e)}"

        except zipfile.BadZipFile:
            return False, "Некорректный ZIP архив (файл поврежден)"
        except Exception as e:
            print(f"[PluginManager] General installation error: {e}")
            traceback.print_exc()
            return False, f"Ошибка установки: {str(e)}"

    def reload_plugin_ui(self, plugin_id: str):
        """Перезагружает UI плагина (удаляет и создает заново)"""
        if plugin_id not in self.plugins:
            print(f"[PluginManager] Cannot reload UI: plugin {plugin_id} not found")
            return False

        plugin = self.plugins[plugin_id]

        if not plugin.enabled or not plugin.loaded:
            print(f"[PluginManager] Cannot reload UI: plugin {plugin.name} not enabled or loaded")
            return False

        try:
            print(f"[PluginManager] Reloading UI for plugin: {plugin.name}")

            # Временно деактивируем плагин
            if plugin.instance:
                plugin.instance.on_disable()

            # Удаляем все виджеты
            if self.api:
                self.api.remove_plugin_widgets(plugin_id)

            # Снова активируем плагин
            plugin.instance.on_enable()

            print(f"[PluginManager] UI for plugin {plugin.name} reloaded successfully")
            return True

        except Exception as e:
            print(f"[PluginManager] Error reloading UI for plugin {plugin_id}: {e}")
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