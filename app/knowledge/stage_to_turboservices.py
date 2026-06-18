from __future__ import annotations

import os
from pathlib import Path


def resolve_turboservices_repo() -> Path:
    explicit = os.getenv("TURBOSERVICES_REPO_PATH")
    if explicit:
        repo = Path(explicit).resolve()
        if not repo.exists():
            raise FileNotFoundError(f"TURBOSERVICES_REPO_PATH bestaat niet: {repo}")
        return repo

    local_root = os.getenv("LOCAL_FS_ROOT")
    if not local_root:
        raise RuntimeError("LOCAL_FS_ROOT of TURBOSERVICES_REPO_PATH is verplicht.")

    repo = (Path(local_root).resolve() / "turboservices").resolve()
    if not repo.exists():
        raise FileNotFoundError(f"Turbo Services repo niet gevonden: {repo}")

    return repo


class TurboservicesMarkdownStager:
    def __init__(self):
        self.repo = resolve_turboservices_repo()
        self.target_dir = self.repo / "content" / "kennisbank-auto"

    def stage(self, slug: str, markdown: str, overwrite: bool = False) -> str:
        self.target_dir.mkdir(parents=True, exist_ok=True)
        target = (self.target_dir / f"{slug}.md").resolve()

        try:
            target.relative_to(self.repo)
        except Exception:
            raise PermissionError("Target pad valt buiten de turboservices repo.")

        if target.exists() and not overwrite:
            raise FileExistsError(f"Bestand bestaat al: {target}")

        target.write_text(markdown.strip() + "\n", encoding="utf-8", newline="\n")
        return str(target)