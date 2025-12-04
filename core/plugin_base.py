"""
Базовый класс для всех плагинов YamalPixel
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class PluginBase(ABC):
    """Абстрактный базовый класс плагина"""

    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.version: str = ""
        self.author: str = ""
        self.description: str = ""
        self.api_version: str = "1.0"
        self.enabled: bool = False

        self.plugin_dir: Optional[Path] = None
        self.manifest: Dict[str, Any] = {}
        self.api: Optional[Any] = None  # PluginAPI будет установлен позже

    @abstractmethod
    def on_enable(self):
        """Вызывается при активации плагина"""
        pass

    @abstractmethod
    def on_disable(self):
        """Вызывается при деактивации плагина"""
        pass

    def set_api(self, api):
        """Устанавливает API для плагина"""
        print(f"[{self.name}] API установлен")  # Для отладки
        self.api = api

    def get_config_path(self) -> Path:
        """Возвращает путь к конфигу плагина"""
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
            except Exception:
                pass

        # Возвращаем конфиг по умолчанию
        return default_config or {}

    def save_config(self, config: Dict):
        """Сохраняет конфигурацию плагина"""
        config_path = self.get_config_path()

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{self.name}] Ошибка сохранения конфига: {e}")


class PluginManifest:
    """Класс для работы с манифестом плагина"""

    REQUIRED_FIELDS = ['name', 'id', 'version', 'api_version']

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
        """Проверяет валидность манифеста - УЛУЧШЕННАЯ ВЕРСИЯ"""
        try:
            # Проверяем наличие всех обязательных полей
            for field in self.REQUIRED_FIELDS:
                if field not in self.data:
                    print(f"[PluginManifest] Отсутствует поле: {field}")
                    return False

            # Проверяем тип полей
            name = self.data.get('name')
            plugin_id = self.data.get('id')
            version = self.data.get('version')

            if not isinstance(name, str):
                print(f"[PluginManifest] Поле 'name' не строка: {type(name)}")
                return False

            if not isinstance(plugin_id, str):
                print(f"[PluginManifest] Поле 'id' не строка: {type(plugin_id)}")
                return False

            if not isinstance(version, str):
                print(f"[PluginManifest] Поле 'version' не строка: {type(version)}")
                return False

            # Проверяем что ID не пустой
            if not plugin_id.strip():
                print("[PluginManifest] ID плагина пустой")
                return False

            # Проверяем формат ID (только латинские буквы, цифры, - и _)
            if not all(c.isalnum() or c in '-_' for c in plugin_id):
                print(f"[PluginManifest] ID содержит недопустимые символы: {plugin_id}")
                return False

            # Проверяем что версия не пустая
            if not version.strip():
                print("[PluginManifest] Версия плагина пустая")
                return False

            print(f"[PluginManifest] Манифест валиден: {name} ({plugin_id}) v{version}")
            return True

        except Exception as e:
            print(f"[PluginManifest] Ошибка валидации: {e}")
            return False

    def get(self, key: str, default=None):
        """Получает значение из манифеста"""
        return self.data.get(key, default)