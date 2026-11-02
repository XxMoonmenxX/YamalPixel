"""Create and restore safe backups of an instance's mutable game data."""

from __future__ import annotations

import logging
import os
import shutil
import stat
import tempfile
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from Core.mod_transaction import safe_filename, safe_target

logger = logging.getLogger("YamalPixel.Backup")


class BackupCancelled(Exception):
    """The backup operation was cancelled before its changes were committed."""


class BackupCancelToken:
    """Synchronize a cancellation request with the final commit point."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cancelled = False
        self._committed = False

    def cancel(self):
        with self._lock:
            if self._committed:
                return False
            self._cancelled = True
            return True

    def check(self):
        with self._lock:
            if self._cancelled:
                raise BackupCancelled('Операция с бэкапом отменена')

    def commit(self, action=None):
        with self._lock:
            if self._cancelled:
                raise BackupCancelled('Операция с бэкапом отменена')
            self._committed = True
        # Once sealed, cancellation is rejected; do not block the UI on I/O.
        if action is not None:
            action()


def _check_cancel(cancel_token):
    if cancel_token is not None:
        cancel_token.check()


def _safe_progress(callback):
    if callback is None:
        return None

    def report(percent, message):
        try:
            callback(percent, message)
        except Exception:
            logger.exception("Не удалось обновить прогресс бэкапа")

    return report


class _ProgressReader:
    """Report bytes read while retaining the usual file-like read interface."""

    def __init__(self, source, callback, cancel_token=None):
        self.source = source
        self.callback = callback
        self.cancel_token = cancel_token

    def read(self, size=-1):
        _check_cancel(self.cancel_token)
        data = self.source.read(size)
        _check_cancel(self.cancel_token)
        if data:
            self.callback(len(data))
            _check_cancel(self.cancel_token)
        return data


class _ByteProgress:
    def __init__(self, total, callback):
        self.total = total
        self.callback = callback
        self.done = 0
        self.last_percent = -1
        self.message = ""

    def advance(self, count):
        self.done += count
        percent = min(95, self.done * 95 // max(self.total, 1))
        if self.callback and percent != self.last_percent:
            self.last_percent = percent
            self.callback(percent, self.message)


class ModsBackupManager:
    """Manage backups of the mods, worlds and configuration of an instance.

    Archives use explicit top-level mods/, saves/ and config/ directories.
    Older backups containing JAR files directly at the archive root are accepted.
    """

    BACKUP_SECTIONS = ("mods", "saves", "config")
    MAX_MEMBERS = 50_000
    MAX_MEMBER_SIZE = 4 * 1024 * 1024 * 1024
    MAX_TOTAL_SIZE = 64 * 1024 * 1024 * 1024

    def __init__(self, minecraft_dir: str):
        self.minecraft_dir = os.path.abspath(os.fspath(minecraft_dir))
        self.mods_dir = os.path.join(self.minecraft_dir, "mods")
        self.backup_dir = os.path.join(self.minecraft_dir, "backups")
        self.last_error = None
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(self.minecraft_dir, exist_ok=True)
        if Path(self.minecraft_dir).is_symlink():
            raise ValueError("Папка инстанса не должна быть символической ссылкой")
        if Path(self.mods_dir).is_symlink():
            raise ValueError("Папка mods не должна быть символической ссылкой")
        if Path(self.backup_dir).is_symlink():
            raise ValueError("Папка бэкапов не должна быть символической ссылкой")
        os.makedirs(self.mods_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def _files_to_backup(self, cancel_token=None) -> List[Tuple[str, str, str]]:
        result: List[Tuple[str, str, str]] = []

        def walk_error(error):
            raise error

        def is_link(path):
            return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())

        for section in self.BACKUP_SECTIONS:
            _check_cancel(cancel_token)
            root = Path(self.minecraft_dir) / section
            if is_link(root):
                raise ValueError(f"Папка {section} является ссылкой и не может быть включена в бэкап")
            if not root.exists():
                continue
            if not root.is_dir():
                raise ValueError(f"{section} не является папкой")
            for current, dirs, files in os.walk(root, topdown=True, followlinks=False, onerror=walk_error):
                _check_cancel(cancel_token)
                current_path = Path(current)
                for name in dirs:
                    if is_link(current_path / name):
                        raise ValueError(f"Бэкап содержит ссылку: {current_path / name}")
                for filename in files:
                    _check_cancel(cancel_token)
                    source = current_path / filename
                    if is_link(source) or not stat.S_ISREG(source.stat().st_mode):
                        raise ValueError(f"Бэкап содержит неподдерживаемый файл: {source}")
                    relative = source.relative_to(root).as_posix()
                    for part in relative.split('/'):
                        safe_filename(part)
                    result.append((section, str(source), f"{section}/{relative}"))
        return result

    def create_backup(self, backup_name: str = None, progress_callback=None,
                      cancel_token=None) -> Optional[str]:
        """Report (percent, status); cancellation raises BackupCancelled after cleanup."""
        self.last_error = None
        progress_callback = _safe_progress(progress_callback)
        temporary_path = None
        try:
            _check_cancel(cancel_token)
            if progress_callback:
                progress_callback(0, "Подготовка файлов для бэкапа…")
            entries = self._files_to_backup(cancel_token)
            _check_cancel(cancel_token)
            if not entries:
                logger.info("Папки mods, saves и config пусты, бэкап не требуется")
                return None
            sections = [section for section in self.BACKUP_SECTIONS
                        if (Path(self.minecraft_dir) / section).is_dir()
                        and not (Path(self.minecraft_dir) / section).is_symlink()]
            if len(entries) + len(sections) > self.MAX_MEMBERS:
                raise ValueError("Слишком много файлов для бэкапа")
            sizes = []
            for _section, source, _name in entries:
                _check_cancel(cancel_token)
                sizes.append(os.path.getsize(source))
            if any(size > self.MAX_MEMBER_SIZE for size in sizes):
                raise ValueError("Файл слишком большой для бэкапа")
            total_size = sum(sizes)
            if total_size > self.MAX_TOTAL_SIZE:
                raise ValueError("Общий объём файлов слишком большой для бэкапа")
            progress = _ByteProgress(total_size, progress_callback)
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                backup_name = f"mods_backup_{timestamp}"
            backup_path = safe_target(self.backup_dir, f"{backup_name}.zip")
            fd, temporary_path = tempfile.mkstemp(prefix=".backup-", suffix=".tmp", dir=self.backup_dir)
            os.close(fd)
            logger.info("Создаём бэкап: %s (%d файлов)", backup_name, len(entries))
            with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for section in sections:
                    _check_cancel(cancel_token)
                    archive.writestr(f"{section}/", b"")
                for _section, source, archive_name in entries:
                    _check_cancel(cancel_token)
                    progress.message = f"Архивирование: {archive_name}"
                    info = zipfile.ZipInfo.from_file(source, archive_name)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    with open(source, "rb") as source_file, archive.open(info, "w", force_zip64=True) as output:
                        shutil.copyfileobj(_ProgressReader(source_file, progress.advance, cancel_token),
                                           output, 1024 * 1024)
            if progress_callback:
                progress_callback(95, "Завершение создания бэкапа…")
            if cancel_token is None:
                os.replace(temporary_path, backup_path)
            else:
                cancel_token.commit(lambda: os.replace(temporary_path, backup_path))
            temporary_path = None
            if progress_callback:
                progress_callback(100, "Бэкап создан")
            logger.info("Бэкап создан: %s", backup_path)
            return backup_path
        except BackupCancelled:
            logger.info("Создание бэкапа отменено")
            raise
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Ошибка создания бэкапа: %s", exc)
            return None
        finally:
            if temporary_path:
                try:
                    os.remove(temporary_path)
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    raise OSError(f"Не удалось удалить временный бэкап: {temporary_path}") from exc

    @staticmethod
    def _is_symlink_member(member: zipfile.ZipInfo) -> bool:
        # Unix file type bits are stored in the upper half of external_attr.
        return ((member.external_attr >> 16) & 0o170000) == 0o120000

    @classmethod
    def _member_parts(cls, filename: str, is_directory: bool) -> Tuple[str, ...]:
        """Validate and normalize a ZIP member path."""
        if not isinstance(filename, str) or "\x00" in filename:
            raise ValueError("Архив содержит недопустимое имя файла")
        normalized = filename.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../"):
            raise ValueError("Архив содержит небезопасный путь")
        raw_parts = normalized.split("/")
        if is_directory and raw_parts and raw_parts[-1] == "":
            raw_parts.pop()
        if not raw_parts or any(part in ("", ".", "..") for part in raw_parts):
            raise ValueError("Архив содержит небезопасный путь")
        for part in raw_parts:
            safe_filename(part)
        return tuple(raw_parts)

    @classmethod
    def _validate_archive(cls, archive: zipfile.ZipFile, cancel_token=None) -> int:
        """Validate ZIP members and return declared uncompressed size."""
        members = archive.infolist()
        if len(members) > cls.MAX_MEMBERS:
            raise ValueError("Архив содержит слишком много файлов")
        total_size = 0
        seen = set()
        supported = 0
        for member in members:
            _check_cancel(cancel_token)
            if cls._is_symlink_member(member):
                raise ValueError("Архив содержит символическую ссылку")
            parts = cls._member_parts(member.filename, member.is_dir())
            if member.is_dir() and member.file_size:
                raise ValueError("Некорректная папка в архиве")
            if member.file_size > cls.MAX_MEMBER_SIZE:
                raise ValueError("Файл в архиве слишком большой")
            total_size += member.file_size
            if total_size > cls.MAX_TOTAL_SIZE:
                raise ValueError("Объём архива после распаковки слишком большой")

            if len(parts) == 1 and parts[0].lower().endswith(".jar") and not member.is_dir():
                key = ("mods", parts[0].casefold())  # legacy format
                supported += 1
            elif parts[0] in cls.BACKUP_SECTIONS:
                if len(parts) == 1 and not member.is_dir():
                    raise ValueError("Папка бэкапа имеет неверный формат")
                key = tuple(parts)
                if not member.is_dir():
                    supported += 1
            else:
                raise ValueError("Архив содержит неизвестную папку")
            if key in seen:
                raise ValueError("Архив содержит повторяющийся путь")
            seen.add(key)
        if not supported:
            raise ValueError("Архив не содержит данных mods, saves или config")
        return total_size

    @classmethod
    def _extract_to_staging(cls, archive: zipfile.ZipFile, destination: Path,
                            progress: _ByteProgress, cancel_token=None) -> List[str]:
        """Extract validated members into a fresh staging directory."""
        sections = set()
        for member in archive.infolist():
            _check_cancel(cancel_token)
            parts = cls._member_parts(member.filename, member.is_dir())
            legacy = len(parts) == 1 and parts[0].lower().endswith(".jar")
            section = "mods" if legacy else parts[0]
            relative = parts if legacy else parts[1:]
            section_root = Path(safe_target(destination, section))
            target = section_root
            for part in relative:
                target /= part
            target_root = section_root.resolve()
            target_resolved = target.resolve()
            if target_root != target_resolved and target_root not in target_resolved.parents:
                raise ValueError("Архив содержит небезопасный путь")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                sections.add(section)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            progress.message = f"Распаковка: {member.filename}"
            with archive.open(member, "r") as source, target.open("xb") as output:
                shutil.copyfileobj(_ProgressReader(source, progress.advance, cancel_token),
                                   output, length=1024 * 1024)
            sections.add(section)
        return sorted(sections)

    def _restore_archive(self, archive_path: str, progress_callback=None, cancel_token=None) -> bool:
        """Restore through staging and roll back all replaced sections on cancellation."""
        progress_callback = _safe_progress(progress_callback)
        staging_path = None
        preserve_staging = False
        committed = False
        try:
            _check_cancel(cancel_token)
            archive_file = Path(archive_path)
            if not archive_file.is_file() or archive_file.is_symlink():
                raise ValueError("Файл бэкапа не найден")
            if progress_callback:
                progress_callback(0, "Проверка архива…")
            _check_cancel(cancel_token)
            staging_path = Path(tempfile.mkdtemp(prefix=".backup-restore-", dir=self.minecraft_dir))
            prepared = staging_path / "prepared"
            prepared.mkdir()
            with zipfile.ZipFile(archive_file, "r") as archive:
                total_size = self._validate_archive(archive, cancel_token)
                if total_size > shutil.disk_usage(self.minecraft_dir).free:
                    raise OSError("Недостаточно свободного места для распаковки бэкапа")
                progress = _ByteProgress(total_size, progress_callback)
                # ZipExtFile verifies the CRC while reading each file into staging.
                sections = self._extract_to_staging(archive, prepared, progress, cancel_token)

            _check_cancel(cancel_token)
            old_root = staging_path / "old"
            old_root.mkdir()
            if progress_callback:
                progress_callback(95, "Применение восстановленных данных…")
            moved: List[Tuple[Path, Path, bool]] = []
            try:
                for section in sections:
                    _check_cancel(cancel_token)
                    destination = Path(self.minecraft_dir) / section
                    replacement = prepared / section
                    if destination.is_symlink():
                        raise ValueError(f"Папка {section} является символической ссылкой")
                    old = old_root / section
                    had_old = destination.exists()
                    if had_old:
                        os.replace(destination, old)
                    # Record the move before checking cancellation or installing the new data.
                    moved.append((destination, old, had_old))
                    _check_cancel(cancel_token)
                    os.replace(replacement, destination)
                    _check_cancel(cancel_token)
                if cancel_token is not None:
                    cancel_token.commit()
                committed = True
            except Exception as exc:
                rollback_failed = False
                for destination, old, had_old in reversed(moved):
                    try:
                        if destination.is_dir() and not destination.is_symlink():
                            shutil.rmtree(destination)
                        elif destination.exists() or destination.is_symlink():
                            destination.unlink()
                        if had_old and old.exists():
                            os.replace(old, destination)
                    except Exception:
                        rollback_failed = True
                        logger.exception("Не удалось откатить восстановление %s", destination)
                if rollback_failed:
                    preserve_staging = True
                    raise RuntimeError(
                        f"Не удалось полностью откатить восстановление. "
                        f"Исходные данные сохранены в {old_root}"
                    ) from exc
                raise
            if progress_callback:
                progress_callback(99, "Завершение восстановления…")
        except BackupCancelled:
            logger.info("Восстановление бэкапа отменено")
            raise
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Ошибка восстановления: %s", exc)
            return False
        finally:
            if staging_path is not None and not preserve_staging:
                try:
                    shutil.rmtree(staging_path)
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    action = "Восстановление завершено, но" if committed else "Операция прервана, но"
                    raise OSError(f"{action} не удалось удалить временную папку: {staging_path}") from exc
        if progress_callback:
            progress_callback(100, "Бэкап восстановлен")
        logger.info("Бэкап восстановлен: %s", archive_file)
        return True

    def restore_backup(self, backup_filename: str, progress_callback=None, cancel_token=None) -> bool:
        """Restore a backup stored in this instance's backups directory."""
        self.last_error = None
        try:
            backup_path = safe_target(self.backup_dir, backup_filename)
        except (TypeError, ValueError):
            return False
        return self._restore_archive(backup_path, progress_callback, cancel_token)

    def restore_archive(self, archive_path: str, progress_callback=None, cancel_token=None) -> bool:
        """Restore a ZIP selected by the user through a file dialog."""
        self.last_error = None
        try:
            return self._restore_archive(os.fspath(archive_path), progress_callback, cancel_token)
        except (TypeError, ValueError) as exc:
            self.last_error = str(exc)
            return False

    def clear_mods(self) -> int:
        """Remove JAR files from mods and return the number removed."""
        if not os.path.exists(self.mods_dir):
            return 0
        count = 0
        for filename in os.listdir(self.mods_dir):
            if filename.endswith(".jar"):
                try:
                    os.remove(os.path.join(self.mods_dir, filename))
                    count += 1
                except Exception as exc:
                    logger.warning("Не удалось удалить %s: %s", filename, exc)
        logger.info("Удалено %d модов", count)
        return count

    def get_backups_list(self) -> List[Dict]:
        """Return available backups sorted newest first."""
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(".zip") and filename.startswith("mods_backup_"):
                file_path = os.path.join(self.backup_dir, filename)
                stat = os.stat(file_path)
                try:
                    date_str = filename.replace("mods_backup_", "").replace(".zip", "")
                    if "_" in date_str:
                        date_part, time_part = date_str.split("_")[:2]
                        date = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                    else:
                        date = datetime.fromtimestamp(stat.st_mtime)
                except (TypeError, ValueError):
                    date = datetime.fromtimestamp(stat.st_mtime)
                backups.append({"filename": filename, "size_mb": stat.st_size / (1024 * 1024),
                                "date": date, "date_str": date.strftime("%d.%m.%Y %H:%M:%S")})
        backups.sort(key=lambda item: item["date"], reverse=True)
        return backups

    def delete_backup(self, backup_filename: str) -> bool:
        """Delete a backup below the instance's backup directory."""
        try:
            backup_path = safe_target(self.backup_dir, backup_filename)
        except (TypeError, ValueError):
            return False
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
                logger.info("Удалён бэкап: %s", backup_filename)
                return True
            except OSError as exc:
                logger.error("Ошибка удаления бэкапа: %s", exc)
        return False

    def delete_all_backups(self) -> int:
        """Delete all backups and return the number removed."""
        count = 0
        for backup in self.get_backups_list():
            if self.delete_backup(backup["filename"]):
                count += 1
        logger.info("Удалено %d бэкапов", count)
        return count
