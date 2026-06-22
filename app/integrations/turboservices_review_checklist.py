import hashlib
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.integrations.service_intent import resolve_service_intent
from app.integrations.turboservices_target_map import SERVICE_GUARD, TARGET_REPO_LABEL

router = APIRouter()

NEXT_ALLOWED_STEP = "create local review branch or draft PR only after explicit final approval"

BLOCKED_ACTIONS = [
    "github_pr_creation",
    "branch_creation",
    "file_write_to_turboservices",
    "staging",
    "commit",
    "push",
    "merge",
    "deploy",
    "publish",
    "google_ads_change",
    "ga4_change",
]

READ_ONLY_GUARANTEES = [
    "no GitHub mutation",
    "no PR creation",
    "no branch creation",
    "no file writes",
    "no commits",
    "no push",
    "no deploy",
    "no publish",
    "no Ads/GA4 changes",
]


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _stable_kebab(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return normalized or "review-checklist"


def _review_checklist_id(branch: str, slug: str) -> str:
    digest = hashlib.sha256(f"{branch}:{slug}".encode("utf-8")).hexdigest()[:12]
    return f"review-checklist-{slug}-{digest}"


def _scope_value(patch_plan: dict, key: str) -> str:
    scope = _as_dict(patch_plan.get("selected_patch_scope"))
    return _clean_string(scope.get(key))


def _slug(payload: dict, patch_plan: dict) -> str:
    return _stable_kebab(
        _clean_string(payload.get("requested_slug"))
        or _scope_value(patch_plan, "slug")
        or _clean_string(_as_dict(patch_plan.get("route_plan")).get("url_path")).split("/")[-1]
        or "landing-page"
    )


def _service_text(payload: dict, patch_plan: dict) -> str:
    return " ".join(
        part
        for part in (
            _clean_string(payload.get("requested_service_intent")),
            _scope_value(patch_plan, "service"),
            _slug(payload, patch_plan),
        )
        if part
    )


def _service_guard(payload: dict, patch_plan: dict) -> dict:
    resolved = resolve_service_intent(_service_text(payload, patch_plan))
    return {
        "service_intent": resolved,
        "guard": dict(SERVICE_GUARD),
    }


def _file_review_items(patch_plan: dict) -> list[dict]:
    items = []
    for group, label in (
        ("existing_target_files", "existing"),
        ("proposed_new_files", "proposed_new"),
        ("proposed_modified_files", "existing"),
        ("proposed_deleted_files", "proposed_deleted"),
    ):
        for item in _as_list(patch_plan.get(group)):
            if not isinstance(item, dict):
                continue
            path = _clean_string(item.get("path"))
            if path:
                items.append(
                    {
                        "path": path,
                        "status": _clean_string(item.get("status")) or label,
                        "review_note": "Review target path and planned change before any future branch or PR work.",
                    }
                )
    return items


def _draft_title(slug: str, region: str, service: str) -> str:
    readable = " ".join(part for part in (service, region) if part).strip()
    return f"Draft review: {readable or slug} landing page patch"


def _draft_body(patch_plan: dict, service_guard: dict) -> str:
    guard = service_guard["guard"]
    return "\n".join(
        [
            "## Read-only draft PR checklist",
            "",
            "This is a proposed review checklist only. No PR, branch, commit, push, deploy or publish action has been performed.",
            "",
            f"- Patch plan: {_clean_string(patch_plan.get('patch_plan_id')) or 'missing'}",
            f"- Plan status: {_clean_string(patch_plan.get('plan_status')) or 'unknown'}",
            f"- Rookdetectie guard: {guard['meaning']}",
            "- Final approval is required before creating any branch or draft PR.",
        ]
    )


def _checklist_status(payload: dict, patch_plan: dict) -> str:
    if not patch_plan:
        return "needs_patch_plan"
    if patch_plan.get("read_only") is False:
        return "blocked_invalid_request"
    return "ready_for_manual_review"


def build_turboservices_review_checklist(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_json_object")

    patch_plan = _as_dict(payload.get("patch_plan"))
    slug = _slug(payload, patch_plan)
    service = _clean_string(payload.get("requested_service_intent")) or _scope_value(patch_plan, "service")
    region = _clean_string(payload.get("requested_region")) or _scope_value(patch_plan, "region")
    proposed_branch_name = (
        _clean_string(payload.get("proposed_branch_name"))
        or _clean_string(patch_plan.get("proposed_branch_name"))
        or f"proposal/{_stable_kebab(f'landing-page-{slug}')}"
    )
    proposed_commit_message = (
        _clean_string(payload.get("proposed_commit_message"))
        or _clean_string(patch_plan.get("proposed_commit_message"))
        or f"Prepare review checklist for {slug}"
    )
    service_guard = _service_guard(payload, patch_plan)
    status = _checklist_status(payload, patch_plan)

    return {
        "ok": True,
        "review_checklist_id": _review_checklist_id(proposed_branch_name, slug),
        "checklist_status": status,
        "target_repo": TARGET_REPO_LABEL,
        "read_only": True,
        "proposed_branch_name": proposed_branch_name,
        "proposed_commit_message": proposed_commit_message,
        "draft_pr_title": _draft_title(slug, region, service),
        "draft_pr_body": _draft_body(patch_plan, service_guard),
        "changed_files_review": _file_review_items(patch_plan),
        "seo_review_items": [
            "Review title and meta description against service intent and region.",
            "Confirm no fire-safety meaning is introduced for rookdetectie.",
            "Confirm canonical URL and metadata plan before implementation.",
        ],
        "content_review_items": [
            "Review H1/H2 outline and service copy for local relevance.",
            "Confirm Turbo Services tone and claims before any file changes.",
            "Confirm rookdetectie means rooktest/geuropsporing/rioolgeur when relevant.",
        ],
        "schema_review_items": [
            "Review Service and LocalBusiness schema fields.",
            "Confirm schema matches the final route and service region.",
            "Do not publish schema until implementation is approved and validated.",
        ],
        "validation_checklist": [
            "Plan npm run build after explicit approval and local patch application.",
            "Plan npm run lint if available after explicit approval and local patch application.",
            "Review rendered page manually before any deploy/publish action.",
        ],
        "rollback_checklist": [
            "Keep future patch small and reviewable.",
            "Prepare local revert plan before deploy/publish.",
            "Do not merge or push without explicit approval.",
        ],
        "manual_approval_checklist": [
            "Human reviewed changed files.",
            "Human reviewed SEO/content/schema plans.",
            "Human explicitly approved branch or draft PR creation.",
            "Human explicitly approved any later apply/deploy/publish step separately.",
        ],
        "service_guard": service_guard,
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_guarantees": list(READ_ONLY_GUARANTEES),
        "final_pr_creation_approval_required": True,
        "next_allowed_step": NEXT_ALLOWED_STEP,
    }


@router.post("/review-checklist")
async def turboservices_review_checklist(request: Request):
    payload = await request.json()
    return build_turboservices_review_checklist(payload)
