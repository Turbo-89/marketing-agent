import os
from pathlib import Path
import asyncio

class DirectoryEngine:
    def __init__(self, base="generated"):
        self.base = Path(base)

    async def run_async(self, relative_path: str):
        return await asyncio.to_thread(self.ensure, relative_path)

    def run(self, relative_path: str):
        return self.ensure(relative_path)

    def ensure(self, relative_path: str):
        path = self.base / relative_path
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def exists(self, relative_path: str):
        return (self.base / relative_path).exists()
