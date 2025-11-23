# models/java_info.py

class JavaInfo:
    def __init__(self, path="java", major_version=None, full_version=None, is_valid=False):
        self.path = path
        self.major_version = major_version
        self.full_version = full_version
        self.is_valid = is_valid

    def to_dict(self):
        return {
            "path": self.path,
            "major_version": self.major_version,
            "full_version": self.full_version,
            "is_valid": self.is_valid
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"JavaInfo(path='{self.path}', major_version={self.major_version}, is_valid={self.is_valid})"
