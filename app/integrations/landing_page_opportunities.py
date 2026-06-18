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


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clamp_max_opportunities(value: Any) -> int:
    if not isinstance(value, int) or value <= 0:
        return 10
    return min(value, 50)


def _safe_bool(value: Any, default: bool = True) -> bool:
    return value if isinstance(value, bool) else default


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
    if not ads_token_path.exists():
        google_ads_notes.append("ads_token_missing")
    if not os.getenv("GOOGLE_ADS_DEV_TOKEN"):
        google_ads_notes.append("developer_token_missing")
    if not os.getenv("GOOGLE_ADS_CUSTOMER_ID"):
        google_ads_notes.append("customer_id_missing")
    google_ads_notes.append("read_skipped_no_internet_calls_allowed")

    service_account_path = _service_account_path()
    ga4_notes = []
    if not service_account_path.exists():
        ga4_notes.append("service_account_missing")
    if not os.getenv("GA4_PROPERTY_ID"):
        ga4_notes.append("property_id_missing")
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
                "notes": google_ads_notes,
            },
            "ga4": {
                "available": ga4_available,
                "configured": ga4_available
                and service_account_path.exists()
                and bool(os.getenv("GA4_PROPERTY_ID")),
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
    }


def _notes(status: dict, service_intent: dict | None) -> list[str]:
    notes = [
        "dry_run_only",
        "external_provider_reads_skipped",
        "signals_empty_until_explicit_read_step_is_enabled",
    ]
    for provider_name, provider in status["providers"].items():
        if not provider["configured"]:
            notes.append(f"{provider_name}_not_configured")
    if service_intent:
        notes.append("service_intent_resolved")
    return list(dict.fromkeys(notes))


def build_landing_page_opportunities(payload: dict) -> dict:
    inputs = _inputs(payload)
    dry_run = _safe_bool(payload.get("dry_run"), True)
    service_intent = resolve_service_intent(
        " ".join(part for part in (inputs["service"], inputs["region"]) if part)
    )
    status = provider_status()

    response = {
        "ok": True,
        "dry_run": dry_run,
        "provider_status": status,
        "inputs": inputs,
        "signals": [],
        "opportunities": [],
        "opportunity_types": OPPORTUNITY_TYPES,
        "approval_required": True,
        "forbidden_actions_now": FORBIDDEN_ACTIONS_NOW,
        "notes": _notes(status, service_intent),
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
