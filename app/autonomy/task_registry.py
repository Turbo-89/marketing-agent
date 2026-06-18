from app.autonomy.marketing_updater import MarketingUpdater
from fastapi import HTTPException


class TaskRegistry:
    """
    Registreert ALLE autonomie-taken.
    Taken moeten async run() implementeren.
    """

    def __init__(self):
        self.tasks = {
            "marketing_updater": MarketingUpdater(),
        }

    def list(self):
        """Geef overzicht van alle autonome taken."""
        return list(self.tasks.keys())

    def get(self, name: str):
        """Ophalen van taak-instantie."""
        task = self.tasks.get(name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Unknown task '{name}'")
        return task

    async def run(self, name: str):
        """Draai één taak op naam."""
        task = self.get(name)
        return await task.run()

    async def run_all(self):
        """Draai ALLE taken."""
        results = {}
        for name, task in self.tasks.items():
            try:
                results[name] = await task.run()
            except Exception as e:
                results[name] = {"error": str(e)}
        return results
