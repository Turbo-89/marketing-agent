from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.agent_cockpit_audit_storage_validator import (
    ALLOWED_EVENT_TYPES,
    BLOCKED_ACTIONS,
    DISALLOWED_EVENT_TYPES,
    NEXT_RECOMMENDED_STEP,
    PROPOSED_STORAGE_PATH,
    REQUIRED_EVENT_FIELDS,
    build_agent_cockpit_audit_storage_validator,
    router,
)


def test_endpoint_returns_ok_true():
    app = FastAPI()
    app.include_router(router, prefix="/api/agent-cockpit")
    client = TestClient(app)

    response = client.get("/api/agent-cockpit/audit-storage-validator")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_validator_status_is_read_only_validator():
    validator = build_agent_cockpit_audit_storage_validator()

    assert validator["validator_status"] == "read_only_validator"
    assert validator["current_phase"] == "2F \u2014 Local audit storage strategy"


def test_proposed_path_and_format_are_correct():
    validator = build_agent_cockpit_audit_storage_validator()

    assert validator["proposed_storage_path"] == PROPOSED_STORAGE_PATH
    assert validator["proposed_storage_path"] == (
        r"C:\Projects\TurboWorkspace\audit\operator-run-history.jsonl"
    )
    assert validator["proposed_storage_format"] == "append_only_jsonl"


def test_validation_result_confirms_no_storage_enabled():
    validator = build_agent_cockpit_audit_storage_validator()

    assert validator["validation_result"] == "strategy_ready_no_storage_enabled"


def test_required_event_fields_are_present():
    validator = build_agent_cockpit_audit_storage_validator()

    for field in (
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
    ):
        assert field in validator["required_event_fields"]
        assert field in REQUIRED_EVENT_FIELDS


def test_allowed_and_disallowed_event_types_are_correct():
    validator = build_agent_cockpit_audit_storage_validator()

    for event_type in (
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
    ):
        assert event_type in validator["allowed_event_types"]
        assert event_type in ALLOWED_EVENT_TYPES

    for event_type in (
        "file_written",
        "deploy_triggered",
        "publish_triggered",
        "merge_executed",
        "push_to_live_executed",
        "google_ads_changed",
        "ga4_changed",
        "github_mutation_executed",
    ):
        assert event_type in validator["disallowed_event_types"]
        assert event_type in DISALLOWED_EVENT_TYPES


def test_privacy_rules_exclude_secrets_tokens_and_credentials():
    validator = build_agent_cockpit_audit_storage_validator()
    rules = " ".join(validator["privacy_rules"]).lower()

    assert "do not store secrets" in validator["privacy_rules"]
    assert "do not store oauth tokens" in rules
    assert "do not store private keys" in rules
    assert "do not store raw ads/ga4 credentials" in rules


def test_blocked_actions_include_persistence_write_and_execution_actions():
    validator = build_agent_cockpit_audit_storage_validator()

    for action in (
        "persistence_write",
        "file_write_to_turboservices",
        "deploy",
        "publish",
        "merge",
        "push_to_live",
        "google_ads_change",
        "ga4_change",
        "github_mutation",
    ):
        assert action in validator["blocked_actions"]
        assert action in BLOCKED_ACTIONS


def test_read_only_guarantees_exclude_persistence_and_execution():
    validator = build_agent_cockpit_audit_storage_validator()

    assert "no persistence" in validator["read_only_guarantees"]
    assert "no database" in validator["read_only_guarantees"]
    assert "no file writes" in validator["read_only_guarantees"]
    assert "no external mutations" in validator["read_only_guarantees"]
    assert "no deployment" in validator["read_only_guarantees"]
    assert "no live website changes" in validator["read_only_guarantees"]


def test_next_recommended_step_closes_2f_before_future_writer_work():
    validator = build_agent_cockpit_audit_storage_validator()

    assert validator["next_recommended_step"] == NEXT_RECOMMENDED_STEP
    assert validator["next_recommended_step"] == (
        "close 2F and start 2G local audit writer only after explicit approval"
    )


def test_endpoint_is_deterministic():
    first = build_agent_cockpit_audit_storage_validator()
    second = build_agent_cockpit_audit_storage_validator()

    assert first == second
    assert first is not second
