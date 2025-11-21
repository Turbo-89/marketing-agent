# app/autonomy/scheduler.py

import os
import asyncio
import datetime
from app.tools_router import ToolRouter
from app.memory import MemoryEngine
from app.autonomy.monitor import MonitorEngine
from app.autonomy.safety import SafetyEngine
from app.projects import ProjectEngine


class AutonomyScheduler:
    """
    TurboAgent autonome scheduler.
    Voert achtergrondtaken uit volgens schema en systeemstatus.
    """

    def __init__(self):
        self.memory = MemoryEngine()
        self.router = ToolRouter()
        self.monitor = MonitorEngine()
        self.safety = SafetyEngine()
        self.projects = ProjectEngine()

        self.pages_path = "generated/pages"
        self.heroes_path = "generated/images"
        self.videos_path = "generated/videos"


    # ========================================================
    # START DE DAGELIJKSE / WEKELIJKSE LOOP
    # ========================================================

    async def start(self):
        """
        Start de permanente autonome loop.
        Wordt door server.py in background gestart.
        """
        while True:
            now = datetime.datetime.utcnow()

            # Log heartbeat
            self.memory.log_autonomy_event("heartbeat", {
                "utc": now.isoformat()
            })

            # 02:00 — dagelijkse taken
            if now.hour == 2:
                await self.run_daily_tasks()

            # 03:00 zondag — wekelijkse taken
            if now.weekday() == 6 and now.hour == 3:
                await self.run_weekly_tasks()

            # Wacht 1 uur
            await asyncio.sleep(3600)


    # ========================================================
    # DAGELIJKSE TAKEN
    # ========================================================

    async def run_daily_tasks(self):
        self.memory.log_autonomy_event("daily_tasks_started", {})

        await self.seo_check()
        await self.content_age_check()
        await self.video_rotation()
        await self.api_status()
        await self.detect_missing_pages()

        self.memory.log_autonomy_event("daily_tasks_completed", {})


    # ========================================================
    # WEKELIJKSE TAKEN
    # ========================================================

    async def run_weekly_tasks(self):
        self.memory.log_autonomy_event("weekly_tasks_started", {})

        await self.regio_expansion()
        await self.system_health_check()

        self.memory.log_autonomy_event("weekly_tasks_completed", {})


    # ========================================================
    # AUTONOME MODULES
    # ========================================================

    async def seo_check(self):
        """
        Dagelijkse SEO-refresh.
        """
        async for update in self.router.run("seo_optimize", {}):
            self.memory.log_autonomy_event("seo_refresh", {"update": update})


    async def content_age_check(self):
        """
        Detecteert pagina’s ouder dan 45 dagen.
        (FASE 11 vult dit aan met automatische hergeneratie)
        """
        pages = self.monitor.list_pages()

        for p in pages:
            file = p["file"]
            mtime = os.path.getmtime(file)
            age_days = (datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(mtime)).days

            if age_days > 45:
                self.memory.log_autonomy_event("content_aged", {
                    "service": p["service"],
                    "region": p["region"],
                    "age_days": age_days
                })


    async def video_rotation(self):
        """
        Dagelijkse check of nieuwe promo-video nodig is.
        (Exact schema komt in FASE 10)
        """
        videos = self.monitor.list_videos()

        if len(videos) < 5:
            self.memory.log_autonomy_event("video_rotation", {"status": "too_few_videos"})


    async def api_status(self):
        """
        API status-check: OpenAI, GitHub, FAL.
        """
        status = self.monitor.check_api_updates()
        self.memory.log_autonomy_event("api_status", status)


    async def detect_missing_pages(self):
        """
        Self-healing:
        - detecteert ontbrekende pagina’s
        - detecteert ontbrekende hero’s
        - detecteert ontbrekende video's
        (Herstel in FASE 12)
        """

        pages = self.monitor.list_pages()
        heroes = self.monitor.list_heroes()
        videos = self.monitor.list_videos()

        # Pagina zonder hero
        for p in pages:
            expected_hero = f"hero-{p['service']}-{p['region']}.png"
            if expected_hero not in heroes:
                self.memory.log_autonomy_event("missing_hero", {
                    "service": p["service"],
                    "region": p["region"]
                })

        # Pagina zonder video
        for p in pages:
            name = f"{p['service']}-{p['region']}"
            videos_for_page = [v for v in videos if name in v]
            if not videos_for_page:
                self.memory.log_autonomy_event("missing_video", {
                    "service": p["service"],
                    "region": p["region"]
                })


    async def regio_expansion(self):
        """
        Wekelijkse automatische uitbreiding van regio’s.
        (FASE 11 maakt connectie met services.json & regions.json)
        """
        self.memory.log_autonomy_event("regio_expansion", {"status": "pending"})


    async def system_health_check(self):
        """
        CPU/RAM/Disk check.
        """
        status = self.safety.system_health_check()
        self.memory.log_autonomy_event("system_health", status)
