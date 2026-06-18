from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime
import uuid

@dataclass
class ToolOutput:
    tool: str
    type: str                  # report | insight | asset | log
    title: str
    summary: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
