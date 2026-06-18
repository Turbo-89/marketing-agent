import os

class ContextBuilder:
    def __init__(self, memory):
        self.memory = memory

        # system_prompt.txt laden
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base, "system_prompt.txt")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except Exception:
            self.system_prompt = "Je bent TurboAgent."

    async def build(self, user_message: str, session_id: str):

        # Historiek ophalen
        history = await self.memory.get_recent(
            session_id=session_id,
            limit=20,
        )

        messages = []

        # 0) SYSTEM PROMPT INJECTEREN
        messages.append(
            {"role": "system", "content": self.system_prompt}
        )

        # 1) Historische context
        for item in history:
            messages.append(
                {
                    "role": item.get("role", "assistant"),
                    "content": item.get("content", ""),
                }
            )

        # 2) Nieuw userbericht
        messages.append(
            {"role": "user", "content": user_message}
        )

        return messages
