# app/projects.py

import datetime
import uuid
from app.memory import MemoryEngine


class ProjectEngine:
    """
    ProjectEngine beheert grote, meervoudige AI-taken.
    - aanmaken en bewaren van projecten
    - stappenlijst beheren
    - state opslaan in Firestore
    - herstartbare flows
    """

    def __init__(self):
        self.memory = MemoryEngine()

    # ==========================================================
    # PROJECT AANMAKEN
    # ==========================================================

    def create_project(self, args: dict) -> dict:
        """
        Maakt een nieuw project met een unieke ID en basisinformatie.
        """

        project_id = str(uuid.uuid4())

        project = {
            "id": project_id,
            "name": args.get("name", f"Project-{project_id[:8]}"),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "steps": args.get("steps", []),
            "status": "pending",
            "current_step": 0,
            "meta": args.get("meta", {}),
        }

        self.memory.write_project_state(project_id, project)

        return project

    # ==========================================================
    # STEP MANAGEMENT
    # ==========================================================

    def get_project(self, project_id: str) -> dict:
        """
        Haalt huidige projecttoestand op.
        """
        return self.memory.get_project_state(project_id)

    def set_status(self, project_id: str, status: str):
        """
        Zet de status van het project (pending, running, done, error)
        """
        state = self.get_project(project_id)
        state["status"] = status
        self.memory.write_project_state(project_id, state)

    def add_step(self, project_id: str, step: dict):
        """
        Voeg een stap toe aan het project.
        step = {
            "intent": "generate_page",
            "args": {...},
            "status": "pending"
        }
        """
        project = self.get_project(project_id)
        if "steps" not in project:
            project["steps"] = []
        project["steps"].append(step)
        self.memory.write_project_state(project_id, project)

    def mark_step_done(self, project_id: str, index: int):
        project = self.get_project(project_id)
        if "steps" in project and index < len(project["steps"]):
            project["steps"][index]["status"] = "done"
            project["current_step"] = index + 1
            self.memory.write_project_state(project_id, project)

    # ==========================================================
    # PROJECT RUNNER
    # ==========================================================

    async def run_project(self, project_id: str, router):
        """
        Voert een volledig project uit:
        - doorloopt alle stappen
        - gebruikt ToolRouter om acties uit te voeren
        - bewaart state
        """

        project = self.get_project(project_id)
        steps = project.get("steps", [])

        self.set_status(project_id, "running")

        for i, step in enumerate(steps):
            intent = step.get("intent")
            args = step.get("args", {})

            # LOG
            self.memory.record("project_step_start", {
                "project": project_id,
                "step": i,
                "intent": intent
            })

            # Uitvoeren
            async for update in router.run(intent, args):
                # Yield doorgeven aan streaming mechanisme
                yield f"[Project {project_id}] {update}"

            # Stap afvinken
            self.mark_step_done(project_id, i)

        # Alles voltooid
        self.set_status(project_id, "done")

        self.memory.record("project_complete", {
            "project": project_id
        })

        yield f"Project {project_id} is volledig afgerond."
        yield "KLAAR"
