import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def log_action(tool_name: str, payload: Dict[str, Any], result: Dict[str, Any]) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / f"actions-{datetime.utcnow().date().isoformat()}.jsonl"

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool_name,
        "payload": payload,
        "result": result,
    }

    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
