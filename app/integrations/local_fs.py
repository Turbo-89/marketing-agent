import os
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException

router = APIRouter()

ROOT_ENV_VARS = {
    "workspace": "WORKSPACE_ROOT",
    "marketing_agent": "MARKETING_AGENT_ROOT",
    "turbo_ui": "TURBO_UI_ROOT",
    "turboservices": "TURBOSERVICES_ROOT",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".css",
    ".html",
    ".sql",
    ".sh",
    ".ps1",
}

TEXT_FILENAMES = {".env.example"}

FORBIDDEN_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "service_account.json",
}

FORBIDDEN_PARTS = {
    ".git",
    ".next",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
}


def get_allowed_roots() -> Dict[str, Path]:
    roots: Dict[str, Path] = {}

    for alias, env_name in ROOT_ENV_VARS.items():
        value = os.getenv(env_name)
        if value:
            roots[alias] = Path(value).expanduser().resolve()

    return roots


def _normalise_rel_path(rel_path: str | None) -> str:
    raw = rel_path or ""
    if raw.startswith(("/", "\\")):
        raise HTTPException(status_code=403, detail="Absolute paths are not allowed")

    rel = raw.replace("\\", "/")
    first_part = rel.split("/")[0] if rel else ""

    if ":" in first_part:
        raise HTTPException(status_code=403, detail="Absolute paths are not allowed")

    return rel


def _assert_not_forbidden(path: Path, root: Path) -> None:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        raise HTTPException(status_code=403, detail="Path is outside the scoped root")

    for part in rel_parts:
        part_l = part.lower()
        if part_l in FORBIDDEN_PARTS:
            raise HTTPException(status_code=403, detail="Path part is not allowed")
        if _is_forbidden_filename(part_l):
            raise HTTPException(status_code=403, detail="File is not allowed")


def _is_forbidden_filename(name: str) -> bool:
    if name in FORBIDDEN_FILENAMES:
        return True
    return name.endswith(".json") and ("oauth" in name or "token" in name)


def resolve_scoped_path(root_alias: str, rel_path: str | None) -> Path:
    roots = get_allowed_roots()
    root = roots.get(root_alias)

    if root is None:
        raise HTTPException(status_code=404, detail="Unknown filesystem root")

    rel = _normalise_rel_path(rel_path)
    target = (root / rel).resolve() if rel else root

    try:
        target.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Path is outside the scoped root")

    _assert_not_forbidden(target, root)
    return target


def is_text_file(path: Path) -> bool:
    name = path.name.lower()
    return name in TEXT_FILENAMES or path.suffix.lower() in TEXT_EXTENSIONS


def _relative_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    return "" if rel == "." else rel


def _safe_entry(path: Path, root: Path) -> dict | None:
    try:
        _assert_not_forbidden(path.resolve(), root)
    except HTTPException:
        return None

    return {
        "name": path.name,
        "path": _relative_path(path, root),
        "dir": path.is_dir(),
        "size": path.stat().st_size if path.is_file() else None,
    }


@router.get("/roots")
def roots():
    return {
        "ok": True,
        "roots": [{"alias": alias} for alias in sorted(get_allowed_roots())],
    }


@router.get("/list")
def list_dir(root: str, path: str = ""):
    base = get_allowed_roots().get(root)
    full = resolve_scoped_path(root, path)

    if base is None:
        raise HTTPException(status_code=404, detail="Unknown filesystem root")
    if not full.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    entries = []
    for item in sorted(full.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        entry = _safe_entry(item, base)
        if entry is not None:
            entries.append(entry)

    return {
        "ok": True,
        "root": root,
        "path": _relative_path(full, base),
        "entries": entries,
    }


@router.get("/read")
def read_file(root: str, path: str):
    base = get_allowed_roots().get(root)
    full = resolve_scoped_path(root, path)

    if base is None:
        raise HTTPException(status_code=404, detail="Unknown filesystem root")
    if not full.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not is_text_file(full):
        raise HTTPException(status_code=403, detail="File type is not allowed")

    try:
        content = full.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="File is not valid UTF-8 text")

    return {
        "ok": True,
        "root": root,
        "path": _relative_path(full, base),
        "content": content,
    }
