import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = BASE_DIR / "generated"

PAGES_DIR = GENERATED_DIR / "pages"
IMAGES_DIR = GENERATED_DIR / "images"
PLANS_DIR = GENERATED_DIR / "plans"

# Zorg dat alle directories bestaan
for d in [PAGES_DIR, IMAGES_DIR, PLANS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class StorageService:
    @staticmethod
    def save_page(filename: str, content: str) -> str:
        path = PAGES_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(path)

    @staticmethod
    def save_plan(filename: str, content: str) -> str:
        path = PLANS_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(path)

    @staticmethod
    def save_image(filename: str, binary: bytes) -> str:
        path = IMAGES_DIR / filename
        with open(path, "wb") as f:
            f.write(binary)
        return str(path)
