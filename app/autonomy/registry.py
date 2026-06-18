# app/autonomy/registry.py

from app.autonomy.auto_tasks import AutoTasks

class TaskRegistry:
    """
    Geeft lijst van beschikbare autonome taken.
    De Scheduler leest deze in en voert ze één voor één uit.
    """

    def __init__(self):
        self.tasks = AutoTasks()

    async def run_all(self):
        results = []

        # 1) SEO
        results.append(await self.tasks.run_seo_update())

        # 2) Hero-check
        results.append(await self.tasks.run_hero_check())

        # 3) Refresh
        results.append(await self.tasks.run_refresh())

        return results
