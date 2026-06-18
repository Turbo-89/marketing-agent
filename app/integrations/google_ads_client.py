import json
import os
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient


class GoogleAdsClientWrapper:
    def __init__(self):
        token_path = Path("generated") / "tokens" / "ads.json"
        if not token_path.exists():
            raise FileNotFoundError(f"Ads token niet gevonden: {token_path}")

        with token_path.open("r", encoding="utf-8") as fh:
            tok = json.load(fh)

        config = {
            "developer_token": os.getenv("GOOGLE_ADS_DEV_TOKEN"),
            "client_id": tok["client_id"],
            "client_secret": tok["client_secret"],
            "refresh_token": tok["refresh_token"],
            "use_proto_plus": True,
        }

        login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        if login_customer_id:
            config["login_customer_id"] = login_customer_id.replace("-", "").strip()

        self.client = GoogleAdsClient.load_from_dict(config)
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "").strip()

    def get_keyword_metrics(self, limit: int = 100):
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
        SELECT
          campaign.name,
          ad_group.name,
          ad_group_criterion.keyword.text,
          ad_group_criterion.keyword.match_type,
          metrics.clicks,
          metrics.impressions,
          metrics.average_cpc
        FROM keyword_view
        WHERE ad_group_criterion.type = KEYWORD
          AND metrics.impressions > 0
        ORDER BY metrics.clicks DESC, metrics.impressions DESC
        LIMIT {int(limit)}
        """

        response = ga_service.search(
            customer_id=self.customer_id,
            query=query,
        )

        result = []
        for row in response:
            result.append(
                {
                    "campaign": str(row.campaign.name or "").strip(),
                    "ad_group": str(row.ad_group.name or "").strip(),
                    "keyword": str(row.ad_group_criterion.keyword.text or "").strip(),
                    "match_type": str(row.ad_group_criterion.keyword.match_type.name or "").lower(),
                    "clicks": int(row.metrics.clicks or 0),
                    "impressions": int(row.metrics.impressions or 0),
                    "avg_cpc": float(row.metrics.average_cpc or 0) / 1_000_000,
                }
            )

        return result

    def get_search_term_signals(self, limit: int = 100):
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
        SELECT
          campaign.name,
          ad_group.name,
          search_term_view.search_term,
          metrics.clicks,
          metrics.impressions,
          metrics.cost_micros,
          metrics.conversions
        FROM search_term_view
        WHERE metrics.impressions > 0
        ORDER BY metrics.clicks DESC, metrics.impressions DESC
        LIMIT {int(limit)}
        """

        response = ga_service.search(
            customer_id=self.customer_id,
            query=query,
        )

        result = []
        for row in response:
            result.append(
                {
                    "search_term": str(row.search_term_view.search_term or "").strip(),
                    "campaign": str(row.campaign.name or "").strip(),
                    "ad_group": str(row.ad_group.name or "").strip(),
                    "clicks": int(row.metrics.clicks or 0),
                    "impressions": int(row.metrics.impressions or 0),
                    "cost": float(row.metrics.cost_micros or 0) / 1_000_000,
                    "conversions": float(row.metrics.conversions or 0),
                }
            )

        return result
