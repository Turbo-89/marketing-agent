from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.landing_page_implementation_draft import (
    build_landing_page_implementation_draft,
)
from app.integrations.landing_page_opportunities import router


def _plan() -> dict:
    return {
        "opportunity_id": "new-landing-page-ontstopping-antwerpen",
        "service_label": "Ontstopping",
        "region": "Antwerpen",
        "proposed_slug": "ontstopping-antwerpen",
        "proposed_url_path": "/diensten/ontstopping-antwerpen",
        "seo_title": "Ontstopping Antwerpen | Turbo Services",
        "meta_description": "Plan een gerichte pagina voor ontstopping in Antwerpen.",
        "h1": "Ontstopping in Antwerpen",
        "internal_links": [{"label": "Diensten", "path": "/diensten"}],
        "validation_commands": [{"command": "npm run build", "purpose": "Validate build"}],
        "risks": [{"risk": "Proposed only", "mitigation": "Review before implementation"}],
    }


def test_normal_approved_handoff_produces_implementation_draft():
    draft = build_landing_page_implementation_draft(
        {
            "selected_opportunity": {"type": "new_landing_page", "score": 86},
            "implementation_plan": _plan(),
            "handoff_brief": "Approved for next planning step only.",
            "approval_timestamp": "2026-06-19 10:00",
            "checklist_status": {"planReviewed": True},
        }
    )

    assert draft["ok"] is True
    assert draft["source_plan_id"] == "new-landing-page-ontstopping-antwerpen"
    assert draft["draft_id"] == "draft-new-landing-page-ontstopping-antwerpen-ontstopping-antwerpen"
    assert draft["approval_summary"]["execution_authorized"] is False
    assert draft["proposed_route_structure"]["route_path"] == "/diensten/ontstopping-antwerpen"
    assert draft["proposed_files"][0]["status"] == "proposed_only"


def test_missing_optional_fields_do_not_crash():
    draft = build_landing_page_implementation_draft({})

    assert draft["ok"] is True
    assert draft["source_plan_id"] == "unknown-plan"
    assert draft["proposed_route_structure"]["slug"] == "turbo-services"
    assert draft["approval_summary"]["execution_authorized"] is False


def test_rookdetectie_draft_keeps_geur_riool_context_not_fire_safety():
    plan = _plan()
    plan.update(
        {
            "opportunity_id": "new-landing-page-rookdetectie-geuropsporing-antwerpen",
            "service_intent": {"canonical_service": "rookdetectie_geuropsporing"},
            "service_label": "Rookdetectie voor geuropsporing",
            "proposed_slug": "rookdetectie-geuropsporing-antwerpen",
            "proposed_url_path": "/diensten/rookdetectie-geuropsporing-antwerpen",
        }
    )

    draft = build_landing_page_implementation_draft({"implementation_plan": plan})
    combined = " ".join(
        [
            draft["proposed_route_structure"]["slug"],
            draft["proposed_seo_metadata"]["meta_description"],
            " ".join(block["draft"] for block in draft["proposed_content_blocks"]),
        ]
    ).lower()

    assert draft["service_intent"]["canonical_service"] == "rookdetectie_geuropsporing"
    assert "geuropsporing" in combined
    assert "rioolgeur" in combined
    assert "rookmelder" not in draft["proposed_seo_metadata"]["meta_description"].lower()
    assert "brandveiligheid" not in draft["proposed_seo_metadata"]["meta_description"].lower()
    assert "branddetectie" not in draft["proposed_seo_metadata"]["meta_description"].lower()
    assert "brandalarm" not in draft["proposed_seo_metadata"]["meta_description"].lower()


def test_blocked_actions_include_all_forbidden_live_actions():
    draft = build_landing_page_implementation_draft({"implementation_plan": _plan()})

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
        assert action in draft["blocked_actions"]


def test_endpoint_returns_read_only_guarantees_and_approval_gates():
    app = FastAPI()
    app.include_router(router, prefix="/api/opportunities")
    client = TestClient(app)

    response = client.post(
        "/api/opportunities/landing-pages/implementation-draft",
        json={"implementation_plan": _plan()},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "approve_file_changes" in data["approval_gates"]
    assert "does_not_write_files" in data["read_only_guarantees"]
