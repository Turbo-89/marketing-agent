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

NEXT_ALLOWED_STEP = "apply prepared patch in turboservices only after explicit final apply approval"


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


def _patch_proposal(payload: dict) -> dict:
    return _payload_dict(payload, "patch_proposal", "patchProposal", "proposal")


def _approval_brief(payload: dict) -> str:
    return _clean_string(
        payload.get("final_patch_approval_brief")
        or payload.get("finalPatchApprovalBrief")
        or payload.get("approval_brief")
        or payload.get("approvalBrief")
    )


def _approval_timestamp(payload: dict) -> str:
    return _clean_string(
        payload.get("final_patch_approval_timestamp")
        or payload.get("finalPatchApprovalTimestamp")
        or payload.get("approval_timestamp")
        or payload.get("approvalTimestamp")
    )


def _service_intent(plan: dict, draft: dict, proposal: dict, package_text: str) -> dict | None:
    for source in (plan, draft):
        existing = source.get("service_intent") if isinstance(source, dict) else None
        if isinstance(existing, dict) and existing.get("canonical_service"):
            if existing.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
                return resolve_service_intent("rookdetectie") or existing
            return existing
    task_text = " ".join(
        part
        for part in (
            _clean_string(plan.get("service_label")),
            _clean_string(draft.get("draft_id")),
            _clean_string(proposal.get("patch_proposal_id")),
            package_text,
        )
        if part
    )
    return resolve_service_intent(task_text)


def safe_branch_name(proposal: dict, plan: dict, draft: dict) -> str:
    seed = (
        _clean_string(proposal.get("patch_proposal_id"))
        or _clean_string(draft.get("draft_id"))
        or _clean_string(plan.get("opportunity_id"))
        or "landing-page-opportunity"
    )
    return f"proposal/{stable_kebab_case(seed) or 'landing-page-opportunity'}"


def _preparation_status(proposal: dict, approval_brief: str, approval_timestamp: str) -> str:
    if not proposal:
        return "review_required"
    if not approval_brief or not approval_timestamp:
        return "blocked"
    if proposal.get("final_user_approval_required") is not True:
        return "blocked"
    return "ready_for_preparation_review"


def _file_items(items: list, default_status: str = "proposed_only") -> list[dict]:
    files = []
    for item in items:
        if isinstance(item, dict):
            files.append(
                {
                    "path": _clean_string(item.get("path")) or "unknown",
                    "status": _clean_string(item.get("status")) or default_status,
                    "reason": _clean_string(item.get("reason") or item.get("patch_description")),
                }
            )
    return files


def _ordered_steps(proposal: dict, service_intent: dict | None) -> list[dict]:
    steps = [
        {
            "step": 1,
            "title": "Confirm explicit final apply approval",
            "instruction": "Do not touch turboservices until the user explicitly approves applying the prepared patch.",
        },
        {
            "step": 2,
            "title": "Review target branch",
            "instruction": "Prepare the branch name only; do not create it from this endpoint.",
        },
        {
            "step": 3,
            "title": "Review proposed file changes",
            "instruction": "Compare proposed files and patches against the real repo only after approval.",
        },
        {
            "step": 4,
            "title": "Prepare patch manually",
            "instruction": "Use the text-only proposal as guidance after explicit apply approval.",
        },
        {
            "step": 5,
            "title": "Run validation after apply approval",
            "instruction": "Run validation commands only after separately approved patch application.",
        },
    ]
    if service_intent and service_intent.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
        steps.insert(
            3,
            {
                "step": 3,
                "title": "Confirm rookdetectie business meaning",
                "instruction": "Keep rookdetectie as rooktest/geuropsporing for rioolgeur, riolering, riool and afvoer; exclude fire-safety positioning.",
            },
        )
        for index, step in enumerate(steps, start=1):
            step["step"] = index
    return steps


def _service_intent_summary(service_intent: dict | None) -> dict | None:
    if not service_intent:
        return None
    if service_intent.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
        return {
            "canonical_service": ROOKDETECTIE_CANONICAL_SERVICE,
            "display_name": "Rookdetectie voor geuropsporing",
            "business_meaning": "Rookdetectie betekent rooktest/geuropsporing voor rioolgeur, riolering, riool en afvoer.",
        }
    return {
        "canonical_service": service_intent.get("canonical_service"),
        "display_name": service_intent.get("display_name"),
    }


def build_landing_page_patch_preparation_package(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    plan = _payload_dict(payload, "implementation_plan", "implementationPlan", "plan")
    draft = _payload_dict(payload, "implementation_draft", "implementationDraft", "draft")
    proposal = _patch_proposal(payload)
    package_text = _clean_string(
        payload.get("implementation_package")
        or payload.get("implementationPackage")
        or payload.get("implementation_package_markdown")
        or payload.get("package_markdown")
        or payload.get("package")
    )
    approval_brief = _approval_brief(payload)
    approval_timestamp = _approval_timestamp(payload)
    service_intent = _service_intent(plan, draft, proposal, package_text + " " + approval_brief)
    proposal_id = _clean_string(proposal.get("patch_proposal_id")) or "unknown-patch-proposal"
    package_id = stable_kebab_case(f"patch-prep-{proposal_id}")
    branch_name = safe_branch_name(proposal, plan, draft)
    files_to_create = _file_items(_as_list(proposal.get("proposed_new_files")))
    files_to_modify = _file_items(_as_list(proposal.get("proposed_modified_files")))
    files_to_delete = _file_items(_as_list(proposal.get("proposed_deleted_files")))

    if service_intent and service_intent.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
        files_to_modify.append(
            {
                "path": "content/business-rules/rookdetectie.md",
                "status": "proposed_only",
                "reason": "Business guard: rookdetectie means geuropsporing/rioolgeur context, not fire safety.",
            }
        )

    return {
        "ok": True,
        "preparation_package_id": package_id or "patch-prep-unknown",
        "source_patch_proposal_id": proposal_id,
        "preparation_status": _preparation_status(proposal, approval_brief, approval_timestamp),
        "implementation_scope": {
            "scope": "prepare_patch_instructions_only",
            "execution_authorized": False,
            "service_intent": _service_intent_summary(service_intent),
        },
        "proposed_target_repo": {
            "path": "C:\\Projects\\GitHub\\turboservices",
            "status": "proposed_target_only_not_accessed",
        },
        "proposed_branch_name": branch_name,
        "proposed_commit_message": f"Prepare landing page patch proposal {proposal_id}",
        "proposed_files_to_create": files_to_create,
        "proposed_files_to_modify": files_to_modify,
        "proposed_files_to_delete": files_to_delete,
        "ordered_patch_steps": _ordered_steps(proposal, service_intent),
        "manual_checks_before_apply": [
            "Confirm explicit final apply approval from the user.",
            "Confirm target repo path before any future file operation.",
            "Confirm proposed branch name before branch creation.",
            "Review proposed file paths against the actual repo.",
            "Confirm no deploy, publish, merge, push, Ads or GA4 action is included.",
        ],
        "validation_commands": _as_list(proposal.get("validation_commands")),
        "rollback_notes": [
            "No rollback is needed for this endpoint because it does not write files.",
            "If a future approved apply step changes files, use normal git diff/revert review before deploy.",
        ],
        "risks": _as_list(proposal.get("risks"))
        + [
            {
                "risk": "Preparation package is read-only and has not inspected the target repo.",
                "mitigation": "Verify all paths manually after explicit final apply approval.",
            }
        ],
        "blocked_actions": BLOCKED_ACTIONS,
        "approval_gates": APPROVAL_GATES,
        "read_only_guarantees": READ_ONLY_GUARANTEES,
        "final_apply_approval_required": True,
        "next_allowed_step": NEXT_ALLOWED_STEP,
    }
