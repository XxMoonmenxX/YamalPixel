## Core/backup.py
import os
import shutil
import zipfile
import tempfile
from Core.mod_transaction import safe_filename, safe_target, replace_mods
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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"mods_backup_{timestamp}"

        backup_path = safe_target(self.backup_dir, f"{backup_name}.zip")

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
        backup_path = safe_target(self.backup_dir, backup_filename)
        if not os.path.exists(backup_path):
            logger.error(f"❌ Бэкап не найден: {backup_filename}")
            return False

        try:
            with tempfile.TemporaryDirectory(prefix='.mods-restore-', dir=self.minecraft_dir) as staging:
                prepared = os.path.join(staging, 'mods')
                os.makedirs(prepared)
                with zipfile.ZipFile(backup_path) as archive:
                    if archive.testzip() is not None:
                        raise ValueError("Повреждённый архив")
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        target = safe_target(prepared, member.filename)
                        if not member.filename.lower().endswith('.jar'):
                            raise ValueError("Архив содержит файл, не являющийся модом")
                        with archive.open(member) as source, open(target, 'wb') as output:
                            shutil.copyfileobj(source, output)
                # Keep configuration files outside the backup's JAR-only scope.
                for entry in os.scandir(self.mods_dir):
                    if not entry.name.lower().endswith('.jar'):
                        target = os.path.join(prepared, entry.name)
                        if entry.is_dir():
                            shutil.copytree(entry.path, target)
                        else:
                            shutil.copy2(entry.path, target)
                replace_mods(prepared, self.mods_dir, os.path.join(staging, 'previous'))
            return True
        except Exception as e:
            logger.error("Ошибка восстановления, текущие моды сохранены: %s", e)
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
        backup_path = safe_target(self.backup_dir, backup_filename)
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