from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.agent_cockpit_run_history import (
    AUDIT_FIELDS,
    BLOCKED_ACTIONS,
    NEXT_RECOMMENDED_STEP,
    TRACKED_EVENT_TYPES,
    build_agent_cockpit_run_history,
    router,
)


def test_endpoint_returns_ok_true():
    app = FastAPI()
    app.include_router(router, prefix="/api/agent-cockpit")
    client = TestClient(app)

    response = client.get("/api/agent-cockpit/run-history")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_history_status_is_read_only_scaffold():
    history = build_agent_cockpit_run_history()

    assert history["history_status"] == "read_only_scaffold"
    assert history["current_phase"] == "2E \u2014 Operator run history and audit trail"


def test_tracked_event_types_include_required_workflow_events():
    history = build_agent_cockpit_run_history()

    for event_type in (
        "opportunity_scanned",
        "implementation_plan_generated",
        "implementation_draft_generated",
        "implementation_package_generated",
        "final_review_generated",
        "patch_proposal_generated",
        "patch_preparation_package_generated",
        "human_approval_recorded",
    ):
        assert event_type in history["tracked_event_types"]
        assert event_type in TRACKED_EVENT_TYPES


def test_sample_events_are_marked_static_sample():
    history = build_agent_cockpit_run_history()

    assert 2 <= len(history["sample_events"]) <= 3
    for event in history["sample_events"]:
        assert event["source"] == "static_sample"
        assert "sample" in event["event_id"]
        assert "sample" in event["safety_state"]
        assert "Static sample only" in event["notes"]


def test_audit_fields_include_required_fields():
    history = build_agent_cockpit_run_history()

    for field in (
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
    ):
        assert field in history["audit_fields"]
        assert field in AUDIT_FIELDS


def test_blocked_actions_include_required_blocked_actions():
    history = build_agent_cockpit_run_history()

    for action in (
        "file_write_to_turboservices",
        "deploy",
        "publish",
        "merge",
        "push_to_live",
        "google_ads_change",
        "ga4_change",
        "github_mutation",
    ):
        assert action in history["blocked_actions"]
        assert action in BLOCKED_ACTIONS


def test_read_only_guarantees_exclude_persistence_and_execution():
    history = build_agent_cockpit_run_history()
    guarantees = " ".join(history["read_only_guarantees"]).lower()

    assert "no persistence" in history["read_only_guarantees"]
    assert "no file writes" in history["read_only_guarantees"]
    assert "no external mutations" in history["read_only_guarantees"]
    assert "no deployment" in history["read_only_guarantees"]
    assert "no live website changes" in history["read_only_guarantees"]
    assert "write" in guarantees
    assert "deployment" in guarantees


def test_next_recommended_step_is_ui_connection():
    history = build_agent_cockpit_run_history()

    assert history["next_recommended_step"] == NEXT_RECOMMENDED_STEP
    assert history["next_recommended_step"] == "connect cockpit UI to read-only run history scaffold"


def test_endpoint_is_deterministic():
    first = build_agent_cockpit_run_history()
    second = build_agent_cockpit_run_history()

    assert first == second
    assert first is not second
