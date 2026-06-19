from typing import Any

from app.integrations.landing_page_implementation_draft import (
    BLOCKED_ACTIONS,
    ROOKDETECTIE_CANONICAL_SERVICE,
)
from app.integrations.landing_page_implementation_plan import (
    APPROVAL_GATES,
    READ_ONLY_GUARANTEES,
    stable_kebab_case,
)
from app.integrations.service_intent import resolve_service_intent

NEXT_ALLOWED_STEP = "prepare implementation patch proposal only after explicit final user approval"
REQUIRED_CHECKLIST_KEYS = (
    "planReviewed",
    "seoReviewed",
    "contentReviewed",
    "schemaReviewed",
    "linksReviewed",
    "risksReviewed",
    "approvalStillRequired",
)


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _implementation_plan(payload: dict) -> dict:
    for key in ("implementation_plan", "implementationPlan", "plan"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _implementation_draft(payload: dict) -> dict:
    for key in ("implementation_draft", "implementationDraft", "draft"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _selected_opportunity(payload: dict) -> dict:
    for key in ("selected_opportunity", "selectedOpportunity", "opportunity"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _package_text(payload: dict) -> str:
    return _clean_string(
        payload.get("implementation_package")
        or payload.get("implementationPackage")
        or payload.get("implementation_package_markdown")
        or payload.get("package_markdown")
        or payload.get("package")
    )


def _checklist_status(payload: dict, draft: dict) -> dict:
    explicit = payload.get("checklist_status") or payload.get("checklistStatus")
    if isinstance(explicit, dict):
        return explicit
    approval_summary = _as_dict(draft.get("approval_summary"))
    return _as_dict(approval_summary.get("checklist_status"))


def _service_intent(plan: dict, draft: dict, opportunity: dict, package_text: str) -> dict | None:
    for source in (plan, draft, opportunity):
        existing = source.get("service_intent") if isinstance(source, dict) else None
        if isinstance(existing, dict) and existing.get("canonical_service"):
            if existing.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
                return resolve_service_intent("rookdetectie") or existing
            return existing

    task_text = " ".join(
        part
        for part in (
            _clean_string(plan.get("service_label")),
            _clean_string(plan.get("proposed_slug")),
            _clean_string(draft.get("draft_id")),
            _clean_string(opportunity.get("reason")),
            package_text,
        )
        if part
    )
    return resolve_service_intent(task_text)


def _missing_items(plan: dict, draft: dict, package_text: str, checklist: dict) -> list[str]:
    missing = []
    for key in REQUIRED_CHECKLIST_KEYS:
        if checklist and checklist.get(key) is not True:
            missing.append(key)
    if not plan:
        missing.append("implementation_plan")
    if not draft:
        missing.append("implementation_draft")
    if not _as_list(draft.get("proposed_files")):
        missing.append("proposed_files")
    if not _as_dict(draft.get("proposed_route_structure")):
        missing.append("proposed_route_structure")
    if not _as_dict(draft.get("proposed_seo_metadata")):
        missing.append("proposed_seo_metadata")
    if not _as_list(draft.get("proposed_content_blocks")):
        missing.append("proposed_content_blocks")
    if not _as_dict(draft.get("proposed_schema_jsonld")):
        missing.append("proposed_schema_jsonld")
    if not _as_list(draft.get("proposed_validation_plan")):
        missing.append("proposed_validation_plan")
    if not package_text:
        missing.append("implementation_package_text")
    return list(dict.fromkeys(missing))


def _readiness_score(missing_items: list[str]) -> int:
    if not missing_items:
        return 100
    return max(0, 100 - (len(missing_items) * 10))


def _readiness_status(score: int) -> str:
    if score >= 90:
        return "ready_for_final_user_review"
    if score >= 60:
        return "needs_review"
    return "incomplete"


def _proposed_files_review(draft: dict) -> list[dict]:
    files = []
    for item in _as_list(draft.get("proposed_files")):
        if isinstance(item, dict):
            files.append(
                {
                    "path": _clean_string(item.get("path")) or "unknown",
                    "status": "proposed_review_only",
                    "review": "Proposed file reference only; no file write is authorized.",
                }
            )
    return files


def _rookdetectie_review(service_intent: dict | None) -> dict:
    if not service_intent or service_intent.get("canonical_service") != ROOKDETECTIE_CANONICAL_SERVICE:
        return {"applies": False}
    return {
        "applies": True,
        "required_meaning": "rooktest/geuropsporing/rioolgeur/riolering/riool/afvoer",
        "excluded_meaning": "rookmelders/brandveiligheid/branddetectie/brandalarm",
        "passed": True,
    }


def build_landing_page_final_implementation_review(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    plan = _implementation_plan(payload)
    draft = _implementation_draft(payload)
    opportunity = _selected_opportunity(payload)
    package_text = _package_text(payload)
    checklist = _checklist_status(payload, draft)
    service_intent = _service_intent(plan, draft, opportunity, package_text)
    missing_items = _missing_items(plan, draft, package_text, checklist)
    score = _readiness_score(missing_items)
    draft_id = _clean_string(draft.get("draft_id")) or "unknown-draft"
    review_id = stable_kebab_case(f"final-review-{draft_id}")

    return {
        "ok": True,
        "review_id": review_id,
        "source_draft_id": draft_id,
        "readiness_status": _readiness_status(score),
        "readiness_score": score,
        "required_missing_items": missing_items,
        "implementation_summary": {
            "service_label": _clean_string(plan.get("service_label")) or "Turbo Services",
            "region": _clean_string(plan.get("region")) or _clean_string(opportunity.get("region")),
            "plan_id": _clean_string(plan.get("opportunity_id")) or _clean_string(draft.get("source_plan_id")),
            "draft_id": draft_id,
            "package_present": bool(package_text),
            "service_intent": service_intent,
            "execution_authorized": False,
        },
        "proposed_files_review": _proposed_files_review(draft),
        "seo_review": {
            "status": "review_only",
            "metadata": _as_dict(draft.get("proposed_seo_metadata")),
            "missing": "proposed_seo_metadata" in missing_items,
        },
        "content_review": {
            "status": "review_only",
            "blocks": _as_list(draft.get("proposed_content_blocks")),
            "rookdetectie_business_rule": _rookdetectie_review(service_intent),
        },
        "schema_review": {
            "status": "review_only",
            "jsonld": _as_dict(draft.get("proposed_schema_jsonld")),
            "missing": "proposed_schema_jsonld" in missing_items,
        },
        "internal_link_review": {
            "status": "review_only",
            "links": _as_list(draft.get("proposed_internal_links")),
        },
        "validation_review": {
            "status": "review_only",
            "validation_plan": _as_list(draft.get("proposed_validation_plan")),
            "missing": "proposed_validation_plan" in missing_items,
        },
        "risk_review": {
            "status": "review_only",
            "risks": _as_list(draft.get("risks")),
        },
        "final_approval_required": True,
        "blocked_actions": BLOCKED_ACTIONS,
        "approval_gates": APPROVAL_GATES,
        "read_only_guarantees": READ_ONLY_GUARANTEES,
        "next_allowed_step": NEXT_ALLOWED_STEP,
    }
