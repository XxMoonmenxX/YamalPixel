"""Official version catalogue, cached for offline launches. и тут поменял"""
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests

CURRENT_VERSION = "0.9.3"
_LOG = logging.getLogger(__name__)
CACHE_FILE = Path.home() / '.yamalpixel_cache' / 'versions.json'
version_configs = {'YamalPixel': ('1.20.1', 'fabric', '0.17.2'),
                   'Minecraft 1.20.1': ('1.20.1', None, None)}
fabric_supported_versions = ['YamalPixel']
quilt_supported_versions = []
forge_supported_versions = []
neoforge_supported_versions = []
all_versions = ['1.20.1']
_catalog = None


def _json(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def _fetch_loader(loader):
    from MCLIB.mod_loader import get_mod_loader
    impl = get_mod_loader(loader)
    return {'all': impl.get_minecraft_versions(False),
            'stable': impl.get_minecraft_versions(True)}


def refresh_catalog():
    global _catalog
    manifest = _json('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')
    if not isinstance(manifest.get('versions'), list) or not manifest['versions']:
        raise ValueError('Некорректный каталог Minecraft')
    loaders = {}
    errors = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {name: pool.submit(_fetch_loader, name) for name in ('fabric', 'quilt', 'forge', 'neoforge')}
        for name, job in jobs.items():
            try:
                loaders[name] = job.result()
            except Exception as exc:
                errors.append(name)
                loaders[name] = (_catalog or {}).get('loaders', {}).get(name, {'all': [], 'stable': []})
                _LOG.warning('Не удалось обновить каталог %s: %s', name, exc)
    catalog = {'versions': [{'id': v['id'], 'type': v['type']} for v in manifest['versions']], 'loaders': loaders}
    _catalog = catalog
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = CACHE_FILE.with_suffix('.tmp')
        temp.write_text(json.dumps(catalog, ensure_ascii=False), encoding='utf-8')
        os.replace(temp, CACHE_FILE)
    except OSError as exc:
        _LOG.warning('Не удалось сохранить каталог: %s', exc)
    apply_catalog(False)
    return errors


def apply_catalog(show_beta=False):
    configs = {'YamalPixel': ('1.20.1', 'fabric', '0.17.2')}
    versions = []
    for entry in (_catalog or {}).get('versions', [{'id': '1.20.1', 'type': 'release'}]):
        if entry['type'] != 'release' and not show_beta:
            continue
        mc = entry['id']
        versions.append(mc)
        configs[f'Minecraft {mc}'] = (mc, None, None)
        for loader, supported in (_catalog or {}).get('loaders', {}).items():
            if mc in supported.get('all' if show_beta else 'stable', []):
                configs[f'Minecraft {mc} + {dict(fabric="Fabric", quilt="Quilt", forge="Forge", neoforge="NeoForge")[loader]}'] = (mc, loader, None)
    version_configs.clear()
    version_configs.update(configs)
    all_versions[:] = versions
    for loader, items in [('fabric', fabric_supported_versions), ('quilt', quilt_supported_versions),
                          ('forge', forge_supported_versions), ('neoforge', neoforge_supported_versions)]:
        items[:] = [name for name, config in configs.items() if config[1] == loader]


def get_all_versions(show_beta=None):
    if show_beta is not None:
        apply_catalog(show_beta)
    from Core.collection_loader import load_all_collections
    return list(version_configs) + [f"📦 {c['name']}" for c in load_all_collections()]


def get_version_config(name):
    if name in version_configs:
        return version_configs[name]
    if name.startswith('📦 '):
        from Core.collection_loader import load_collection_data
        data = load_collection_data(name[2:])
        if data:
            return data['minecraft_version'], data['loader'], data.get('loader_version')
    # Allow a saved release or snapshot to launch even if currently filtered out.
    if name.startswith('Minecraft '):
        parts = name[len('Minecraft '):].split(' + ')
        mc = parts[0]
        if any(v['id'] == mc for v in (_catalog or {}).get('versions', [])):
            loader = parts[1].lower() if len(parts) == 2 else None
            if loader is None or mc in (_catalog or {}).get('loaders', {}).get(loader, {}).get('all', []):
                return mc, loader, None
    return None


def get_minecraft_version(name):
    config = get_version_config(name)
    if config is None:
        raise ValueError(f'Неизвестная версия: {name}')
    return config[0]


def is_modloader_needed(name):
    config = get_version_config(name)
    return config[1] if config else None


def get_all_version_configs():
    return {name: get_version_config(name) for name in get_all_versions()}


def load_user_collections():
    from Core.collection_loader import load_all_collections
    return load_all_collections()


try:
    _catalog = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    apply_catalog(False)
except (OSError, ValueError, KeyError, TypeError):
    _catalog = None
