from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.landing_page_final_implementation_review import (
    NEXT_ALLOWED_STEP,
    build_landing_page_final_implementation_review,
)
from app.integrations.landing_page_opportunities import router


def _plan() -> dict:
    return {
        "opportunity_id": "new-landing-page-ontstopping-antwerpen",
        "service_label": "Ontstopping",
        "region": "Antwerpen",
    }


def _draft() -> dict:
    return {
        "draft_id": "draft-new-landing-page-ontstopping-antwerpen",
        "source_plan_id": "new-landing-page-ontstopping-antwerpen",
        "proposed_files": [{"path": "app/diensten/ontstopping-antwerpen/page.tsx"}],
        "proposed_route_structure": {"route_path": "/diensten/ontstopping-antwerpen"},
        "proposed_content_blocks": [{"block": "hero", "draft": "Ontstopping in Antwerpen"}],
        "proposed_seo_metadata": {"title": "Ontstopping Antwerpen | Turbo Services"},
        "proposed_schema_jsonld": {"@type": "Service", "name": "Ontstopping"},
        "proposed_internal_links": [{"label": "Diensten", "path": "/diensten"}],
        "proposed_validation_plan": [{"command": "npm run build"}],
        "risks": [{"risk": "Proposed only"}],
    }


def _checklist(done: bool = True) -> dict:
    return {
        "planReviewed": done,
        "seoReviewed": done,
        "contentReviewed": done,
        "schemaReviewed": done,
        "linksReviewed": done,
        "risksReviewed": done,
        "approvalStillRequired": done,
    }


def test_normal_implementation_package_returns_final_review():
    review = build_landing_page_final_implementation_review(
        {
            "selected_opportunity": {"type": "new_landing_page", "score": 90},
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "implementation_package": "Implementation package markdown",
            "approval_timestamp": "2026-06-19 12:00",
            "checklist_status": _checklist(),
        }
    )

    assert review["ok"] is True
    assert review["source_draft_id"] == "draft-new-landing-page-ontstopping-antwerpen"
    assert review["readiness_status"] == "ready_for_final_user_review"
    assert review["readiness_score"] == 100
    assert review["final_approval_required"] is True


def test_missing_optional_fields_do_not_crash():
    review = build_landing_page_final_implementation_review({})

    assert review["ok"] is True
    assert review["source_draft_id"] == "unknown-draft"
    assert review["readiness_status"] == "incomplete"
    assert "implementation_plan" in review["required_missing_items"]


def test_incomplete_checklist_lowers_readiness_and_reports_missing_items():
    checklist = _checklist()
    checklist["seoReviewed"] = False
    review = build_landing_page_final_implementation_review(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "implementation_package": "Package",
            "checklist_status": checklist,
        }
    )

    assert review["readiness_score"] < 100
    assert review["readiness_status"] == "ready_for_final_user_review"
    assert "seoReviewed" in review["required_missing_items"]


def test_rookdetectie_review_keeps_geur_riool_context_not_fire_safety():
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
            "proposed_route_structure": {"route_path": "/diensten/rookdetectie-geuropsporing-antwerpen"},
            "proposed_content_blocks": [
                {"block": "hero", "draft": "Rooktest voor geuropsporing bij rioolgeur en riolering"}
            ],
            "proposed_seo_metadata": {"title": "Rookdetectie voor geuropsporing"},
        }
    )

    review = build_landing_page_final_implementation_review(
        {
            "implementation_plan": plan,
            "implementation_draft": draft,
            "implementation_package": "rooktest geuropsporing rioolgeur riolering riool afvoer",
            "checklist_status": _checklist(),
        }
    )

    rule = review["content_review"]["rookdetectie_business_rule"]
    combined = " ".join(
        [
            rule["required_meaning"],
            str(review["seo_review"]["metadata"]),
            str(review["content_review"]["blocks"]),
        ]
    ).lower()
    assert rule["applies"] is True
    assert "geuropsporing" in combined
    assert "rioolgeur" in combined
    assert "rookmelder" not in str(review["seo_review"]["metadata"]).lower()
    assert "brandveiligheid" not in str(review["seo_review"]["metadata"]).lower()
    assert "branddetectie" not in str(review["seo_review"]["metadata"]).lower()
    assert "brandalarm" not in str(review["seo_review"]["metadata"]).lower()


def test_blocked_actions_include_all_forbidden_live_actions():
    review = build_landing_page_final_implementation_review(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "implementation_package": "Package",
            "checklist_status": _checklist(),
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
        assert action in review["blocked_actions"]


def test_endpoint_returns_read_only_guarantees_and_approval_gates():
    app = FastAPI()
    app.include_router(router, prefix="/api/opportunities")
    client = TestClient(app)

    response = client.post(
        "/api/opportunities/landing-pages/final-implementation-review",
        json={
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "implementation_package": "Package",
            "checklist_status": _checklist(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "approve_file_changes" in data["approval_gates"]
    assert "does_not_write_files" in data["read_only_guarantees"]


def test_next_allowed_step_does_not_authorize_execution():
    review = build_landing_page_final_implementation_review(
        {
            "implementation_plan": _plan(),
            "implementation_draft": _draft(),
            "implementation_package": "Package",
            "checklist_status": _checklist(),
        }
    )

    assert review["next_allowed_step"] == NEXT_ALLOWED_STEP
    assert "only after explicit final user approval" in review["next_allowed_step"]
    assert "deploy" not in review["next_allowed_step"]
