
import os
from dotenv import load_dotenv

# ===============================================================
# 1. ENV LADEN (absolute pad, altijd correct, Windows-proof)
# ===============================================================

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# ===============================================================
# 2. FASTAPI & MODELS
# ===============================================================

from fastapi import FastAPI
from pydantic import BaseModel

# ===============================================================
# 3. IMPORTS VAN JOUW AGENTS (pas NA load_dotenv)
# ===============================================================

from app.website_generator import WebsiteGenerator
from app.seo_manager import SEOManager
from app.video.video_generator import VideoGenerator
from app.autonomy.deploy_agent import DeployAgent

# ===============================================================
# 4. APP INITIALISATIE + AGENTS
# ===============================================================

app = FastAPI()

gen = WebsiteGenerator()
seo = SEOManager()
video = VideoGenerator()
deploy = DeployAgent()

# ===============================================================
# 5. REQUEST MODELS
# ===============================================================

class ChatReq(BaseModel):
    message: str

class ActionReq(BaseModel):
    endpoint: str
    args: dict | None = None

# ===============================================================
# 6. ROUTES
# ===============================================================

@app.post("/chat")
def chat(req: ChatReq):
    return {"reply": f"Ontvangen: {req.message}"}

@app.post("/generate")
def generate_api():
    return gen.generate_page("ontstoppingen", "antwerpen-stad")

@app.post("/seo")
def seo_api():
    return {"status": "SEO OK"}

@app.post("/video")
def video_api():
    file_path = video.generate_promo("ontstoppingen", "antwerpen-stad")
    return {"file": file_path}

@app.post("/deploy")
def deploy_api():
    return deploy.deploy()

@app.get("/logs")
def logs_api():
    with open("generated/logs/continuous.log") as f:
        return {"log": f.read()}
