from typing import Any

from app.integrations.landing_page_final_implementation_review import (
    NEXT_ALLOWED_STEP as FINAL_REVIEW_NEXT_ALLOWED_STEP,
)
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

NEXT_ALLOWED_STEP = "apply patch only after explicit final user approval in the turboservices repo"


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _payload_dict(payload: dict, *keys: str) -> dict:
    for key in keys:
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


def _service_intent(plan: dict, draft: dict, review: dict, opportunity: dict, package_text: str) -> dict | None:
    for source in (plan, draft, review.get("implementation_summary", {}), opportunity):
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
            _clean_string(review.get("review_id")),
            _clean_string(opportunity.get("reason")),
            package_text,
        )
        if part
    )
    return resolve_service_intent(task_text)


def _review_allows_patch_proposal(review: dict) -> bool:
    return (
        _clean_string(review.get("readiness_status")) == "ready_for_final_user_review"
        and review.get("final_approval_required") is True
        and _clean_string(review.get("next_allowed_step")) == FINAL_REVIEW_NEXT_ALLOWED_STEP
    )


def _patch_readiness_status(review: dict) -> str:
    if not review:
        return "review_required"
    if not _review_allows_patch_proposal(review):
        return "blocked"
    return "ready_for_patch_proposal"


def _proposed_file_patches(draft: dict, service_intent: dict | None) -> list[dict]:
    patches = []
    for item in _as_list(draft.get("proposed_files")):
        if not isinstance(item, dict):
            continue
        path = _clean_string(item.get("path")) or "unknown"
        patches.append(
            {
                "path": path,
                "status": "proposed_only",
                "patch_description": (
                    f"Text-only proposal for {path}. No file is created or modified by this endpoint."
                ),
            }
        )
    if service_intent and service_intent.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
        patches.append(
            {
                "path": "content/business-rules/rookdetectie.md",
                "status": "proposed_only",
                "patch_description": (
                    "Keep rookdetectie copy focused on rooktest/geuropsporing/rioolgeur/"
                    "riolering/riool/afvoer and exclude fire-safety positioning."
                ),
            }
        )
    return patches


def _new_files(file_patches: list[dict]) -> list[dict]:
    return [
        {
            "path": item["path"],
            "status": "proposed_only",
            "reason": "Potential new file; final implementation approval required before any write.",
        }
        for item in file_patches
        if item.get("path", "").endswith("page.tsx")
    ]


def _modified_files(file_patches: list[dict]) -> list[dict]:
    return [
        {
            "path": item["path"],
            "status": "proposed_only",
            "reason": "Potential metadata/content update; no modification authorized.",
        }
        for item in file_patches
        if not item.get("path", "").endswith("page.tsx")
    ]


def _manual_review_checklist(review: dict) -> list[str]:
    return [
        "Confirm final user approval explicitly names the turboservices repo.",
        "Review proposed file paths against the real repo before applying anything.",
        "Review SEO title and meta description.",
        "Review schema JSON-LD before use.",
        "Review internal links and route path.",
        "Run validation only after separately approved patch application.",
        "Confirm blocked actions remain blocked until separate approval.",
        f"Confirm prior review next step was: {review.get('next_allowed_step') or 'missing'}",
    ]


def build_landing_page_patch_proposal(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    opportunity = _payload_dict(payload, "selected_opportunity", "selectedOpportunity", "opportunity")
    plan = _payload_dict(payload, "implementation_plan", "implementationPlan", "plan")
    draft = _payload_dict(payload, "implementation_draft", "implementationDraft", "draft")
    review = _payload_dict(payload, "final_implementation_review", "finalImplementationReview", "review")
    package_text = _package_text(payload)
    service_intent = _service_intent(plan, draft, review, opportunity, package_text)
    source_review_id = _clean_string(review.get("review_id")) or "unknown-review"
    draft_id = _clean_string(draft.get("draft_id")) or _clean_string(review.get("source_draft_id")) or "unknown-draft"
    proposal_id = stable_kebab_case(f"patch-proposal-{source_review_id}-{draft_id}")
    file_patches = _proposed_file_patches(draft, service_intent)
    route = _as_dict(draft.get("proposed_route_structure"))
    seo = _as_dict(draft.get("proposed_seo_metadata"))
    schema = _as_dict(draft.get("proposed_schema_jsonld"))

    proposed_content_changes = _as_list(draft.get("proposed_content_blocks"))
    if service_intent and service_intent.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
        proposed_content_changes.append(
            {
                "block": "rookdetectie_business_guard",
                "status": "proposed_only",
                "draft": (
                    "Rookdetectie must mean rooktest/geuropsporing for rioolgeur, riolering, "
                    "riool and afvoer. Do not use rookmelders, brandveiligheid, branddetectie "
                    "or brandalarm as positive service context."
                ),
            }
        )

    return {
        "ok": True,
        "patch_proposal_id": proposal_id,
        "source_review_id": source_review_id,
        "patch_readiness_status": _patch_readiness_status(review),
        "proposed_file_patches": file_patches,
        "proposed_new_files": _new_files(file_patches),
        "proposed_modified_files": _modified_files(file_patches),
        "proposed_deleted_files": [],
        "proposed_content_changes": proposed_content_changes,
        "proposed_seo_changes": {
            "status": "proposed_only",
            "metadata": seo,
            "route_path": route.get("route_path"),
        },
        "proposed_schema_changes": {
            "status": "proposed_only",
            "jsonld": schema,
        },
        "proposed_internal_link_changes": {
            "status": "proposed_only",
            "links": _as_list(draft.get("proposed_internal_links")),
        },
        "validation_commands": _as_list(draft.get("proposed_validation_plan")),
        "manual_review_checklist": _manual_review_checklist(review),
        "risks": _as_list(draft.get("risks"))
        + [
            {
                "risk": "Patch proposal is text only and was generated without reading the turboservices repo.",
                "mitigation": "Require explicit final user approval before applying anything in the turboservices repo.",
            }
        ],
        "blocked_actions": BLOCKED_ACTIONS,
        "approval_gates": APPROVAL_GATES,
        "read_only_guarantees": READ_ONLY_GUARANTEES,
        "final_user_approval_required": True,
        "next_allowed_step": NEXT_ALLOWED_STEP,
    }
