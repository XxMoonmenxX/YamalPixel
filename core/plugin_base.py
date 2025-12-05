"""
БЕЗОПАСНЫЙ базовый класс для плагинов YamalPixel
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from abc import ABC, abstractmethod
import hashlib


class PluginBase(ABC):
    """Безопасный базовый класс плагина с проверкой разрешений"""

    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.version: str = ""
        self.author: str = ""
        self.description: str = ""
        self.api_version: str = "1.1"  # Обновленная версия API
        self.enabled: bool = False
        self.permissions: Set[str] = set()  # Разрешения этого плагина[citation:6]

        self.plugin_dir: Optional[Path] = None
        self.manifest: Dict[str, Any] = {}
        self.api: Optional[Any] = None  # Безопасный PluginAPI

    @abstractmethod
    def on_enable(self):
        """Вызывается при активации плагина"""
        pass

    @abstractmethod
    def on_disable(self):
        """Вызывается при деактивации плагина"""
        pass

    def set_api(self, api):
        """Устанавливает защищенный API для плагина"""
        self.api = api

    def get_config_path(self) -> Path:
        """Возвращает путь к конфигу плагина (в его собственной папке)"""
        if self.plugin_dir:
            return self.plugin_dir / "config.json"
        raise RuntimeError("Plugin directory not set")

    def load_config(self, default_config: Dict = None) -> Dict:
        """Загружает конфигурацию плагина"""
        config_path = self.get_config_path()

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[{self.name}] Ошибка загрузки конфига: {e}")

        return default_config or {}

    def save_config(self, config: Dict):
        """Сохраняет конфигурацию плагина (только свою)"""
        config_path = self.get_config_path()

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{self.name}] Ошибка сохранения конфига: {e}")


class PluginManifest:
    """Класс для работы с манифестом плагина с проверкой безопасности"""

    REQUIRED_FIELDS = ['name', 'id', 'version', 'api_version', 'permissions']  # Добавлено permissions!

    def __init__(self, manifest_path: Path):
        self.path = manifest_path
        self.data: Dict[str, Any] = {}

        if manifest_path.exists():
            self.load()

    def load(self):
        """Загружает манифест из файла"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            raise ValueError(f"Не удалось загрузить манифест: {e}")

    def validate(self) -> bool:
        """Проверяет, что плагин имеет максимум 2 файла"""
        plugin_dir = self.path.parent

        # 1. Считаем файлы в директории плагина
        all_files = list(plugin_dir.iterdir())

        # 2. Допускаем только 2 файла: __init__.py и manifest.json
        if len(all_files) > 2:
            print(f"[SECURITY] Plugin has {len(all_files)} files, max allowed: 2")
            return False

        # 3. Проверяем обязательные файлы
        required_files = {'__init__.py', 'manifest.json'}
        actual_files = {f.name for f in all_files}

        if not required_files.issubset(actual_files):
            print(f"[SECURITY] Missing required files. Have: {actual_files}, Need: {required_files}")
            return False

        # 4. Запрещаем поддиректории
        if any(f.is_dir() for f in all_files):
            print(f"[SECURITY] Subdirectories are not allowed")
            return False

        # 5. Запрещаем любые другие файлы кроме разрешенных двух
        if actual_files - required_files:
            print(f"[SECURITY] Extra files not allowed: {actual_files - required_files}")
            return False

        print(f"[PluginManifest] Plugin structure OK: {actual_files}")
        return True

    def get(self, key: str, default=None):
        """Получает значение из манифеста"""
        return self.data.get(key, default)

    def calculate_hash(self) -> str:
        """Вычисляет хэш манифеста для проверки целостности"""
        try:
            content = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        except:
            return ""