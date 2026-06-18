# C:\Projects\marketing-agent\app\api\diff_api.py

import os
import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class DiffRequest(BaseModel):
    # pad binnen turboservices repo, bv: "app/diensten/ontstoppingen/scheldeland/page.tsx"
    file: str

def _repo_root() -> Path:
    base = os.getenv("LOCAL_FS_ROOT")
    if not base:
        raise HTTPException(status_code=500, detail="LOCAL_FS_ROOT niet ingesteld")
    root = Path(base).resolve()
    repo = (root / "turboservices").resolve()
    if not repo.exists():
        raise HTTPException(status_code=500, detail="turboservices repo niet gevonden onder LOCAL_FS_ROOT")
    return repo

def _safe_repo_relpath(repo: Path, rel: str) -> Path:
    rp = (rel or "").replace("\\", "/").lstrip("/")
    if rp == "":
        raise HTTPException(status_code=400, detail="file is verplicht")

    # blokkeer drive letters / absolute paden
    first = rp.split("/")[0]
    if ":" in first:
        raise HTTPException(status_code=403, detail="Toegang geweigerd: absoluut pad niet toegestaan")

    full = (repo / rp).resolve()

    # enforce: binnen repo
    try:
        full.relative_to(repo)
    except Exception:
        raise HTTPException(status_code=403, detail="Toegang geweigerd: buiten turboservices repo")

    return full

@router.post("/diff")
def diff_file(req: DiffRequest):
    repo = _repo_root()
    full = _safe_repo_relpath(repo, req.file)

    # We diffen relatief t.o.v. repo
    rel = full.relative_to(repo).as_posix()

    try:
        p = subprocess.run(
            ["git", "diff", "--", rel],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="git niet gevonden op dit systeem")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"git diff fout: {str(e)}")

    # git diff exit code is meestal 0 (geen diff) of 1 (wel diff) afhankelijk van context; we gebruiken output
    out = (p.stdout or "").rstrip("\n")
    err = (p.stderr or "").rstrip("\n")

    if err:
        # bv. als rel niet bestaat in repo
        raise HTTPException(status_code=400, detail=err)

    return {
        "ok": True,
        "file": rel,
        "diff": out,          # leeg = geen wijzigingen
        "has_changes": (out.strip() != ""),
    }