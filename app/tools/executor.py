class ToolExecutor:
    def __init__(self, memory):
        self.memory = memory

    def run(self, task_id: str, tool_name: str, **kwargs):
        self.memory.log_event(task_id, "tool_start", {
            "tool": tool_name,
            "args": kwargs,
        })

        try:
            # bestaande tool-logica hier
            result = {"ok": True}

            self.memory.log_event(task_id, "tool_end", {
                "tool": tool_name,
                "result": result,
            })
            return result

        except Exception as e:
            self.memory.log_event(task_id, "tool_error", {
                "tool": tool_name,
                "error": str(e),
            })
            raise
