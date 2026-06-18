import os
import asyncio
from pathlib import Path

class FileWriter:
    def __init__(self, base="generated"):
        self.base = Path(base)

    async def run_async(self, relative_path: str, content: str, overwrite=False):
        return await asyncio.to_thread(
            self.write, relative_path, content, overwrite
        )

    def run(self, relative_path: str, content: str, overwrite=False):
        return self.write(relative_path, content, overwrite)

    def write(self, relative_path: str, content: str, overwrite=False):
        full_path = self.base / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if full_path.exists() and not overwrite:
            raise FileExistsError(f"Bestand bestaat al: {full_path}")

        full_path.write_text(content, encoding="utf-8")
        return str(full_path)
