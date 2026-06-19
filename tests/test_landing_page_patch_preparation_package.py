from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.landing_page_opportunities import router
from app.integrations.landing_page_patch_preparation_package import (
    NEXT_ALLOWED_STEP,
    build_landing_page_patch_preparation_package,
    safe_branch_name,
)


def _plan() -> dict:
    return {
        "opportunity_id": "new-landing-page-ontstopping-antwerpen",
        "service_label": "Ontstopping",
        "region": "Antwerpen",
    }


def _draft() -> dict:
    return {
        "draft_id": "draft-new-landing-page-ontstopping-antwerpen",
    }


def _proposal() -> dict:
    return {
        "patch_proposal_id": "patch-proposal-final-review-ontstopping-antwerpen",
        "proposed_new_files": [{"path": "app/diensten/ontstopping-antwerpen/page.tsx"}],
        "proposed_modified_files": [{"path": "config/services.json"}],
        "proposed_deleted_files": [],
        "validation_commands": [{"command": "npm run build"}],
        "risks": [{"risk": "Proposed only"}],
        "final_user_approval_required": True,
    }


def test_normal_patch_proposal_returns_preparation_package():
    package = build_landing_page_patch_preparation_package(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "patch_proposal": _proposal(),
            "final_patch_approval_brief": "Patch proposal approved for preparation only.",
            "final_patch_approval_timestamp": "2026-06-19 15:00",
        }
    )

    assert package["ok"] is True
    assert package["source_patch_proposal_id"] == "patch-proposal-final-review-ontstopping-antwerpen"
    assert package["preparation_status"] == "ready_for_preparation_review"
    assert package["proposed_files_to_create"][0]["status"] == "proposed_only"
    assert package["proposed_target_repo"]["status"] == "proposed_target_only_not_accessed"


def test_missing_optional_fields_do_not_crash():
    package = build_landing_page_patch_preparation_package({})

    assert package["ok"] is True
    assert package["source_patch_proposal_id"] == "unknown-patch-proposal"
    assert package["preparation_status"] == "review_required"
    assert package["final_apply_approval_required"] is True


def test_missing_final_patch_approval_keeps_status_blocked():
    package = build_landing_page_patch_preparation_package(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "patch_proposal": _proposal(),
        }
    )

    assert package["preparation_status"] == "blocked"


def test_rookdetectie_keeps_geur_riool_context_not_fire_safety():
    plan = _plan()
    plan.update(
        {
            "service_label": "Rookdetectie voor geuropsporing",
            "service_intent": {"canonical_service": "rookdetectie_geuropsporing"},
        }
    )
    proposal = _proposal()
    proposal["patch_proposal_id"] = "patch-proposal-rookdetectie-geuropsporing-antwerpen"

    package = build_landing_page_patch_preparation_package(
        {
            "implementation_plan": plan,
            "implementation_draft": _draft(),
            "patch_proposal": proposal,
            "implementation_package": "rooktest geuropsporing rioolgeur riolering riool afvoer",
            "final_patch_approval_brief": "approved",
            "final_patch_approval_timestamp": "2026-06-19 15:00",
        }
    )
    combined = " ".join(
        [
            str(package["implementation_scope"]),
            str(package["proposed_files_to_modify"]),
            str(package["ordered_patch_steps"]),
        ]
    ).lower()

    assert "geuropsporing" in combined
    assert "rioolgeur" in combined
    assert "rookmelder" not in combined
    assert "brandveiligheid" not in combined
    assert "branddetectie" not in combined
    assert "brandalarm" not in combined


def test_blocked_actions_include_all_forbidden_live_actions():
    package = build_landing_page_patch_preparation_package(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "patch_proposal": _proposal(),
        }
    )

    for action in (
        "file_write",
        "deploy",
        "publish",
        "merge",
        "push",
        "google_ads_change",
        "ga4_change",
        "github_mutation",
    ):
        assert action in package["blocked_actions"]


def test_endpoint_returns_read_only_guarantees_and_approval_gates():
    app = FastAPI()
    app.include_router(router, prefix="/api/opportunities")
    client = TestClient(app)

    response = client.post(
        "/api/opportunities/landing-pages/patch-preparation-package",
        json={
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "patch_proposal": _proposal(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "approve_file_changes" in data["approval_gates"]
    assert "does_not_write_files" in data["read_only_guarantees"]


def test_next_allowed_step_does_not_authorize_execution():
    package = build_landing_page_patch_preparation_package({"patch_proposal": _proposal()})

    assert package["next_allowed_step"] == NEXT_ALLOWED_STEP
    assert "only after explicit final apply approval" in package["next_allowed_step"]
    assert package["final_apply_approval_required"] is True


def test_proposed_branch_name_is_deterministic_and_safe():
    proposal = _proposal()
    first = safe_branch_name(proposal, _plan(), _draft())
    second = safe_branch_name(proposal, _plan(), _draft())

    assert first == second
    assert first == "proposal/patch-proposal-final-review-ontstopping-antwerpen"
    assert " " not in first
    assert first.lower() == first
