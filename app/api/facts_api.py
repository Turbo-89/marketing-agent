from fastapi import APIRouter, HTTPException
from app.memory.memory_engine import MemoryEngine
from app.agent.facts import FactRegistry

router = APIRouter(prefix="/api", tags=["facts"])

# 🔒 SINGLETONS
memory = MemoryEngine()
memory.initialize()
facts_registry = FactRegistry(memory)

@router.post("/facts/upsert")
def upsert_fact(payload: dict):
    session_id = payload.get("session_id")
    key = payload.get("key")
    value = payload.get("value")
    source = payload.get("source", "user")
    verified = payload.get("verified", True)
    meta = payload.get("meta", {})

    if not session_id or not key:
        raise HTTPException(status_code=400, detail="session_id en key zijn verplicht")

    doc_id = facts_registry.upsert_fact(
        session_id=session_id,
        key=key,
        value=value,
        source=source,
        verified=bool(verified),
        meta=meta if isinstance(meta, dict) else {},
    )

    return {"ok": True, "id": doc_id}

@router.get("/facts/{session_id}")
def list_facts(session_id: str):
    return {"facts": facts_registry.list_facts(session_id, verified_only=False)}

# =========================
# INTERNE HELPER (CRUCIAAL)
# =========================

def get_facts_for_session(session_id: str):
    """
    Wordt gebruikt door RouterEngine.
    BELANGRIJK: gebruikt exact dezelfde FactRegistry.
    """
    return facts_registry.list_facts(session_id, verified_only=True)

