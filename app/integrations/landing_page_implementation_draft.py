import re
from typing import Any

from app.integrations.landing_page_implementation_plan import (
    APPROVAL_GATES,
    READ_ONLY_GUARANTEES,
    stable_kebab_case,
)
from app.integrations.service_intent import resolve_service_intent

BLOCKED_ACTIONS = [
    "file_write",
    "deploy",
    "publish",
    "merge",
    "push",
    "google_ads_change",
    "ga4_change",
    "github_mutation",
]
ROOKDETECTIE_CANONICAL_SERVICE = "rookdetectie_geuropsporing"


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _source_plan(payload: dict) -> dict:
    for key in ("implementation_plan", "plan", "implementationPlan"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return payload if isinstance(payload, dict) else {}


def _selected_opportunity(payload: dict) -> dict:
    for key in ("selected_opportunity", "selectedOpportunity", "opportunity"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _opportunity_text(plan: dict, selected_opportunity: dict, handoff_brief: str) -> str:
    parts = [
        _clean_string(plan.get("service_label")),
        _clean_string(plan.get("region")),
        _clean_string(plan.get("proposed_slug")),
        _clean_string(selected_opportunity.get("type")),
        _clean_string(selected_opportunity.get("reason")),
        handoff_brief,
    ]
    service_intent = plan.get("service_intent") or selected_opportunity.get("service_intent")
    if isinstance(service_intent, dict):
        parts.extend(
            [
                _clean_string(service_intent.get("canonical_service")),
                _clean_string(service_intent.get("display_name")),
                _clean_string(service_intent.get("business_meaning")),
            ]
        )
    return " ".join(part for part in parts if part)


def _service_intent(plan: dict, selected_opportunity: dict, handoff_brief: str) -> dict | None:
    existing = plan.get("service_intent") or selected_opportunity.get("service_intent")
    if isinstance(existing, dict) and existing.get("canonical_service"):
        if existing.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
            return resolve_service_intent("rookdetectie") or existing
        return existing
    return resolve_service_intent(_opportunity_text(plan, selected_opportunity, handoff_brief))


def _service_label(plan: dict, service_intent: dict | None) -> str:
    if service_intent:
        return _clean_string(service_intent.get("display_name"))
    return _clean_string(plan.get("service_label")) or "Turbo Services"


def _slug(plan: dict, service_label: str, region: str, service_intent: dict | None) -> str:
    explicit = _clean_string(plan.get("proposed_slug"))
    if explicit:
        return stable_kebab_case(explicit)
    if service_intent and service_intent.get("canonical_service") == ROOKDETECTIE_CANONICAL_SERVICE:
        base = "rookdetectie-geuropsporing"
    else:
        base = service_label
    return stable_kebab_case("-".join(part for part in (base, region) if part)) or "turbo-services"


def _draft_id(source_plan_id: str, slug: str) -> str:
    return stable_kebab_case("-".join(part for part in ("draft", source_plan_id, slug) if part)) or "draft-turbo-services"


def _route_path(plan: dict, slug: str) -> str:
    return _clean_string(plan.get("proposed_url_path")) or f"/diensten/{slug}"


def _safe_component_name(slug: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[-_\s]+", slug) if part) or "LandingPage"


def _approval_summary(payload: dict) -> dict:
    return {
        "approval_timestamp": _clean_string(payload.get("approval_timestamp") or payload.get("approvalTimestamp")),
        "checklist_status": _as_dict(payload.get("checklist_status") or payload.get("checklistStatus")),
        "handoff_brief_present": bool(_clean_string(payload.get("handoff_brief") or payload.get("handoffBrief"))),
        "authorization_scope": "prepare_implementation_draft_only",
        "execution_authorized": False,
    }


def _rookdetectie_guard(service_intent: dict | None) -> list[str]:
    if not service_intent or service_intent.get("canonical_service") != ROOKDETECTIE_CANONICAL_SERVICE:
        return []
    return [
        "Rookdetectie must be written as rooktest/geuropsporing for rioolgeur, riolering, riool and afvoer.",
        "Do not write positive page content about rookmelders, brandveiligheid, branddetectie or brandalarm.",
    ]


def build_landing_page_implementation_draft(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    plan = _source_plan(payload)
    selected_opportunity = _selected_opportunity(payload)
    handoff_brief = _clean_string(payload.get("handoff_brief") or payload.get("handoffBrief"))
    source_plan_id = _clean_string(plan.get("opportunity_id")) or "unknown-plan"
    region = _clean_string(plan.get("region")) or _clean_string(selected_opportunity.get("region"))
    service_intent = _service_intent(plan, selected_opportunity, handoff_brief)
    service_label = _service_label(plan, service_intent)
    slug = _slug(plan, service_label, region, service_intent)
    route_path = _route_path(plan, slug)
    component_name = _safe_component_name(slug)
    h1 = _clean_string(plan.get("h1")) or service_label
    seo_title = _clean_string(plan.get("seo_title")) or f"{service_label} | Turbo Services"
    meta_description = _clean_string(plan.get("meta_description")) or f"Proposed SEO description for {service_label}."

    proposed_content_blocks = [
        {"block": "hero", "draft": f"H1: {h1}. Explain the local problem and invite the visitor to contact Turbo Services."},
        {"block": "service_explanation", "draft": "Describe the service, when it is needed, and how Turbo Services approaches the request."},
        {"block": "local_relevance", "draft": f"Connect the service to {region or 'the selected region'} without making unsupported availability claims."},
        {"block": "conversion", "draft": "Add clear call-to-action copy for contact or request intake after business approval."},
    ]
    for guard in _rookdetectie_guard(service_intent):
        proposed_content_blocks.append({"block": "business_guard", "draft": guard})

    return {
        "ok": True,
        "draft_id": _draft_id(source_plan_id, slug),
        "source_plan_id": source_plan_id,
        "approval_summary": _approval_summary(payload),
        "proposed_files": [
            {
                "path": f"app{route_path}/page.tsx",
                "status": "proposed_only",
                "draft_patch": f"Create a proposed {component_name} page component for {route_path}.",
            },
            {
                "path": "config/services.json",
                "status": "proposed_only",
                "draft_patch": f"Review whether {slug} needs service metadata. Do not change without approval.",
            },
        ],
        "proposed_route_structure": {
            "route_path": route_path,
            "slug": slug,
            "page_type": _clean_string(plan.get("page_type")) or "planning_review",
            "status": "proposed_only",
        },
        "proposed_content_blocks": proposed_content_blocks,
        "proposed_seo_metadata": {
            "title": seo_title,
            "meta_description": meta_description,
            "canonical_path": route_path,
            "status": "proposed_only",
        },
        "proposed_schema_jsonld": {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": service_label,
            "areaServed": region or "Proposed service area",
            "provider": {"@type": "LocalBusiness", "name": "Turbo Services"},
            "status": "proposed_only",
        },
        "proposed_internal_links": _as_list(plan.get("internal_links")),
        "proposed_validation_plan": _as_list(plan.get("validation_commands"))
        or [
            {"command": "npm run build", "purpose": "Validate after separately approved implementation."},
        ],
        "risks": _as_list(plan.get("risks"))
        + [
            {
                "risk": "This draft was generated without reading the Turbo Services repo.",
                "mitigation": "Treat file paths and patches as proposed only until a separately approved implementation step.",
            }
        ],
        "blocked_actions": BLOCKED_ACTIONS,
        "approval_gates": APPROVAL_GATES,
        "read_only_guarantees": READ_ONLY_GUARANTEES,
        "service_intent": service_intent,
    }
