from copy import deepcopy

from fastapi import APIRouter

router = APIRouter()

CURRENT_PHASE = "2E \u2014 Operator run history and audit trail"
NEXT_RECOMMENDED_STEP = "connect cockpit UI to read-only run history scaffold"

TRACKED_EVENT_TYPES = [
    "opportunity_scanned",
    "implementation_plan_generated",
    "implementation_draft_generated",
    "implementation_package_generated",
    "final_review_generated",
    "patch_proposal_generated",
    "patch_preparation_package_generated",
    "human_approval_recorded",
]

AUDIT_FIELDS = [
    "event_id",
    "event_type",
    "created_at",
    "source",
    "actor",
    "related_opportunity_id",
    "related_plan_id",
    "related_draft_id",
    "related_review_id",
    "related_patch_proposal_id",
    "safety_state",
    "blocked_actions",
    "notes",
]

BLOCKED_ACTIONS = [
    "file_write_to_turboservices",
    "deploy",
    "publish",
    "merge",
    "push_to_live",
    "google_ads_change",
    "ga4_change",
    "github_mutation",
]

READ_ONLY_GUARANTEES = [
    "no persistence",
    "no file writes",
    "no external mutations",
    "no deployment",
    "no live website changes",
]

SAMPLE_EVENTS = [
    {
        "event_id": "sample-run-history-001",
        "event_type": "opportunity_scanned",
        "created_at": "2026-06-19T09:00:00Z",
        "source": "static_sample",
        "actor": "sample_operator",
        "related_opportunity_id": "sample-opportunity-rookdetectie-antwerpen",
        "related_plan_id": None,
        "related_draft_id": None,
        "related_review_id": None,
        "related_patch_proposal_id": None,
        "safety_state": "sample_static_read_only",
        "blocked_actions": list(BLOCKED_ACTIONS),
        "notes": "Static sample only; not real operator history.",
    },
    {
        "event_id": "sample-run-history-002",
        "event_type": "implementation_plan_generated",
        "created_at": "2026-06-19T09:05:00Z",
        "source": "static_sample",
        "actor": "sample_operator",
        "related_opportunity_id": "sample-opportunity-rookdetectie-antwerpen",
        "related_plan_id": "sample-plan-rookdetectie-antwerpen",
        "related_draft_id": None,
        "related_review_id": None,
        "related_patch_proposal_id": None,
        "safety_state": "sample_static_read_only",
        "blocked_actions": list(BLOCKED_ACTIONS),
        "notes": "Static sample only; no files were written.",
    },
    {
        "event_id": "sample-run-history-003",
        "event_type": "human_approval_recorded",
        "created_at": "2026-06-19T09:10:00Z",
        "source": "static_sample",
        "actor": "sample_operator",
        "related_opportunity_id": "sample-opportunity-rookdetectie-antwerpen",
        "related_plan_id": "sample-plan-rookdetectie-antwerpen",
        "related_draft_id": "sample-draft-rookdetectie-antwerpen",
        "related_review_id": "sample-review-rookdetectie-antwerpen",
        "related_patch_proposal_id": "sample-patch-proposal-rookdetectie-antwerpen",
        "safety_state": "sample_static_read_only",
        "blocked_actions": list(BLOCKED_ACTIONS),
        "notes": "Static sample only; not approval for execution.",
    },
]


def build_agent_cockpit_run_history() -> dict:
    return {
        "ok": True,
        "history_status": "read_only_scaffold",
        "current_phase": CURRENT_PHASE,
        "purpose": (
            "Describe the future operator run history and audit trail without "
            "persisting events or executing workflow actions."
        ),
        "tracked_event_types": list(TRACKED_EVENT_TYPES),
        "sample_events": deepcopy(SAMPLE_EVENTS),
        "audit_fields": list(AUDIT_FIELDS),
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_guarantees": list(READ_ONLY_GUARANTEES),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


@router.get("/run-history")
def agent_cockpit_run_history():
    return build_agent_cockpit_run_history()
