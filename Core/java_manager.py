"""Portable Java runtimes and per-launcher Java selection (no system changes)."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import re
import shutil
import stat
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import requests

logger = logging.getLogger("YamalPixel.JavaManager")
JAVA_VERSIONS = (8, 11, 16, 17, 21, 25)
MAX_DOWNLOAD_SIZE = 512 * 1024 * 1024
MAX_EXTRACTED_SIZE = 1536 * 1024 * 1024


class JavaInstallCancelled(RuntimeError):
    pass


def _cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise JavaInstallCancelled("Установка Java отменена")


def _game_dir(minecraft_dir):
    if minecraft_dir is None:
        from ConfDir.Configs import CONFIG
        minecraft_dir = CONFIG["minecraft_dir"]
    return Path(minecraft_dir)


def required_java_major(minecraft_version, minecraft_dir=None):
    """Prefer Mojang's local profile; historical ranges are only a fallback."""
    version = str(minecraft_version)
    if minecraft_dir is not None and re.fullmatch(r"[A-Za-z0-9_.+\-]+", version):
        profile = Path(minecraft_dir) / "versions" / version / (version + ".json")
        try:
            major = json.loads(profile.read_text(encoding="utf-8"))["javaVersion"]["majorVersion"]
            if isinstance(major, int) and not isinstance(major, bool) and 8 <= major <= 100:
                return major
        except (OSError, ValueError, KeyError, TypeError):
            pass
    match = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?(?:$|[-+ ])", version)
    if match:
        first, minor, patch = (int(value or 0) for value in match.groups())
        if first >= 26:
            return 25
        if first == 1:
            if minor >= 21 or (minor == 20 and patch >= 5):
                return 21
            if minor >= 18:
                return 17
            if minor == 17:
                return 16
            return 8
    # Unknown snapshots require manifest metadata, not a guessed newest runtime.
    raise ValueError(f"Не удалось определить Java для Minecraft {version}. Установите профиль игры, чтобы прочитать javaVersion.")


def probe_java(path, timeout=4):
    """Return a proven executable's identity; merely existing folders don't count."""
    executable = Path(os.path.expandvars(os.path.expanduser(str(path))))
    if executable.name.lower() == "javaw.exe":
        executable = executable.with_name("java.exe")
    if not executable.is_file():
        return None
    try:
        result = subprocess.run(
            [str(executable), "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        output = (result.stderr or "") + "\n" + (result.stdout or "")
        match = re.search(r'(?:openjdk|java)\s+(?:version\s+)?["\']?(\d+(?:[._+\-]\w+)*)', output, re.I)
        if result.returncode != 0 or not match:
            return None
        version = match.group(1)
        numbers = version.split(".")
        major_token = numbers[1] if numbers[0] == "1" and len(numbers) > 1 else numbers[0]
        major = int(re.match(r"\d+", major_token).group())
        vendor = next((name for name in ("Temurin", "Adoptium", "Microsoft", "Zulu", "GraalVM", "Oracle", "OpenJDK") if name.lower() in output.lower()), "Java")
        return {"path": str(executable.resolve()), "major": major, "version": version, "vendor": vendor}
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _java_candidates(minecraft_dir):
    game = _game_dir(minecraft_dir)
    selection = load_java_selection(game)
    if selection != "auto":
        yield Path(selection)
    home = os.environ.get("JAVA_HOME")
    if home:
        yield Path(home) / "bin" / "java.exe"
        yield Path(home) / "bin" / "java"
    for name in ("java.exe", "java"):
        found = shutil.which(name)
        if found:
            yield Path(found)
    # Inspect every PATH entry, including runtimes hidden behind an earlier Java.
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if directory:
            yield Path(directory.strip('"')) / ("java.exe" if os.name == "nt" else "java")
    roots = [game / "java-runtimes", game / "runtime", game / "java"]
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(variable)
        if base:
            roots.extend(Path(base) / vendor for vendor in ("Java", "Eclipse Adoptium", "Microsoft", "Zulu", "BellSoft", "Amazon Corretto"))
    roots.extend([Path.home() / ".jdks", Path.home() / ".minecraft" / "runtime"])
    if os.name != "nt":
        roots.extend([Path("/usr/lib/jvm"), Path("/Library/Java/JavaVirtualMachines")])
    for root in roots:
        if root.is_dir():
            try:
                # Bounded depth avoids scanning the whole disk or user profile.
                for pattern in ("bin/java*", "*/bin/java*", "*/*/bin/java*", "*/*/*/bin/java*"):
                    for candidate in root.glob(pattern):
                        if candidate.name.lower() in ("java", "java.exe"):
                            yield candidate
            except OSError:
                logger.debug("Cannot inspect Java folder %s", root, exc_info=True)


def discover_java(minecraft_dir=None, cancel_event=None):
    found, seen = [], set()
    for candidate in _java_candidates(minecraft_dir):
        _cancel(cancel_event)
        key = os.path.normcase(os.path.abspath(candidate))
        if key in seen:
            continue
        seen.add(key)
        info = probe_java(candidate)
        if info:
            resolved = os.path.normcase(info["path"])
            if not any(os.path.normcase(item["path"]) == resolved for item in found):
                found.append(info)
    return sorted(found, key=lambda item: (-item["major"], item["path"].lower()))


def load_java_selection(minecraft_dir=None):
    try:
        data = json.loads((_game_dir(minecraft_dir) / "launcher-java.json").read_text(encoding="utf-8"))
        value = data.get("selection", "auto")
        return value if isinstance(value, str) and value else "auto"
    except (OSError, ValueError, TypeError, AttributeError):
        return "auto"


def save_java_selection(minecraft_dir, selection):
    game = _game_dir(minecraft_dir)
    game.mkdir(parents=True, exist_ok=True)
    value = "auto" if selection in (None, "", "auto") else str(Path(selection).resolve())
    descriptor, temporary = tempfile.mkstemp(prefix=".launcher-java-", suffix=".json", dir=game)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump({"selection": value}, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, game / "launcher-java.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def select_java(minecraft_version, minecraft_dir, selection=None):
    """Auto uses the exact major to avoid old mod loaders failing on newer Java."""
    required = required_java_major(minecraft_version, minecraft_dir)
    selection = load_java_selection(minecraft_dir) if selection is None else selection
    if selection not in (None, "", "auto"):
        info = probe_java(selection)
        if not info:
            raise RuntimeError("Выбранная Java отсутствует или не запускается. Откройте «Версия JAVA» и выберите другую.")
        if info["major"] < required:
            raise RuntimeError(f"Для Minecraft {minecraft_version} нужна Java {required}, выбрана Java {info['major']}. Измените её в «Версия JAVA».")
        return info["path"]
    runtimes = discover_java(minecraft_dir)
    return next((item["path"] for item in runtimes if item["major"] == required), None)


def _https(url):
    parsed = urlparse(str(url))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("Источник Java вернул небезопасную ссылку")
    return str(url)


def _package(major, session):
    architecture = platform.machine().lower()
    arch = "aarch64" if architecture in ("arm64", "aarch64") else "x64" if architecture in ("amd64", "x86_64") else None
    if platform.system() != "Windows" or arch is None:
        raise RuntimeError("Автоустановка доступна для Windows x64/ARM64. Можно выбрать уже установленный java вручную.")
    for image_type in ("jre", "jdk"):
        with session.get(
            f"https://api.adoptium.net/v3/assets/latest/{major}/hotspot",
            params={"architecture": arch, "os": "windows", "image_type": image_type, "release_type": "ga", "vendor": "eclipse"},
            timeout=(8, 25),
        ) as response:
            if response.status_code == 404:
                continue
            response.raise_for_status()
            _https(response.url)
            for asset in response.json():
                package = asset.get("binary", {}).get("package", {})
                if str(package.get("name", "")).lower().endswith(".zip"):
                    checksum = str(package.get("checksum", ""))
                    size = package.get("size")
                    if not re.fullmatch(r"[a-fA-F0-9]{64}", checksum) or not isinstance(size, int) or not 0 < size <= MAX_DOWNLOAD_SIZE:
                        raise RuntimeError("Adoptium вернул некорректный размер или SHA256 Java")
                    return {"url": _https(package["link"]), "checksum": checksum.lower(), "size": size}
    raise RuntimeError(f"Adoptium сейчас не предлагает Java {major} для этой системы. Выберите java.exe вручную.")


def _extract_java(archive, destination, cancel_event=None):
    total = 0
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            _cancel(cancel_event)
            name = entry.filename.replace("\\", "/")
            parts = PurePosixPath(name).parts
            if not parts or name.startswith("/") or any(part in ("..", ".") or ":" in part for part in parts):
                raise RuntimeError("Архив Java содержит небезопасный путь")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise RuntimeError("Архив Java содержит символическую ссылку")
            total += entry.file_size
            if total > MAX_EXTRACTED_SIZE:
                raise RuntimeError("Слишком большой распакованный архив Java")
            target = destination.joinpath(*parts)
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(entry) as content, target.open("xb") as output:
                while chunk := content.read(1024 * 1024):
                    _cancel(cancel_event)
                    output.write(chunk)


def install_java(major, minecraft_dir, progress_callback=None, cancel_event=None):
    """Download official Temurin ZIP, verify SHA256, then atomically publish it."""
    major = int(major)
    if major not in JAVA_VERSIONS:
        raise ValueError("Неподдерживаемая версия Java")
    root = _game_dir(minecraft_dir) / "java-runtimes"
    root.mkdir(parents=True, exist_ok=True)

    def report(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    _cancel(cancel_event)
    report(0, f"Получение Java {major} с Adoptium…")
    with requests.Session() as session, tempfile.TemporaryDirectory(prefix=".install-", dir=root) as work:
        session.headers.update({"User-Agent": "YamalPixel/0.9.3", "Accept-Encoding": "identity"})
        package = _package(major, session)
        _cancel(cancel_event)
        archive = Path(work) / "java.zip"
        digest, downloaded, last = hashlib.sha256(), 0, 0.0
        with session.get(package["url"], stream=True, timeout=(8, 30)) as response:
            response.raise_for_status()
            _https(response.url)
            with archive.open("wb") as output:
                for chunk in response.iter_content(1024 * 256):
                    _cancel(cancel_event)
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > package["size"] or downloaded > MAX_DOWNLOAD_SIZE:
                        raise RuntimeError("Размер загрузки Java превышает заявленный")
                    output.write(chunk)
                    digest.update(chunk)
                    if time.monotonic() - last >= 0.1:
                        last = time.monotonic()
                        report(min(85, int(downloaded / package["size"] * 85)), f"Java {major}: {downloaded / 1048576:.1f} / {package['size'] / 1048576:.1f} МБ")
        if downloaded != package["size"] or digest.hexdigest() != package["checksum"]:
            raise RuntimeError("Проверка SHA256/размера Java не пройдена. Повторите загрузку.")
        report(88, "SHA256 проверен. Распаковка Java…")
        extracted = Path(work) / "unpacked"
        extracted.mkdir()
        _extract_java(archive, extracted, cancel_event)
        executables = list(extracted.glob("*/bin/java.exe")) + list(extracted.glob("bin/java.exe"))
        info = next((result for path in executables if (result := probe_java(path)) and result["major"] == major), None)
        if info is None:
            raise RuntimeError("Скачанная Java не запускается или имеет другую версию")
        _cancel(cancel_event)
        runtime = Path(info["path"]).parent.parent
        # New versioned folders preserve any runtime currently used by Minecraft.
        folder = f"temurin-{major}-{package['checksum'][:16]}"
        final = root / folder
        if final.exists():
            existing = probe_java(final / "bin" / "java.exe")
            if existing and existing["major"] == major:
                report(100, f"Java {major} уже установлена")
                return existing["path"]
            raise RuntimeError(f"Папка {final.name} уже существует, но Java в ней повреждена. Выберите другую Java или переименуйте эту папку.")
        os.replace(runtime, final)
        report(100, f"Java {major} установлена")
        return str(final / "bin" / "java.exe")
