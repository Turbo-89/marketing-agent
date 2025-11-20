import openai
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SYSTEM_PROMPT = (BASE_DIR / "prompts" / "agent_system_prompt.txt").read_text(encoding="utf-8")

class MarketingAgent:
    """
    Roept de OpenAI agent aan met de system prompt.
    """

    def run(self, user_input: str):
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message
