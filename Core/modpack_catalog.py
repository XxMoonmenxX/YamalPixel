"""Search and parse Modrinth and CurseForge Minecraft modpacks."""

import json
import hashlib
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from Core.mod_transaction import safe_filename, safe_target
from Network.CurseForgeLoader import CurseForgeAPI
from Network.Downloader import download_file_sync
from Network.ModrinthLoader import ModrinthAPI


class ModpackCatalogError(RuntimeError):
    """Raised when a catalog item cannot be downloaded or parsed."""


class ModpackCatalogService:
    """Network service used by the collection editor's background workers."""

    MODRINTH_SORTS = {"relevance", "downloads", "updated"}
    CURSEFORGE_SORT_FIELDS = {
        "relevance": None,
        "downloads": 6,
        "updated": 3,
    }
    MAX_MANIFEST_BYTES = 8 * 1024 * 1024
    MAX_MANIFEST_ENTRIES = 10_000
    MAX_ARCHIVE_BYTES = 4 * 1024 * 1024 * 1024
    MAX_OVERRIDE_BYTES = 4 * 1024 * 1024 * 1024

    def __init__(self, modrinth=None, curseforge=None):
        self.modrinth = modrinth or ModrinthAPI()
        self.curseforge = curseforge or CurseForgeAPI()

    def search(self, source, query="", sort="relevance", limit=50):
        """Return normalized catalog entries for the requested marketplace."""
        query = (query or "").strip()
        if sort not in self.MODRINTH_SORTS:
            sort = "relevance"

        if source == "modrinth":
            hits = self.modrinth.search_modpacks(query, sort, limit) or []
            return [self._normalize_modrinth_hit(hit) for hit in hits]
        if source == "curseforge":
            hits = self.curseforge.search_modpacks(
                query,
                sort_field=self.CURSEFORGE_SORT_FIELDS[sort],
                limit=limit,
            )
            return [self._normalize_curseforge_hit(hit) for hit in (hits or [])]
        if source == "both":
            # Keep the existing source selector useful if a user leaves it on
            # "Modrinth + CurseForge" when switching modes.
            results = []
            errors = []
            for marketplace in ("modrinth", "curseforge"):
                try:
                    results.extend(self.search(marketplace, query, sort, limit))
                except Exception as exc:
                    errors.append(f"{marketplace}: {exc}")
            if not results and errors:
                raise ModpackCatalogError("; ".join(errors))
            if sort == 'downloads':
                results.sort(key=lambda item: item.get('downloads', 0), reverse=True)
            elif sort == 'updated':
                results.sort(key=lambda item: item.get('date_modified') or '', reverse=True)
            else:
                # The providers use unrelated relevance scores; interleave
                # their individually ranked lists rather than inventing one.
                first = [item for item in results if item['source'] == 'modrinth']
                second = [item for item in results if item['source'] == 'curseforge']
                results = [item for index in range(max(len(first), len(second)))
                           for group in (first, second) if index < len(group)
                           for item in [group[index]]]
            return results[:limit]
        raise ValueError(f"Неизвестный источник модпаков: {source}")

    @staticmethod
    def _normalize_modrinth_hit(hit):
        versions = hit.get("versions") or []
        return {
            "source": "modrinth",
            "project_id": str(hit.get("project_id") or hit.get("id") or ""),
            "slug": hit.get("slug", ""),
            "name": hit.get("title") or hit.get("name") or "Без названия",
            "description": hit.get("description", ""),
            "downloads": int(hit.get("downloads") or 0),
            "date_modified": hit.get("date_modified") or hit.get("dateModified", ""),
            "icon_url": hit.get("icon_url", ""),
            "version": hit.get("latest_version") or hit.get("version", ""),
            "minecraft_version": hit.get("minecraft_version") or (versions[0] if versions else ""),
            "loader": hit.get("loader", ""),
        }

    @staticmethod
    def _normalize_curseforge_hit(hit):
        latest_files = hit.get("latestFiles") or hit.get("latest_files") or []
        latest = latest_files[0] if latest_files else {}
        game_versions = latest.get("gameVersions") or latest.get("game_versions") or []
        mod_loaders = latest.get("modLoaders") or latest.get("mod_loaders") or []
        return {
            "source": "curseforge",
            "project_id": str(hit.get("id") or hit.get("project_id") or ""),
            "slug": hit.get("slug", ""),
            "name": hit.get("name") or hit.get("title") or "Без названия",
            "description": hit.get("summary") or hit.get("description", ""),
            "downloads": int(hit.get("downloadCount") or hit.get("downloads") or 0),
            "date_modified": hit.get("dateModified") or hit.get("date_modified", ""),
            "icon_url": hit.get("logo", {}).get("thumbnailUrl", "")
            if isinstance(hit.get("logo"), dict) else hit.get("icon_url", ""),
            "version": latest.get("displayName") or latest.get("fileName", ""),
            "minecraft_version": game_versions[0] if game_versions else "",
            "loader": mod_loaders[0] if mod_loaders else "",
            "download_url": latest.get("downloadUrl") or latest.get("download_url", ""),
            "file_id": latest.get("id") or latest.get("file_id"),
        }

    def download_and_parse(self, project, source, progress_callback=None):
        """Download one catalog item to a temporary file and parse its manifest."""
        if source not in ("modrinth", "curseforge"):
            raise ModpackCatalogError(f"Неподдерживаемый источник: {source}")

        with tempfile.TemporaryDirectory(prefix=".modpack-") as temporary:
            extension = ".mrpack" if source == "modrinth" else ".zip"
            archive_path = Path(temporary) / ("pack" + extension)
            if progress_callback:
                progress_callback(0, 1, "Получение ссылки на модпак…")
            url = (self._resolve_modrinth_url(project)
                   if source == "modrinth"
                   else self._resolve_curseforge_url(project))
            if not url:
                raise ModpackCatalogError("Для модпака не найдена ссылка на архив")
            if not download_file_sync(url, str(archive_path),
                                      url_validator=lambda candidate: self._url_allowed(candidate, source),
                                      max_bytes=self.MAX_ARCHIVE_BYTES):
                raise ModpackCatalogError("Не удалось скачать архив модпака")
            if progress_callback:
                progress_callback(1, 1, "Архив скачан, чтение манифеста…")

            if source == "modrinth":
                return self._parse_mrpack(archive_path, project, progress_callback)
            return self._parse_curseforge_zip(archive_path, project, progress_callback)

    def download_and_install(self, project, source, progress_callback=None, persist_collection=False):
        """Install the entire pack in a new instance, publishing it only on success."""
        from Core.collection_loader import get_collections_dir
        from Core.instances import collection_directory
        from Core.local_mods import import_local_mods
        from Core.mrpack_handler import MrpackImporter

        if source not in ('modrinth', 'curseforge'):
            raise ModpackCatalogError('Неподдерживаемый источник модпака')
        with tempfile.TemporaryDirectory(prefix='.modpack-') as temporary:
            archive_path = Path(temporary) / ('pack.mrpack' if source == 'modrinth' else 'pack.zip')
            if progress_callback:
                progress_callback(0, 1, 'Скачивание архива модпака…')
            url = (self._resolve_modrinth_url(project) if source == 'modrinth'
                   else self._resolve_curseforge_url(project))
            if not url or not download_file_sync(
                    url, str(archive_path),
                    url_validator=lambda candidate: self._url_allowed(candidate, source),
                    max_bytes=self.MAX_ARCHIVE_BYTES):
                raise ModpackCatalogError('Не удалось скачать архив модпака')
            metadata = (self._parse_mrpack(archive_path, project) if source == 'modrinth'
                        else self._parse_curseforge_zip(archive_path, project, progress_callback))
            name = str(metadata['name']).strip()
            safe_name = ''.join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            if not safe_name:
                raise ModpackCatalogError('Название модпака не содержит допустимых символов')
            filename = safe_filename(safe_name + '.json')
            if Path(safe_target(get_collections_dir(), filename)).exists():
                raise ModpackCatalogError('Сборка с таким именем уже существует')
            destination = collection_directory({'name': name, 'filename': filename,
                                                'instance_id': 'file:' + filename})
            importer = MrpackImporter(archive_path, name, instance_directory=destination,
                                      progress_callback=progress_callback,
                                      persist_collection=persist_collection)
            if source == 'modrinth':
                return importer.import_pack()

            destination = importer._new_instance_destination()
            with tempfile.TemporaryDirectory(prefix='.modpack-install-', dir=destination.parent) as staging:
                target = Path(staging) / 'instance'
                target.mkdir()
                for number, mod in enumerate(metadata['mods'], 1):
                    mod_path = importer._target(target, 'mods/' + mod['filename'])
                    if mod_path.exists():
                        raise ModpackCatalogError('В модпаке повторяется имя файла мода')
                    if progress_callback:
                        progress_callback(number - 1, len(metadata['mods']),
                                          f"Скачивание {number}/{len(metadata['mods'])}: {mod['filename']}")
                    if not download_file_sync(mod['url'], str(mod_path),
                                              url_validator=lambda candidate: self._url_allowed(candidate, 'curseforge'),
                                              max_bytes=self.MAX_ARCHIVE_BYTES):
                        raise ModpackCatalogError(f"Не удалось скачать {mod['filename']}")
                    if mod.get('_file_size') is not None and mod_path.stat().st_size != mod['_file_size']:
                        raise ModpackCatalogError(f"Размер файла {mod['filename']} не совпал")
                    for algorithm, expected in mod.get('_hashes', {}).items():
                        with mod_path.open('rb') as stream:
                            actual = hashlib.file_digest(stream, algorithm).hexdigest()
                        if actual.lower() != expected.lower():
                            raise ModpackCatalogError(f"Контрольная сумма {mod['filename']} не совпала")
                with zipfile.ZipFile(archive_path) as archive:
                    manifest = self._read_zip_json(archive, 'manifest.json')
                    prefix = str(manifest.get('overrides') or 'overrides').replace('\\', '/').rstrip('/') + '/'
                    # Validate the prefix as well as every extracted member.
                    importer._target(target, prefix[:-1] + '/.validate')
                    total = 0
                    for info in archive.infolist():
                        if not info.filename.startswith(prefix) or info.is_dir():
                            continue
                        if stat.S_ISLNK(info.external_attr >> 16):
                            raise ModpackCatalogError('Символические ссылки в архиве запрещены')
                        total += info.file_size
                        if info.file_size > self.MAX_OVERRIDE_BYTES or total > self.MAX_OVERRIDE_BYTES:
                            raise ModpackCatalogError('Слишком большой размер overrides')
                        destination_file = importer._target(target, info.filename[len(prefix):])
                        with archive.open(info) as src, destination_file.open('wb') as dst:
                            shutil.copyfileobj(src, dst, 1024 * 1024)
                mods_dir = target / 'mods'
                metadata['mods'] = (import_local_mods([mods_dir], get_collections_dir())
                                    if mods_dir.is_dir() and any(p.is_file() and p.suffix.lower() == '.jar'
                                                                 for p in mods_dir.iterdir()) else [])
                metadata['mod_count'] = len(metadata['mods'])
                if persist_collection:
                    from Core.modpack_install_transaction import publish_collection_instance
                    return publish_collection_instance(target, destination, metadata)
                if destination.exists() or destination.is_symlink():
                    raise ModpackCatalogError('Инстанс с таким именем уже существует')
                os.rename(target, destination)
            return metadata

    @classmethod
    def _url_allowed(cls, candidate, source):
        try:
            cls._validated_url(candidate, source)
            return True
        except (ModpackCatalogError, ValueError):
            return False

    def _resolve_modrinth_url(self, project):
        if project.get("download_url"):
            return self._validated_url(project["download_url"], "modrinth")
        project_id = project.get("project_id") or project.get("id") or project.get("slug")
        if not project_id:
            return None
        response = self.modrinth.session.get(
            f"{self.modrinth.base_url}/project/{project_id}/version",
            params={"limit": 20},
            timeout=20,
        )
        response.raise_for_status()
        versions = response.json()
        for version in versions:
            files = version.get("files", [])
            candidates = [file for file in files
                          if str(file.get("filename", "")).lower().endswith(".mrpack")]
            if candidates:
                primary = next((file for file in candidates if file.get("primary")), candidates[0])
                return self._validated_url(primary.get("url"), "modrinth")
        return None

    def _resolve_curseforge_url(self, project):
        if project.get("download_url"):
            return self._validated_url(project["download_url"], "curseforge")
        project_id = project.get("project_id") or project.get("id")
        if not project_id:
            return None
        files = self.curseforge.get_modpack_files(str(project_id), limit=20)
        for file in files:
            filename = file.get("fileName") or file.get("filename") or ""
            if not filename.lower().endswith(".zip"):
                continue
            url = file.get("downloadUrl") or file.get("download_url")
            if url:
                return self._validated_url(url, "curseforge")
            file_id = file.get("id") or file.get("file_id")
            if file_id:
                return self._curseforge_cdn_url(file_id, filename)
        return None

    def _parse_mrpack(self, archive_path, project, progress_callback=None):
        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                index = self._read_zip_json(archive, "modrinth.index.json")
                if not isinstance(index, dict):
                    raise ModpackCatalogError("modrinth.index.json имеет неверный формат")
        except (OSError, zipfile.BadZipFile) as exc:
            raise ModpackCatalogError("Неверный архив .mrpack") from exc
        except json.JSONDecodeError as exc:
            raise ModpackCatalogError("modrinth.index.json содержит неверный JSON") from exc

        dependencies = index.get("dependencies") or {}
        minecraft_version = dependencies.get("minecraft", "")
        loader, loader_version = self._find_loader(dependencies)
        mods = []
        files = index.get("files") or []
        if len(files) > self.MAX_MANIFEST_ENTRIES:
            raise ModpackCatalogError("Список files в .mrpack слишком большой")
        for number, entry in enumerate(files, start=1):
            if not isinstance(entry, dict):
                continue
            path = str(entry.get("path") or "").replace("\\", "/")
            env = entry.get("env") or {}
            if not path.lower().startswith("mods/") or not path.lower().endswith(".jar"):
                continue
            if env.get("client") in ("unsupported", "disabled"):
                continue
            downloads = entry.get("downloads") or []
            filename = PurePosixPath(path).name
            if not downloads or not filename:
                continue
            url = self._validated_url(downloads[0], "modrinth")
            try:
                safe_filename(filename)
            except ValueError as exc:
                raise ModpackCatalogError(
                    f"Небезопасное имя мода в .mrpack: {filename!r}") from exc
            mods.append({
                "source": "modrinth",
                "name": PurePosixPath(filename).stem,
                "filename": filename,
                "modrinth_id": entry.get("project_id", ""),
                "project_id": entry.get("project_id", ""),
                "version_id": entry.get("version_id"),
                "url": url,
                "download_url": url,
                "direct_link": url,
                "minecraft_version": minecraft_version,
                "loader": loader,
            })
            if progress_callback:
                progress_callback(number, max(len(files), 1), f"Разбор модов: {number}/{len(files)}")

        return {
            "source": "modrinth",
            "name": index.get("name") or project.get("name") or "Модпак Modrinth",
            "summary": index.get("summary", project.get("description", "")),
            "minecraft_version": minecraft_version,
            "loader": loader,
            "loader_version": loader_version,
            "mods": mods,
            "mod_count": len(mods),
        }

    def _parse_curseforge_zip(self, archive_path, project, progress_callback=None):
        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                manifest = self._read_zip_json(archive, "manifest.json")
                if not isinstance(manifest, dict):
                    raise ModpackCatalogError("manifest.json имеет неверный формат")
        except (OSError, zipfile.BadZipFile) as exc:
            raise ModpackCatalogError("Неверный CurseForge ZIP-архив") from exc
        except json.JSONDecodeError as exc:
            raise ModpackCatalogError("manifest.json содержит неверный JSON") from exc

        minecraft = manifest.get("minecraft") or {}
        minecraft_version = minecraft.get("version", "")
        loader, loader_version = self._parse_curseforge_loader(minecraft.get("modLoaders") or [])
        entries = manifest.get("files") or []
        if len(entries) > self.MAX_MANIFEST_ENTRIES:
            raise ModpackCatalogError("Список files в manifest.json слишком большой")
        mods = []
        for number, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                continue
            project_id = entry.get("projectID") or entry.get("projectId")
            file_id = entry.get("fileID") or entry.get("fileId")
            if project_id is None or file_id is None:
                continue
            info = self.curseforge.get_file_info(str(project_id), str(file_id)) or {}
            filename = info.get("fileName") or info.get("filename")
            if not filename:
                raise ModpackCatalogError(f'Не удалось получить сведения о файле CurseForge {project_id}/{file_id}')
            filename = PurePosixPath(str(filename).replace("\\", "/")).name
            try:
                safe_filename(filename)
            except ValueError as exc:
                raise ModpackCatalogError(
                    f"Небезопасное имя мода в manifest.json: {filename!r}") from exc
            url = info.get("downloadUrl") or info.get("download_url")
            if not url:
                url = self._curseforge_cdn_url(file_id, filename)
            else:
                url = self._validated_url(url, "curseforge")
            mods.append({
                "source": "curseforge",
                "name": Path(filename).stem,
                "filename": filename,
                "curseforge_id": str(project_id),
                "project_id": str(project_id),
                "file_id": str(file_id),
                "version_id": str(file_id),
                "url": url,
                "download_url": url,
                "direct_link": url,
                "minecraft_version": minecraft_version,
                "loader": loader,
                "_file_size": info.get('fileLength'),
                "_hashes": {('sha1' if item.get('algo') == 1 else 'md5'): item['value']
                            for item in info.get('hashes', [])
                            if isinstance(item, dict) and item.get('algo') in (1, 2)
                            and isinstance(item.get('value'), str)},
            })
            if progress_callback:
                progress_callback(number, max(len(entries), 1), f"Разбор модов: {number}/{len(entries)}")

        return {
            "source": "curseforge",
            "name": manifest.get("name") or project.get("name") or "Модпак CurseForge",
            "summary": project.get("description", ""),
            "minecraft_version": minecraft_version,
            "loader": loader,
            "loader_version": loader_version,
            "mods": mods,
            "mod_count": len(mods),
        }

    @staticmethod
    def _find_loader(dependencies):
        for key, loader in (("fabric-loader", "fabric"), ("forge", "forge"),
                            ("neoforge", "neoforge"), ("quilt-loader", "quilt")):
            if dependencies.get(key):
                return loader, str(dependencies[key])
        return "", ""

    @classmethod
    def _read_zip_json(cls, archive, name):
        try:
            info = archive.getinfo(name)
        except KeyError as exc:
            raise ModpackCatalogError(f"В архиве отсутствует {name}") from exc
        if info.file_size > cls.MAX_MANIFEST_BYTES:
            raise ModpackCatalogError(f"Файл {name} слишком большой")
        try:
            return json.loads(archive.read(info).decode("utf-8-sig"))
        except UnicodeDecodeError as exc:
            raise ModpackCatalogError(f"Файл {name} содержит неверную кодировку") from exc
        except json.JSONDecodeError as exc:
            raise ModpackCatalogError(f"Файл {name} содержит неверный JSON") from exc

    @staticmethod
    def _validated_url(value, source):
        if not isinstance(value, str) or not value.strip():
            raise ModpackCatalogError("В манифесте отсутствует ссылка на файл")
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme.lower() != "https" or not host or parsed.username or parsed.password:
            raise ModpackCatalogError("Манифест содержит небезопасную ссылку")
        if source == "modrinth":
            allowed = host == "modrinth.com" or host.endswith(".modrinth.com")
        else:
            allowed = (host == "curseforge.com" or host.endswith(".curseforge.com")
                       or host == "forgecdn.net" or host.endswith(".forgecdn.net"))
        if not allowed:
            raise ModpackCatalogError(f"Ссылка ведёт на неподдерживаемый домен: {host}")
        return value.strip()

    def _curseforge_cdn_url(self, file_id, filename):
        builder = getattr(self.curseforge, "_build_direct_cdn_url", None)
        if callable(builder):
            return builder(str(file_id), filename)
        file_id = str(file_id)
        if len(file_id) >= 7:
            return f"https://edge.forgecdn.net/files/{file_id[:-3]}/{file_id[-3:]}/{filename}"
        return f"https://media.forgecdn.net/files/{file_id}/{filename}"

    @staticmethod
    def _parse_curseforge_loader(loaders):
        for value in loaders:
            identifier = value.get("id", "") if isinstance(value, dict) else str(value)
            identifier = str(identifier)
            if "-" in identifier:
                loader, version = identifier.split("-", 1)
            else:
                loader, version = identifier, ""
            loader = loader.lower()
            if loader in ("fabric", "forge", "neoforge", "quilt"):
                return loader, version
        return "", ""


__all__ = ["ModpackCatalogError", "ModpackCatalogService"]
