from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.oauth2 import service_account

load_dotenv()

def _service_account_path() -> str:
    path = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_PATH",
        os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS",
            str(Path("config") / "service_account.json"),
        ),
    )
    if not path:
        raise RuntimeError("Geen service-account pad gevonden voor GA4.")
    return path


def _property_id() -> str:
    value = os.getenv("GA4_PROPERTY_ID")
    if not value:
        raise RuntimeError("GA4_PROPERTY_ID ontbreekt.")
    return str(value).strip()


class GA4Client:
    def __init__(self, property_id: str | None = None):
        self.property_id = property_id or _property_id()
        credentials = service_account.Credentials.from_service_account_file(
            _service_account_path()
        )
        self.client = BetaAnalyticsDataClient(credentials=credentials)

    def get_pageviews(self, page_path: str, start_date: str = "30daysAgo", end_date: str = "today") -> int:
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter={
                "filter": {
                    "field_name": "pagePath",
                    "string_filter": {"value": page_path},
                }
            },
        )

        response = self.client.run_report(request)

        if response.rows:
            return int(response.rows[0].metric_values[0].value)

        return 0

    def get_top_pages(self, limit: int = 20, start_date: str = "30daysAgo", end_date: str = "today") -> list[dict]:
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            limit=limit,
        )

        response = self.client.run_report(request)

        results = []
        for row in response.rows:
            results.append(
                {
                    "page_path": row.dimension_values[0].value,
                    "screen_page_views": int(row.metric_values[0].value),
                }
            )

        return results

    def get_landing_page_signals(self, limit: int = 20, start_date: str = "30daysAgo", end_date: str = "today") -> list[dict]:
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[
                Dimension(name="landingPagePlusQueryString"),
                Dimension(name="sessionSourceMedium"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="engagementRate"),
                Metric(name="conversions"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            limit=limit,
        )

        response = self.client.run_report(request)

        results = []
        for row in response.rows:
            results.append(
                {
                    "landing_page_path": row.dimension_values[0].value,
                    "source_medium": row.dimension_values[1].value,
                    "sessions": int(float(row.metric_values[0].value or 0)),
                    "users": int(float(row.metric_values[1].value or 0)),
                    "engagement_rate": float(row.metric_values[2].value or 0),
                    "conversions": float(row.metric_values[3].value or 0),
                }
            )

        return results
