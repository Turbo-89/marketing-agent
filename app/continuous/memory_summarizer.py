from app.router.llm_router import LLMRouter


class MemorySummarizer:

    def __init__(self):
        self.llm = LLMRouter()

    async def summarize(self, session_id: str, full_text: str) -> str:
        prompt = f"""
Vat deze sessie samen in één compacte, feitelijke samenvatting.

Alle irrelevante tekst moet verdwijnen. 
Behoud alleen juridisch/technisch belangrijke feiten.

Sessie ID: {session_id}

Conversatie:

{full_text[:20000]}

"""
        messages = [{"role": "user", "content": prompt}]
        output = ""

        async for token in self.llm.stream(messages):
            output += token

        return output.strip()
