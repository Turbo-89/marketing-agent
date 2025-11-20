import os
from pathlib import Path

class DirectoryEngine:
    def __init__(self, base="generated"):
        self.base = base

    def ensure(self, relative_path: str):
        path = os.path.join(self.base, relative_path)
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def exists(self, relative_path: str):
        return os.path.exists(os.path.join(self.base, relative_path))
