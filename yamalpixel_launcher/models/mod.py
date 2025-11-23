# models/mod.py

class Mod:
    def __init__(self, name=None, file=None, url=None, project_id=None, version_id=None, sha512=None):
        self.name = name
        self.file = file
        self.url = url # или использовать project_id/version_id
        self.project_id = project_id
        self.version_id = version_id
        self.sha512 = sha512 # Опционально, для проверки целостности
        # и другие поля по необходимости

    def to_dict(self):
        return {
            "name": self.name,
            "file": self.file,
            "url": self.url,
            "project_id": self.project_id,
            "version_id": self.version_id,
            "sha512": self.sha512
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"Mod(name='{self.name}', file='{self.file}', url='{self.url}')"

    def __eq__(self, other):
        if not isinstance(other, Mod):
            return False
        return self.file == other.file # Сравниваем по имени файла как основному идентификатору

    def __hash__(self):
        return hash(self.file) # Хэшируем по имени файла
