import os
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.integrations.local_fs import search_workspace_files
from app.integrations.service_intent import resolve_service_intent

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
STOPWORDS = {
    "maak",
    "maken",
    "plan",
    "voor",
    "een",
    "de",
    "het",
    "en",
    "met",
    "van",
    "op",
    "in",
    "te",
    "om",
    "als",
    "naar",
    "geef",
    "welke",
    "make",
    "create",
    "for",
    "with",
    "the",
    "a",
    "an",
    "and",
    "of",
    "to",
    "on",
}
USEFUL_SHORT_TERMS = {"seo", "ai", "ga4"}
ROOKDETECTIE_QUERIES = [
    "rookdetectie",
    "rook detectie",
    "rooktest",
    "geurdetectie",
    "geuropsporing",
    "rioolgeur",
    "riolering",
    "riool",
    "ontstopping",
]
GEUR_QUERIES = [
    "geurdetectie",
    "geuropsporing",
    "rooktest",
    "riolering",
    "riool",
]
LANDING_QUERIES = [
    "landingspagina",
    "landing",
    "metadata",
    "seo",
    "schema",
    "services",
    "service",
    "routes",
    "content",
]
GOVERNANCE_TERMS = ("governance", "session", "protocol", "checklist")
SERVICE_PATH_TERMS = (
    "services",
    "service",
    "dienst",
    "landingspagina",
    "metadata",
    "schema",
    "seo",
    "route",
    "routes",
    "page",
    "content",
)


def _clamp_max_files(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        return DEFAULT_MAX_FILES
    return min(value, MAX_FILES_CAP)


def _add_query(queries: list[dict], seen: set[str], query: str, kind: str, weight: int) -> None:
    query = query.strip().lower().strip(" \t\r\n\"'()[]{}").rstrip(".,;:!?")
    if not query or query in seen:
        return
    if query in STOPWORDS:
        return
    if len(query) < 3 and query not in USEFUL_SHORT_TERMS:
        return
    seen.add(query)
    queries.append({"query": query, "kind": kind, "weight": weight})


def _extract_search_query_specs(task: str) -> list[dict]:
    words = re.findall(r"[A-Za-z0-9_.-]+", task.lower())
    queries: list[dict] = []
    seen = set()
    task_l = task.lower()
    service_intent = resolve_service_intent(task)

    if service_intent:
        for query in service_intent["positive_terms"]:
            _add_query(queries, seen, query, "service", 120)

    if "rookdetectie" in task_l or "rook detectie" in task_l:
        for query in ROOKDETECTIE_QUERIES:
            _add_query(queries, seen, query, "domain", 100)

    if "geur" in task_l or "rioolgeur" in task_l:
        for query in GEUR_QUERIES:
            _add_query(queries, seen, query, "service", 90)

    if "landingspagina" in task_l or "landing" in task_l:
        for query in LANDING_QUERIES:
            _add_query(queries, seen, query, "landing/seo", 80)

    for word in words:
        if word in STOPWORDS:
            continue
        _add_query(queries, seen, word, "task", 60)

    should_add_project_terms = any(
        term in task_l
        for term in ("workspace", "chat", "agent", "landing", "landingspagina", "seo", "schema", "metadata")
    )
    for term in STABLE_SEARCH_TERMS:
        if should_add_project_terms:
            _add_query(queries, seen, term, "project", 30)

    return queries[:24]


def _extract_search_queries(task: str) -> list[str]:
    return [item["query"] for item in _extract_search_query_specs(task)]


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


def _reason_for_match(result: dict, query_spec: dict) -> str:
    path = result.get("path") or ""
    if path == "config/services.json":
        return "matched path: config/services.json"
    kind = query_spec["kind"]
    query = query_spec["query"]
    if kind == "domain":
        return f"matched domain query: {query}"
    if kind == "service":
        return f"matched service query: {query}"
    if kind == "landing/seo":
        return f"matched landing/seo query: {query}"
    return f"matched query: {query}"


def _score_result(result: dict, query_spec: dict, task_l: str) -> int:
    path = (result.get("path") or "").lower()
    root = (result.get("root") or "").lower()
    score = query_spec["weight"]

    if root == "turboservices":
        score += 35
    if path == "config/services.json":
        score += 80
    if "content model" in path or "content_model" in path or "content-model" in path:
        score += 45
    for term in SERVICE_PATH_TERMS:
        if term in path:
            score += 12

    if result.get("match_type") == "path":
        score += 10

    explicit_governance = any(term in task_l for term in GOVERNANCE_TERMS)
    if not explicit_governance and any(term in path for term in GOVERNANCE_TERMS):
        score -= 80

    return score


def _has_negative_service_match(result: dict, service_intent: dict | None, task_l: str) -> bool:
    if not service_intent:
        return False

    negative_terms = service_intent.get("negative_terms") or []
    if any(term in task_l for term in negative_terms):
        return False

    path = (result.get("path") or "").lower()
    matched_text = " ".join(
        (line.get("text") or "").lower()
        for line in result.get("matched_lines", [])
        if isinstance(line, dict)
    )
    haystack = f"{path} {matched_text}"
    return any(term in haystack for term in negative_terms)


def is_auto_context_discovery_enabled() -> bool:
    value = os.getenv("ENABLE_AUTO_CONTEXT_DISCOVERY", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_context_plan(
    task: str,
    roots: list[str] | None = None,
    max_files: int = DEFAULT_MAX_FILES,
) -> dict:
    task = task.strip()
    max_files = _clamp_max_files(max_files)
    search_roots = _normalise_roots(roots)
    query_specs = _extract_search_query_specs(task)
    search_queries = [item["query"] for item in query_specs]
    context_by_path: dict[tuple[str, str], dict] = {}
    task_l = task.lower()
    service_intent = resolve_service_intent(task)

    for query_spec in query_specs:
        for root in search_roots:
            results = search_workspace_files(
                query=query_spec["query"],
                root_alias=root,
                max_results=max_files,
            )
            for result in results:
                if _has_negative_service_match(result, service_intent, task_l):
                    continue

                key = (result["root"], result["path"])
                score = _score_result(result, query_spec, task_l)
                reason = _reason_for_match(result, query_spec)
                current = context_by_path.get(key)
                if current is None:
                    context_by_path[key] = {
                        **result,
                        "_score": score,
                        "reason": reason,
                    }
                elif score > current.get("_score", 0):
                    current["_score"] = score
                    current["reason"] = reason
                else:
                    current["reason"] = _context_reason(current.get("reason"), query_spec["query"])

    context_files = sorted(
        context_by_path.values(),
        key=lambda item: (-item.get("_score", 0), item.get("root", ""), item.get("path", "")),
    )[:max_files]
    for item in context_files:
        item.pop("_score", None)

    plan = {
        "ok": True,
        "task": task,
        "search_queries": search_queries,
        "context_files": context_files,
    }
    if service_intent:
        plan["service_intent"] = service_intent
    return plan


def log_auto_context_plan(plan: dict) -> None:
    context_files = plan.get("context_files") or []
    search_queries = plan.get("search_queries") or []
    print(
        "workspace auto_context "
        f"enabled=true files={len(context_files)} queries={len(search_queries)}"
    )
    service_intent = plan.get("service_intent")
    if service_intent:
        print(
            "workspace service_intent "
            f"canonical={service_intent.get('canonical_service')} "
            f"display={service_intent.get('display_name')}"
        )
    for item in context_files:
        print(
            "workspace auto_context file "
            f"root={item.get('root')} "
            f"path={item.get('path')} "
            f"reason={item.get('reason')}"
        )


@router.post("/build")
async def build_context(request: Request):
    payload = await request.json()
    task = payload.get("task")
    if not isinstance(task, str) or not task.strip():
        raise HTTPException(status_code=400, detail="task is required")

    return build_context_plan(
        task=task,
        roots=payload.get("roots"),
        max_files=payload.get("max_files"),
    )
