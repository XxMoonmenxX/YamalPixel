# models/collection.py
from models.mod import Mod

class Collection:
    def __init__(self, name, minecraft_version, loader, mods, description=""):
        self.name = name
        self.minecraft_version = minecraft_version
        self.loader = loader # fabric, forge, vanilla
        self.mods = [Mod.from_dict(m) if isinstance(m, dict) else m for m in mods] # Приведение к объектам Mod
        self.description = description

    def to_dict(self):
        return {
            "name": self.name,
            "minecraft_version": self.minecraft_version,
            "loader": self.loader,
            "mods": [m.to_dict() for m in self.mods],
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"Collection(name='{self.name}', version='{self.minecraft_version}', loader='{self.loader}', mod_count={len(self.mods)})"
