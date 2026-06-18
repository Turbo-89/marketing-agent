from typing import Optional, List
from app.memory import MemoryEngine


class MemorySearchTool:
    """
    Tool: [TOOL:memory_search(query="...", limit=5)]
    Doorzoekt sessiesamenvattingen (agent_memory).
    """

    name = "memory_search"

    def __init__(self):
        self.memory = MemoryEngine()

    async def run(self, query: str = "", limit: int = 5, session_id: Optional[str] = None):
        summaries = await self.memory.list_session_summaries(session_id=session_id, limit=50)

        results = []
        for s in summaries:
            score = 0
            if query.lower() in s["summary"].lower():
                score += 10
            if query.lower() in (s["title"] or "").lower():
                score += 5
            if score > 0:
                results.append((score, s))

        results.sort(key=lambda x: -x[0])
        results = [r[1] for r in results[:limit]]

        return {
            "results": [
                {
                    "id": s["id"],
                    "title": s["title"],
                    "summary": s["summary"][:500],
                    "scope": s["scope"],
                    "tags": s["tags"],
                }
                for s in results
            ]
        }
