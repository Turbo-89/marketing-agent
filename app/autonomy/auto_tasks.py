# app/autonomy/auto_tasks.py

from datetime import datetime
from app.seo.seo_analyzer import SEOAnalyzer
from app.tools.hero_image import HeroImageEngine
from app.tools.content_engine import ContentEngine

class AutoTasks:
    """
    Bundelt alle periodieke autonome acties.
    Wordt aangeroepen door Scheduler.
    """

    def __init__(self):
        self.seo = SEOAnalyzer()
        self.hero = HeroImageEngine()
        self.content = ContentEngine()

    # ------------------------------------------------------
    # 1. SEO-update
    # ------------------------------------------------------
    async def run_seo_update(self):
        report = self.seo.scan_site()
        return {
            "task": "seo_update",
            "timestamp": datetime.utcnow().isoformat(),
            "result": report,
        }

    # ------------------------------------------------------
    # 2. Hero-afbeeldingen controleren
    # ------------------------------------------------------
    async def run_hero_check(self):
        missing = []
        for s in self.content.services.keys():
            for r in self.content.regions:
                slug = r["slug"]
                path = f"generated/pages/{s}/{slug}/hero.webp"
                # eenvoudig check
                import os
                if not os.path.exists(path):
                    missing.append({"service": s, "region": slug})
        return {
            "task": "hero_missing_check",
            "missing": missing,
            "count": len(missing),
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------
    # 3. Revalidate / refresher
    # ------------------------------------------------------
    async def run_refresh(self):
        # placeholder — kan gekoppeld worden aan Vercel webhook
        return {
            "task": "refresh_site",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ok"
        }
