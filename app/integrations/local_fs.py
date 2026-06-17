import os
import hashlib
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
    ".venv312",
    "venv",
    "__pycache__",
    "uploaded",
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


def _clamped_positive_int(value: int, default: int, hard_cap: int) -> int:
    if value <= 0:
        return default
    return min(value, hard_cap)


def _safe_search_roots(root_alias: str | None) -> Dict[str, Path]:
    roots = get_allowed_roots()

    if root_alias:
        root = roots.get(root_alias)
        if root is None:
            raise HTTPException(status_code=404, detail="Unknown filesystem root")
        return {root_alias: root}

    return roots


def _safe_walk(root: Path):
    for current, dirs, files in os.walk(root):
        current_path = Path(current).resolve()
        try:
            _assert_not_forbidden(current_path, root)
        except HTTPException:
            dirs[:] = []
            continue

        safe_dirs = []
        for dirname in dirs:
            try:
                _assert_not_forbidden((current_path / dirname).resolve(), root)
                safe_dirs.append(dirname)
            except HTTPException:
                continue
        dirs[:] = safe_dirs

        yield current_path, files


def _short_line(line: str) -> str:
    stripped = line.strip()
    return stripped[:300]


def _file_search_result(
    root_alias: str,
    root: Path,
    path: Path,
    query_l: str,
    max_file_size: int,
) -> dict | None:
    try:
        resolved = path.resolve()
        _assert_not_forbidden(resolved, root)

        if not resolved.is_file() or not is_text_file(resolved):
            return None

        size = resolved.stat().st_size
        if size > max_file_size:
            return None

        rel_path = _relative_path(resolved, root)
        path_matches = query_l in rel_path.lower()

        try:
            content = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None

        matched_lines = []
        for line_no, line in enumerate(content.splitlines(), start=1):
            if query_l in line.lower():
                matched_lines.append({"line": line_no, "text": _short_line(line)})
                if len(matched_lines) >= 5:
                    break

        if not path_matches and not matched_lines:
            return None

        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

        return {
            "root": root_alias,
            "path": rel_path,
            "match_type": "content" if matched_lines else "path",
            "sha256": sha256,
            "size": size,
            "matched_lines": matched_lines,
        }
    except Exception:
        return None


def search_workspace_files(
    query: str,
    root_alias: str | None = None,
    max_results: int = 50,
    max_file_size: int = 300000,
) -> list[dict]:
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")

    max_results = _clamped_positive_int(max_results, 50, 200)
    max_file_size = _clamped_positive_int(max_file_size, 300000, 1000000)
    query_l = query.lower()
    results = []

    for current_root_alias, root_path in _safe_search_roots(root_alias).items():
        for current_path, files in _safe_walk(root_path):
            for filename in files:
                result = _file_search_result(
                    root_alias=current_root_alias,
                    root=root_path,
                    path=current_path / filename,
                    query_l=query_l,
                    max_file_size=max_file_size,
                )
                if result is not None:
                    results.append(result)
                    if len(results) >= max_results:
                        return results

    return results


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


@router.get("/search")
def search_files(
    q: str,
    root: str | None = None,
    max_results: int = 50,
    max_file_size: int = 300000,
):
    query = q.strip()
    results = search_workspace_files(
        query=query,
        root_alias=root,
        max_results=max_results,
        max_file_size=max_file_size,
    )
    return {"ok": True, "query": query, "results": results}
