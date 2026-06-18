import json
import sys
import urllib.parse
import urllib.request

API_URL = "http://127.0.0.1:8000/api/fs/hash"


def main():
    if len(sys.argv) != 2:
        print("Gebruik: python scripts/workspace_verify.py <target_path>")
        sys.exit(1)

    target_path = sys.argv[1]
    url = f"{API_URL}?path={urllib.parse.quote(target_path)}"

    req = urllib.request.Request(url, method="GET")

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()