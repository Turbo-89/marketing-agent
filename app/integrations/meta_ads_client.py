import requests
import os

class MetaAdsClient:
    def __init__(self):
        self.token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account = os.getenv("META_AD_ACCOUNT_ID")

    def get_campaign_metrics(self):
        url = f"https://graph.facebook.com/v19.0/{self.ad_account}/insights"
        params = {
            "access_token": self.token,
            "fields": "campaign_name,impressions,clicks,ctr,spend"
        }

        r = requests.get(url, params=params)
        return r.json().get("data", [])
