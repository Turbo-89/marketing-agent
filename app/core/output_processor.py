import json
from app.core.tool_output import ToolOutput
from app.integrations.drive_connector import DriveConnector
from app.memory import MemoryEngine

class OutputProcessor:

    def __init__(self, drive: DriveConnector, memory: MemoryEngine):
        self.drive = drive
        self.memory = memory

    def process(self, output: ToolOutput) -> dict:
        # 1. Opslaan in Drive
        drive_path = self._store_in_drive(output)

        # 2. Opslaan in Firestore
        self._store_in_memory(output, drive_path)

        return {
            "ok": True,
            "id": output.id,
            "drive_path": drive_path
        }

    def _store_in_drive(self, output: ToolOutput) -> str:
        folder = f"outputs/{output.tool}"
        filename = f"{output.created_at}_{output.id}.json"

        payload = {
            "tool": output.tool,
            "type": output.type,
            "title": output.title,
            "summary": output.summary,
            "content": output.content,
            "metadata": output.metadata,
            "tags": output.tags,
            "created_at": output.created_at,
        }

        return self.drive.upload_json(
            folder=folder,
            filename=filename,
            data=payload
        )

    def _store_in_memory(self, output: ToolOutput, drive_path: str):
        self.memory.store({
            "id": output.id,
            "tool": output.tool,
            "type": output.type,
            "title": output.title,
            "summary": output.summary,
            "drive_path": drive_path,
            "tags": output.tags,
            "created_at": output.created_at
        })
