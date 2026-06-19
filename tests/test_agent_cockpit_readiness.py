from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.agent_cockpit_readiness import (
    BLOCKED_ACTIONS,
    CURRENT_PHASE,
    PREVIOUS_PHASE,
    build_agent_cockpit_readiness,
    router,
)


def test_endpoint_returns_ok_true():
    app = FastAPI()
    app.include_router(router, prefix="/api/agent-cockpit")
    client = TestClient(app)

    response = client.get("/api/agent-cockpit/readiness")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_current_and_previous_phase_are_correct():
    readiness = build_agent_cockpit_readiness()

    assert readiness["current_phase"] == CURRENT_PHASE
    assert readiness["previous_phase"] == PREVIOUS_PHASE
    assert readiness["current_phase"] == "2D \u2014 Cockpit, status overview and operator control"
    assert readiness["previous_phase"] == "2C \u2014 Opportunity to read-only patch preparation workflow"


def test_blocked_actions_include_all_required_actions():
    readiness = build_agent_cockpit_readiness()

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
        assert action in readiness["blocked_actions"]
        assert action in BLOCKED_ACTIONS


def test_write_deploy_ads_and_ga4_access_are_disabled():
    readiness = build_agent_cockpit_readiness()

    assert readiness["site_write_access"] == "disabled"
    assert readiness["ads_ga4_write_access"] == "disabled"
    assert readiness["deploy_publish_access"] == "disabled"


def test_execution_requires_human_approval():
    readiness = build_agent_cockpit_readiness()

    assert readiness["execution_requires_human_approval"] is True


def test_rookdetectie_guard_is_present_and_keeps_fire_safety_terms_excluded():
    readiness = build_agent_cockpit_readiness()
    guard = readiness["service_guards"]["rookdetectie"]
    positive_text = " ".join(guard["positive_terms"] + [guard["meaning"]]).lower()

    assert guard["canonical_service"] == "rookdetectie_geuropsporing"
    assert "rooktest" in positive_text
    assert "geuropsporing" in positive_text
    assert "rioolgeur" in positive_text
    assert "riolering" in positive_text
    assert "rookmelders" in guard["excluded_terms"]
    assert "brandveiligheid" in guard["excluded_terms"]
    assert "branddetectie" in guard["excluded_terms"]
    assert "brandalarm" in guard["excluded_terms"]
    assert "rookmelders" not in positive_text
    assert "brandveiligheid" not in positive_text
    assert "branddetectie" not in positive_text
    assert "brandalarm" not in positive_text


def test_endpoint_is_deterministic():
    first = build_agent_cockpit_readiness()
    second = build_agent_cockpit_readiness()

    assert first == second
    assert first is not second
