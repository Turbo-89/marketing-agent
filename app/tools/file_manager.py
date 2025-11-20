import os
import json
from pathlib import Path

class FileManager:
    def __init__(self, base_path="generated"):
        self.base_path = base_path

    def ensure_dir(self, path: str):
        full = os.path.join(self.base_path, path)
        Path(full).mkdir(parents=True, exist_ok=True)
        return full

    def write_file(self, relative_path: str, content: str, overwrite=False):
        full = os.path.join(self.base_path, relative_path)

        if os.path.exists(full) and not overwrite:
            raise FileExistsError(f"File already exists: {full}")

        self.ensure_dir(os.path.dirname(relative_path))

        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

        return full

    def file_exists(self, relative_path: str):
        return os.path.exists(os.path.join(self.base_path, relative_path))
