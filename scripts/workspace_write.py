import json
import sys
import urllib.request
from pathlib import Path

API_URL = "http://127.0.0.1:8000/api/fs/write"


def main():
    if len(sys.argv) != 3:
        print("Gebruik: python scripts/workspace_write.py <target_path> <source_file>")
        sys.exit(1)

    target_path = sys.argv[1]
    source_file = Path(sys.argv[2])

    if not source_file.exists():
        print(f"Bronbestand niet gevonden: {source_file}")
        sys.exit(1)

    content = source_file.read_text(encoding="utf-8")

    payload = {
        "path": target_path,
        "content": content,
        "overwrite": True,
        "encoding": "utf-8",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode("utf-8"))


if __name__ == "__main__":
    main()