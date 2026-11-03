"""Import Modrinth ``.mrpack`` archives into an isolated launcher instance.

The importer deliberately uses the launcher's existing path and downloader
helpers.  It does not install Minecraft or a mod loader; it only imports the
pack files and returns the metadata needed by the launcher's local collection
JSON.
"""

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from Core import instances
from Core.mod_transaction import safe_target
from Network import Downloader


class MrpackImportError(RuntimeError):
    """Raised when a Modrinth pack cannot be read or installed."""


class MrpackImporter:
    """Import one Modrinth pack into a new launcher instance.

    :param mrpack_path: Path to the ``.mrpack`` ZIP archive.
    :param instance_name: Display name used to create the new instance.
    :param progress_callback: Optional callback ``(current, total, status)``.
    :param instance_directory: Optional already-resolved instance path.  This
        is useful for callers that manage instance paths themselves; the
        normal launcher path is derived from ``instance_name``.
    """

    _LOADER_KEYS = (
        ("forge", "forge"),
        ("neoforge", "neoforge"),
        ("fabric-loader", "fabric"),
        ("quilt-loader", "quilt"),
    )
    _MAX_INDEX_BYTES = 8 * 1024 * 1024
    _MAX_OVERRIDE_FILE_BYTES = 256 * 1024 * 1024
    _MAX_OVERRIDE_TOTAL_BYTES = 1024 * 1024 * 1024
    _MAX_FILES = 10_000
    _MAX_DOWNLOAD_BYTES = 4 * 1024 * 1024 * 1024

    def __init__(self, mrpack_path, instance_name, progress_callback=None,
                 instance_directory=None, persist_collection=False):
        if not isinstance(instance_name, str) or not instance_name.strip():
            raise ValueError("Имя инстанса не может быть пустым")

        self.mrpack_path = Path(mrpack_path).expanduser()
        self.instance_name = instance_name.strip()
        self.progress_callback = progress_callback
        self.instance_directory = (Path(instance_directory).expanduser()
                                   if instance_directory is not None else None)
        self.persist_collection = persist_collection

    def import_pack(self):
        """Import the archive and return collection metadata.

        The returned ``mod_count`` is the number of entries in the Modrinth
        ``files`` list, which is the complete set of downloaded pack files.
        """
        if not self.mrpack_path.is_file():
            raise MrpackImportError(
                f"Файл .mrpack не найден: {self.mrpack_path}")

        try:
            with zipfile.ZipFile(self.mrpack_path, "r") as archive:
                index = self._read_index(archive)
                minecraft_version, loader, loader_version = self._read_dependencies(index)
                files = index.get("files")
                if not isinstance(files, list):
                    raise MrpackImportError("В modrinth.index.json отсутствует список files")
                if len(files) > self._MAX_FILES:
                    raise MrpackImportError("Слишком много файлов в .mrpack")

                destination = self._new_instance_destination()
                with tempfile.TemporaryDirectory(prefix='.mrpack-', dir=destination.parent) as temporary:
                    target = Path(temporary) / 'instance'
                    target.mkdir()
                    self._download_files(files, target)
                    self._extract_overrides(archive, target)
                    mods = []
                    mods_dir = target / 'mods'
                    if mods_dir.is_dir() and any(p.is_file() and p.suffix.lower() == '.jar'
                                                 for p in mods_dir.iterdir()):
                        from Core.collection_loader import get_collections_dir
                        from Core.local_mods import import_local_mods
                        mods = import_local_mods([mods_dir], get_collections_dir())
                    metadata = {
                        "name": self.instance_name,
                        "minecraft_version": minecraft_version,
                        "loader": loader,
                        "loader_version": loader_version,
                        "mods": mods,
                        "mod_count": len(mods),
                    }
                    if self.persist_collection:
                        from Core.modpack_install_transaction import publish_collection_instance
                        return publish_collection_instance(target, destination, metadata)
                    if destination.exists() or destination.is_symlink():
                        raise MrpackImportError("Инстанс с таким именем уже существует")
                    os.rename(target, destination)
                return metadata
        except MrpackImportError:
            raise
        except zipfile.BadZipFile as exc:
            raise MrpackImportError("Неверный ZIP-архив .mrpack") from exc
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MrpackImportError(f"Не удалось импортировать .mrpack: {exc}") from exc

    # ``run`` makes the class convenient to use from a generic worker while
    # keeping ``import_pack`` as the descriptive public API.
    run = import_pack
    import_mrpack = import_pack

    def _read_index(self, archive):
        try:
            info = archive.getinfo("modrinth.index.json")
        except KeyError as exc:
            raise MrpackImportError(
                "В архиве отсутствует modrinth.index.json") from exc
        if info.file_size > self._MAX_INDEX_BYTES:
            raise MrpackImportError("modrinth.index.json слишком большой")

        try:
            index = json.loads(archive.read(info).decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MrpackImportError(
                "Файл modrinth.index.json содержит неверный JSON") from exc
        if not isinstance(index, dict):
            raise MrpackImportError("modrinth.index.json должен содержать объект JSON")
        return index

    @classmethod
    def _read_dependencies(cls, index):
        dependencies = index.get("dependencies")
        if not isinstance(dependencies, dict):
            raise MrpackImportError(
                "В modrinth.index.json отсутствует объект dependencies")

        minecraft_version = dependencies.get("minecraft")
        if not isinstance(minecraft_version, str) or not minecraft_version.strip():
            raise MrpackImportError("В dependencies отсутствует версия Minecraft")

        loader = None
        loader_version = None
        for dependency_key, loader_name in cls._LOADER_KEYS:
            value = dependencies.get(dependency_key)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise MrpackImportError(
                        f"Некорректная версия загрузчика {dependency_key}")
                loader = loader_name
                loader_version = value
                break

        if loader is None:
            raise MrpackImportError(
                "В dependencies не найден поддерживаемый загрузчик "
                "(fabric, forge, neoforge или quilt)")
        return minecraft_version, loader, loader_version

    def _new_instance_destination(self):
        requested = (self.instance_directory
                     if self.instance_directory is not None
                     else instances.game_directory(self.instance_name))
        try:
            root = instances.launcher_root() / 'instances'
            if root.is_symlink():
                raise ValueError('Папка instances не должна быть символической ссылкой')
            root.mkdir(parents=True, exist_ok=True)
            requested = Path(requested).absolute()
            if requested.parent.resolve() != root.resolve():
                raise ValueError('Инстанс должен находиться внутри instances')
            target = Path(safe_target(root, requested.name))
            if target.exists() or target.is_symlink():
                raise FileExistsError('Инстанс с таким именем уже существует')
            return target
        except (OSError, ValueError) as exc:
            raise MrpackImportError(
                f"Не удалось подготовить папку инстанса: {exc}") from exc

    @staticmethod
    def _target(root, relative_path):
        """Resolve a relative pack path through the launcher's safe helper."""
        if not isinstance(relative_path, str) or not relative_path:
            raise MrpackImportError("В архиве указан пустой путь файла")
        # The launcher's safe_target intentionally accepts one filename only.
        # Walk each relative component through it so paths such as
        # ``mods/sodium.jar`` remain protected without changing its existing
        # API for other callers.
        normalized = relative_path.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("//"):
            raise MrpackImportError(
                f"Небезопасный путь в .mrpack: {relative_path!r}")
        parts = normalized.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise MrpackImportError(
                f"Небезопасный путь в .mrpack: {relative_path!r}")

        try:
            current = Path(root)
            if current.is_symlink():
                raise ValueError("Базовая папка не должна быть символической ссылкой")
            for directory_name in parts[:-1]:
                if current.is_symlink():
                    raise ValueError("Путь содержит символическую ссылку")
                directory = Path(safe_target(str(current), directory_name))
                if directory.is_symlink():
                    raise ValueError("Путь содержит символическую ссылку")
                if directory.exists() and not directory.is_dir():
                    raise ValueError("Компонент пути не является папкой")
                directory.mkdir(parents=False, exist_ok=True)
                current = directory
            return Path(safe_target(str(current), parts[-1]))
        except (OSError, ValueError) as exc:
            raise MrpackImportError(
                f"Небезопасный путь в .mrpack: {relative_path!r}") from exc

    def _download_files(self, files, target):
        total = len(files)
        for number, file_entry in enumerate(files, start=1):
            if not isinstance(file_entry, dict):
                raise MrpackImportError("Элемент files должен быть объектом JSON")
            env = file_entry.get('env') or {}
            if isinstance(env, dict) and env.get('client') == 'unsupported':
                continue
            relative_path = file_entry.get("path")
            downloads = file_entry.get("downloads")
            if not isinstance(downloads, list) or not downloads:
                raise MrpackImportError(
                    f"Для файла {relative_path!r} отсутствует ссылка downloads")
            url = downloads[0]
            if not isinstance(url, str) or not url.strip():
                raise MrpackImportError(
                    f"Для файла {relative_path!r} указана неверная ссылка")
            if not self._is_trusted_download_url(url):
                raise MrpackImportError(
                    f"Для файла {relative_path!r} указана небезопасная ссылка")

            destination = self._target(target, relative_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            self._emit(number - 1, total,
                       f"Скачивание {number}/{total}: {relative_path}")
            expected_size = file_entry.get('fileSize')
            if expected_size is not None and (not isinstance(expected_size, int) or
                                               isinstance(expected_size, bool) or
                                               expected_size < 0 or expected_size > self._MAX_DOWNLOAD_BYTES):
                raise MrpackImportError(f"Неверный размер файла {relative_path!r}")
            hashes = file_entry.get('hashes')
            if not isinstance(hashes, dict) or not any(hashes.get(key) for key in ('sha512', 'sha1')):
                raise MrpackImportError(f"Для файла {relative_path!r} отсутствует контрольная сумма")
            if not Downloader.download_file_sync(url, str(destination),
                                                 url_validator=self._is_trusted_download_url,
                                                 max_bytes=expected_size if expected_size is not None else self._MAX_DOWNLOAD_BYTES):
                raise MrpackImportError(
                    f"Не удалось скачать файл {relative_path!r}")
            if expected_size is not None and destination.stat().st_size != expected_size:
                raise MrpackImportError(f"Размер файла {relative_path!r} не совпал")
            for algorithm in ('sha512', 'sha1'):
                expected = hashes.get(algorithm)
                if expected is not None:
                    if not isinstance(expected, str):
                        raise MrpackImportError(f"Неверная контрольная сумма {relative_path!r}")
                    with destination.open('rb') as stream:
                        actual = hashlib.file_digest(stream, algorithm).hexdigest()
                    if actual.lower() != expected.lower():
                        raise MrpackImportError(f"Контрольная сумма файла {relative_path!r} не совпала")
            self._emit(number, total,
                       f"Скачивание {number}/{total}: {relative_path}")

    def _extract_overrides(self, archive, target):
        # Apply the generic overrides first and client-overrides second, which
        # gives the client-specific tree the expected precedence on collisions.
        members = [
            info for info in archive.infolist()
            if (info.filename.startswith("overrides/")
                or info.filename.startswith("client-overrides/"))
            and not info.is_dir()
        ]
        members.sort(key=lambda info: info.filename.startswith("client-overrides/"))
        total_size = 0
        self._emit(0, len(members), "Распаковка overrides...")
        for number, info in enumerate(members, start=1):
            if info.file_size > self._MAX_OVERRIDE_FILE_BYTES:
                raise MrpackImportError(
                    f"Файл override слишком большой: {info.filename}")
            total_size += info.file_size
            if total_size > self._MAX_OVERRIDE_TOTAL_BYTES:
                raise MrpackImportError("Общий размер overrides слишком большой")
            if info.filename.startswith("client-overrides/"):
                relative_path = info.filename[len("client-overrides/"):]
            else:
                relative_path = info.filename[len("overrides/"):]
            destination = self._target(target, relative_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, open(destination, "wb") as output:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            self._emit(number, len(members), f"Распаковка {number}/{len(members)}")

        self._emit(1, 1, "Импорт .mrpack завершён")

    def _emit(self, current, total, status):
        if self.progress_callback is not None:
            self.progress_callback(current, total, status)

    @staticmethod
    def _is_trusted_download_url(url):
        parsed = urlparse(url.strip())
        host = (parsed.hostname or '').lower().rstrip('.')
        if parsed.scheme.lower() != 'https' or not host or parsed.username or parsed.password:
            return False
        return host == 'modrinth.com' or host.endswith('.modrinth.com')


__all__ = ["MrpackImporter", "MrpackImportError"]
