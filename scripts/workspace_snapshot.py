import shutil
import sys
from pathlib import Path
from datetime import datetime


def main():
    if len(sys.argv) not in (2, 3):
        print("Gebruik: python scripts/workspace_snapshot.py <source_path> [output_zip_base]")
        sys.exit(1)

    source = Path(sys.argv[1]).resolve()
    if not source.exists():
        print(f"Bronpad niet gevonden: {source}")
        sys.exit(1)

    if len(sys.argv) == 3:
        output_base = Path(sys.argv[2]).resolve()
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_base = Path.cwd() / "generated" / "snapshots" / f"{source.name}-snapshot-{ts}"

    output_base.parent.mkdir(parents=True, exist_ok=True)

    archive_path = shutil.make_archive(
        base_name=str(output_base),
        format="zip",
        root_dir=str(source.parent),
        base_dir=str(source.name),
    )

    print(archive_path)


if __name__ == "__main__":
    main()