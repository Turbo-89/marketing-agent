from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.landing_page_implementation_plan import (
    build_landing_page_implementation_plan,
    stable_kebab_case,
)
from app.integrations.landing_page_opportunities import router


def test_normal_opportunity_builds_implementation_plan():
    plan = build_landing_page_implementation_plan(
        {
            "type": "new_landing_page",
            "canonical_service": "ontstopping",
            "region": "Antwerpen",
            "score": 82,
        }
    )

    assert plan["ok"] is True
    assert plan["action_type"] == "new_landing_page"
    assert plan["page_type"] == "new_service_location_landing_page"
    assert plan["proposed_slug"] == "ontstopping-antwerpen"
    assert plan["proposed_url_path"] == "/diensten/ontstopping-antwerpen"
    assert plan["seo_title"]
    assert plan["h1"]


def test_rookdetectie_uses_geuropsporing_context_not_fire_safety():
    plan = build_landing_page_implementation_plan(
        {
            "type": "new_landing_page",
            "service_intent": {"canonical_service": "rookdetectie_geuropsporing"},
            "region": "Antwerpen",
        }
    )

    assert plan["service_intent"]["canonical_service"] == "rookdetectie_geuropsporing"
    combined = " ".join(
        [
            plan["service_label"],
            plan["meta_description"],
            plan["proposed_slug"],
            " ".join(plan["content_outline"]),
        ]
    ).lower()
    assert "geuropsporing" in combined
    assert "rioolgeur" in combined
    assert "rookmelder" not in combined
    assert "brandveiligheid" not in combined
    assert "branddetectie" not in combined
    assert "brandalarm" not in combined


def test_approval_gates_and_read_only_guarantees_are_present():
    plan = build_landing_page_implementation_plan({"type": "metadata_update"})

    assert "approve_file_changes" in plan["approval_gates"]
    assert "approve_deploy" in plan["approval_gates"]
    assert "approve_ads_changes" in plan["approval_gates"]
    assert "does_not_write_files" in plan["read_only_guarantees"]
    assert "does_not_call_google_ads" in plan["read_only_guarantees"]
    assert "does_not_call_ga4" in plan["read_only_guarantees"]


def test_missing_optional_fields_do_not_crash_endpoint():
    app = FastAPI()
    app.include_router(router, prefix="/api/opportunities")
    client = TestClient(app)

    response = client.post("/api/opportunities/landing-pages/implementation-plan", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action_type"] == "planning_review"
    assert data["proposed_slug"] == "turbo-services"


def test_slug_is_stable_lowercase_kebab_case():
    assert stable_kebab_case("Rookdetectie Geuropsporing Antwerpen!") == "rookdetectie-geuropsporing-antwerpen"
    first = build_landing_page_implementation_plan(
        {"type": "new_landing_page", "canonical_service": "Riool Ontstopping", "region": "Antwerpen"}
    )
    second = build_landing_page_implementation_plan(
        {"type": "new_landing_page", "canonical_service": "Riool Ontstopping", "region": "Antwerpen"}
    )

    assert first["proposed_slug"] == "riool-ontstopping-antwerpen"
    assert first["proposed_slug"] == second["proposed_slug"]
