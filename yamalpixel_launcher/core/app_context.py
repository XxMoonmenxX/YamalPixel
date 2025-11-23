# core/app_context.py
import json
import sys
import os
import time
import signal
from pathlib import Path

import tkinter as tk
from ttkthemes import ThemedTk

# Импортируем твои модули
from utils.config import Config
from utils.session import load_last_session, save_last_session
from core.minecraft_manager import MinecraftManager
from core.mod_manager import ModManager
from core.java_manager import JavaManager
from core.launcher import MinecraftLauncher
from core.updater import Updater
from core.resource_manager import ResourceManager
from core.backup_manager import BackupManager
from core.collection_manager import CollectionManager


class LauncherApp:
    def __init__(self):
        self.root = None
        self.config = None
        self.minecraft_manager = None
        self.mod_manager = None
        self.java_manager = None
        self.launcher = None
        self.updater = None
        self.resource_manager = None
        self.backup_manager = None
        self.collection_manager = None

        # Состояния из оригинального кода
        self.LAUNCH_IN_PROGRESS = False
        self.LAUNCH_START_TIME = None

    def initialize(self):
        """Инициализация всех компонентов"""
        try:
            # Создаем главное окно
            self.root = ThemedTk(theme="arc")
            self.root.geometry("1920x1080")
            self.root.title("YamPixel")

            # Инициализируем конфиг
            self.config = Config()

            # Инициализируем менеджеры
            self.minecraft_manager = MinecraftManager(self.config)
            self.mod_manager = ModManager(self.config)
            self.java_manager = JavaManager(self.config)
            self.launcher = MinecraftLauncher(self.config, self.java_manager, self.mod_manager)
            self.updater = Updater(self.config)
            self.resource_manager = ResourceManager(self.config)
            self.backup_manager = BackupManager(self.config)
            self.collection_manager = CollectionManager(self.config)

            return True

        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False

    def run(self):
        """Запуск приложения"""
        if not self.initialize():
            return

        # Загружаем сессию
        session_data = load_last_session()
        if session_data:
            self.apply_session_settings(session_data)

        # Импортируем и создаем UI (чтобы избежать циклических импортов)
        from gui.main_window import MainWindow
        self.ui = MainWindow(self.root, self)
        self.ui.setup_ui()

        # Проверка обновлений в фоне
        self.updater.check_for_updates_async()

        # Проверка Java при старте
        self.java_manager.check_on_startup()

        # Запускаем главный цикл
        self.root.mainloop()

    def graceful_shutdown(self, signum=None, frame=None):
        """Корректное завершение работы"""
        print("💾 Сохраняем настройки...")
        save_last_session(self.get_session_data())

        # Останавливаем музыку если играет
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass

        if self.root:
            self.root.destroy()
        sys.exit(0)

    def get_session_data(self):
        """Собирает данные для сохранения сессии"""
        session = {}

        # Сохраняем имя пользователя из UI
        if hasattr(self, 'ui') and hasattr(self.ui, 'username'):
            current_username = self.ui.username.get()
            if current_username and current_username != "Введите никнейм":
                session["username"] = current_username

        # Сохраняем выбранную версию
        if hasattr(self, 'ui') and hasattr(self.ui, 'version_selector'):
            current_version = self.ui.version_selector.get()
            if current_version:
                session["version"] = current_version

        # Сохраняем настройки памяти
        session["memory"] = self.config.get("jvm_memory", "4G")

        # Сохраняем другие настройки
        if hasattr(self, 'ui'):
            if hasattr(self.ui, 'enabled'):
                session["fullscreen"] = bool(self.ui.enabled.get())
            if hasattr(self.ui, 'enabled1'):
                session["music"] = bool(self.ui.enabled1.get())

        session["launcher_version"] = self.config.get("launcher_version", "0.6.61")
        return session

    def apply_session_settings(self, session_data):
        """Применяет настройки из сессии"""
        print("🔄 Восстанавливаем предыдущую сессию...")

        # Применяем настройки после полной инициализации UI
        def apply_after_ui():
            try:
                # Восстанавливаем имя пользователя
                if "username" in session_data and hasattr(self.ui, 'username'):
                    self.ui.username.text_value.set(session_data["username"])
                    self.ui.username.entry.configure(fg="#2b2b2b")
                    print(f"👤 Восстановлен ник: {session_data['username']}")

                # Восстанавливаем версию
                if "version" in session_data and hasattr(self.ui, 'version_selector'):
                    target_version = session_data["version"]
                    self.ui.version_selector.current_value.set(target_version)
                    self.ui.version_selector.draw_selector()
                    print(f"🎯 Восстановлена версия: {target_version}")

                # Восстанавливаем память
                if "memory" in session_data:
                    self.config.set("jvm_memory", session_data["memory"])
                    print(f"💾 Восстановлена память: {session_data['memory']}")

                # Восстанавливаем полноэкранный режим
                if "fullscreen" in session_data and session_data["fullscreen"] and hasattr(self.ui, 'enabled'):
                    self.ui.enabled.set(True)
                    self.ui.fullsc()
                    print("🖥️ Восстановлен полноэкранный режим")

                # Восстанавливаем музыку
                if "music" in session_data and session_data["music"] and hasattr(self.ui, 'enabled1'):
                    self.ui.enabled1.set(True)
                    self.ui.mscon()
                    print("🎵 Восстановлена музыка")

            except Exception as e:
                print(f"⚠️ Не удалось применить некоторые настройки: {e}")

        # Запускаем после полной инициализации UI
        self.root.after(3000, apply_after_ui)