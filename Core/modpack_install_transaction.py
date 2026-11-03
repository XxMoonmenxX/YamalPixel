"""Publish a prepared modpack and recover interrupted collection registration."""
import json
import logging
import os
import uuid
from pathlib import Path

from Core import instances
from Core.mod_transaction import safe_filename, safe_target

logger = logging.getLogger(__name__)
JOURNAL_NAME = '.modpack-install.json'
MAX_JOURNAL_BYTES = 16 * 1024 * 1024


class ModpackRegistrationError(RuntimeError):
    """The instance is safe, but its collection registration needs attention."""


def collection_filename(name):
    if not isinstance(name, str):
        raise ValueError('Неверное название сборки')
    name = ''.join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
    if not name:
        raise ValueError('Название сборки не содержит допустимых символов')
    return safe_filename(name + '.json')


def _collection_data(metadata):
    name = metadata.get('name')
    filename = collection_filename(name)
    raw_mods = metadata.get('mods', [])
    if not isinstance(raw_mods, list):
        raise ValueError('Неверный список модов')
    mods = []
    for raw in raw_mods:
        if not isinstance(raw, dict):
            raise ValueError('Неверные сведения о моде')
        mod = dict(raw)
        mod_filename = mod.get('filename') or f"{mod.get('name', 'mod')}.jar"
        safe_filename(mod_filename)
        mod['filename'] = mod_filename
        mod.setdefault('name', Path(mod_filename).stem)
        mods.append(mod)
    return {
        'name': name, 'minecraft_version': metadata.get('minecraft_version', ''),
        'loader': metadata.get('loader', ''), 'loader_version': metadata.get('loader_version', ''),
        'mods': mods, 'mod_count': len(mods), 'source': 'mrpack',
        'collection_type': 'modpack', 'mrpack_installed': True,
        'instance_id': 'file:' + filename, '_modpack_transaction_id': uuid.uuid4().hex,
    }


def _collection_path(data):
    from Core.collection_loader import get_collections_dir
    filename = collection_filename(data['name'])
    if data.get('instance_id') != 'file:' + filename:
        raise ValueError('Неверный идентификатор инстанса')
    return Path(safe_target(get_collections_dir(), filename))


def _already_saved(data):
    try:
        path = _collection_path(data)
        if path.stat().st_size > MAX_JOURNAL_BYTES:
            return False
        with path.open(encoding='utf-8') as stream:
            saved = json.load(stream)
        return (isinstance(saved, dict) and
                saved.get('_modpack_transaction_id') == data['_modpack_transaction_id'] and
                saved.get('instance_id') == data['instance_id'])
    except (OSError, ValueError, KeyError, TypeError):
        return False


def _finish_registration(directory, data):
    from Core.collection_loader import save_collection
    if not _already_saved(data):
        try:
            success, detail = save_collection(dict(data))
        except Exception as exc:
            success, detail = False, str(exc)
        # A write may have succeeded even if temporary-file cleanup failed;
        # another launcher may also have completed the same transaction.
        if not success and not _already_saved(data):
            raise ModpackRegistrationError(
                f'Не удалось сохранить JSON сборки: {detail}. '
                f'Данные сохранены в {directory}. После устранения ошибки перезапустите лаунчер '
                'или обновите список версий: сохранение повторится автоматически.')
    try:
        (directory / JOURNAL_NAME).unlink(missing_ok=True)
    except OSError:
        logger.warning('Не удалось удалить завершённый журнал установки %s', directory, exc_info=True)
    return data


def publish_collection_instance(staged_instance, destination, metadata):
    """Publish fully prepared files, retaining a durable registration journal."""
    staged_instance, destination = Path(staged_instance), Path(destination)
    data = _collection_data(metadata)
    expected = instances.collection_directory(data)
    if destination.absolute() != expected.absolute():
        raise ValueError('Папка инстанса не соответствует имени сборки')
    path = _collection_path(data)
    if path.exists() or path.is_symlink():
        raise FileExistsError('Сборка с таким именем уже существует')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Инстанс с таким именем уже существует')
    journal = staged_instance / JOURNAL_NAME
    payload = {'version': 1, 'collection': data}
    encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
    if len(encoded) > MAX_JOURNAL_BYTES:
        raise ValueError('Метаданные сборки слишком велики')
    # A pack must not pre-create the reserved journal, including as a link.
    with journal.open('xb') as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Инстанс с таким именем уже существует')
    os.rename(staged_instance, destination)
    return _finish_registration(destination, data)


def recover_pending_modpacks():
    """Retry saved journals without replacing any existing collection or files."""
    root = instances.launcher_root() / 'instances'
    if root.is_symlink() or not root.is_dir():
        return []
    recovered = []
    try:
        directories = list(root.iterdir())
    except OSError:
        logger.warning('Не удалось проверить незавершённые установки', exc_info=True)
        return recovered
    for directory in directories:
        try:
            if directory.is_symlink() or not directory.is_dir():
                continue
            if hasattr(directory, 'is_junction') and directory.is_junction():
                continue
            journal = directory / JOURNAL_NAME
            if journal.is_symlink() or not journal.is_file() or journal.stat().st_size > MAX_JOURNAL_BYTES:
                continue
            with journal.open(encoding='utf-8') as stream:
                record = json.load(stream)
            data = record['collection']
            transaction_id = data.get('_modpack_transaction_id', '')
            if (record.get('version') != 1 or not isinstance(data, dict) or
                    not isinstance(transaction_id, str) or len(transaction_id) != 32 or
                    any(c not in '0123456789abcdef' for c in transaction_id) or
                    data.get('source') != 'mrpack' or data.get('mrpack_installed') is not True or
                    not isinstance(data.get('mods'), list) or
                    not isinstance(data.get('minecraft_version'), str) or
                    not isinstance(data.get('loader'), str)):
                raise ValueError('Некорректный журнал установки')
            _collection_path(data)
            if instances.collection_directory(data).absolute() != directory.absolute():
                raise ValueError('Журнал относится к другому инстансу')
            _finish_registration(directory, data)
            recovered.append(data)
        except (OSError, ValueError, TypeError, KeyError, AttributeError, ModpackRegistrationError):
            logger.warning('Не удалось восстановить установку модпака в %s', directory, exc_info=True)
    return recovered
