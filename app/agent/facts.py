from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime


class FactRegistry:
    """
    Opslag van geverifieerde feiten per session_id.
    Verified facts mogen gebruikt worden in analyses.
    Unverified facts mogen NIET gebruikt worden.

    Firestore collection: agent_facts
    """

    REQUIRED_FACTS = [
        "services_offered",
        "geographic_scope",
        "target_customers",
        "existing_channels",
    ]

    def __init__(self, memory_engine):
        # memory_engine = MemoryEngine()
        self.memory = memory_engine
        if not self.memory.client:
            self.memory.initialize()
        self.col = self.memory.client.collection("agent_facts")

    def upsert_fact(
        self,
        session_id: str,
        key: str,
        value: Any,
        *,
        source: str,
        verified: bool,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Upsert per (session_id, key) zodat er 1 waarheid per key bestaat.
        """
        query = (
            self.col.where("session_id", "==", session_id)
            .where("key", "==", key)
            .limit(1)
        )
        docs = list(query.stream())

        payload = {
            "session_id": session_id,
            "key": key,
            "value": value,
            "source": source,  # user | verified_web | document
            "verified": verified,
            "meta": meta or {},
            "updated_at": datetime.utcnow(),
        }

        if docs:
            doc_id = docs[0].id
            self.col.document(doc_id).set(payload, merge=True)
            return doc_id

        payload["created_at"] = datetime.utcnow()
        ref = self.col.document()
        ref.set(payload)
        return ref.id

    def list_facts(self, session_id: str, *, verified_only: bool = True) -> List[Dict[str, Any]]:
        q = self.col.where("session_id", "==", session_id)
        out: List[Dict[str, Any]] = []
        for d in q.stream():
            data = d.to_dict()
            if verified_only and not data.get("verified"):
                continue
            data["id"] = d.id
            out.append(data)
        return out

    def get_verified_facts_map(self, session_id: str) -> Dict[str, Any]:
        facts = self.list_facts(session_id, verified_only=True)
        return {f["key"]: f.get("value") for f in facts if f.get("key")}

    def missing_required(self, session_id: str) -> List[str]:
        facts_map = self.get_verified_facts_map(session_id)
        return [k for k in self.REQUIRED_FACTS if k not in facts_map]
