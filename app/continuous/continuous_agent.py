import asyncio
from app.autonomy.marketing_supervisor import MarketingSupervisor
from app.continuous.scheduler import Scheduler
from app.continuous.logger import Log
from app.continuous.safety import Safety
from app.video.video_agent import VideoAgent
self.video_agent = VideoAgent()

...

for task in tasks:
    if "updated" in task or "created" in task:
        s = task.get("service")
        r = task.get("region")
        seo = task.get("seo_score", 0)

        maybe_video = self.video_agent.auto_generate_for_page(s, r, seo)
        if maybe_video:
            self.logger.write(f"Promo video gemaakt: {maybe_video}")


class ContinuousAgent:
    def __init__(self, interval_minutes=30, auto_deploy=False):
        self.scheduler = Scheduler(interval_minutes)
        self.supervisor = MarketingSupervisor()
        self.logger = Log()
        self.safety = Safety()
        self.auto_deploy = auto_deploy

    async def cycle(self):
        try:
            self.logger.write("START: Nieuwe autonome cyclus")

            result = self.supervisor.run(auto_deploy=self.auto_deploy)
            tasks = result["tasks"]

            # safety check
            self.safety.check_limits(tasks)

            self.logger.write(f"Uitgevoerde taken: {tasks}")

            if self.auto_deploy:
                self.logger.write(f"Deploy uitgevoerd: {result['deploy']}")

            self.logger.write("EINDE cyclus")
        except Exception as e:
            self.logger.write(f"FOUT: {str(e)}")

    async def run(self):
        await self.scheduler.loop(self.cycle)
