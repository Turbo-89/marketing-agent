from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.turboservices_release_safety_checklist import (
    BLOCKED_ACTIONS,
    NEXT_ALLOWED_STEP,
    READ_ONLY_GUARANTEES,
    build_turboservices_release_safety_checklist,
    router,
)


def _patch_plan() -> dict:
    return {
        "patch_plan_id": "patch-plan-ontstopping-antwerpen",
        "read_only": True,
        "selected_patch_scope": {
            "service": "ontstopping",
            "region": "Antwerpen",
            "slug": "ontstopping-antwerpen",
        },
        "proposed_branch_name": "proposal/landing-page-ontstopping-antwerpen",
        "proposed_commit_message": "Prepare landing page patch plan for ontstopping-antwerpen",
    }


def _review_checklist() -> dict:
    return {
        "review_checklist_id": "review-checklist-ontstopping-antwerpen",
        "read_only": True,
        "draft_pr_title": "Draft review: ontstopping Antwerpen landing page patch",
        "proposed_branch_name": "proposal/landing-page-ontstopping-antwerpen",
    }


def _valid_payload() -> dict:
    return {
        "patch_plan": _patch_plan(),
        "review_checklist": _review_checklist(),
        "validation_results": {"build": "reviewed"},
        "rollback_plan": ["Revert local patch before deploy if validation fails."],
        "final_user_approval": {"approved_for_release_review": True},
    }


def test_valid_release_checklist_result():
    checklist = build_turboservices_release_safety_checklist(_valid_payload())

    assert checklist["ok"] is True
    assert checklist["release_status"] == "ready_for_final_release_review"
    assert checklist["read_only"] is True
    assert checklist["required_pre_release_checks"]


def test_missing_validation_results_gives_needs_validation_results():
    payload = _valid_payload()
    payload.pop("validation_results")

    checklist = build_turboservices_release_safety_checklist(payload)

    assert checklist["release_status"] == "needs_validation_results"


def test_missing_rollback_plan_gives_needs_rollback_plan():
    payload = _valid_payload()
    payload.pop("rollback_plan")

    checklist = build_turboservices_release_safety_checklist(payload)

    assert checklist["release_status"] == "needs_rollback_plan"


def test_missing_final_user_approval_gives_needs_final_user_approval():
    payload = _valid_payload()
    payload.pop("final_user_approval")

    checklist = build_turboservices_release_safety_checklist(payload)

    assert checklist["release_status"] == "needs_final_user_approval"


def test_blocked_actions_are_present():
    checklist = build_turboservices_release_safety_checklist(_valid_payload())

    for action in BLOCKED_ACTIONS:
        assert action in checklist["blocked_actions"]


def test_read_only_guarantees_exclude_release_deploy_merge_push_github_write_ads_ga4():
    checklist = build_turboservices_release_safety_checklist(_valid_payload())

    for guarantee in READ_ONLY_GUARANTEES:
        assert guarantee in checklist["read_only_guarantees"]
    assert "no release" in checklist["read_only_guarantees"]
    assert "no deploy" in checklist["read_only_guarantees"]
    assert "no merge" in checklist["read_only_guarantees"]
    assert "no push" in checklist["read_only_guarantees"]
    assert "no GitHub mutation" in checklist["read_only_guarantees"]
    assert "no file writes" in checklist["read_only_guarantees"]
    assert "no Ads/GA4 changes" in checklist["read_only_guarantees"]


def test_final_release_approval_required_is_true():
    checklist = build_turboservices_release_safety_checklist(_valid_payload())

    assert checklist["final_release_approval_required"] is True


def test_next_allowed_step_requires_explicit_final_release_approval():
    checklist = build_turboservices_release_safety_checklist(_valid_payload())

    assert checklist["next_allowed_step"] == NEXT_ALLOWED_STEP
    assert "explicit final release approval" in checklist["next_allowed_step"]


def test_rookdetectie_guard_stays_correct():
    payload = _valid_payload()
    payload["patch_plan"]["selected_patch_scope"] = {
        "service": "rookdetectie",
        "region": "Antwerpen",
        "slug": "rookdetectie-antwerpen",
    }
    payload["review_checklist"]["draft_pr_title"] = "Rookdetectie geuropsporing Antwerpen"

    checklist = build_turboservices_release_safety_checklist(payload)
    guard = checklist["release_context"]["service_guard"]["guard"]
    meaning = guard["meaning"].lower()

    assert "rooktest" in meaning
    assert "geuropsporing" in meaning
    assert "rioolgeur" in meaning
    assert "rookmelders" in guard["excluded_meanings"]
    assert "brandveiligheid" in guard["excluded_meanings"]
    assert "branddetectie" in guard["excluded_meanings"]
    assert "brandalarm" in guard["excluded_meanings"]
    assert "rookmelders" not in meaning
    assert "brandveiligheid" not in meaning
    assert "branddetectie" not in meaning
    assert "brandalarm" not in meaning


def test_endpoint_returns_release_checklist():
    app = FastAPI()
    app.include_router(router, prefix="/api/turboservices")
    client = TestClient(app)

    response = client.post(
        "/api/turboservices/release-safety-checklist",
        json=_valid_payload(),
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
