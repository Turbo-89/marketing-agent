# app/tools/auto_marketing_tool.py

class AutoMarketingTool:
    name = "auto_marketing"

    def __init__(self):
        self.memory = None

    def set_memory(self, memory):
        self.memory = memory

    def run(self, **kwargs):
        if self.memory is None:
            raise RuntimeError("MemoryEngine niet geïnjecteerd in AutoMarketingTool")

        # hier je bestaande logic
        return {
            "status": "ok",
            "message": "Auto marketing executed"
        }
