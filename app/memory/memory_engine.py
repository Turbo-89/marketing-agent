import os
from datetime import datetime
from uuid import uuid4
from typing import List, Optional, Dict, Any

from google.cloud import firestore
from google.oauth2 import service_account


def _build_firestore_client(project_id: Optional[str] = None) -> firestore.Client:
    service_account_path = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_PATH",
        os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS",
            os.path.join("config", "service_account.json"),
        ),
    )

    credentials = service_account.Credentials.from_service_account_file(
        service_account_path
    )

    if project_id:
        return firestore.Client(project=project_id, credentials=credentials)

    return firestore.Client(credentials=credentials)


class MemoryEngine:
    """
    Firestore-gebaseerd geheugen voor TurboAgent.

    Collecties:
    - sessions        : actieve sessies + huidige task
    - tasks           : task lifecycle (created/running/completed/failed)
    - events          : tool-events per task
    - ai_logs         : ruwe chatberichten (kortetermijn)
    - agent_memory    : langetermijn-samenvattingen
    - documents       : Drive-document index + metadata
    """

    def __init__(self):
        self.project_id = os.getenv("FIRESTORE_PROJECT_ID")
        self.client: Optional[firestore.Client] = None

        self.sessions_col = "sessions"
        self.tasks_col = "tasks"
        self.events_col = "events"

        self.logs_col = "ai_logs"
        self.memory_col = "agent_memory"
        self.docs_col = "documents"

    def initialize(self):
        """Initialiseer Firestore client éénmalig."""
        if self.client:
            return

        self.client = _build_firestore_client(self.project_id)

    def get_or_create_session(self, session_id: str) -> None:
        if not self.client:
            self.initialize()

        ref = self.client.collection(self.sessions_col).document(session_id)
        snap = ref.get()

        if not snap.exists:
            ref.set(
                {
                    "created_at": datetime.utcnow(),
                    "last_seen": datetime.utcnow(),
                    "current_task_id": None,
                }
            )
        else:
            ref.update({"last_seen": datetime.utcnow()})

    def create_task(self, session_id: str, task_type: str) -> str:
        if not self.client:
            self.initialize()

        task_id = str(uuid4())

        self.client.collection(self.tasks_col).document(task_id).set(
            {
                "session_id": session_id,
                "type": task_type,
                "status": "created",
                "step": None,
                "started_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "result": None,
            }
        )

        self.client.collection(self.sessions_col).document(session_id).update(
            {"current_task_id": task_id}
        )

        return task_id

    def update_task(
        self,
        task_id: str,
        *,
        status: Optional[str] = None,
        step: Optional[str] = None,
        result: Optional[Any] = None,
    ) -> None:
        if not self.client:
            self.initialize()

        payload = {"updated_at": datetime.utcnow()}
        if status:
            payload["status"] = status
        if step:
            payload["step"] = step
        if result is not None:
            payload["result"] = result

        self.client.collection(self.tasks_col).document(task_id).update(payload)

    def log_event(self, task_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.client:
            self.initialize()

        self.client.collection(self.events_col).add(
            {
                "task_id": task_id,
                "type": event_type,
                "payload": payload,
                "timestamp": datetime.utcnow(),
            }
        )

    async def log_message(self, session_id: str, role: str, content: str) -> None:
        if not self.client:
            self.initialize()

        self.client.collection(self.logs_col).add(
            {
                "session_id": session_id,
                "role": role,
                "content": content,
                "timestamp": firestore.SERVER_TIMESTAMP,
            }
        )

    async def get_recent(
        self,
        session_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        if not self.client:
            self.initialize()

        query = (
            self.client.collection(self.logs_col)
            .where("session_id", "==", session_id)
            .order_by("timestamp", direction=firestore.Query.ASCENDING)
            .limit(limit)
        )

        out: List[Dict[str, Any]] = []
        for d in query.stream():
            data = d.to_dict()
            out.append(
                {
                    "role": data.get("role", ""),
                    "content": data.get("content", ""),
                }
            )

        return out

    async def fetch_session_logs(self, session_id: str) -> str:
        if not self.client:
            self.initialize()

        query = (
            self.client.collection(self.logs_col)
            .where("session_id", "==", session_id)
            .order_by("timestamp")
        )

        lines = []
        for d in query.stream():
            data = d.to_dict()
            lines.append(f"{data.get('role')}: {data.get('content')}")

        return "\n".join(lines)

    async def store_session_summary(
        self,
        session_id: str,
        summary: str,
        *,
        title: Optional[str] = None,
        scope: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        if not self.client:
            self.initialize()

        ref = self.client.collection(self.memory_col).document()
        ref.set(
            {
                "session_id": session_id,
                "title": title,
                "summary": summary,
                "scope": scope or "conversation",
                "tags": tags or [],
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )

        return ref.id

    async def list_session_summaries(
        self,
        session_id: str,
        *,
        scope: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        if not self.client:
            self.initialize()

        query = self.client.collection(self.memory_col).where(
            "session_id", "==", session_id
        )

        if scope:
            query = query.where("scope", "==", scope)

        query = query.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        ).limit(limit)

        out: List[Dict[str, Any]] = []
        for d in query.stream():
            data = d.to_dict()
            data["id"] = d.id
            out.append(data)

        return out

    async def list_unprocessed_sessions(self, limit: int = 10) -> List[str]:
        if not self.client:
            self.initialize()

        logs = self.client.collection(self.logs_col).stream()
        sessions = {
            d.to_dict().get("session_id")
            for d in logs
            if d.to_dict().get("session_id")
        }

        summaries = self.client.collection(self.memory_col).stream()
        summarized = {d.to_dict().get("session_id") for d in summaries}

        pending = [sid for sid in sessions if sid and sid not in summarized]
        return pending[:limit]

    async def index_document(
        self,
        session_id: str,
        drive_file_id: str,
        filename: str,
        drive_path: Optional[str],
        mime_type: Optional[str],
        summary: str,
        tags: Optional[List[str]] = None,
    ) -> str:
        if not self.client:
            self.initialize()

        ref = self.client.collection(self.docs_col).document()
        ref.set(
            {
                "session_id": session_id,
                "drive_file_id": drive_file_id,
                "filename": filename,
                "drive_path": drive_path,
                "mime_type": mime_type,
                "summary": summary,
                "tags": tags or [],
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )

        return ref.id

    async def list_documents(
        self,
        *,
        session_id: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        if not self.client:
            self.initialize()

        query = self.client.collection(self.docs_col)

        if session_id:
            query = query.where("session_id", "==", session_id)
        if tag:
            query = query.where("tags", "array_contains", tag)

        query = query.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        ).limit(limit)

        out: List[Dict[str, Any]] = []
        for d in query.stream():
            data = d.to_dict()
            data["id"] = d.id
            out.append(data)

        return out

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            self.initialize()

        ref = self.client.collection(self.docs_col).document(doc_id)
        snap = ref.get()

        if not snap.exists:
            return None

        data = snap.to_dict()
        data["id"] = snap.id
        return data