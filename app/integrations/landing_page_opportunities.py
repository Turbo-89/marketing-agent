import importlib.util
import os
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

from app.integrations.landing_page_implementation_plan import (
    build_landing_page_implementation_plan,
)
from app.integrations.landing_page_implementation_draft import (
    build_landing_page_implementation_draft,
)
from app.integrations.service_intent import resolve_service_intent

router = APIRouter()

FORBIDDEN_ACTIONS_NOW = [
    "write_files",
    "deploy",
    "publish",
    "change_ads",
    "merge",
    "push_to_live",
    "execute_shell_commands",
]
OPPORTUNITY_TYPES = [
    "new_landing_page",
    "improve_existing_landing_page",
    "metadata_update",
    "schema_update",
    "internal_linking",
    "ads_keyword_review",
    "negative_keyword_review",
]
NEGATIVE_SERVICE_TERMS = (
    "rookmelder",
    "rookmelders",
    "brandveiligheid",
    "branddetectie",
    "brandalarm",
)
REGION_TERMS = (
    "antwerpen",
    "mechelen",
    "boom",
    "bornem",
    "kontich",
    "mortsel",
    "wilrijk",
    "deurne",
    "berchem",
)


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clamp_max_opportunities(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        return 10
    return min(value, 50)


def _safe_bool(value: Any, default: bool = True) -> bool:
    return value if isinstance(value, bool) else default


def _safe_number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _date_range(payload_date_range: dict) -> tuple[str, str]:
    start_date = _clean_string(payload_date_range.get("start_date")) or "30daysAgo"
    end_date = _clean_string(payload_date_range.get("end_date")) or "today"
    return start_date, end_date


def _service_account_path() -> Path:
    return Path(
        os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_PATH",
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", str(Path("config") / "service_account.json")),
        )
    )


def provider_status() -> dict:
    google_ads_available = importlib.util.find_spec("app.integrations.google_ads_client") is not None
    ga4_available = importlib.util.find_spec("app.integrations.ga4_client") is not None

    ads_token_path = Path("generated") / "tokens" / "ads.json"
    google_ads_notes = []
    if (
        not ads_token_path.exists()
        or not os.getenv("GOOGLE_ADS_DEV_TOKEN")
        or not os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    ):
        google_ads_notes.append("configuration_incomplete")
    google_ads_notes.append("read_skipped_no_internet_calls_allowed")

    service_account_path = _service_account_path()
    ga4_notes = []
    if not service_account_path.exists() or not os.getenv("GA4_PROPERTY_ID"):
        ga4_notes.append("configuration_incomplete")
    ga4_notes.append("read_skipped_no_internet_calls_allowed")

    return {
        "ok": True,
        "providers": {
            "google_ads": {
                "available": google_ads_available,
                "configured": google_ads_available
                and ads_token_path.exists()
                and bool(os.getenv("GOOGLE_ADS_DEV_TOKEN"))
                and bool(os.getenv("GOOGLE_ADS_CUSTOMER_ID")),
                "reads_enabled": _env_enabled("ENABLE_GOOGLE_ADS_READS"),
                "notes": google_ads_notes,
            },
            "ga4": {
                "available": ga4_available,
                "configured": ga4_available
                and service_account_path.exists()
                and bool(os.getenv("GA4_PROPERTY_ID")),
                "reads_enabled": _env_enabled("ENABLE_GA4_READS"),
                "notes": ga4_notes,
            },
        },
    }


def _inputs(payload: dict) -> dict:
    return {
        "service": _clean_string(payload.get("service")),
        "region": _clean_string(payload.get("region")),
        "date_range": payload.get("date_range") if isinstance(payload.get("date_range"), dict) else {},
        "max_opportunities": _clamp_max_opportunities(payload.get("max_opportunities")),
        "read_live": _safe_bool(payload.get("read_live"), False),
    }


def _notes(status: dict, service_intent: dict | None, read_live: bool) -> list[str]:
    notes = [
        "dry_run_only",
    ]
    if not read_live:
        notes.append("external_provider_reads_skipped")
    for provider_name, provider in status["providers"].items():
        if not provider["configured"]:
            notes.append(f"{provider_name}_not_configured")
        elif read_live and not provider.get("reads_enabled"):
            notes.append(f"{provider_name}_reads_disabled")
    if service_intent:
        notes.append("service_intent_resolved")
    return list(dict.fromkeys(notes))


def _safe_error(exc: Exception) -> str:
    return exc.__class__.__name__


def _provider_read_status(name: str, state: str, signals: list[dict] | None = None, notes: list[str] | None = None) -> dict:
    return {
        "provider": name,
        "status": state,
        "signals": signals or [],
        "notes": notes or [],
    }


def _read_google_ads_signals(inputs: dict, status: dict) -> dict:
    provider = status["providers"]["google_ads"]
    if not inputs["read_live"]:
        return _provider_read_status("google_ads", "skipped", notes=["read_live_false"])
    if not provider.get("reads_enabled"):
        return _provider_read_status("google_ads", "disabled", notes=["ENABLE_GOOGLE_ADS_READS_false"])
    if not provider["configured"]:
        return _provider_read_status("google_ads", "not_configured", notes=provider["notes"])

    try:
        from app.integrations.google_ads_client import GoogleAdsClientWrapper

        client = GoogleAdsClientWrapper()
        rows = client.get_search_term_signals(limit=inputs["max_opportunities"])
    except Exception as exc:
        return _provider_read_status("google_ads", "unavailable", notes=[f"provider_error:{_safe_error(exc)}"])

    signals = []
    for row in rows:
        signals.append(
            {
                "provider": "google_ads",
                "type": "search_term",
                "search_term": _clean_string(row.get("search_term")),
                "campaign": _clean_string(row.get("campaign")),
                "ad_group": _clean_string(row.get("ad_group")),
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "cost": row.get("cost"),
                "conversions": row.get("conversions"),
            }
        )
    return _provider_read_status("google_ads", "available", signals=signals)


def _read_ga4_signals(inputs: dict, status: dict) -> dict:
    provider = status["providers"]["ga4"]
    if not inputs["read_live"]:
        return _provider_read_status("ga4", "skipped", notes=["read_live_false"])
    if not provider.get("reads_enabled"):
        return _provider_read_status("ga4", "disabled", notes=["ENABLE_GA4_READS_false"])
    if not provider["configured"]:
        return _provider_read_status("ga4", "not_configured", notes=provider["notes"])

    start_date, end_date = _date_range(inputs["date_range"])
    try:
        from app.integrations.ga4_client import GA4Client

        client = GA4Client()
        rows = client.get_landing_page_signals(
            limit=inputs["max_opportunities"],
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as exc:
        return _provider_read_status("ga4", "unavailable", notes=[f"provider_error:{_safe_error(exc)}"])

    signals = []
    for row in rows:
        signals.append(
            {
                "provider": "ga4",
                "type": "landing_page",
                "landing_page_path": _clean_string(row.get("landing_page_path")),
                "sessions": row.get("sessions"),
                "users": row.get("users"),
                "engagement_rate": row.get("engagement_rate"),
                "conversions": row.get("conversions"),
                "source_medium": _clean_string(row.get("source_medium")),
            }
        )
    return _provider_read_status("ga4", "available", signals=signals)


def _signal_text(signal: dict) -> str:
    return " ".join(
        _clean_string(signal.get(key)).lower()
        for key in ("search_term", "campaign", "ad_group", "landing_page_path", "source_medium")
    )


def _normalise_sample_signal(signal: dict) -> dict:
    source = _clean_string(signal.get("source")) or _clean_string(signal.get("provider")) or "sample"
    provider = "sample" if source == "sample" else source
    normalised = {
        "provider": provider,
        "source": source,
        "sample": True,
        "type": _clean_string(signal.get("type")) or "sample",
        "search_term": _clean_string(signal.get("search_term") or signal.get("query")),
        "campaign": _clean_string(signal.get("campaign")),
        "ad_group": _clean_string(signal.get("ad_group")),
        "landing_page_path": _clean_string(signal.get("landing_page_path") or signal.get("page_path")),
        "source_medium": _clean_string(signal.get("source_medium")),
        "clicks": _safe_number(signal.get("clicks")),
        "impressions": _safe_number(signal.get("impressions")),
        "cost": _safe_number(signal.get("cost")),
        "conversions": _safe_number(signal.get("conversions")),
        "sessions": _safe_number(signal.get("sessions")),
        "users": _safe_number(signal.get("users")),
        "engagement_rate": _safe_number(signal.get("engagement_rate")),
    }
    if normalised["search_term"]:
        normalised["type"] = "search_term"
    elif normalised["landing_page_path"]:
        normalised["type"] = "landing_page"
    return normalised


def _sample_signals(payload: dict, dry_run: bool) -> list[dict]:
    if not dry_run:
        return []
    value = payload.get("sample_signals")
    if not isinstance(value, list):
        return []
    return [_normalise_sample_signal(item) for item in value if isinstance(item, dict)]


def _signal_service_intent(signal: dict, fallback_service: str) -> dict | None:
    return resolve_service_intent(" ".join([_signal_text(signal), fallback_service]))


def _detect_region(signal: dict, fallback_region: str) -> str:
    if fallback_region:
        return fallback_region
    text = _signal_text(signal)
    for region in REGION_TERMS:
        if region in text:
            return region.title()
    path = _clean_string(signal.get("landing_page_path")).lower()
    parts = [part for part in re.split(r"[-/_\s]+", path) if part]
    for part in parts:
        if part in REGION_TERMS:
            return part.title()
    return ""


def _is_generic_page(signal: dict, service_intent: dict | None, region: str) -> bool:
    path = _clean_string(signal.get("landing_page_path")).lower()
    if not path:
        return False
    has_service = False
    if service_intent:
        has_service = any(term in path for term in service_intent.get("positive_terms", []))
    has_region = bool(region and region.lower() in path)
    return not has_service or not has_region


def _group_key(signal: dict, inputs: dict) -> tuple:
    service_intent = _signal_service_intent(signal, inputs["service"])
    canonical_service = service_intent.get("canonical_service") if service_intent else _clean_string(inputs["service"]) or "unknown_service"
    region = _detect_region(signal, inputs["region"])
    text = _signal_text(signal)
    if any(term in text for term in NEGATIVE_SERVICE_TERMS):
        return (canonical_service, region, "negative_keyword_review")
    if signal.get("type") == "landing_page":
        if _is_generic_page(signal, service_intent, region):
            return (canonical_service, region, "metadata_update")
        return (canonical_service, region, "improve_existing_landing_page")
    return (canonical_service, region, "new_landing_page" if service_intent else "ads_keyword_review")


def _group_signals(signals: list[dict], inputs: dict) -> dict:
    groups = {}
    for signal in signals:
        key = _group_key(signal, inputs)
        group = groups.setdefault(key, {"signals": [], "service_intent": _signal_service_intent(signal, inputs["service"])})
        group["signals"].append(signal)
        if group["service_intent"] is None:
            group["service_intent"] = _signal_service_intent(signal, inputs["service"])
    return groups


def _score_group(signals: list[dict], opportunity_type: str) -> dict:
    impressions = sum(_safe_number(signal.get("impressions")) for signal in signals)
    clicks = sum(_safe_number(signal.get("clicks")) for signal in signals)
    cost = sum(_safe_number(signal.get("cost")) for signal in signals)
    conversions = sum(_safe_number(signal.get("conversions")) for signal in signals)
    sessions = sum(_safe_number(signal.get("sessions")) for signal in signals)
    users = sum(_safe_number(signal.get("users")) for signal in signals)
    engagement_values = [_safe_number(signal.get("engagement_rate")) for signal in signals if signal.get("engagement_rate") is not None]
    avg_engagement = sum(engagement_values) / len(engagement_values) if engagement_values else 0

    demand = _clamp_score((impressions / 20) + (clicks * 8) + (sessions / 5) + (users / 5))
    conversion_or_value = _clamp_score((conversions * 25) + min(cost * 2, 30) + (avg_engagement * 40))
    content_gap = 80 if opportunity_type == "new_landing_page" else 65 if opportunity_type in {"metadata_update", "internal_linking"} else 35
    local_relevance = 80 if any(_detect_region(signal, "") for signal in signals) else 45
    confidence = _clamp_score(35 + (len(signals) * 15) + (20 if any(signal.get("sample") for signal in signals) else 35))
    score = _clamp_score(
        demand * 0.35
        + conversion_or_value * 0.2
        + content_gap * 0.2
        + local_relevance * 0.15
        + confidence * 0.1
    )
    return {
        "score": score,
        "priority": "high" if score >= 70 else "medium" if score >= 40 else "low",
        "score_breakdown": {
            "demand": demand,
            "conversion_or_value": conversion_or_value,
            "content_gap": content_gap,
            "local_relevance": local_relevance,
            "confidence": confidence,
        },
    }


def _opportunity_reason(opportunity_type: str) -> str:
    reasons = {
        "new_landing_page": "High demand signal without matching landing-page evidence suggests a possible new landing page.",
        "improve_existing_landing_page": "Existing landing-page signal suggests a possible page improvement review.",
        "metadata_update": "Service or location terms appear on a generic page, suggesting metadata review.",
        "schema_update": "Service/location evidence may require structured data review.",
        "internal_linking": "Service/location evidence may need internal linking review.",
        "ads_keyword_review": "Search term evidence suggests keyword review.",
        "negative_keyword_review": "Fire-safety wording should be reviewed as negative context, not service positioning.",
    }
    return reasons.get(opportunity_type, "Signal group suggests a review opportunity.")


def _build_opportunities(signals: list[dict], inputs: dict) -> list[dict]:
    opportunities = []
    groups = _group_signals(signals, inputs)
    for (canonical_service, region, opportunity_type), group in groups.items():
        scored = _score_group(group["signals"], opportunity_type)
        opportunity = {
            "type": opportunity_type,
            "canonical_service": canonical_service,
            "region": region,
            "sources": sorted({signal.get("provider", "unknown") for signal in group["signals"]}),
            "reason": _opportunity_reason(opportunity_type),
            "evidence_count": len(group["signals"]),
            "approval_required": True,
            **scored,
        }
        if group["service_intent"]:
            opportunity["service_intent"] = group["service_intent"]
        opportunities.append(opportunity)
    opportunities.sort(key=lambda item: item["score"], reverse=True)
    return opportunities


def build_landing_page_opportunities(payload: dict) -> dict:
    inputs = _inputs(payload)
    dry_run = _safe_bool(payload.get("dry_run"), True)
    service_intent = resolve_service_intent(
        " ".join(part for part in (inputs["service"], inputs["region"]) if part)
    )
    status = provider_status()
    google_ads_result = _read_google_ads_signals(inputs, status)
    ga4_result = _read_ga4_signals(inputs, status)
    sample_signals = _sample_signals(payload, dry_run)
    signals = google_ads_result["signals"] + ga4_result["signals"] + sample_signals
    opportunities = _build_opportunities(signals, inputs)[: inputs["max_opportunities"]]

    response = {
        "ok": True,
        "dry_run": dry_run,
        "read_live": inputs["read_live"],
        "provider_status": status,
        "inputs": inputs,
        "provider_results": {
            "google_ads": google_ads_result,
            "ga4": ga4_result,
        },
        "signals": signals,
        "opportunities": opportunities,
        "opportunity_types": OPPORTUNITY_TYPES,
        "approval_required": True,
        "forbidden_actions_now": FORBIDDEN_ACTIONS_NOW,
        "notes": _notes(status, service_intent, inputs["read_live"]),
    }
    if service_intent:
        response["service_intent"] = service_intent
    return response


@router.get("/status")
def opportunities_status():
    return provider_status()


@router.post("/landing-pages")
async def landing_pages(request: Request):
    payload = await request.json()
    return build_landing_page_opportunities(payload)


@router.post("/landing-pages/implementation-plan")
async def landing_page_implementation_plan(request: Request):
    payload = await request.json()
    return build_landing_page_implementation_plan(payload)


@router.post("/landing-pages/implementation-draft")
async def landing_page_implementation_draft(request: Request):
    payload = await request.json()
    return build_landing_page_implementation_draft(payload)
