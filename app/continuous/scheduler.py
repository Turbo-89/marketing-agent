import asyncio
import time

class Scheduler:
    def __init__(self, interval: int = 3600):
        self.interval = interval
        self.running = False

    async def tick(self):
        from app.memory import MemoryEngine
        from app.continuous.memory_summarizer import MemorySummarizer

        mem = MemoryEngine()
        ms = MemorySummarizer()

        pending = await mem.list_unprocessed_sessions(limit=5)

        for session_id in pending:
            logs = await mem.fetch_session_logs(session_id)

            if not logs or len(logs.strip()) < 20:
                continue

            summary = await ms.summarize(session_id, logs)
            await mem.store_session_summary(session_id, summary)

        return {"processed_sessions": pending}

    async def start(self):
        """Asynchrone loop – vereist door asyncio.create_task()."""
        if self.running:
            return

        self.running = True

        while True:
            try:
                await self._tick()
            except Exception as e:
                print(f"[Scheduler] Fout in tick: {e}")

            await asyncio.sleep(self.interval)
