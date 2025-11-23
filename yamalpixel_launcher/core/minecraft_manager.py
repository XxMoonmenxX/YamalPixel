# core/minecraft_manager.py
import os
import minecraft_launcher_lib
from pathlib import Path
from utils.logging_utils import logger

class MinecraftManager:
    def __init__(self, config_instance):
        self.config = config_instance
        self.minecraft_dir = Path(self.config.get("minecraft_dir"))
        self.version = self.config.get("version")
        self.fabric_loader = self.config.get("fabric_loader")

    def setup_minecraft_directory(self):
        """Создает основные поддиректории .minecraft, если они не существуют."""
        required_dirs = ["mods", "versions", "config", "shaderpacks", "worlds"]
        for dir_name in required_dirs:
            dir_path = self.minecraft_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Проверена/создана директория: {dir_path}")

    def select_minecraft_version(self, version_string):
        """Обновляет выбранную версию в конфиге и, возможно, проверяет/устанавливает её."""
        self.config.set("version", version_string)
        # Здесь можно добавить логику проверки, установки версии через minecraft_launcher_lib
        logger.info(f"Выбрана версия Minecraft: {version_string}")
        # self.install_version_if_needed(version_string) # Пример вызова

    def select_fabric_loader(self, loader_version):
        """Обновляет выбранную версию Fabric Loader в конфиге."""
        self.config.set("fabric_loader", loader_version)
        logger.info(f"Выбран Fabric Loader: {loader_version}")

    def is_fabric_needed(self, selected_version):
        """Проверяет, требуется ли Fabric для выбранной версии."""
        fabric_supported_versions = [
            "YamalPixel", # Пример
            "Minecraft 1.14.4 + Fabric",
            "Minecraft 1.15.2 + Fabric",
            "Minecraft 1.16.5 + Fabric",
            "Minecraft 1.17.1 + Fabric",
            "Minecraft 1.18.2 + Fabric",
            "Minecraft 1.19.2 + Fabric",
            "Minecraft 1.20.1 + Fabric",
            # ... добавить другие версии с Fabric
        ]
        return selected_version in fabric_supported_versions

    def check_fabric_installed(self):
        """Проверяет, установлен ли нужный Fabric Loader для текущей версии."""
        if not self.is_fabric_needed(self.config.get("version")):
            logger.debug("Fabric не требуется для выбранной версии.")
            return True # Fabric не нужен -> считаем, что установлен

        fabric_version = f"fabric-loader-{self.config.get('fabric_loader')}-{self.config.get('version')}"
        fabric_version_dir = self.minecraft_dir / "versions" / fabric_version

        if fabric_version_dir.exists():
            logger.info(f"Fabric {fabric_version} уже установлен.")
            return True
        else:
            logger.warning(f"Fabric {fabric_version} не установлен.")
            return False

    def install_fabric_if_needed(self):
        """Устанавливает Fabric Loader, если он нужен и не установлен."""
        if self.is_fabric_needed(self.config.get("version")) and not self.check_fabric_installed():
            logger.info(f"Установка Fabric Loader {self.config.get('fabric_loader')} для версии {self.config.get('version')}")
            try:
                # Используем библиотеку для установки
                minecraft_launcher_lib.fabric.install_fabric(
                    versionid=self.config.get("version"),
                    minecraft_directory=str(self.minecraft_dir),
                    loader_version=self.config.get("fabric_loader")
                )
                logger.info(f"Fabric Loader успешно установлен.")
                return True
            except Exception as e:
                logger.error(f"Ошибка установки Fabric: {e}")
                return False
        return True # Уже установлен или не нужен

    def install_version_if_needed(self, version):
        """Устанавливает версию Minecraft, если она не установлена."""
        logger.info(f"Проверка установки версии Minecraft: {version}")
        try:
            # minecraft_launcher_lib проверит и установит, если нужно
            # Пока что используем простую проверку через наличие папки версии
            version_dir = self.minecraft_dir / "versions" / version
            if not version_dir.exists():
                 logger.info(f"Установка версии Minecraft: {version}")
                 # minecraft_launcher_lib.install.install_minecraft_version(
                 #    versionid=version,
                 #    minecraft_directory=str(self.minecraft_dir)
                 # )
                 # ^ Реальная установка требует callback для прогресса, что лучше делать в UI
                 # или в отдельной задаче. Для простоты пока просто проверяем.
                 print(f"Папка версии {version} не найдена. Требуется установка через minecraft_launcher_lib.")
                 return False # Сигнализируем, что нужно установить
            else:
                 logger.info(f"Версия Minecraft {version} уже установлена.")
                 return True
        except Exception as e:
            logger.error(f"Ошибка проверки/установки версии {version}: {e}")
            return False

    def get_minecraft_directory(self):
        """Возвращает путь к .minecraft директории."""
        return self.minecraft_dir

    def get_current_version(self):
        """Возвращает текущую выбранную версию Minecraft."""
        return self.config.get("version")

    def get_current_fabric_loader(self):
        """Возвращает текущую выбранную версию Fabric Loader."""
        return self.config.get("fabric_loader")
