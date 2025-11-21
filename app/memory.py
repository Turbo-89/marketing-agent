# app/memory.py
# ----------------------------------------------------
# TURBO MEMORY ENGINE – FIRESTORE
# ----------------------------------------------------
# Centrale geheugenmanager voor de Marketing Agent.
# Functies:
#   - Intent logging
#   - Chat history opslaan
#   - Document metadata opslaan + koppelen
#   - Error logging
#   - Memory search
#   - Drive-connector integratie
# ----------------------------------------------------

import os
import uuid
import datetime
import firebase_admin
from firebase_admin import credentials, firestore


class MemoryEngine:
    def __init__(self):
        # --------------------------------------------
        # FIREBASE INITIALISATIE
        # --------------------------------------------
        service_path = os.path.join(os.getcwd(), "service_account.json")

        if not firebase_admin._apps:
            cred = credentials.Certificate(service_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

    # ------------------------------------------------
    # INTERNE HELPERS
    # ------------------------------------------------
    def _now(self):
        return datetime.datetime.utcnow()

    def _new_id(self):
        return str(uuid.uuid4())

    # ------------------------------------------------
    # SESSIE MANAGEMENT
    # ------------------------------------------------
    def start_session(self) -> str:
        """Start een nieuwe AI-geheugensessie."""
        sid = self._new_id()
        self.db.collection("memory_sessions").document(sid).set({
            "created": self._now(),
            "messages": [],
        })
        return sid

    def append_message(self, session_id: str, role: str, content: str):
        """Voegt een chatbericht toe aan een sessie."""
        ref = self.db.collection("memory_sessions").document(session_id)
        ref.update({
            "messages": firestore.ArrayUnion([{
                "role": role,
                "content": content,
                "timestamp": self._now()
            }])
        })

    def get_session(self, session_id: str):
        """Haalt één sessie op."""
        doc = self.db.collection("memory_sessions").document(session_id).get()
        return doc.to_dict() if doc.exists else None

    # ------------------------------------------------
    # INTENT LOGGING
    # ------------------------------------------------
    def record_intent(self, intent: str, args: dict):
        iid = self._new_id()
        self.db.collection("intents").document(iid).set({
            "intent": intent,
            "args": args,
            "timestamp": self._now()
        })
        return iid

    # ------------------------------------------------
    # DOCUMENT OPSLAG (metadata)
    # ------------------------------------------------
    def save_document_metadata(self, *, filename: str, mime: str, size: int,
                               local_path: str = None, drive_file_id: str = None,
                               tags=None):
        if tags is None:
            tags = []

        doc_id = self._new_id()
        self.db.collection("documents").document(doc_id).set({
            "filename": filename,
            "mime": mime,
            "size": size,
            "local_path": local_path,
            "drive_file_id": drive_file_id,
            "tags": tags,
            "timestamp": self._now()
        })
        return doc_id

    def link_document_to_memory(self, memory_id: str, document_id: str):
        self.db.collection("memory_sessions").document(memory_id).update({
            "documents": firestore.ArrayUnion([document_id])
        })

    # ------------------------------------------------
    # ERROR LOGGING
    # ------------------------------------------------
    def record_error(self, message: str, trace: str = None, meta: dict = None):
        eid = self._new_id()
        self.db.collection("errors").document(eid).set({
            "message": message,
            "trace": trace,
            "meta": meta or {},
            "timestamp": self._now()
        })
        return eid

    # ------------------------------------------------
    # SEARCH — eenvoudige tekstfilter
    # ------------------------------------------------
    def search_memory(self, query: str):
        """Zoekt intents + documenten + sessies op basis van tags of content."""
        results = {
            "intents": [],
            "documents": [],
            "sessions": []
        }

        # intents
        intents = self.db.collection("intents").stream()
        for i in intents:
            data = i.to_dict()
            if query.lower() in str(data).lower():
                results["intents"].append(data)

        # documents
        docs = self.db.collection("documents").stream()
        for d in docs:
            data = d.to_dict()
            if query.lower() in str(data).lower():
                results["documents"].append(data)

        # sessions
        sessions = self.db.collection("memory_sessions").stream()
        for s in sessions:
            data = s.to_dict()
            if query.lower() in str(data).lower():
                results["sessions"].append(data)

        return results
