import google.ads.googleads.client
import os

class GoogleAdsClient:
    def __init__(self):
        self.client = google.ads.googleads.client.GoogleAdsClient.load_from_storage(
            path=os.getenv("GOOGLE_ADS_YAML_PATH")
        )

    def get_keyword_metrics(self, keyword: str):
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
        SELECT
            keyword_view.resource_name,
            metrics.avg_cpc,
            metrics.clicks,
            metrics.ctr
        FROM keyword_view
        WHERE segments.keyword.text = '{keyword}'
        """

        response = ga_service.search_stream(
            customer_id=os.getenv("GOOGLE_ADS_CUSTOMER_ID"),
            query=query
        )

        result = []
        for batch in response:
            for row in batch.results:
                result.append({
                    "keyword": keyword,
                    "avg_cpc": row.metrics.avg_cpc,
                    "clicks": row.metrics.clicks,
                    "ctr": row.metrics.ctr
                })

        return result
