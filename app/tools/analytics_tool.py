# app/tools/analytics_tool.py

import os
from typing import Any, Dict, List

from app.agent.analytics_engine import AnalyticsEngine


class AnalyticsSummaryTool:
    """
    AnalyticsSummaryTool
    --------------------
    Dunne laag bovenop AnalyticsEngine.
    Doel: 1 call → bruikbaar analytics-pakket voor de agent.

    Gebruik:
        tool = AnalyticsSummaryTool()
        data = tool.run()                              # gebruikt GA4_PROPERTY_ID uit .env
        data = tool.run(property_id="494314714")       # expliciet property_id

    Output-structuur (dict):
        {
            "property_id": "...",
            "pageviews_last_7d": int,
            "sessions_last_30d": int,
            "top_pages": [
                {"path": "/diensten/...", "views": 35},
                ...
            ],
            "engagement": [
                {
                    "path": "/diensten/ontstoppingen/antwerpen-stad",
                    "engagement_rate": 0.58,
                    "engaged_sessions": 7,
                    "views": 35,
                },
                ...
            ],
        }
    """

    def __init__(self, default_property_env: str = "GA4_PROPERTY_ID") -> None:
        self.default_property_env = default_property_env

    # -----------------------------------------------------
    # Low-level helpers om GA4 responses om te zetten
    # -----------------------------------------------------
    @staticmethod
    def _parse_single_metric(response) -> int:
        """
        Verwacht een RunReportResponse met 1 metric en 1 rij.
        Geeft 0 terug als er geen rijen zijn.
        """
        if not response.rows:
            return 0
        try:
            return int(response.rows[0].metric_values[0].value)
        except Exception:
            return 0

    @staticmethod
    def _parse_top_pages(response) -> list:
        """
        Verwacht dimensions=[pagePath], metrics=[screenPageViews].
        Geeft lijst van dicts: [{"path": "...", "views": int}, ...]
        """
        results = []
        for row in response.rows:
            try:
                path = row.dimension_values[0].value
                views = int(row.metric_values[0].value)
                results.append({"path": path, "views": views})
            except Exception:
                continue
        # sorteer aflopend op views
        results.sort(key=lambda r: r["views"], reverse=True)
        return results

    @staticmethod
    def _parse_engagement(response) -> list:
        """
        Verwacht:
            dimensions=[pagePath]
            metrics=[
                engagementRate,
                engagedSessions,
                screenPageViews,
            ]
        Geeft lijst van dicts:
            [
                {
                    "path": str,
                    "engagement_rate": float,
                    "engaged_sessions": int,
                    "views": int,
                },
                ...
            ]
        """
        results = []
        for row in response.rows:
            try:
                path = row.dimension_values[0].value
                engagement_rate = float(row.metric_values[0].value)
                engaged_sessions = int(row.metric_values[1].value)
                views = int(row.metric_values[2].value)
                results.append(
                    {
                        "path": path,
                        "engagement_rate": engagement_rate,
                        "engaged_sessions": engaged_sessions,
                        "views": views,
                    }
                )
            except Exception:
                continue

        # sorteer bv. op engaged_sessions aflopend
        results.sort(key=lambda r: r["engaged_sessions"], reverse=True)
        return results

    # -----------------------------------------------------
    # Publieke entrypoint voor de agent
    # -----------------------------------------------------
    def run(self, property_id: str | None = None) -> Dict[str, Any]:
        """
        Hoofd-entrypoint. Wordt door de agent aangeroepen.

        - property_id expliciet meegeven, of
        - via env GA4_PROPERTY_ID (string) inladen
        """
        pid = property_id or os.getenv(self.default_property_env)
        if not pid:
            raise RuntimeError(
                f"GA4 property_id ontbreekt. Geef 'property_id' mee of stel {self.default_property_env} in."
            )

        engine = AnalyticsEngine(pid)

        # 1) Pageviews laatste 7 dagen
        pageviews_resp = engine.get_pageviews(start="7daysAgo", end="today")
        pageviews_last_7d = self._parse_single_metric(pageviews_resp)

        # 2) Sessions laatste 30 dagen
        sessions_resp = engine.get_sessions(days=30)
        sessions_last_30d = self._parse_single_metric(sessions_resp)

        # 3) Top pages (30 dagen)
        top_pages_resp = engine.get_top_pages(days=30, limit=50)
        top_pages = self._parse_top_pages(top_pages_resp)

        # 4) Engagement per pagina (30 dagen)
        engagement_resp = engine.get_engagement_by_page(days=30)
        engagement = self._parse_engagement(engagement_resp)

        return {
            "property_id": pid,
            "pageviews_last_7d": pageviews_last_7d,
            "sessions_last_30d": sessions_last_30d,
            "top_pages": top_pages,
            "engagement": engagement,
        }
