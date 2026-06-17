import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.integrations.local_fs import search_workspace_files

router = APIRouter()

DEFAULT_MAX_FILES = 12
MAX_FILES_CAP = 30
STABLE_SEARCH_TERMS = [
    "service",
    "services",
    "landing",
    "landingspagina",
    "seo",
    "metadata",
    "schema",
    "routes",
    "content",
]


def _clamp_max_files(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        return DEFAULT_MAX_FILES
    return min(value, MAX_FILES_CAP)


def _extract_search_queries(task: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_.-]+", task.lower())
    queries: list[str] = []
    seen = set()

    for word in words:
        if len(word) < 3 or word in seen:
            continue
        seen.add(word)
        queries.append(word)

    task_l = task.lower()
    should_add_project_terms = any(
        term in task_l
        for term in ("workspace", "chat", "agent", "landing", "landingspagina", "seo", "schema", "metadata")
    )
    for term in STABLE_SEARCH_TERMS:
        if should_add_project_terms and term not in seen:
            seen.add(term)
            queries.append(term)

    return queries[:16]


def _normalise_roots(value: Any) -> list[str | None]:
    if value is None:
        return [None]
    if not isinstance(value, list):
        raise HTTPException(status_code=400, detail="roots must be a list")

    roots = []
    for item in value:
        if isinstance(item, str) and item.strip():
            roots.append(item.strip())
    return roots or [None]


def _context_reason(existing: str | None, query: str) -> str:
    reason = f"matched query: {query}"
    return existing or reason


@router.post("/build")
async def build_context(request: Request):
    payload = await request.json()
    task = payload.get("task")
    if not isinstance(task, str) or not task.strip():
        raise HTTPException(status_code=400, detail="task is required")

    task = task.strip()
    max_files = _clamp_max_files(payload.get("max_files"))
    roots = _normalise_roots(payload.get("roots"))
    search_queries = _extract_search_queries(task)
    context_by_path: dict[tuple[str, str], dict] = {}

    for query in search_queries:
        for root in roots:
            results = search_workspace_files(
                query=query,
                root_alias=root,
                max_results=max_files,
            )
            for result in results:
                key = (result["root"], result["path"])
                current = context_by_path.get(key)
                if current is None:
                    context_by_path[key] = {
                        **result,
                        "reason": f"matched query: {query}",
                    }
                else:
                    current["reason"] = _context_reason(current.get("reason"), query)

                if len(context_by_path) >= max_files:
                    return {
                        "ok": True,
                        "task": task,
                        "search_queries": search_queries,
                        "context_files": list(context_by_path.values())[:max_files],
                    }

    return {
        "ok": True,
        "task": task,
        "search_queries": search_queries,
        "context_files": list(context_by_path.values())[:max_files],
    }
