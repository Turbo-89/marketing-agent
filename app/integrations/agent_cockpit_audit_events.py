import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

AUDIT_STORAGE_PATH = Path(r"C:\Projects\TurboWorkspace\audit\operator-run-history.jsonl")
SAFETY_STATE = "audit_only_no_execution"

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

OPTIONAL_RELATED_FIELDS = [
    "notes",
    "related_opportunity_id",
    "related_plan_id",
    "related_draft_id",
    "related_review_id",
    "related_patch_proposal_id",
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

READ_ONLY_EXECUTION_GUARANTEES = [
    "audit logging only",
    "no turboservices write",
    "no deploy",
    "no publish",
    "no Ads/GA4 mutation",
    "no GitHub mutation",
]

SECRET_MARKERS = [
    "api_key",
    "client_secret",
    "credentials",
    "oauth",
    "private_key",
    "refresh_token",
    "secret",
]


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _event_id(created_at: str, event: dict) -> str:
    timestamp = (
        created_at.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("+", "")
        .replace("Z", "Z")
    )
    seed = json.dumps(event, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"{created_at}:{seed}".encode("utf-8")).hexdigest()[:12]
    return f"audit_{timestamp}_{digest}"


def _validate_event_type(event_type: str) -> None:
    if event_type in DISALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="disallowed_event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="unknown_event_type")


def _reject_secret_like_content(values: list[str]) -> None:
    combined = " ".join(values).lower()
    if any(marker in combined for marker in SECRET_MARKERS):
        raise HTTPException(status_code=400, detail="secret_like_content_rejected")


def _build_audit_event(payload: dict, created_at: str) -> dict:
    event_type = _clean_string(payload.get("event_type"))
    _validate_event_type(event_type)

    required = {
        "event_type": event_type,
        "source": _clean_string(payload.get("source")),
        "actor": _clean_string(payload.get("actor")),
        "workflow_phase": _clean_string(payload.get("workflow_phase")),
        "user_visible_summary": _clean_string(payload.get("user_visible_summary")),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise HTTPException(status_code=400, detail={"missing_fields": missing})
    optional_values = [
        _clean_string(payload.get(field))
        for field in OPTIONAL_RELATED_FIELDS
        if _clean_string(payload.get(field))
    ]
    _reject_secret_like_content(list(required.values()) + optional_values)

    event = {
        **required,
        "created_at": created_at,
        "safety_state": SAFETY_STATE,
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_execution_guarantees": list(READ_ONLY_EXECUTION_GUARANTEES),
    }

    for field in OPTIONAL_RELATED_FIELDS:
        value = _clean_string(payload.get(field))
        if value:
            event[field] = value

    event["event_id"] = _event_id(created_at, event)
    return event


def append_audit_event(payload: dict, storage_path: Path | None = None) -> dict:
    path = storage_path or AUDIT_STORAGE_PATH
    created_at = _utc_now()
    event = _build_audit_event(payload, created_at)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")

    return {
        "ok": True,
        "audit_write_status": "appended",
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "created_at": event["created_at"],
        "storage_path": str(path),
        "safety_state": event["safety_state"],
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_execution_guarantees": list(READ_ONLY_EXECUTION_GUARANTEES),
        "message": "Audit event appended locally. No execution actions were performed.",
    }


@router.post("/audit-events")
async def agent_cockpit_audit_events(request: Request):
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_json_object")
    return append_audit_event(payload)
