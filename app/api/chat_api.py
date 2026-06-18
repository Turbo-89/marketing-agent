from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api")

@router.post("/chat")
async def chat(request: Request):
    payload = await request.json()

    session_id = payload.get("session_id")
    message = payload.get("message")

    if not session_id or not message:
        return JSONResponse(
            status_code=400,
            content={"error": "session_id en message zijn verplicht"},
        )

    router_engine = request.app.state.router_engine

    result = await router_engine.handle(
        session_id=session_id,
        message=message,
    )

    return JSONResponse(result)
