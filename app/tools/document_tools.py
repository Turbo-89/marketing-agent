from typing import Optional, List
from app.memory import MemoryEngine


class DocsSearchTool:
    """
    Tool: [TOOL:docs_search(query="...", limit=5)]
    Doorzoekt de inhoudelijke samenvattingen en metadata van documenten.
    """

    name = "docs_search"

    def __init__(self):
        self.memory = MemoryEngine()

    async def run(self, query: str = "", limit: int = 5, session_id: Optional[str] = None):
        docs = await self.memory.list_documents(session_id=session_id, limit=50)

        # eenvoudige scoring: match query in filename of summary
        results = []
        for d in docs:
            score = 0
            if query.lower() in d["filename"].lower():
                score += 5
            if query.lower() in d["summary"].lower():
                score += 10
            if score > 0:
                results.append((score, d))

        results.sort(key=lambda x: -x[0])
        results = [r[1] for r in results[:limit]]

        return {
            "results": [
                {
                    "id": d["id"],
                    "filename": d["filename"],
                    "mime_type": d["mime_type"],
                    "summary": d["summary"][:500],
                }
                for d in results
            ]
        }


class DocsGetTool:
    """
    Tool: [TOOL:docs_get(id="...")]
    Haalt documentmetadata + samenvatting op.
    """

    name = "docs_get"

    def __init__(self):
        self.memory = MemoryEngine()

    async def run(self, id: str):
        doc = await self.memory.get_document(id)
        if not doc:
            return {"error": f"Document {id} bestaat niet."}

        return {
            "id": doc["id"],
            "filename": doc["filename"],
            "mime_type": doc["mime_type"],
            "summary": doc["summary"],
            "drive_file_id": doc["drive_file_id"],
        }
