from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router import router as agent_router

app = FastAPI(
    title="Marketing Agent",
    version="1.0.0"
)

# CORS – veilig default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# >>> BELANGRIJK <<<  
# registreer agent router
app.include_router(agent_router)

@app.get("/")
def root():
    return {"status": "ok", "message": "agent online"}
