import time
import traceback
from datetime import datetime
from app.memory import MemoryEngine
from app.projects import ProjectEngine

class Monitor:
    """
    TurboAgent 3.0 Monitor Engine
    - Houdt health/state bij
    - Logt run-cycli
    - Synchroniseert met Firestore
    """

    def __init__(self):
        self.memory = MemoryEngine()
        self.projects = ProjectEngine()

    async def heartbeat(self):
        """
        Wordt periodiek aangeroepen door Scheduler.
        Houdt status bij van agent, projects, en errors.
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            data = {
                "timestamp": timestamp,
                "status": "ok",
                "runtime": time.time(),
                "active_projects": self.projects.list_projects(),
            }

            # schrijf health-check naar Firestore
            self.memory.write("system/heartbeat", data)

        except Exception as exc:
            error_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(exc),
                "trace": traceback.format_exc()
            }

            # log fout in Firestore
            self.memory.write("system/errors", error_data)
