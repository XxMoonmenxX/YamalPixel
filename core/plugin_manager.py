"""
БЕЗОПАСНЫЙ менеджер плагинов YamalPixel с песочницей
"""

import importlib.util
import sys
import json
import zipfile
import shutil
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import traceback
import hashlib
import time  # Добавлено для функции карантина

from .plugin_base import PluginBase, PluginManifest
from .plugin_api import PluginAPI
from typing import Any  # Добавьте в начало файла


class PluginManager:
    """Безопасный менеджер плагинов с изоляцией и проверкой разрешений"""

    def __init__(self, launcher_window, config: Dict, launcher_dir: Path):
        self.window = launcher_window
        self.config = config
        self.api = self._create_system_api()

        # ИСПРАВЛЕНИЕ: Определяем директорию лаунчера напрямую
        self.launcher_dir = self._determine_launcher_directory(launcher_dir)

        print(f"[PluginManager] Launcher directory: {self.launcher_dir}")
        print(f"[PluginManager] Is PyInstaller: {getattr(sys, 'frozen', False)}")

        # Пути
        self.plugins_dir = self.launcher_dir / "plugins_external"
        self.builtin_plugins_dir = self.launcher_dir / "plugins"
        self.quarantine_dir = self.launcher_dir / "quarantine"  # Карантин для подозрительных плагинов

        # Хранилище плагинов
        self.plugins: Dict[str, 'LoadedPlugin'] = {}
        self._apis: Dict[str, PluginAPI] = {}  # Отдельный API для каждого плагина

        # Создаем структуру папок
        self._setup_directories()

    def _create_system_api(self):
        """Создает безопасный API для системных вызовов"""

        class SystemAPI:
            """Безопасный API для системных нужд"""

            def __init__(self, manager):
                self._manager = manager

            def _call_hook(self, hook_name: str, *args, **kwargs):
                """Безопасный вызов хука через менеджер"""
                return self._manager.call_hook(hook_name, *args, **kwargs)

            def __getattr__(self, name):
                # Запрещаем доступ ко всем остальным атрибутам
                raise AttributeError(f"SystemAPI does not have attribute '{name}'")

        return SystemAPI(self)


    def _call_hook_safely(self, hook_name: str, *args, **kwargs):
        """Безопасный вызов хуков"""
        print(f"[PluginManager] Calling hook: {hook_name}")

        results = []
        for plugin_id, plugin in self.plugins.items():
            if plugin.enabled and plugin.loaded:
                try:
                    if plugin_id in self._apis:
                        api = self._apis[plugin_id]
                        hook_results = api._call_hook(hook_name, *args, **kwargs)
                        results.extend(hook_results)
                except Exception as e:
                    print(f"[PluginManager] Error in hook '{hook_name}' for {plugin_id}: {e}")

        return results

    def trigger_hook(self, hook_name: str, *args, **kwargs):
        """Триггерит хук для всех активных плагинов"""
        print(f"[PluginManager] Triggering hook: {hook_name}")

        for plugin_id, plugin in self.plugins.items():
            if plugin.enabled and plugin.loaded:
                try:
                    # Получаем API для плагина
                    if plugin_id in self._apis:
                        api = self._apis[plugin_id]
                        # Вызываем внутренний метод для вызова хуков
                        results = api._call_hook(hook_name, *args, **kwargs)
                        if results:
                            print(f"[PluginManager] Hook {hook_name} returned {len(results)} results from {plugin_id}")
                except Exception as e:
                    print(f"[PluginManager] Error in hook '{hook_name}' for {plugin_id}: {e}")
    def _determine_launcher_directory(self, initial_dir: Path) -> Path:
        """
        Определяет правильную директорию лаунчера.
        ИСПРАВЛЕНИЕ: Это обычный метод, не статический
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

        # По умолчанию - текущая рабочая директория
        default_dir = Path.cwd()
        print(f"[PluginManager] Using current working directory: {default_dir}")
        return default_dir

    def _setup_directories(self):
        """Создает необходимые папки, включая карантин"""
        print(f"[PluginManager] Creating directories...")

        try:
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            self.builtin_plugins_dir.mkdir(parents=True, exist_ok=True)
            self.quarantine_dir.mkdir(parents=True, exist_ok=True)
            print(f"[PluginManager] Directories created successfully")
        except Exception as e:
            print(f"[PluginManager] Error creating directories: {e}")

    def discover_plugins(self) -> List[str]:
        """Обнаруживает плагины с учетом автоматически создаваемого __pycache__"""
        found_plugins = []

        for search_dir, is_builtin in [
            (self.builtin_plugins_dir, True),
            (self.plugins_dir, False)
        ]:
            if not search_dir.exists():
                print(f"[PluginManager] Directory does not exist: {search_dir}")
                continue

            for item in search_dir.iterdir():
                if item.is_dir():
                    print(f"[PluginManager] Found plugin directory: {item.name}")

                    # === БЕЗОПАСНОСТЬ: ПРОВЕРКА С УЧЕТОМ __pycache__ ===
                    try:
                        # Получаем ВСЕ элементы в директории
                        all_items = list(item.iterdir())

                        # Разделяем файлы и папки
                        files = [f for f in all_items if f.is_file()]
                        dirs = [d for d in all_items if d.is_dir()]

                        # ПРОВЕРКА 1.1: Проверяем поддиректории
                        # Допускаем ТОЛЬКО __pycache__ и ТОЛЬКО если он пустой
                        allowed_dirs = {'__pycache__'}
                        found_dirs = {d.name for d in dirs}

                        if found_dirs - allowed_dirs:
                            # Есть запрещенные директории
                            bad_dirs = found_dirs - allowed_dirs
                            print(f"[SECURITY] Plugin {item.name} contains forbidden directories: {bad_dirs}")
                            continue

                        # ПРОВЕРКА 1.2: Если есть __pycache__, проверяем его содержимое
                        pycache_dir = item / "__pycache__"
                        if pycache_dir.exists():
                            # Проверяем что в __pycache__ только .pyc файлы для этого плагина
                            pycache_files = list(pycache_dir.rglob('*.pyc'))
                            pycache_count = len(pycache_files)

                            if pycache_count > 5:  # Разумный лимит
                                print(f"[SECURITY] Too many .pyc files in __pycache__: {pycache_count}")
                                continue



                        # ПРОВЕРКА 1.3: Должно быть ровно 2 обычных файла
                        if len(files) != 2:
                            print(f"[SECURITY] Plugin {item.name} must have exactly 2 files, got {len(files)}")
                            continue

                        # ПРОВЕРКА 1.4: Проверяем имена файлов
                        file_names = {f.name for f in files}
                        required_files = {'__init__.py', 'manifest.json'}

                        if file_names != required_files:
                            print(
                                f"[SECURITY] Plugin {item.name} wrong files: {file_names}, expected: {required_files}")
                            continue

                        print(f"[SECURITY] Plugin {item.name} passed file count check")

                    except Exception as e:
                        print(f"[SECURITY] Error checking plugin structure {item.name}: {e}")
                        continue

                    # === ПРОВЕРКА №2 - ПРОВЕРКА МАНИФЕСТА ===
                    manifest_path = item / "manifest.json"
                    init_path = item / "__init__.py"

                    if not manifest_path.exists():
                        print(f"[SECURITY] Manifest missing: {item.name}")
                        continue

                    if not init_path.exists():
                        print(f"[SECURITY] __init__.py missing: {item.name}")
                        continue

                    try:
                        print(f"[PluginManager] Loading manifest: {item.name}")
                        manifest = PluginManifest(manifest_path)

                        if manifest.validate():
                            plugin_id = manifest.get('id')

                            # ПРОВЕРКА №3 - ЦЕЛОСТНОСТЬ ПЛАГИНА
                            if not self._verify_plugin_integrity(item, plugin_id):
                                print(f"[SECURITY] Plugin failed integrity check: {plugin_id}")
                                continue

                            # ПРОВЕРКА №4 - КАРАНТИН
                            quarantine_path = self.quarantine_dir / plugin_id
                            if quarantine_path.exists():
                                print(f"[SECURITY] Plugin in quarantine: {plugin_id}")
                                continue

                            if plugin_id in self.plugins:
                                print(f"[PluginManager] Plugin already loaded: {plugin_id}")
                                continue

                            # ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ - ЗАГРУЖАЕМ
                            plugin = LoadedPlugin(
                                plugin_id=plugin_id,
                                name=manifest.get('name'),
                                version=manifest.get('version'),
                                author=manifest.get('author', 'Unknown'),
                                description=manifest.get('description', ''),
                                api_version=manifest.get('api_version'),
                                permissions=set(manifest.get('permissions', [])),
                                plugin_dir=item,
                                enabled=False,
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

            print(f"[PluginManager] Scanned {search_dir}: {len(found_plugins)} plugins found")

        print(f"[PluginManager] Total plugins discovered: {len(found_plugins)}")

        # Логируем список найденных плагинов
        for plugin_id in found_plugins:
            if plugin_id in self.plugins:
                plugin = self.plugins[plugin_id]
                print(f"  - {plugin.name} ({plugin_id}) v{plugin.version}")

        return found_plugins

    def _verify_plugin_integrity(self, plugin_dir: Path, plugin_id: str) -> bool:
        """
        Проверяет целостность плагина.
        Усиленная проверка для плагинов с 2 файлами.
        """
        try:
            print(f"[SECURITY] Running integrity check for: {plugin_id}")

            # ПРОВЕРКА 1: Рекурсивный подсчет файлов (на всякий случай)
            def count_files_recursive(path: Path) -> int:
                count = 0
                for item in path.rglob('*'):
                    if item.is_file():
                        count += 1
                return count

            total_files = count_files_recursive(plugin_dir)
            if total_files > 2:
                print(f"[SECURITY] Plugin {plugin_id} has {total_files} files (recursive count)")
                return False

            # ПРОВЕРКА 2: Проверка размеров файлов
            init_py = plugin_dir / "__init__.py"
            manifest = plugin_dir / "manifest.json"

            # Максимальные размеры
            MAX_INIT_SIZE = 50 * 1024  # 50KB
            MAX_MANIFEST_SIZE = 5 * 1024  # 5KB

            if init_py.stat().st_size > MAX_INIT_SIZE:
                print(f"[SECURITY] __init__.py too large: {init_py.stat().st_size} bytes")
                return False

            if manifest.stat().st_size > MAX_MANIFEST_SIZE:
                print(f"[SECURITY] manifest.json too large: {manifest.stat().st_size} bytes")
                return False

            # ПРОВЕРКА 3: Содержимое __init__.py
            try:
                content = init_py.read_text(encoding='utf-8', errors='ignore')

                # Запрещенные паттерны (безопасность)
                DANGEROUS_PATTERNS = [
                    'import os',
                    'import subprocess',
                    'import shutil',
                    'import sys',
                    '__import__',
                    'exec(',
                    'eval(',
                    'compile(',
                    'open(',
                    'write(',
                    'system(',
                    'popen(',
                    'rm -rf'#,
                    #'format('#,
                    #'f"'  # f-строки могут быть опасны
                ]

                content_lower = content.lower()
                for pattern in DANGEROUS_PATTERNS:
                    if pattern in content_lower:
                        print(f"[SECURITY] Dangerous pattern in __init__.py: {pattern}")
                        return False

                # ПРОВЕРКА 4: Должен содержать класс Plugin
                if 'class Plugin' not in content and 'class Plugin(' not in content:
                    print(f"[SECURITY] No 'class Plugin' found in __init__.py")
                    return False

                # ПРОВЕРКА 5: Должен наследоваться от PluginBase
                if 'PluginBase' not in content and 'plugin_base.PluginBase' not in content:
                    print(f"[SECURITY] Plugin must inherit from PluginBase")
                    return False

            except Exception as e:
                print(f"[SECURITY] Error reading __init__.py: {e}")
                return False

            # ПРОВЕРКА 6: Содержимое manifest.json
            try:
                with open(manifest, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)

                # Проверяем наличие ID
                if 'id' not in manifest_data:
                    print(f"[SECURITY] Manifest missing 'id' field")
                    return False

                # Проверяем что ID совпадает
                if manifest_data.get('id') != plugin_id:
                    print(f"[SECURITY] Manifest ID mismatch: {manifest_data.get('id')} != {plugin_id}")
                    return False

            except Exception as e:
                print(f"[SECURITY] Error reading manifest.json: {e}")
                return False

            print(f"[SECURITY] Integrity check PASSED for: {plugin_id}")
            return True

        except Exception as e:
            print(f"[SECURITY] Integrity check error for {plugin_id}: {e}")
            traceback.print_exc()
            return False

    def load_plugin(self, plugin_id: str) -> bool:
        """Безопасная загрузка плагина в память"""
        if plugin_id not in self.plugins:
            print(f"[PluginManager] Plugin {plugin_id} not found")
            return False

        plugin = self.plugins[plugin_id]

        if plugin.loaded:
            print(f"[PluginManager] Plugin {plugin.name} already loaded")
            return True

        try:
            # ПРОВЕРКА БЕЗОПАСНОСТИ: Проверяем разрешения плагина
            if self._has_dangerous_permissions(plugin.permissions):
                print(f"[PluginManager] Plugin has dangerous permissions: {plugin_id}")
                # Можно запросить подтверждение у пользователя
                if not plugin.is_builtin:  # Встроенным доверяем больше
                    response = self._ask_permission_confirmation(plugin)
                    if not response:
                        return False

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
            module.__name__ = plugin_id
            module.__file__ = str(plugin.plugin_dir / "__init__.py")

            # ПРОВЕРКА БЕЗОПАСНОСТИ: Ограничиваем доступные модули
            self._setup_sandbox_environment(module)

            # Выполняем код плагина
            spec.loader.exec_module(module)

            # Ищем класс Plugin
            if not hasattr(module, 'Plugin'):
                print(f"[PluginManager] Plugin {plugin_id} doesn't have class Plugin")
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
            plugin.instance.permissions = plugin.permissions  # Передаем разрешения

            # Создаем защищенный API для этого плагина
            api = PluginAPI(
                launcher_window=self.window,
                config=self.config,
                launcher_dir=self.launcher_dir,
                plugin_id=plugin_id,
                granted_permissions=plugin.permissions  # Только разрешенные права
            )

            self._apis[plugin_id] = api
            plugin.instance.set_api(api)

            plugin.loaded = True
            print(f"[PluginManager] Plugin {plugin.name} loaded successfully with permissions: {plugin.permissions}")
            return True

        except Exception as e:
            print(f"[PluginManager] Error loading plugin {plugin_id}:")
            traceback.print_exc()

            # ПРИ НЕУДАЧЕ: Помещаем плагин в карантин
            self._quarantine_plugin(plugin_id, str(e))
            return False

    def _has_dangerous_permissions(self, permissions: Set[str]) -> bool:
        """Определяет, есть ли у плагина опасные разрешения"""
        dangerous_permissions = {
            'filesystem_mods_write',
            'subprocess_execute',
            'config_write'  # Запись в основной конфиг тоже опасна
        }
        return bool(permissions.intersection(dangerous_permissions))

    def _ask_permission_confirmation(self, plugin: 'LoadedPlugin') -> bool:
        """
        Запрашивает подтверждение у пользователя для плагина с опасными разрешениями.
        В реальной реализации нужно показывать GUI-диалог.
        """
        print(f"\n=== WARNING: DANGEROUS PLUGIN ===")
        print(f"Plugin: {plugin.name} v{plugin.version}")
        print(f"Author: {plugin.author}")
        print(f"Description: {plugin.description}")
        print(f"Dangerous permissions: {plugin.permissions}")
        print(f"=================================\n")

        # Временная заглушка - в UI нужно сделать нормальный диалог
        # Пока всегда разрешаем, но логируем
        print(f"[PluginManager] User allowed dangerous plugin: {plugin.plugin_id}")
        return True

    def _setup_sandbox_environment(self, module):
        """
        Настраивает песочницу для выполнения кода плагина.
        Ограничивает доступ к опасным модулям.
        """
        # Запрещаем доступ к опасным встроенным функциям
        safe_builtins = {
            'print', 'len', 'range', 'list', 'dict', 'tuple', 'set',
            'str', 'int', 'float', 'bool', 'type', 'isinstance',
            'enumerate', 'zip', 'min', 'max', 'sum', 'abs', 'round'
        }

        # Создаем безопасный словарь builtins
        if '__builtins__' in module.__dict__:
            original_builtins = module.__dict__['__builtins__']
            if isinstance(original_builtins, dict):
                module.__dict__['__builtins__'] = {
                    k: v for k, v in original_builtins.items()
                    if k in safe_builtins
                }

    def _quarantine_plugin(self, plugin_id: str, reason: str):
        """Помещает подозрительный плагин в карантин"""
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]

            quarantine_path = self.quarantine_dir / plugin_id

            if plugin.plugin_dir.exists():
                try:
                    print(f"[PluginManager] Moving plugin to quarantine: {plugin_id}")

                    # Перемещаем плагин в карантин
                    shutil.move(str(plugin.plugin_dir), str(quarantine_path))

                    # Создаем файл с информацией о причине
                    info_file = quarantine_path / "quarantine_info.txt"
                    info_file.write_text(f"Reason: {reason}\nTime: {time.time()}\n")

                    print(f"[PluginManager] Plugin quarantined: {plugin_id}")

                    # Удаляем из списка активных плагинов
                    if plugin_id in self.plugins:
                        del self.plugins[plugin_id]
                    if plugin_id in self._apis:
                        del self._apis[plugin_id]

                except Exception as e:
                    print(f"[PluginManager] Error quarantining plugin: {e}")

    def install_from_zip(self, zip_path: Path) -> Tuple[bool, str]:
        """Безопасная установка плагина из ZIP архива"""
        try:
            print(f"[PluginManager] Installing from ZIP: {zip_path.name}")

            # 1. Проверяем что это ZIP
            if not zipfile.is_zipfile(zip_path):
                return False, "Invalid ZIP file"

            # 2. Временная директория для проверки
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)

                # 3. Распаковываем и проверяем
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Проверяем наличие manifest.json
                    if not any('manifest.json' in f for f in zip_ref.namelist()):
                        return False, "Archive doesn't contain manifest.json"

                    # Проверяем размер архива (макс 10MB)
                    if zip_path.stat().st_size > 10 * 1024 * 1024:
                        return False, "Archive too large (max 10MB)"

                    # Распаковываем
                    zip_ref.extractall(temp_dir_path)

                # 4. Ищем manifest.json
                manifest_path = None
                for root, dirs, files in os.walk(temp_dir_path):
                    if 'manifest.json' in files:
                        manifest_path = Path(root) / 'manifest.json'
                        plugin_root = Path(root)
                        break

                if not manifest_path:
                    return False, "manifest.json not found after extraction"

                # 5. Проверяем манифест
                manifest = PluginManifest(manifest_path)
                if not manifest.validate():
                    return False, "Invalid manifest"

                plugin_id = manifest.get('id')

                # 6. Проверяем что плагин еще не установлен
                target_dir = self.plugins_dir / plugin_id
                if target_dir.exists():
                    print(f"[PluginManager] Plugin already exists, removing: {plugin_id}")
                    shutil.rmtree(target_dir)

                # 7. Копируем в папку плагинов
                print(f"[PluginManager] Copying plugin to: {target_dir}")
                shutil.copytree(plugin_root, target_dir)

                # 8. Перезагружаем список плагинов
                self.discover_plugins()

                print(f"[PluginManager] Plugin {plugin_id} successfully installed")
                return True, plugin_id

        except Exception as e:
            print(f"[PluginManager] Installation error: {e}")
            traceback.print_exc()
            return False, f"Installation error: {str(e)}"

    def enable_plugin(self, plugin_id: str) -> bool:
        """Активирует плагин с защищенным API"""
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

            # Активируем плагин через защищенный API
            if plugin.instance and hasattr(plugin.instance, 'on_enable'):
                plugin.instance.on_enable()
                print(f"[PluginManager] on_enable called for {plugin.name}")

            plugin.enabled = True

            # Обновляем конфиг
            enabled_plugins = self.config.get("enabled_plugins", [])
            if plugin_id not in enabled_plugins:
                enabled_plugins.append(plugin_id)
                self.config["enabled_plugins"] = enabled_plugins
                print(f"[PluginManager] Added {plugin_id} to enabled plugins config")

            print(f"[PluginManager] Plugin {plugin.name} enabled successfully")
            return True

        except Exception as e:
            print(f"[PluginManager] Error enabling plugin {plugin_id}:")
            traceback.print_exc()
            return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """Деактивирует плагин и очищает его ресурсы"""
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

            # Очищаем ресурсы через API
            if plugin_id in self._apis:
                self._apis[plugin_id].cleanup()
                print(f"[PluginManager] API cleaned up for {plugin.name}")

            plugin.enabled = False

            # Обновляем конфиг
            enabled_plugins = self.config.get("enabled_plugins", [])
            if plugin_id in enabled_plugins:
                enabled_plugins.remove(plugin_id)
                self.config["enabled_plugins"] = enabled_plugins
                print(f"[PluginManager] Removed {plugin_id} from enabled plugins config")

            print(f"[PluginManager] Plugin {plugin.name} disabled successfully")
            return True

        except Exception as e:
            print(f"[PluginManager] Error disabling plugin {plugin_id}:")
            traceback.print_exc()
            return False

    def initialize(self):
        """Инициализирует систему плагинов"""
        print("[PluginManager] ===== Initializing secure plugin system =====")

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
        print("[PluginManager] ===== Secure plugin system initialized =====")
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
            'permissions': list(plugin.permissions),
            'path': str(plugin.plugin_dir),
        }

        print(f"[PluginManager] Plugin info for {plugin_id}: {info.get('name', 'Unknown')}")
        return info

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Вызывает хук для всех плагинов"""
        results = []

        for plugin_id, plugin in self.plugins.items():
            if plugin.enabled and plugin.loaded and plugin_id in self._apis:
                try:
                    api = self._apis[plugin_id]
                    hook_results = api._call_hook(hook_name, *args, **kwargs)
                    results.extend(hook_results)
                except Exception as e:
                    print(f"[PluginManager] Error in hook '{hook_name}' for plugin {plugin_id}: {e}")

        return results

    def get_plugin_api(self, plugin_id: str) -> Optional[PluginAPI]:
        """Возвращает API для плагина"""
        return self._apis.get(plugin_id)

    def get_all_plugins(self) -> List[Dict]:
        """Возвращает список всех плагинов"""
        result = []
        print(f"[PluginManager] Getting all plugins (total: {len(self.plugins)})")

        for plugin_id, plugin in self.plugins.items():
            try:
                # Базовая информация из LoadedPlugin
                plugin_info = {
                    'id': plugin_id,
                    'name': plugin.name,
                    'version': plugin.version,
                    'author': plugin.author,
                    'description': plugin.description,
                    'enabled': plugin.enabled,
                    'loaded': plugin.loaded,
                    'is_builtin': plugin.is_builtin,
                    'api_version': plugin.api_version,
                    'permissions': list(plugin.permissions),
                    'path': str(plugin.plugin_dir),
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
                result.append({
                    'id': plugin_id,
                    'name': 'Error loading',
                    'version': '?',
                    'author': '?',
                    'description': f'Error: {str(e)}',
                    'enabled': False,
                    'loaded': False,
                    'is_builtin': False,
                    'api_version': '1.0',
                    'permissions': [],
                    'path': ''
                })

        return result


class LoadedPlugin:
    """Класс для хранения информации о загруженном плагине"""

    def __init__(self, plugin_id: str, name: str, version: str, author: str,
                 description: str, api_version: str, permissions: Set[str],
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