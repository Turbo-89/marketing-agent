from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.landing_page_final_implementation_review import NEXT_ALLOWED_STEP as REVIEW_NEXT_ALLOWED_STEP
from app.integrations.landing_page_opportunities import router
from app.integrations.landing_page_patch_proposal import (
    NEXT_ALLOWED_STEP,
    build_landing_page_patch_proposal,
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
        "proposed_files": [
            {"path": "app/diensten/ontstopping-antwerpen/page.tsx"},
            {"path": "config/services.json"},
        ],
        "proposed_route_structure": {"route_path": "/diensten/ontstopping-antwerpen"},
        "proposed_content_blocks": [{"block": "hero", "draft": "Ontstopping in Antwerpen"}],
        "proposed_seo_metadata": {"title": "Ontstopping Antwerpen | Turbo Services"},
        "proposed_schema_jsonld": {"@type": "Service", "name": "Ontstopping"},
        "proposed_internal_links": [{"label": "Diensten", "path": "/diensten"}],
        "proposed_validation_plan": [{"command": "npm run build"}],
        "risks": [{"risk": "Proposed only"}],
    }


def _review(ready: bool = True) -> dict:
    return {
        "review_id": "final-review-draft-new-landing-page-ontstopping-antwerpen",
        "source_draft_id": "draft-new-landing-page-ontstopping-antwerpen",
        "readiness_status": "ready_for_final_user_review" if ready else "needs_review",
        "final_approval_required": True,
        "next_allowed_step": REVIEW_NEXT_ALLOWED_STEP if ready else "review missing items",
    }


def test_normal_final_review_produces_patch_proposal():
    proposal = build_landing_page_patch_proposal(
        {
            "selected_opportunity": {"type": "new_landing_page"},
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "implementation_package": "Implementation package markdown",
            "final_implementation_review": _review(),
            "approval_timestamp": "2026-06-19 14:00",
            "checklist_status": {"planReviewed": True},
        }
    )

    assert proposal["ok"] is True
    assert proposal["source_review_id"] == "final-review-draft-new-landing-page-ontstopping-antwerpen"
    assert proposal["patch_readiness_status"] == "ready_for_patch_proposal"
    assert proposal["proposed_file_patches"]
    assert proposal["proposed_new_files"][0]["status"] == "proposed_only"


def test_missing_optional_fields_do_not_crash():
    proposal = build_landing_page_patch_proposal({})

    assert proposal["ok"] is True
    assert proposal["source_review_id"] == "unknown-review"
    assert proposal["patch_readiness_status"] == "review_required"
    assert proposal["final_user_approval_required"] is True


def test_incomplete_or_missing_final_approval_keeps_patch_blocked():
    proposal = build_landing_page_patch_proposal(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "final_implementation_review": _review(ready=False),
        }
    )

    assert proposal["patch_readiness_status"] == "blocked"
    assert proposal["final_user_approval_required"] is True


def test_rookdetectie_proposal_keeps_geur_riool_context_not_fire_safety():
    plan = _plan()
    plan.update(
        {
            "service_label": "Rookdetectie voor geuropsporing",
            "service_intent": {"canonical_service": "rookdetectie_geuropsporing"},
        }
    )
    draft = _draft()
    draft.update(
        {
            "draft_id": "draft-rookdetectie-geuropsporing-antwerpen",
            "proposed_files": [{"path": "app/diensten/rookdetectie-geuropsporing-antwerpen/page.tsx"}],
            "proposed_route_structure": {"route_path": "/diensten/rookdetectie-geuropsporing-antwerpen"},
            "proposed_content_blocks": [{"block": "hero", "draft": "Rooktest voor geuropsporing bij rioolgeur"}],
            "proposed_seo_metadata": {"title": "Rookdetectie voor geuropsporing"},
        }
    )
    proposal = build_landing_page_patch_proposal(
        {
            "implementation_plan": plan,
            "implementation_draft": draft,
            "implementation_package": "rooktest geuropsporing rioolgeur riolering riool afvoer",
            "final_implementation_review": _review(),
        }
    )
    combined = " ".join(
        [
            str(proposal["proposed_content_changes"]),
            str(proposal["proposed_file_patches"]),
            str(proposal["proposed_seo_changes"]),
        ]
    ).lower()

    assert "geuropsporing" in combined
    assert "rioolgeur" in combined
    assert "rookmelder" not in str(proposal["proposed_seo_changes"]).lower()
    assert "brandveiligheid" not in str(proposal["proposed_seo_changes"]).lower()
    assert "branddetectie" not in str(proposal["proposed_seo_changes"]).lower()
    assert "brandalarm" not in str(proposal["proposed_seo_changes"]).lower()


def test_blocked_actions_include_all_forbidden_live_actions():
    proposal = build_landing_page_patch_proposal(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "final_implementation_review": _review(),
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
        assert action in proposal["blocked_actions"]


def test_endpoint_returns_read_only_guarantees_and_approval_gates():
    app = FastAPI()
    app.include_router(router, prefix="/api/opportunities")
    client = TestClient(app)

    response = client.post(
        "/api/opportunities/landing-pages/patch-proposal",
        json={
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "final_implementation_review": _review(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "approve_file_changes" in data["approval_gates"]
    assert "does_not_write_files" in data["read_only_guarantees"]


def test_next_allowed_step_does_not_authorize_execution_without_final_approval():
    proposal = build_landing_page_patch_proposal(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "final_implementation_review": _review(),
        }
    )

    assert proposal["next_allowed_step"] == NEXT_ALLOWED_STEP
    assert "only after explicit final user approval" in proposal["next_allowed_step"]
    assert proposal["final_user_approval_required"] is True
