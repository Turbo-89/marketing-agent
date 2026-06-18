# app/agent/seo_engine.py

class SEOEngine:
    """
    Analyseert GA4-gegevens en bepaalt SEO-signalen:
    - onderpresterende pagina’s
    - regio’s met hoge vraag maar weinig pagina’s
    - diensten die ontbreken of zwak scoren
    """

    def __init__(self, analytics):
        self.analytics = analytics

    def analyze(self):
        """
        Retourneert een dict met:
        - top_pages
        - low_pages
        - regions
        - recommended_targets (service + regio combinaties)
        """

        pageviews = self.analytics.get_top_pages(days=30, limit=100)
        engagement = self.analytics.get_engagement_by_page(days=30)
        regions = self.analytics.get_regions(days=30)
        sessions = self.analytics.get_sessions(days=30)

        # Technisch correcte extractie uit Google API response
        pages = []
        for row in pageviews.rows:
            pages.append({
                "path": row.dimension_values[0].value,
                "views": int(row.metric_values[0].value)
            })

        # Sorteren
        pages_sorted = sorted(pages, key=lambda x: x["views"], reverse=True)

        # onderpresterende pagina's = alles onder mediaan
        views = [p["views"] for p in pages_sorted]
        median = views[len(views)//2] if views else 0

        low_pages = [p for p in pages_sorted if p["views"] < median]

        # regio-inzichten
        region_stats = []
        for row in regions.rows:
            region_stats.append({
                "city": row.dimension_values[0].value,
                "users": int(row.metric_values[0].value)
            })

        # Automatische aanbeveling:
        # Regio’s + services = targets voor nieuwe pagina’s
        recommended_targets = []
        for reg in region_stats:
            if reg["users"] > 5:
                recommended_targets.append({
                    "region": reg["city"].lower().replace(" ", "-"),
                    "service": "ontstoppingen"
                })

        return {
            "pages_sorted": pages_sorted,
            "low_pages": low_pages,
            "regions": region_stats,
            "recommended_targets": recommended_targets,
            "sessions": sessions
        }
