# app/tools/marketing_insights.py

import os
from openai import OpenAI

from app.tools.analytics_tool import AnalyticsSummaryTool
from app.tools.ads_tool import GoogleAdsTool
from app.tools.search_console_tool import SearchConsoleTool


class MarketingInsightsTool:
    name = "marketing_insights"

    def __init__(self):
        self.analytics = AnalyticsSummaryTool()
        self._ads = None
        self._sc = None
        self.ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _get_ads(self):
        if self._ads is None:
            self._ads = GoogleAdsTool()
        return self._ads

    def _get_sc(self):
        if self._sc is None:
            self._sc = SearchConsoleTool()
        return self._sc

    def run(self):
        property_id = os.getenv("GA4_PROPERTY_ID")
        ads_customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
        sc_site = os.getenv("SC_SITE_URL")

        result = {}

        # GA4 (mag altijd)
        result["ga4"] = self.analytics.run(property_id=property_id)

        # Google Ads (alleen als token bestaat)
        try:
            result["ads"] = self._get_ads().get_campaigns(
                customer_id=ads_customer_id
            )
        except Exception as e:
            result["ads_error"] = str(e)

        # Search Console
        try:
            result["search_console"] = self._get_sc().get_site_data(
                site_url=sc_site
            )
        except Exception as e:
            result["search_console_error"] = str(e)

        # AI-samenvatting
        prompt = f"""
        Analyseer deze marketingdata en geef JSON:
        {{
          "health_score": 0-100,
          "issues": [],
          "opportunities": [],
          "recommended_pages": [],
          "priority_actions": []
        }}

        Data:
        {result}
        """

        ai = self.ai.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        ).output[0].content[0].text

        result["ai_summary"] = ai
        return result
