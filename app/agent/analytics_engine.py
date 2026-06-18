import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Metric, Dimension, RunReportRequest
)
from google.oauth2 import service_account


class AnalyticsEngine:
    """
    GA4 via service-account.
    Geen OAuth tokens. Geen user login.
    """
    def __init__(self, property_id: str):
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path or not os.path.exists(credentials_path):
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS ontbreekt of bestaat niet.")

        creds = service_account.Credentials.from_service_account_file(credentials_path)

        self.client = BetaAnalyticsDataClient(credentials=creds)
        self.property_id = property_id

    # --------------------------
    # 1. Total pageviews
    # --------------------------
    def get_pageviews(self, days=7):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )
        return self.client.run_report(request)

    # --------------------------
    # 2. Top pages
    # --------------------------
    def get_top_pages(self, days=30, limit=50):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
            limit=limit
        )
        return self.client.run_report(request)

    # --------------------------
    # 3. Engagement per pagina
    # --------------------------
    def get_engagement_by_page(self, days=30):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="engagementRate"),
                Metric(name="engagedSessions"),
                Metric(name="screenPageViews"),
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )
        return self.client.run_report(request)

    # --------------------------
    # 4. Gebruikerslocaties
    # --------------------------
    def get_regions(self, days=30):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[Dimension(name="city")],
            metrics=[Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )
        return self.client.run_report(request)

    # --------------------------
    # 5. Sessions totaal
    # --------------------------
    def get_sessions(self, days=30):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )
        return self.client.run_report(request)

