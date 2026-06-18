# app/tools/ads_tool.py

import os, json
from google.ads.googleads.client import GoogleAdsClient


class GoogleAdsTool:

    name = "google_ads"

    def __init__(self):
        self.client = None

    def _ensure_client(self):
        if self.client:
            return

        token_path = Path("generated/tokens/google_ads_token.json")
        if not token_path.exists():
            raise RuntimeError(
                "Google Ads niet geautoriseerd. "
                "Voer eerst OAuth uit via /api/auth/google/ads/start"
            )

        self.client = GoogleAdsClient.load_from_storage(token_path)

    async def run(self, **kwargs):
        self._ensure_client()
        # hier pas Ads-logica
        return {"status": "ads bereikbaar"}


        with open(token_file, "r") as f:
            tok = json.load(f)

        # Bouw Google Ads config object
        self.config = {
            "developer_token": os.getenv("GOOGLE_ADS_DEV_TOKEN"),
            "client_id": tok["client_id"],
            "client_secret": tok["client_secret"],
            "refresh_token": tok["refresh_token"],
            "use_proto_plus": True,
        }

        self.client = GoogleAdsClient.load_from_dict(self.config)

    # ---- Campagnes ophalen ----
    def get_campaigns(self, customer_id: str):
        ga_service = self.client.get_service("GoogleAdsService")

        query = """
        SELECT campaign.id, campaign.name, campaign.status,
               metrics.clicks, metrics.impressions, metrics.ctr
        FROM campaign
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        results = []
        for row in response:
            results.append({
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "clicks": row.metrics.clicks,
                "impressions": row.metrics.impressions,
                "ctr": float(row.metrics.ctr),
            })

        return results

