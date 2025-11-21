from fastapi import APIRouter
from pydantic import BaseModel

from app.website_generator import WebsiteGenerator
from app.tools_router import ToolsRouter
from app.services.deploy_service import DeployService

class GenerateRequest(BaseModel):
    service: str
    region: str

class DeployRequest(BaseModel):
    service: str
    region: str

class RouterEngine:
    def __init__(self):
        self.router = APIRouter()
        self.tools = ToolsRouter()

        # officiële API’s
        self.router.post("/chat")(self.tools.chat)
        self.router.post("/generate")(self.generate_page)
        self.router.post("/video")(self.tools.video)
        self.router.post("/deploy")(self.deploy)

        # alias routes
        aliases = [
            "/agent/chat", "/api/chat", "/api/agent/chat",
            "/agent/generate", "/api/generate", "/api/agent/generate",
            "/agent/video", "/api/video", "/api/agent/video",
            "/agent/deploy", "/api/deploy", "/api/agent/deploy",
        ]

        for alias in aliases:
            if "chat" in alias:
                self.router.post(alias)(self.tools.chat)
            elif "generate" in alias:
                self.router.post(alias)(self.generate_page)
            elif "video" in alias:
                self.router.post(alias)(self.tools.video)
            elif "deploy" in alias:
                self.router.post(alias)(self.deploy)

    # -------------------------------------------------
    # Handlers
    # -------------------------------------------------
    def generate_page(self, req: GenerateRequest):
        gen = WebsiteGenerator()
        return gen.generate_page(req.service, req.region)

    def deploy(self, req: DeployRequest):
        d = DeployService("Turbo-89", "turboservices")
        return d.deploy_page(req.service, req.region)

