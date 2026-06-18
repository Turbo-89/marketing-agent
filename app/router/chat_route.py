from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.router.engine import RouterEngine
from app.memory import MemoryEngine
from app.router.streaming import StreamingPipeline

router = APIRouter()

@router.post("/chat-stream")
async def chat_stream(request: Request):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")

    memory = MemoryEngine()
    engine = RouterEngine(memory)
    pipeline = StreamingPipeline(engine)

    async def generator():
        async for token in pipeline.stream(message, session_id=session_id):
            yield token
        yield StreamingPipeline.end()

    return StreamingResponse(generator(), media_type="text/event-stream")
