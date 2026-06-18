from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.autonomy.task_registry import TaskRegistry

router = APIRouter(prefix="/agent/autonomy", tags=["Autonomy"])

@router.get("/list")
async def list_tasks():
    registry = TaskRegistry()
    return {"tasks": registry.list()}


@router.post("/run/{task_name}")
async def run_single(task_name: str):
    try:
        registry = TaskRegistry()
        result = await registry.run(task_name)
        return JSONResponse({"status": "OK", "task": task_name, "result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run_all")
async def run_all_tasks():
    registry = TaskRegistry()
    result = await registry.run_all()
    return JSONResponse({"status": "OK", "results": result})
