from openai import OpenAI
import os
import json
from typing import List, Dict, Any


SYSTEM_PROMPT = """
Je bent een feitelijke, analytische assistent voor Turbo Services.

Geverifieerde Firestore facts (verified = true) zijn bindend en volledig.
Je mag NOOIT vragen naar informatie die als verified fact bestaat.
Indien voldoende facts aanwezig zijn, MOET je de opdracht uitvoeren.

Blokkeren is enkel toegestaan indien vereiste informatie NIET bestaat als verified Firestore fact.
Antwoord NOOIT met enkel 'OK'.
Gebruik geen marketingtaal.
"""


class LLMRouter:
    def __init__(self):
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY ontbreekt")
        self.client = OpenAI(api_key=key)

    async def route(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # -------------------------------------------------
        # FORCEER system prompt ALS EERSTE BERICHT
        # -------------------------------------------------
        final_messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + messages

        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=final_messages,
        )

        raw = completion.choices[0].message.content or ""
        text = raw.strip()

        # Veiligheidsnet
        if text.lower() in {"ok", ""}:
            text = "Er zijn voldoende feiten beschikbaar om deze opdracht uit te voeren, maar het model gaf geen inhoudelijk antwoord."

        return {
            "status": "completed",
            "result": {
                "response": text
            }
        }
