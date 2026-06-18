# C:\Projects\marketing-agent\app\api\stage_api.py

import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class StagePageRequest(BaseModel):
    service: str
    region: str

def _require_local_root() -> Path:
    base = os.getenv("LOCAL_FS_ROOT")
    if not base:
        raise HTTPException(status_code=500, detail="LOCAL_FS_ROOT niet ingesteld")
    return Path(base).resolve()

@router.post("/stage/page")
def stage_page(req: StagePageRequest):
    # Source: marketing-agent generated output
    src = (Path("generated") / "pages" / req.service / req.region / "page.tsx").resolve()
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Bronbestand niet gevonden: {src.as_posix()}")

    # Target: local turboservices repo under LOCAL_FS_ROOT
    root = _require_local_root()

    # We verwachten dat turboservices binnen LOCAL_FS_ROOT staat als 'turboservices'
    repo = (root / "turboservices").resolve()

    try:
        repo.relative_to(root)
    except Exception:
        raise HTTPException(status_code=500, detail="Interne fout: turboservices repo ligt niet binnen LOCAL_FS_ROOT")

    dst = (repo / "app" / "diensten" / req.service / req.region / "page.tsx").resolve()

    # Enforce: dst blijft binnen repo
    try:
        dst.relative_to(repo)
    except Exception:
        raise HTTPException(status_code=403, detail="Toegang geweigerd: target buiten turboservices repo")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

    return {
        "ok": True,
        "source": str(src),
        "target": str(dst),
        "bytes": src.stat().st_size,
    }