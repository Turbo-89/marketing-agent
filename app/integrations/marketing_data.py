from app.integrations.ga4_client import GA4Client
from app.integrations.google_ads_client import GoogleAdsClient
from app.integrations.youtube_client import YouTubeClient
from app.integrations.meta_ads_client import MetaAdsClient
from app.integrations.traffic_analyzer import TrafficAnalyzer

class MarketingData:
    def __init__(self):
        self.ga4 = GA4Client()
        self.gads = GoogleAdsClient()
        self.yt = YouTubeClient()
        self.meta = MetaAdsClient()

        self.analyzer = TrafficAnalyzer(
            ga4=self.ga4,
            gads=self.gads,
            yt=self.yt,
            meta=self.meta
        )

    def score_page(self, page_path: str, keyword: str):
        return self.analyzer.score(page_path, keyword)
