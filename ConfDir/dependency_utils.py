## ConfDir/dependency_utils.py
import os
from typing import List, Dict
from ConfDir.Configs import CONFIG, CURSEFORGE_CONFIG


def check_missing_dependencies(collection_data: Dict) -> List[Dict]:
    """Проверяет наличие обязательных зависимостей"""
    missing = []
    mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")

    if not os.path.exists(mods_dir):
        return collection_data.get("mods", [])  # Все моды отсутствуют

    existing_files = set(os.listdir(mods_dir))

    for mod in collection_data.get("mods", []):
        filename = mod.get("filename")
        if filename and filename not in existing_files:
            missing.append(mod)

        # Проверяем зависимости мода
        for dep in mod.get("resolved_dependencies", []):
            if dep.get("dependency_type") == "required":
                dep_filename = f"{dep.get('modrinth_slug', 'mod')}.jar"
                if dep_filename not in existing_files:
                    missing.append({
                        "name": dep["name"],
                        "filename": dep_filename,
                        "source": dep["source"],
                        "mod_id": dep.get("modrinth_id") or dep.get("curseforge_id")
                    })

    return missing


def download_missing_dependencies(missing_deps: List[Dict]):
    """Загружает недостающие зависимости"""
    from Network.ModrinthLoader import ModrinthAPI
    from Network.CurseForgeLoader import CurseForgeAPI

    modrinth_api = ModrinthAPI()
    curseforge_api = None

    if CURSEFORGE_CONFIG.get("enabled", False):
        try:
            proxy_url = CURSEFORGE_CONFIG.get("proxy_url", "http://localhost:8000")
            curseforge_api = CurseForgeAPI(proxy_url)
        except:
            pass

    mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
    os.makedirs(mods_dir, exist_ok=True)

    for dep in missing_deps:
        try:
            source = dep.get("source")
            mod_id = dep.get("mod_id")

            if source == "modrinth" and mod_id:
                # Получаем последнюю версию для текущей версии MC
                versions = modrinth_api.get_mod_versions(
                    mod_id,
                    CONFIG.get("version", "1.20.1"),
                    CONFIG.get("loader_type", "fabric").lower()
                )

                if versions:
                    latest = versions[0]
                    if latest["files"]:
                        file_info = latest["files"][0]
                        filename = file_info["filename"]

                        modrinth_api.download_mod(
                            mod_id,
                            latest["id"],
                            filename,
                            mods_dir
                        )

            elif source == "curseforge" and curseforge_api and mod_id:
                # Загрузка через CurseForge API
                versions = curseforge_api.get_mod_versions(
                    mod_id,
                    CONFIG.get("version", "1.20.1"),
                    CONFIG.get("loader_type", "fabric").lower()
                )

                if versions:
                    version_info = versions[0]
                    filename = version_info.get("filename", f"mod-{mod_id}.jar")

                    curseforge_api.download_mod(
                        mod_id,
                        version_info["id"],
                        filename,
                        mods_dir
                    )

        except Exception as e:
            print(f"Ошибка загрузки зависимости {dep.get('name')}: {e}")