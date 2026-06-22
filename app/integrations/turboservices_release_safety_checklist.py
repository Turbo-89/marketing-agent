import hashlib
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.integrations.service_intent import resolve_service_intent
from app.integrations.turboservices_target_map import SERVICE_GUARD, TARGET_REPO_LABEL

router = APIRouter()

NEXT_ALLOWED_STEP = "release only after explicit final release approval"

REQUIRED_PRE_RELEASE_CHECKS = [
    "changed files reviewed",
    "SEO reviewed",
    "content reviewed",
    "schema reviewed",
    "build validation reviewed",
    "rollback plan reviewed",
    "manual approval confirmed",
    "no Ads/GA4 changes included",
    "no GitHub mutation authorized yet",
    "no deploy authorized yet",
]

BLOCKED_ACTIONS = [
    "release_execution",
    "deploy",
    "publish",
    "merge",
    "push_to_live",
    "github_mutation",
    "github_pr_creation",
    "branch_creation",
    "staging",
    "commit",
    "file_write_to_turboservices",
    "google_ads_change",
    "ga4_change",
]

READ_ONLY_GUARANTEES = [
    "no release",
    "no deploy",
    "no publish",
    "no merge",
    "no push",
    "no GitHub mutation",
    "no file writes",
    "no Ads/GA4 changes",
    "no live website changes",
]


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _stable_kebab(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return normalized or "release-safety"


def _scope_value(patch_plan: dict, key: str) -> str:
    scope = _as_dict(patch_plan.get("selected_patch_scope"))
    return _clean_string(scope.get(key))


def _slug(payload: dict, patch_plan: dict) -> str:
    route_plan = _as_dict(patch_plan.get("route_plan"))
    return _stable_kebab(
        _scope_value(patch_plan, "slug")
        or _clean_string(route_plan.get("url_path")).split("/")[-1]
        or _clean_string(payload.get("proposed_branch_name")).split("/")[-1]
        or "landing-page"
    )


def _release_checklist_id(slug: str, branch: str) -> str:
    digest = hashlib.sha256(f"{slug}:{branch}".encode("utf-8")).hexdigest()[:12]
    return f"release-safety-{slug}-{digest}"


def _service_guard(payload: dict, patch_plan: dict) -> dict:
    text = " ".join(
        part
        for part in (
            _scope_value(patch_plan, "service"),
            _slug(payload, patch_plan),
            _clean_string(_as_dict(payload.get("review_checklist")).get("draft_pr_title")),
        )
        if part
    )
    return {
        "service_intent": resolve_service_intent(text),
        "guard": dict(SERVICE_GUARD),
    }


def _release_status(payload: dict) -> str:
    patch_plan = _as_dict(payload.get("patch_plan"))
    review_checklist = _as_dict(payload.get("review_checklist"))
    if patch_plan.get("read_only") is False or review_checklist.get("read_only") is False:
        return "blocked_invalid_request"
    if not _has_value(payload.get("validation_results")):
        return "needs_validation_results"
    if not _has_value(payload.get("rollback_plan")):
        return "needs_rollback_plan"
    if not _has_value(payload.get("final_user_approval")):
        return "needs_final_user_approval"
    return "ready_for_final_release_review"


def build_turboservices_release_safety_checklist(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_json_object")

    patch_plan = _as_dict(payload.get("patch_plan"))
    review_checklist = _as_dict(payload.get("review_checklist"))
    slug = _slug(payload, patch_plan)
    branch = (
        _clean_string(payload.get("proposed_branch_name"))
        or _clean_string(patch_plan.get("proposed_branch_name"))
        or _clean_string(review_checklist.get("proposed_branch_name"))
        or f"proposal/{_stable_kebab(f'landing-page-{slug}')}"
    )
    commit_message = (
        _clean_string(payload.get("proposed_commit_message"))
        or _clean_string(patch_plan.get("proposed_commit_message"))
        or _clean_string(review_checklist.get("proposed_commit_message"))
        or f"Prepare release safety checklist for {slug}"
    )

    return {
        "ok": True,
        "release_checklist_id": _release_checklist_id(slug, branch),
        "release_status": _release_status(payload),
        "target_repo": TARGET_REPO_LABEL,
        "read_only": True,
        "required_pre_release_checks": list(REQUIRED_PRE_RELEASE_CHECKS),
        "validation_requirements": [
            "Review validation_results before release.",
            "Confirm build validation has passed after any approved local patch.",
            "Confirm no deploy is authorized by this checklist.",
        ],
        "rollback_requirements": [
            "Rollback plan must be reviewed before release approval.",
            "Confirm how to revert local patch before any deploy/publish action.",
            "Do not merge or push without final release approval.",
        ],
        "approval_requirements": [
            "Final user approval is required before release.",
            "Approval must be explicit and separate from review/patch approval.",
            "GitHub, deploy, publish, merge and push remain blocked here.",
        ],
        "deployment_blockers": [
            "No deploy authorized yet.",
            "No publish authorized yet.",
            "No merge authorized yet.",
            "No push-to-live authorized yet.",
            "No Ads/GA4 changes included.",
        ],
        "release_risks": [
            {"risk": "Validation may be incomplete.", "mitigation": "Require validation_results review."},
            {"risk": "Rollback may be unclear.", "mitigation": "Require rollback_plan review."},
            {"risk": "Approval may be ambiguous.", "mitigation": "Require explicit final release approval."},
        ],
        "release_context": {
            "proposed_branch_name": branch,
            "proposed_commit_message": commit_message,
            "patch_plan_id": _clean_string(patch_plan.get("patch_plan_id")),
            "review_checklist_id": _clean_string(review_checklist.get("review_checklist_id")),
            "service_guard": _service_guard(payload, patch_plan),
        },
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_guarantees": list(READ_ONLY_GUARANTEES),
        "final_release_approval_required": True,
        "next_allowed_step": NEXT_ALLOWED_STEP,
    }


@router.post("/release-safety-checklist")
async def turboservices_release_safety_checklist(request: Request):
    payload = await request.json()
    return build_turboservices_release_safety_checklist(payload)
