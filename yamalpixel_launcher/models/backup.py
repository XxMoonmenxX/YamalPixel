# models/backup.py
from datetime import datetime

class Backup:
    def __init__(self, name, path, timestamp=None, backup_type="unknown", size=None):
        self.name = name
        self.path = path
        self.timestamp = timestamp or datetime.now()
        self.type = backup_type # "mods", "world", "versions", "full"
        self.size = size # Опционально, размер бэкапа

    def to_dict(self):
        return {
            "name": self.name,
            "path": str(self.path), # Конвертируем Path в строку для JSON
            "timestamp": self.timestamp.isoformat(), # Конвертируем datetime в строку
            "type": self.type,
            "size": self.size
        }

    @classmethod
    def from_dict(cls, data):
        # Преобразуем строку timestamp обратно в datetime
        timestamp = datetime.fromisoformat(data["timestamp"])
        # Преобразуем строку path обратно в Path
        path = Path(data["path"])
        return cls(
            name=data["name"],
            path=path,
            timestamp=timestamp,
            backup_type=data.get("type", "unknown"),
            size=data.get("size")
        )

    def __repr__(self):
        return f"Backup(name='{self.name}', path='{self.path}', type='{self.type}', timestamp='{self.timestamp}')"
