# SPDX-FileCopyrightText: Copyright (c) 2019-2025 JakobDev and contributors
# SPDX-License-Identifier: BSD-2-Clause
"""NeoForge metadata and installation through the official installer."""
import json
import os
import re
import subprocess
import tempfile
import zipfile
import requests
from .._helper import empty, SUBPROCESS_STARTUP_INFO
from ..vanilla_launcher import do_vanilla_launcher_profiles_exists, create_empty_vanilla_launcher_profiles_file
from ..types import CallbackDict
from ._base import ModLoaderBase

_API_URL = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"


def version_key(version):
    numbers = tuple(int(n) for n in re.findall(r"\d+", version.split("-", 1)[0]))
    return numbers, not is_beta(version), version


def is_beta(version):
    return any(marker in version.lower() for marker in ("beta", "alpha", "snapshot", "-rc", "-pre"))


class Neoforge(ModLoaderBase):
    def get_id(self):
        return "neoforge"

    def get_name(self):
        return "NeoForge"

    def _normalize_minecraft_version(self, version):
        return version.removesuffix('.0') if int(version.split('.')[0]) >= 26 else "1." + version.removesuffix(".0")

    def _versions(self):
        response = requests.get(_API_URL, timeout=20)
        response.raise_for_status()
        return [v for v in response.json()["versions"] if re.match(r"^\d+\.\d+", v) and not v.startswith("0.")]

    def _minecraft_version(self, loader_version):
        parts = loader_version.split('-')[0].split('.')
        length = 3 if int(parts[0]) >= 26 else 2
        return self._normalize_minecraft_version('.'.join(parts[:length]))

    def get_minecraft_versions(self, stable_only):
        versions = {self._minecraft_version(v)
                    for v in self._versions() if not stable_only or not is_beta(v)}
        return sorted(versions, key=version_key, reverse=True)

    def get_loader_versions(self, minecraft_version, stable_only):
        return sorted([v for v in self._versions()
                       if self._minecraft_version(v) == minecraft_version
                       and (not stable_only or not is_beta(v))], key=version_key, reverse=True)

    def get_installer_url(self, minecraft_version, loader_version):
        return f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{loader_version}/neoforge-{loader_version}-installer.jar"

    def _try_download_from_sources(self, loader_version, temp_path, callback):
        suffix = f"net/neoforged/neoforge/{loader_version}/neoforge-{loader_version}-installer.jar"
        errors = []
        for base in ("https://maven.neoforged.net/releases/", "https://maven.creeperhost.net/"):
            part = temp_path + ".part"
            try:
                callback.get("setStatus", empty)("Downloading NeoForge installer")
                with requests.get(base + suffix, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    with open(part, "wb") as output:
                        for chunk in response.iter_content(65536):
                            if chunk:
                                output.write(chunk)
                with zipfile.ZipFile(part) as archive:
                    if "install_profile.json" not in archive.namelist() or archive.testzip() is not None:
                        raise ValueError("Invalid NeoForge installer")
                os.replace(part, temp_path)
                return True
            except (requests.RequestException, OSError, ValueError, zipfile.BadZipFile) as exc:
                errors.append(str(exc))
            finally:
                if os.path.exists(part):
                    os.remove(part)
        callback.get("setStatus", empty)("Installer download failed: " + "; ".join(errors))
        return False

    def get_installed_version(self, minecraft_version, loader_version):
        return f"neoforge-{loader_version}"

    def install(self, minecraft_version, minecraft_directory, callback: CallbackDict, java, loader_version):
        if not do_vanilla_launcher_profiles_exists(minecraft_directory):
            create_empty_vanilla_launcher_profiles_file(minecraft_directory)
        version = self.get_installed_version(minecraft_version, loader_version)
        profile = os.path.join(minecraft_directory, 'versions', version, version + '.json')
        previous = None
        if os.path.isfile(profile):
            with open(profile, 'rb') as source:
                previous = source.read()
        try:
            with tempfile.TemporaryDirectory(prefix="mclib-neoforge-") as tempdir:
                installer = os.path.join(tempdir, "installer.jar")
                if not self._try_download_from_sources(loader_version, installer, callback):
                    raise RuntimeError(f"Не удалось скачать установщик NeoForge {loader_version}")
                callback.get("setStatus", empty)("Running NeoForge installer")
                subprocess.run([java, "-jar", installer, "--install-client", minecraft_directory],
                               cwd=tempdir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               startupinfo=SUBPROCESS_STARTUP_INFO)
            with open(profile, encoding='utf-8') as source:
                data = json.load(source)
            if data.get('id') != version or data.get('inheritsFrom') != minecraft_version:
                raise RuntimeError('Установщик создал несовместимый профиль NeoForge')
        except Exception:
            if previous is not None:
                with open(profile, 'wb') as output:
                    output.write(previous)
            elif os.path.isfile(profile):
                os.remove(profile)
            raise
        callback.get('setStatus', empty)('NeoForge installed successfully')
