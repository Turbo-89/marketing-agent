import importlib.util
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

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


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clamp_max_opportunities(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        return 10
    return min(value, 50)


def _safe_bool(value: Any, default: bool = True) -> bool:
    return value if isinstance(value, bool) else default


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


def _signal_service_intent(signal: dict, fallback_service: str) -> dict | None:
    return resolve_service_intent(" ".join([_signal_text(signal), fallback_service]))


def _opportunity_for_signal(signal: dict, inputs: dict) -> dict | None:
    text = _signal_text(signal)
    if any(term in text for term in NEGATIVE_SERVICE_TERMS):
        return {
            "type": "negative_keyword_review",
            "source": signal["provider"],
            "reason": "Signal appears related to fire-safety wording and should be reviewed as a negative context.",
            "approval_required": True,
        }

    service_intent = _signal_service_intent(signal, inputs["service"])
    if signal["provider"] == "google_ads":
        opportunity_type = "new_landing_page" if service_intent else "ads_keyword_review"
        reason = "Search term signal may indicate landing-page or keyword-review demand."
    else:
        opportunity_type = "improve_existing_landing_page"
        reason = "GA4 landing-page signal may indicate an existing page to review."

    opportunity = {
        "type": opportunity_type,
        "source": signal["provider"],
        "reason": reason,
        "region": inputs["region"],
        "approval_required": True,
    }
    if service_intent:
        opportunity["service_intent"] = service_intent
    return opportunity


def _build_opportunities(signals: list[dict], inputs: dict) -> list[dict]:
    opportunities = []
    seen = set()
    for signal in signals:
        opportunity = _opportunity_for_signal(signal, inputs)
        if not opportunity:
            continue
        key = (opportunity["type"], opportunity["source"], str(opportunity.get("service_intent")))
        if key in seen:
            continue
        seen.add(key)
        opportunities.append(opportunity)
        if len(opportunities) >= inputs["max_opportunities"]:
            break
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
    signals = google_ads_result["signals"] + ga4_result["signals"]
    opportunities = _build_opportunities(signals, inputs)

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
