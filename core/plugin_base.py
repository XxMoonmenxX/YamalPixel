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
        """Проверяет валидность манифеста с фокусом на безопасности"""
        try:
            # 1. Проверяем наличие всех обязательных полей
            for field in self.REQUIRED_FIELDS:
                if field not in self.data:
                    print(f"[PluginManifest] Отсутствует обязательное поле: {field}")
                    return False

            # 2. Валидация ID плагина
            plugin_id = self.data['id']
            if not isinstance(plugin_id, str):
                return False
            if not plugin_id.strip():
                return False
            # Только латинские буквы, цифры, - и _
            if not all(c.isalnum() or c in '-_' for c in plugin_id):
                return False
            if len(plugin_id) > 50:
                return False

            # 3. Валидация разрешений[citation:6]
            permissions = self.data.get('permissions', [])
            if not isinstance(permissions, list):
                return False

            # Допустимые разрешения (должны совпадать с PluginAPI.PERMISSIONS)
            valid_permissions = {
                'ui_button', 'ui_notification', 'config_read', 'config_write',
                'filesystem_read', 'filesystem_mods_write', 'filesystem_config_write',
                'hook_registration'
            }

            for perm in permissions:
                if perm not in valid_permissions:
                    print(f"[PluginManifest] Неизвестное разрешение: {perm}")
                    return False

            # 4. Валидация версии API
            api_version = self.data['api_version']
            if not isinstance(api_version, str):
                return False
            # Поддерживаем только версию 1.1 (с системой разрешений)
            if api_version != "1.1":
                print(f"[PluginManifest] Неподдерживаемая версия API: {api_version}")
                return False

            # 5. Валидация автора (опционально)
            author = self.data.get('author', '')
            if author and len(author) > 100:
                return False

            print(f"[PluginManifest] Манифест валиден: {self.data['name']}")
            return True

        except Exception as e:
            print(f"[PluginManifest] Ошибка валидации: {e}")
            return False

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