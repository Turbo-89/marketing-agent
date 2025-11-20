import os

class FileWriter:
    def __init__(self, base="generated"):
        self.base = base

    def write(self, relative_path: str, content: str, overwrite=False):
        full_path = os.path.join(self.base, relative_path)

        if os.path.exists(full_path) and not overwrite:
            raise FileExistsError(f"Bestand bestaat al: {full_path}")

        folder = os.path.dirname(full_path)
        os.makedirs(folder, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return full_path
