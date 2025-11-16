from fastapi import FastAPI
from app.router import router as agent_router

app = FastAPI(title="Turbo Marketing Agent")

app.include_router(agent_router, prefix="/agent", tags=["agent"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
