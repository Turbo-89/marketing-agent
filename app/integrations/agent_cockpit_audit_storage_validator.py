from fastapi import APIRouter

router = APIRouter()

CURRENT_PHASE = "2F \u2014 Local audit storage strategy"
PROPOSED_STORAGE_PATH = r"C:\Projects\TurboWorkspace\audit\operator-run-history.jsonl"
NEXT_RECOMMENDED_STEP = (
    "close 2F and start 2G local audit writer only after explicit approval"
)

REQUIRED_EVENT_FIELDS = [
    "event_id",
    "event_type",
    "created_at",
    "source",
    "actor",
    "workflow_phase",
    "safety_state",
    "blocked_actions",
    "user_visible_summary",
    "notes",
]

ALLOWED_EVENT_TYPES = [
    "opportunity_scanned",
    "implementation_plan_generated",
    "implementation_draft_generated",
    "implementation_package_generated",
    "final_review_generated",
    "patch_proposal_generated",
    "patch_preparation_package_generated",
    "human_approval_recorded",
    "readiness_checked",
    "run_history_viewed",
]

DISALLOWED_EVENT_TYPES = [
    "file_written",
    "deploy_triggered",
    "publish_triggered",
    "merge_executed",
    "push_to_live_executed",
    "google_ads_changed",
    "ga4_changed",
    "github_mutation_executed",
]

PRIVACY_RULES = [
    "do not store secrets",
    "do not store OAuth tokens",
    "do not store private keys",
    "do not store raw Ads/GA4 credentials",
    "avoid customer personal data unless explicitly required",
]

SAFETY_RULES = [
    "no persistence is enabled yet",
    "append-only storage must be used when enabled later",
    "do not record execution as completed unless it actually happened after approval",
    "audit storage must not trigger execution",
    "audit storage must not write to turboservices",
]

BLOCKED_ACTIONS = [
    "persistence_write",
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
    "no database",
    "no file writes",
    "no external mutations",
    "no deployment",
    "no live website changes",
]


def build_agent_cockpit_audit_storage_validator() -> dict:
    return {
        "ok": True,
        "validator_status": "read_only_validator",
        "current_phase": CURRENT_PHASE,
        "proposed_storage_path": PROPOSED_STORAGE_PATH,
        "proposed_storage_format": "append_only_jsonl",
        "validation_result": "strategy_ready_no_storage_enabled",
        "required_event_fields": list(REQUIRED_EVENT_FIELDS),
        "allowed_event_types": list(ALLOWED_EVENT_TYPES),
        "disallowed_event_types": list(DISALLOWED_EVENT_TYPES),
        "privacy_rules": list(PRIVACY_RULES),
        "safety_rules": list(SAFETY_RULES),
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_guarantees": list(READ_ONLY_GUARANTEES),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


@router.get("/audit-storage-validator")
def agent_cockpit_audit_storage_validator():
    return build_agent_cockpit_audit_storage_validator()
