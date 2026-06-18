# C:\Projects\marketing-agent\app\api\bulk_api.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
import os
import subprocess
from pathlib import Path
import shutil

from app.tools.website import WebsiteGenerator
from app.tools.content_engine import ContentEngine

router = APIRouter()


class BulkRequest(BaseModel):
    services: Optional[List[str]] = None   # default: alle
    regions: Optional[List[str]] = None    # default: alle
    include_diff: bool = False             # default: enkel has_changes
    limit: int = 25                        # combinaties per call
    offset: int = 0                        # startindex in combinatielijst


def _local_root() -> Path:
    base = os.getenv("LOCAL_FS_ROOT")
    if not base:
        raise HTTPException(status_code=500, detail="LOCAL_FS_ROOT niet ingesteld")
    return Path(base).resolve()


def _turboservices_repo() -> Path:
    root = _local_root()
    repo = (root / "turboservices").resolve()
    if not repo.exists():
        raise HTTPException(status_code=500, detail="turboservices repo niet gevonden onder LOCAL_FS_ROOT")
    return repo


def _stage(service: str, region: str) -> str:
    src = (Path("generated") / "pages" / service / region / "page.tsx").resolve()
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Bronbestand niet gevonden: {src.as_posix()}")

    repo = _turboservices_repo()
    dst = (repo / "app" / "diensten" / service / region / "page.tsx").resolve()

    try:
        dst.relative_to(repo)
    except Exception:
        raise HTTPException(status_code=403, detail="Toegang geweigerd: target buiten turboservices repo")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return str(dst)


def _diff(repo: Path, rel_file: str) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            ["git", "diff", "--", rel_file],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="git niet gevonden op dit systeem")

    out = (p.stdout or "").rstrip("\n")
    err = (p.stderr or "").rstrip("\n")
    if err:
        raise HTTPException(status_code=400, detail=err)

    return {"has_changes": (out.strip() != ""), "diff": out}


@router.post("/bulk")
def bulk_generate(req: BulkRequest):
    ce = ContentEngine()
    all_services = sorted(ce.services.keys())
    all_regions = sorted([r["slug"] for r in ce.regions])

    services = req.services or all_services
    regions = req.regions or all_regions

    # validatie input
    bad_services = [s for s in services if s not in all_services]
    bad_regions = [r for r in regions if r not in all_regions]
    if bad_services or bad_regions:
        raise HTTPException(
            status_code=400,
            detail={"unknown_services": bad_services, "unknown_regions": bad_regions},
        )

    # combinaties in vaste volgorde
    pairs: List[Tuple[str, str]] = [(s, r) for s in services for r in regions]
    total = len(pairs)

    # paging + cap
    limit = int(req.limit) if req.limit is not None else 25
    offset = int(req.offset) if req.offset is not None else 0

    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200
    if offset < 0:
        offset = 0
    if offset > total:
        offset = total

    start = offset
    end = min(start + limit, total)
    slice_pairs = pairs[start:end]

    gen = WebsiteGenerator()
    repo = _turboservices_repo()

    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for s, r in slice_pairs:
        try:
            tsx = gen.generate_page(s, r)
            gen.write_page_to_disk(s, r, tsx)

            target = _stage(s, r)

            rel = Path(target).resolve().relative_to(repo).as_posix()
            d = _diff(repo, rel)

            item: Dict[str, Any] = {
                "service": s,
                "region": r,
                "target": target,
                "has_changes": d["has_changes"],
            }
            if req.include_diff:
                item["diff"] = d["diff"]

            results.append(item)

        except Exception as e:
            # 1 combinatie faalt => log en ga verder
            errors.append({"service": s, "region": r, "error": str(e)})

    next_offset = end if end < total else None

    return {
        "ok": True,
        "total": total,
        "offset": start,
        "limit": limit,
        "count": len(results),
        "next_offset": next_offset,
        "results": results,
        "errors": errors,
        "error_count": len(errors),
    }