from app.seo.seo_keywords import SEOKeywords
from app.seo.seo_metadata import MetadataEngine
from app.seo.seo_analyzer import SEOAnalyzer

class SEOManager:
    def __init__(self):
        self.k = SEOKeywords()
        self.m = MetadataEngine()
        self.a = SEOAnalyzer()

    def run(self, service: str, region: str, raw_title: str, raw_description: str):
        keywords = self.k.get_keywords(service, region)
        metadata = self.m.optimize_metadata(raw_title, raw_description, keywords)
        score = self.a.score_page(keywords, metadata)

        return {
            "keywords": keywords,
            "optimized_metadata": metadata,
            "seo_score": score
        }
