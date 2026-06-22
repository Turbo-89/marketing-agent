from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.turboservices_review_checklist import (
    BLOCKED_ACTIONS,
    NEXT_ALLOWED_STEP,
    READ_ONLY_GUARANTEES,
    build_turboservices_review_checklist,
    router,
)


def _patch_plan() -> dict:
    return {
        "patch_plan_id": "patch-plan-ontstopping-antwerpen",
        "plan_status": "ready_for_review",
        "read_only": True,
        "selected_patch_scope": {
            "service": "ontstopping",
            "region": "Antwerpen",
            "slug": "ontstopping-antwerpen",
        },
        "proposed_branch_name": "proposal/landing-page-ontstopping-antwerpen",
        "proposed_commit_message": "Prepare landing page patch plan for ontstopping-antwerpen",
        "existing_target_files": [{"path": "content/services.json", "status": "existing"}],
        "proposed_new_files": [
            {"path": "app/diensten/ontstopping-antwerpen/page.tsx", "status": "proposed_new"}
        ],
        "proposed_modified_files": [{"path": "content/services.json", "status": "existing"}],
        "proposed_deleted_files": [],
    }


def test_valid_checklist_result():
    checklist = build_turboservices_review_checklist({"patch_plan": _patch_plan()})

    assert checklist["ok"] is True
    assert checklist["checklist_status"] == "ready_for_manual_review"
    assert checklist["read_only"] is True
    assert checklist["changed_files_review"]


def test_missing_patch_plan_gives_needs_patch_plan():
    checklist = build_turboservices_review_checklist({})

    assert checklist["ok"] is True
    assert checklist["checklist_status"] == "needs_patch_plan"


def test_draft_pr_title_and_body_are_generated():
    checklist = build_turboservices_review_checklist({"patch_plan": _patch_plan()})

    assert checklist["draft_pr_title"]
    assert "landing page patch" in checklist["draft_pr_title"]
    assert "Read-only draft PR checklist" in checklist["draft_pr_body"]
    assert "No PR, branch, commit, push, deploy or publish action" in checklist["draft_pr_body"]


def test_blocked_actions_are_present():
    checklist = build_turboservices_review_checklist({"patch_plan": _patch_plan()})

    for action in BLOCKED_ACTIONS:
        assert action in checklist["blocked_actions"]


def test_read_only_guarantees_exclude_github_pr_branch_write_and_deploy():
    checklist = build_turboservices_review_checklist({"patch_plan": _patch_plan()})

    for guarantee in READ_ONLY_GUARANTEES:
        assert guarantee in checklist["read_only_guarantees"]
    assert "no GitHub mutation" in checklist["read_only_guarantees"]
    assert "no PR creation" in checklist["read_only_guarantees"]
    assert "no branch creation" in checklist["read_only_guarantees"]
    assert "no file writes" in checklist["read_only_guarantees"]
    assert "no deploy" in checklist["read_only_guarantees"]


def test_final_pr_creation_approval_required_is_true():
    checklist = build_turboservices_review_checklist({"patch_plan": _patch_plan()})

    assert checklist["final_pr_creation_approval_required"] is True


def test_next_allowed_step_requires_explicit_approval():
    checklist = build_turboservices_review_checklist({"patch_plan": _patch_plan()})

    assert checklist["next_allowed_step"] == NEXT_ALLOWED_STEP
    assert "explicit final approval" in checklist["next_allowed_step"]


def test_rookdetectie_guard_stays_correct():
    patch_plan = _patch_plan()
    patch_plan["selected_patch_scope"] = {
        "service": "rookdetectie",
        "region": "Antwerpen",
        "slug": "rookdetectie-antwerpen",
    }
    checklist = build_turboservices_review_checklist(
        {
            "patch_plan": patch_plan,
            "requested_service_intent": "rookdetectie",
            "requested_slug": "rookdetectie-antwerpen",
        }
    )
    guard = checklist["service_guard"]["guard"]
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


def test_endpoint_returns_checklist():
    app = FastAPI()
    app.include_router(router, prefix="/api/turboservices")
    client = TestClient(app)

    response = client.post("/api/turboservices/review-checklist", json={"patch_plan": _patch_plan()})

    assert response.status_code == 200
    assert response.json()["ok"] is True
