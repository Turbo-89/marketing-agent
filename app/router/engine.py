from typing import Dict, Any, List
import uuid

from app.memory.memory_engine import MemoryEngine
from app.router.context_builder import ContextBuilder
from app.router.llm_router import LLMRouter
from app.api import facts_api


class RouterEngine:
    """
    Centrale router die:
    - chatlog opslaat
    - context opbouwt
    - geverifieerde facts afdwingbaar injecteert
    - LLM aanstuurt
    - ALTIJD UI-compatibel antwoord retourneert
    """

    def __init__(self, memory: MemoryEngine):
        self.memory = memory
        self.context = ContextBuilder(memory)
        self.llm = LLMRouter()

    async def handle(self, session_id: str, message: str) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())

        # -------------------------------------------------
        # 1. Log inkomend bericht
        # -------------------------------------------------
        await self.memory.log_message(
            session_id=session_id,
            role="user",
            content=message,
        )

        # -------------------------------------------------
        # 2. Haal geverifieerde facts op
        # -------------------------------------------------
        facts = facts_api.get_facts_for_session(session_id)

        verified_facts: Dict[str, Any] = {
            f["key"]: f["value"]
            for f in facts
            if f.get("verified") is True
        }

        # -------------------------------------------------
        # 3. Forceer facts IN de user prompt
        # -------------------------------------------------
        if verified_facts:
            facts_lines: List[str] = []

            for key, value in verified_facts.items():
                facts_lines.append(f"- {key}: {value}")

            facts_block = (
                "Geverifieerde feiten voor deze sessie "
                "(deze zijn volledig en correct):\n"
                + "\n".join(facts_lines)
                + "\n\n"
                "Gebruik deze feiten als bron van waarheid. "
                "Vraag hier NIET opnieuw naar. "
                "Ga uit van volledigheid.\n\n"
            )

            forced_user_message = facts_block + message
        else:
            forced_user_message = message

        # -------------------------------------------------
        # 4. Bouw context
        # -------------------------------------------------
        messages = await self.context.build(
            user_message=forced_user_message,
            session_id=session_id,
        )

        # -------------------------------------------------
        # 5. Route naar LLM
        # -------------------------------------------------
        llm_result = await self.llm.route(messages)

        # -------------------------------------------------
        # 6. Normaliseer response (CRUCIAAL)
        # -------------------------------------------------
        response_text: str

        if isinstance(llm_result, dict):
            # Ideaal pad
            response_text = (
                llm_result.get("result", {}).get("response")
                or llm_result.get("response")
                or ""
            )

            # Fallback: dump als tekst
            if not response_text:
                response_text = str(llm_result)
        else:
            response_text = str(llm_result)

        # Absolute garantie: nooit leeg
        if not response_text.strip():
            response_text = "Geen inhoudelijk antwoord gegenereerd."

        # -------------------------------------------------
        # 7. Log antwoord
        # -------------------------------------------------
        await self.memory.log_message(
            session_id=session_id,
            role="assistant",
            content=response_text,
        )

        # -------------------------------------------------
        # 8. RETURN CONTRACT (vast, UI-compatibel)
        # -------------------------------------------------
        return {
            "status": "completed",
            "task_id": task_id,
            "result": {
                "response": response_text
            }
        }

