import requests
import json
import os

class GA4Client:
    def __init__(self, property_id=None, api_key=None):
        self.property_id = property_id or os.getenv("GA4_PROPERTY_ID")
        self.api_key = api_key or os.getenv("GA4_API_KEY")
        self.url = f"https://analyticsdata.googleapis.com/v1beta/properties/{self.property_id}:runReport?key={self.api_key}"

    def get_pageviews(self, page_path: str):
        payload = {
            "dimensions": [{"name": "pagePath"}],
            "metrics": [{"name": "screenPageViews"}],
            "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
            "dimensionFilter": {
                "filter": {
                    "fieldName": "pagePath",
                    "stringFilter": {"value": page_path}
                }
            }
        }

        r = requests.post(self.url, json=payload)
        data = r.json()

        if "rows" in data and len(data["rows"]) > 0:
            return int(data["rows"][0]["metricValues"][0]["value"])

        return 0
