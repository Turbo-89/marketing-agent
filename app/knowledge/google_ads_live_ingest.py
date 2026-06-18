from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from google.ads.googleads.client import GoogleAdsClient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


ADS_SCOPE = "https://www.googleapis.com/auth/adwords"


def _token_path() -> Path:
    return Path("generated") / "tokens" / "ads.json"


def _developer_token() -> str:
    value = os.getenv("GOOGLE_ADS_DEV_TOKEN")
    if not value:
        raise RuntimeError("GOOGLE_ADS_DEV_TOKEN ontbreekt.")
    return value.replace(" ", "").strip()


def _customer_id() -> str:
    value = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    if not value:
        raise RuntimeError("GOOGLE_ADS_CUSTOMER_ID ontbreekt.")
    return value.replace("-", "").strip()


def _login_customer_id() -> str | None:
    value = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if not value:
        return None
    return value.replace("-", "").strip()


def _load_authorized_user_credentials() -> Credentials:
    path = _token_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Ads token niet gevonden: {path}. Voer eerst OAuth uit via /api/auth/google/ads/start"
        )

    creds = Credentials.from_authorized_user_file(str(path), scopes=[ADS_SCOPE])

    if not creds.refresh_token:
        raise RuntimeError("Ads token bevat geen refresh_token.")

    if not creds.valid:
        creds.refresh(Request())

    if not creds.token:
        raise RuntimeError("Ads token kon niet vernieuwd worden naar een access token.")

    if not creds.client_id:
        raise RuntimeError("Ads credentials bevatten geen client_id.")
    if not creds.client_secret:
        raise RuntimeError("Ads credentials bevatten geen client_secret.")
    if not creds.token_uri:
        raise RuntimeError("Ads credentials bevatten geen token_uri.")

    return creds


def _build_client() -> GoogleAdsClient:
    creds = _load_authorized_user_credentials()

    config = {
        "developer_token": _developer_token(),
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "use_proto_plus": True,
    }

    login_customer_id = _login_customer_id()
    if login_customer_id:
        config["login_customer_id"] = login_customer_id

    return GoogleAdsClient.load_from_dict(config)


def _micros_to_currency(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value) / 1_000_000
    except Exception:
        return 0.0


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except Exception:
        return 0


class GoogleAdsLiveIngest:
    """
    Haalt keyword-prestatie live uit Google Ads op en zet die om naar exact
    hetzelfde row-formaat als GoogleAdsCsvIngest.load().
    """

    def __init__(self) -> None:
        self.client = _build_client()
        self.customer_id = _customer_id()

    def load(
        self,
        limit: int = 500,
        min_clicks: int = 0,
        include_paused: bool = False,
    ) -> list[dict[str, Any]]:
        ga_service = self.client.get_service("GoogleAdsService")

        status_filter = ""
        if not include_paused:
            status_filter = """
              AND ad_group_criterion.status = ENABLED
              AND campaign.status = ENABLED
              AND ad_group.status = ENABLED
            """

        query = f"""
        SELECT
          campaign.name,
          campaign.status,
          ad_group.name,
          ad_group.status,
          ad_group_criterion.status,
          ad_group_criterion.keyword.text,
          ad_group_criterion.keyword.match_type,
          ad_group_criterion.final_urls,
          metrics.impressions,
          metrics.clicks,
          metrics.interactions,
          metrics.conversions,
          metrics.conversions_from_interactions_rate,
          metrics.average_cpc,
          metrics.cost_micros,
          metrics.cost_per_conversion,
          customer.currency_code
        FROM keyword_view
        WHERE ad_group_criterion.type = KEYWORD
          AND metrics.impressions > 0
          {status_filter}
        ORDER BY metrics.clicks DESC, metrics.impressions DESC
        LIMIT {int(limit)}
        """

        response = ga_service.search(
            customer_id=self.customer_id,
            query=query,
        )

        results: list[dict[str, Any]] = []

        for row in response:
            keyword_text = str(row.ad_group_criterion.keyword.text or "").strip()
            if not keyword_text:
                continue

            clicks = _safe_int(row.metrics.clicks)
            if clicks < min_clicks:
                continue

            match_type = str(row.ad_group_criterion.keyword.match_type.name or "").lower()

            final_url = ""
            try:
                if row.ad_group_criterion.final_urls:
                    final_url = str(row.ad_group_criterion.final_urls[0] or "").strip()
            except Exception:
                final_url = ""

            results.append(
                {
                    "keyword": keyword_text,
                    "keyword_status": str(row.ad_group_criterion.status.name or "").strip(),
                    "match_type": match_type,
                    "campaign": str(row.campaign.name or "").strip(),
                    "ad_group": str(row.ad_group.name or "").strip(),
                    "status": str(row.ad_group_criterion.status.name or "").strip(),
                    "final_url": final_url,
                    "interactions": _safe_int(row.metrics.interactions),
                    "clicks": clicks,
                    "impressions": _safe_int(row.metrics.impressions),
                    "conversions": _safe_float(row.metrics.conversions),
                    "conversion_rate": _safe_float(
                        row.metrics.conversions_from_interactions_rate
                    ),
                    "avg_cpc": _micros_to_currency(row.metrics.average_cpc),
                    "avg_cost": _micros_to_currency(row.metrics.average_cpc),
                    "cost": _micros_to_currency(row.metrics.cost_micros),
                    "cost_per_conversion": _micros_to_currency(
                        row.metrics.cost_per_conversion
                    ),
                    "currency": str(row.customer.currency_code or "").strip(),
                }
            )

        return results