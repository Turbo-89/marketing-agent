import re
from typing import Any

from app.integrations.service_intent import resolve_service_intent

APPROVAL_GATES = [
    "approve_implementation_plan",
    "approve_file_changes",
    "approve_deploy",
    "approve_ads_changes",
    "approve_ga4_changes",
    "approve_merge",
    "approve_push_to_live",
]
READ_ONLY_GUARANTEES = [
    "does_not_write_files",
    "does_not_modify_repositories",
    "does_not_deploy",
    "does_not_call_google_ads",
    "does_not_call_ga4",
    "does_not_change_ads_or_analytics",
    "does_not_call_github",
    "does_not_touch_production",
]

def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def stable_kebab_case(value: str) -> str:
    normalized = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def _opportunity_text(opportunity: dict) -> str:
    parts = [
        _clean_string(opportunity.get("type")),
        _clean_string(opportunity.get("action_type")),
        _clean_string(opportunity.get("canonical_service")),
        _clean_string(opportunity.get("service_label")),
        _clean_string(opportunity.get("region")),
        _clean_string(opportunity.get("reason")),
    ]
    service_intent = opportunity.get("service_intent")
    if isinstance(service_intent, dict):
        parts.extend(
            [
                _clean_string(service_intent.get("canonical_service")),
                _clean_string(service_intent.get("display_name")),
                _clean_string(service_intent.get("business_meaning")),
            ]
        )
    return " ".join(part for part in parts if part)


def _service_intent(opportunity: dict) -> dict | None:
    existing = opportunity.get("service_intent")
    if isinstance(existing, dict) and existing.get("canonical_service"):
        if existing.get("canonical_service") == "rookdetectie_geuropsporing":
            return resolve_service_intent("rookdetectie") or existing
        return existing
    return resolve_service_intent(_opportunity_text(opportunity))


def _service_label(opportunity: dict, service_intent: dict | None) -> str:
    if service_intent:
        return _clean_string(service_intent.get("display_name"))
    return (
        _clean_string(opportunity.get("service_label"))
        or _clean_string(opportunity.get("canonical_service")).replace("_", " ").title()
        or "Turbo Services"
    )


def _page_type(action_type: str) -> str:
    if action_type == "new_landing_page":
        return "new_service_location_landing_page"
    if action_type in {"metadata_update", "schema_update", "internal_linking"}:
        return "existing_page_optimization"
    if action_type == "improve_existing_landing_page":
        return "existing_landing_page_improvement"
    return "planning_review"


def _base_slug_terms(service_label: str, service_intent: dict | None, region: str) -> list[str]:
    if service_intent and service_intent.get("canonical_service") == "rookdetectie_geuropsporing":
        terms = ["rookdetectie", "geuropsporing"]
    else:
        terms = [service_label]
    if region:
        terms.append(region)
    return terms


def _seo_terms(service_label: str, service_intent: dict | None) -> str:
    if service_intent and service_intent.get("canonical_service") == "rookdetectie_geuropsporing":
        return "rooktest en geuropsporing bij rioolgeur"
    return service_label.lower()


def _rookdetectie_guard(service_intent: dict | None) -> list[str]:
    if not service_intent or service_intent.get("canonical_service") != "rookdetectie_geuropsporing":
        return []
    return [
        "Use rookdetectie only as rooktest/geuropsporing for rioolgeur, riolering, riool and afvoer.",
        "Do not position the page around rookmelders, brandveiligheid, branddetectie or brandalarm.",
    ]


def build_landing_page_implementation_plan(opportunity: dict) -> dict:
    if not isinstance(opportunity, dict):
        opportunity = {}

    action_type = _clean_string(opportunity.get("type")) or _clean_string(opportunity.get("action_type")) or "planning_review"
    region = _clean_string(opportunity.get("region"))
    service_intent = _service_intent(opportunity)
    service_label = _service_label(opportunity, service_intent)
    page_type = _page_type(action_type)
    slug = stable_kebab_case("-".join(_base_slug_terms(service_label, service_intent, region))) or "turbo-services"
    url_path = f"/diensten/{slug}"
    seo_subject = _seo_terms(service_label, service_intent)
    region_suffix = f" in {region}" if region else ""
    opportunity_id = stable_kebab_case(
        "-".join(part for part in [action_type, service_intent.get("canonical_service") if service_intent else service_label, region] if part)
    )

    plan = {
        "ok": True,
        "opportunity_id": opportunity_id,
        "action_type": action_type,
        "page_type": page_type,
        "service_intent": service_intent,
        "service_label": service_label,
        "region": region,
        "proposed_slug": slug,
        "proposed_url_path": url_path,
        "seo_title": f"{service_label}{region_suffix} | Turbo Services",
        "meta_description": (
            f"Plan een gerichte Turbo Services pagina voor {seo_subject}{region_suffix}. "
            "Focus op duidelijke hulpvraag, lokale relevantie en conversie."
        ),
        "h1": f"{service_label}{region_suffix}",
        "h2_outline": [
            "Wanneer is deze service nodig?",
            "Hoe Turbo Services dit aanpakt",
            "Lokale beschikbaarheid en snelle opvolging",
            "Veelgestelde vragen",
        ],
        "content_outline": [
            "Start met de concrete klantvraag en het lokale probleem.",
            "Leg de service uit in gewone taal en benoem relevante signalen uit de opportunity.",
            "Beschrijf aanpak, bewijsvoering, planning en contactmomenten.",
            "Voeg conversiegerichte call-to-actions toe zonder claims te overdrijven.",
        ],
        "schema_plan": [
            "Review LocalBusiness schema.",
            "Review Service schema for the proposed service.",
            "Add FAQPage schema only after content approval.",
        ],
        "internal_links": [
            {"label": "Diensten overzicht", "path": "/diensten", "status": "proposed"},
            {"label": service_label, "path": url_path, "status": "proposed"},
        ],
        "likely_turboservices_files": [
            {
                "path": "config/services.json",
                "reason": "Likely service metadata source; proposed only, not read by this endpoint.",
            },
            {
                "path": "app",
                "reason": "Likely Next.js route/page area; proposed only, not read by this endpoint.",
            },
            {
                "path": "content",
                "reason": "Likely content model area if present; proposed only, not read by this endpoint.",
            },
        ],
        "validation_commands": [
            {"command": "npm run build", "purpose": "Validate the Turbo Services frontend after approved changes."},
            {"command": "npm run lint", "purpose": "Validate code style if the project provides linting."},
        ],
        "risks": [
            {
                "risk": "The proposed file paths are inferred without reading the Turbo Services repo.",
                "mitigation": "Confirm actual project structure before any approved implementation.",
            },
            {
                "risk": "SEO copy could overstate claims if written without business review.",
                "mitigation": "Require approval before publishing content.",
            },
        ],
        "approval_gates": APPROVAL_GATES,
        "read_only_guarantees": READ_ONLY_GUARANTEES,
    }
    plan["risks"].extend(
        {"risk": item, "mitigation": "Keep the business meaning guard in the implementation brief."}
        for item in _rookdetectie_guard(service_intent)
    )
    return plan
