import os
from datetime import datetime

class Log:
    def __init__(self, path="generated/logs/continuous.log"):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def write(self, message: str):
        ts = datetime.now().isoformat()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {message}\n")
