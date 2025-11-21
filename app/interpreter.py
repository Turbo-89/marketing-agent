# app/interpreter.py
# ------------------------------------------------------------
# Interpreter: verwerkt natuurlijke taal → intent + args
# via OpenAI 5.1 model.
# ------------------------------------------------------------

import os
import json
from openai import OpenAI

MODEL = "gpt-5.1"

class Interpreter:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def parse(self, message: str):
        """
        Analyseer tekst → bepaal intent → extraheer parameters
        Resultaat:
            intent (str)
            args (dict)
        """
        system_prompt = """
Je bent een Intent-Parser voor TurboAgent.

Je taak:
1. Bepaal de intent van de gebruiker.
2. Geef args als JSON.
3. Gebruik ALLEEN deze intents:

- generate_page
- generate_hero
- generate_video
- deploy
- seo_optimize
- drive_upload
- drive_list
- drive_sync
- fs_read
- fs_write
- fs_list
- analyze_file
- chat

Als intent onbekend is → 'chat'.
"""

        completion = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]
        )

        raw = completion.choices[0].message.content

        try:
            data = json.loads(raw)
            return data.get("intent", "chat"), data.get("args", {})
        except Exception:
            return "chat", {"message": message}

