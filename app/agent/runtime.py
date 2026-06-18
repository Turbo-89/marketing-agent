from __future__ import annotations

from typing import Dict, Any, Optional
from app.memory.memory_engine import MemoryEngine
from app.agent.facts import FactRegistry
from app.agent.preflight import build_blocked_payload
from app.agent.output_validator import validate_output
from app.tools.web_crawl import WebCrawlExecutor


class AgentRuntime:
    def __init__(self):
        self.memory = MemoryEngine()
        # initialize client nu zodat facts/validator direct kunnen werken
        self.memory.initialize()
        self.facts = FactRegistry(self.memory)

    def handle_user_message(
        self,
        *,
        session_id: str,
        user_message: str,
        intent: str = "generic",
        generated_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        generated_output: optie om bestaande LLM-output door validator te halen.
        In jouw integratie vervang je dit later door je echte LLM call.
        """

        # 1) Sessie
        self.memory.get_or_create_session(session_id)

        # 2) Task
        task_id = self.memory.create_task(session_id, intent)
        self.memory.update_task(task_id, status="running", step="preflight")
        self.memory.log_event(task_id, "user_message", {"content": user_message})

        # 3) Preflight gate op verified facts
        missing = self.facts.missing_required(session_id)
        if missing:
            self.memory.update_task(
                task_id,
                status="blocked",
                step="missing_information",
                result={"missing": missing},
            )
            self.memory.log_event(task_id, "blocked", {"missing": missing})
            payload = build_blocked_payload(missing)
            payload["task_id"] = task_id
            return payload

        # 4) Analyse mag starten
        self.memory.update_task(task_id, status="running", step="analysis")

        facts_map = self.facts.get_verified_facts_map(session_id)

        # 5) Hier komt jouw bestaande agent/LLM/tool-logica
        crawler = WebCrawlExecutor()

        if "CRAWL TASK" in user_message:
            self.memory.update_task(task_id, step="crawling")

            # URL voorlopig hardcoded voor deze test
            crawl_result = crawler.crawl("https://turboservices.be")

            output_text = (
                "- Laatste zichtbare activiteit: ONBEKEND\n"
                "- Zichtbare contenttypes: tekst, afbeeldingen\n"
                "- Aantal zichtbare posts/video’s: ONBEKEND\n"
                "- Zichtbare CTA: ONBEKEND\n"
                f"- Branding zichtbaar: {'JA' if crawl_result['has_images'] else 'ONBEKEND'}\n"
                f"- Overige zichtbare feiten: {len(crawl_result['text_sample'])} zichtbare tekstblokken gevonden"
    )

            self.memory.log_event(task_id, "crawl_raw", crawl_result)

        else:
            output_text = "OK"


        # 6) Output validator (hard)
        violations = validate_output(output_text, facts_map)
        if violations:
            self.memory.update_task(
                task_id,
                status="failed",
                step="assumptions_detected",
                result={"violations": violations},
            )
            self.memory.log_event(task_id, "validation_failed", {"violations": violations})
            return {
                "status": "failed",
                "task_id": task_id,
                "reason": "assumptions_detected",
                "details": violations,
            }

        # 7) Completed
        result = {"response": output_text, "facts_used": facts_map}
        self.memory.update_task(task_id, status="completed", step="done", result=result)
        self.memory.log_event(task_id, "completed", {"ok": True})

        return {
            "status": "completed",
            "task_id": task_id,
            "result": result,
        }
