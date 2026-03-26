# Core/backup.py
import os
import shutil
import zipfile
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger("YamalPixel.Backup")


class ModsBackupManager:
    """Менеджер бэкапов модов"""

    def __init__(self, minecraft_dir: str):
        self.minecraft_dir = minecraft_dir
        self.mods_dir = os.path.join(minecraft_dir, "mods")
        self.backup_dir = os.path.join(minecraft_dir, "backups")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Создаёт необходимые папки"""
        os.makedirs(self.mods_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, backup_name: str = None) -> Optional[str]:
        """
        Создаёт бэкап всех текущих модов
        Возвращает путь к бэкапу или None при ошибке
        """
        if not os.path.exists(self.mods_dir):
            logger.info("📁 Папка mods не существует, бэкап не требуется")
            return None

        # Получаем список jar-файлов
        mod_files = [f for f in os.listdir(self.mods_dir) if f.endswith('.jar')]
        if not mod_files:
            logger.info("📦 Папка mods пуста, бэкап не требуется")
            return None

        # Создаём имя бэкапа
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"mods_backup_{timestamp}"

        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")

        logger.info(f"📦 Создаём бэкап: {backup_name} ({len(mod_files)} модов)")

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for mod_file in mod_files:
                    file_path = os.path.join(self.mods_dir, mod_file)
                    zipf.write(file_path, mod_file)

            logger.info(f"✅ Бэкап создан: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"❌ Ошибка создания бэкапа: {e}")
            return None

    def restore_backup(self, backup_filename: str) -> bool:
        """
        Восстанавливает бэкап
        """
        backup_path = os.path.join(self.backup_dir, backup_filename)
        if not os.path.exists(backup_path):
            logger.error(f"❌ Бэкап не найден: {backup_filename}")
            return False

        # Очищаем папку mods
        self.clear_mods()

        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.mods_dir)

            logger.info(f"✅ Бэкап восстановлен: {backup_filename}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления бэкапа: {e}")
            return False

    def clear_mods(self) -> int:
        """
        Очищает папку mods
        Возвращает количество удалённых файлов
        """
        if not os.path.exists(self.mods_dir):
            return 0

        count = 0
        for filename in os.listdir(self.mods_dir):
            if filename.endswith('.jar'):
                try:
                    os.remove(os.path.join(self.mods_dir, filename))
                    count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить {filename}: {e}")

        logger.info(f"🗑️ Удалено {count} модов")
        return count

    def get_backups_list(self) -> List[Dict]:
        """
        Возвращает список доступных бэкапов
        """
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups

        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.zip') and filename.startswith('mods_backup_'):
                file_path = os.path.join(self.backup_dir, filename)
                stat = os.stat(file_path)

                # Извлекаем дату из имени или из mtime
                try:
                    # Формат: mods_backup_20250101_120000.zip
                    date_str = filename.replace('mods_backup_', '').replace('.zip', '')
                    if '_' in date_str:
                        date_part, time_part = date_str.split('_')
                        date = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                    else:
                        date = datetime.fromtimestamp(stat.st_mtime)
                except:
                    date = datetime.fromtimestamp(stat.st_mtime)

                backups.append({
                    'filename': filename,
                    'size_mb': stat.st_size / (1024 * 1024),
                    'date': date,
                    'date_str': date.strftime("%d.%m.%Y %H:%M:%S")
                })

        # Сортируем по дате (новые сверху)
        backups.sort(key=lambda x: x['date'], reverse=True)
        return backups

    def delete_backup(self, backup_filename: str) -> bool:
        """
        Удаляет бэкап
        """
        backup_path = os.path.join(self.backup_dir, backup_filename)
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
                logger.info(f"🗑️ Удалён бэкап: {backup_filename}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка удаления бэкапа: {e}")
                return False
        return False

    def delete_all_backups(self) -> int:
        """
        Удаляет все бэкапы
        """
        count = 0
        for backup in self.get_backups_list():
            if self.delete_backup(backup['filename']):
                count += 1
        logger.info(f"🗑️ Удалено {count} бэкапов")
        return count