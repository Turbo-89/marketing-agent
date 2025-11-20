from app.autonomy.monitor import Monitor
from app.autonomy.prioritizer import Prioritizer
from app.autonomy.update_agent import UpdateAgent
from app.autonomy.create_agent import CreateAgent
from app.autonomy.deploy_agent import DeployAgent

class MarketingSupervisor:
    def __init__(self):
        self.monitor = Monitor()
        self.prio = Prioritizer()
        self.update = UpdateAgent()
        self.create = CreateAgent()
        self.deploy_agent = DeployAgent()

    def run(self, auto_deploy=False):
        analysis = self.monitor.analyze()
        tasks = self.prio.prioritize(analysis)

        results = []

        for task in tasks:
            if task["type"] == "update":
                results.append(self.update.update(task["service"], task["region"]))

            elif task["type"] == "create":
                results.append(self.create.create(task["service"], task["region"]))

        if auto_deploy:
            deploy_result = self.deploy_agent.deploy()
            return {"tasks": results, "deploy": deploy_result}

        return {"tasks": results}
