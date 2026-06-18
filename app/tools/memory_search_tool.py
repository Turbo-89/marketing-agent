from app.memory import MemoryEngine

class MemorySearchTool:
    name = "memory_search"

    async def run(self, query: str):
        memory = MemoryEngine()
        results = await memory.search(query)
        return {
            "query": query,
            "results": results
        }
