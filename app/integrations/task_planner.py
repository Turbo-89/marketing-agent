from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.integrations.context_builder import build_context_plan
from app.integrations.intelligence_planner import list_intelligence_jobs
from app.integrations.service_intent import resolve_service_intent

router = APIRouter()

APPROVAL_REQUIRED_BEFORE = [
    "write_files",
    "deploy",
    "publish",
    "change_ads",
    "merge",
    "push_to_live",
]
FORBIDDEN_ACTIONS_NOW = [
    "write_files",
    "deploy",
    "publish",
    "change_ads",
    "merge",
    "push_to_live",
    "execute_shell_commands",
]


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalise_roots(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    roots = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return roots or None


def _clamp_max_context_files(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        return 12
    return min(value, 30)


def _task_flags(task: str) -> dict:
    task_l = task.lower()
    return {
        "landing": any(term in task_l for term in ("landing", "landingspagina")),
        "seo": "seo" in task_l or "metadata" in task_l,
        "schema": "schema" in task_l or "metadata" in task_l,
        "local": any(term in task_l for term in ("local", "lokale", "stad", "antwerpen", "gemeente")),
        "ai": "ai" in task_l or "artificial intelligence" in task_l,
        "rookdetectie": any(term in task_l for term in ("rookdetectie", "rook detectie", "rooktest")),
    }


def _suggest_intelligence_jobs(task: str, service_intent: dict | None) -> list[dict]:
    flags = _task_flags(task)
    reasons = {}

    if flags["ai"] or flags["seo"]:
        reasons["weekly_ai_seo_watch"] = "Task mentions AI, SEO, metadata, or search visibility."
    if flags["local"]:
        reasons["weekly_local_seo_watch"] = "Task appears to involve a city or local service page."
    if flags["schema"]:
        reasons["weekly_structured_data_watch"] = "Task mentions metadata or schema planning."
    if flags["landing"]:
        reasons["weekly_content_strategy_watch"] = "Task involves a landing page or content strategy."
    if service_intent and service_intent.get("canonical_service") == "rookdetectie_geuropsporing":
        reasons["monthly_rookdetectie_geuropsporing_watch"] = (
            "Task resolves rookdetectie as rooktest/geuropsporing for rioolgeur and riolering."
        )

    available_jobs = {job["job_id"] for job in list_intelligence_jobs()}
    return [
        {"job_id": job_id, "reason": reason}
        for job_id, reason in reasons.items()
        if job_id in available_jobs
    ]


def _execution_plan(task: str, service_intent: dict | None) -> list[dict]:
    flags = _task_flags(task)
    steps = [
        {
            "step": 1,
            "title": "Review local context",
            "description": "Inspect the dry-run context plan and likely files before proposing any edits.",
            "type": "analysis",
            "requires_approval": False,
        },
        {
            "step": 2,
            "title": "Validate service intent",
            "description": (
                "Confirm rookdetectie means rooktest/geuropsporing for rioolgeur, riolering and afvoer."
                if service_intent
                else "Confirm the task's service and business meaning before planning changes."
            ),
            "type": "analysis",
            "requires_approval": False,
        },
    ]

    if flags["landing"]:
        steps.append(
            {
                "step": len(steps) + 1,
                "title": "Plan landing page structure",
                "description": "Outline page sections, service proof points, calls to action, and local relevance.",
                "type": "content_planning",
                "requires_approval": False,
            }
        )

    if flags["seo"]:
        steps.append(
            {
                "step": len(steps) + 1,
                "title": "Plan content and SEO metadata",
                "description": "Prepare title, description, headings, internal links, and SEO content notes.",
                "type": "seo_planning",
                "requires_approval": False,
            }
        )

    if flags["schema"]:
        steps.append(
            {
                "step": len(steps) + 1,
                "title": "Plan metadata and schema",
                "description": "Identify structured data and metadata updates to review before implementation.",
                "type": "seo_planning",
                "requires_approval": False,
            }
        )

    steps.extend(
        [
            {
                "step": len(steps) + 1,
                "title": "Identify likely file changes",
                "description": "Map proposed work to candidate files without editing them in this dry-run.",
                "type": "code_planning",
                "requires_approval": False,
            },
            {
                "step": len(steps) + 1,
                "title": "Plan validation",
                "description": "Define build, lint, or focused checks that should run after approved changes.",
                "type": "validation",
                "requires_approval": False,
            },
            {
                "step": len(steps) + 1,
                "title": "Approval gate",
                "description": "Require explicit approval before writes, deploys, publishing, ads changes, merges, or live pushes.",
                "type": "approval_gate",
                "requires_approval": True,
            },
        ]
    )
    return steps


def _likely_files_to_review(context_plan: dict) -> list[dict]:
    files = []
    for item in context_plan.get("context_files", [])[:12]:
        files.append(
            {
                "root": item.get("root"),
                "path": item.get("path"),
                "reason": item.get("reason") or "Matched local context query.",
            }
        )
    return files


def _risks(service_intent: dict | None) -> list[dict]:
    risks = [
        {
            "risk": "Dry-run context may miss files that require manual review.",
            "mitigation": "Review likely files and broaden roots or task terms before approving implementation.",
        },
        {
            "risk": "SEO or schema recommendations may need business approval.",
            "mitigation": "Keep all metadata, schema, ads, and content changes behind an approval gate.",
        },
    ]
    if service_intent:
        risks.append(
            {
                "risk": "Rookdetectie could be confused with fire-safety or smoke-alarm content.",
                "mitigation": "Use only the Turbo Services meaning: rooktest/geuropsporing for rioolgeur, riolering and afvoer.",
            }
        )
    return risks


def _suggested_validation() -> list[dict]:
    return [
        {
            "command": "python -m py_compile server.py",
            "purpose": "Backend syntax check after approved backend changes.",
        },
        {
            "command": "npm run build",
            "purpose": "Frontend or site build check after approved UI/site changes.",
        },
    ]


def build_task_plan(task: str, roots: list[str] | None = None, max_context_files: int = 12) -> dict:
    service_intent = resolve_service_intent(task)
    context_plan = build_context_plan(
        task=task,
        roots=roots,
        max_files=max_context_files,
    )

    response = {
        "ok": True,
        "task": task,
        "context_plan": context_plan,
        "suggested_intelligence_jobs": _suggest_intelligence_jobs(task, service_intent),
        "execution_plan": _execution_plan(task, service_intent),
        "likely_files_to_review": _likely_files_to_review(context_plan),
        "risks": _risks(service_intent),
        "suggested_validation": _suggested_validation(),
        "approval_required_before": APPROVAL_REQUIRED_BEFORE,
        "forbidden_actions_now": FORBIDDEN_ACTIONS_NOW,
    }
    if service_intent:
        response["service_intent"] = service_intent
    return response


@router.post("/plan")
async def plan_task(request: Request):
    payload = await request.json()
    task = _clean_string(payload.get("task"))
    if not task:
        raise HTTPException(status_code=400, detail="task is required")

    return build_task_plan(
        task=task,
        roots=_normalise_roots(payload.get("roots")),
        max_context_files=_clamp_max_context_files(payload.get("max_context_files")),
    )
