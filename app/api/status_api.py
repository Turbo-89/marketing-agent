from fastapi import APIRouter
from app.memory.memory_engine import MemoryEngine

router = APIRouter(prefix="/api", tags=["status"])
memory = MemoryEngine()
memory.initialize()

@router.get("/status/{session_id}")
def status(session_id: str):
    memory.get_or_create_session(session_id)
    sess = memory.client.collection("sessions").document(session_id).get().to_dict() or {}
    task_id = sess.get("current_task_id")

    if not task_id:
        return {"status": "idle"}

    task = memory.client.collection("tasks").document(task_id).get().to_dict() or {}
    return {
        "task_id": task_id,
        "status": task.get("status"),
        "step": task.get("step"),
        "type": task.get("type"),
        "updated_at": str(task.get("updated_at")),
    }
