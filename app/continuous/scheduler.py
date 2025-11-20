import asyncio

class Scheduler:
    def __init__(self, interval_minutes=30):
        self.interval = interval_minutes * 60

    async def loop(self, callback):
        while True:
            await callback()
            await asyncio.sleep(self.interval)
