# app/continuous/scheduler.py

import asyncio
from datetime import datetime
from app.autonomy.registry import TaskRegistry

class Scheduler:
    """
    Eenvoudige async scheduler.
    Voert automatisch alle autonomie-taken uit.
    """

    def __init__(self, interval: int = 3600):
        self.interval = interval
        self.registry = TaskRegistry()
        self.running = False

    async def start(self):
        self.running = True
        print(f"[Scheduler] Gestart interval={self.interval}s")

        while self.running:
            try:
                print("[Scheduler] Tick – autonome taken starten...")
                results = await self.registry.run_all()
                print("[Scheduler] Resultaten:", results)
            except Exception as e:
                print("[Scheduler] Fout:", e)

            await asyncio.sleep(self.interval)
