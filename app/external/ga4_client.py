from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
import json, os
from google.oauth2.credentials import Credentials

class GA4Client:
    def __init__(self, property_id: str):
        token_file = "generated/tokens/google_ga4_token.json"
        if not os.path.exists(token_file):
            raise RuntimeError("GA4 token niet gevonden. Voer eerst OAuth flow uit.")

        with open(token_file, "r") as f:
            data = json.load(f)

        creds = Credentials(
            token=data["token"],
            refresh_token=data.get("refresh_token"),
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            token_uri="https://oauth2.googleapis.com/token"
        )

        self.client = BetaAnalyticsDataClient(credentials=creds)
        self.property_id = property_id

    def get_pageviews(self, start="7daysAgo", end="today"):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=start, end_date=end)]
        )
        return self.client.run_report(request)

    def get_top_pages(self, limit=25):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            limit=limit
        )
        return self.client.run_report(request)
