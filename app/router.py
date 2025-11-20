from fastapi import APIRouter
from pydantic import BaseModel
from app.tools.website import WebsiteGenerator
from app.services.deploy_service import DeployService


router = APIRouter(prefix="/agent")


class GenerateRequest(BaseModel):
    service: str
    region: str


class DeployRequest(BaseModel):
    service: str
    region: str


@router.post("/test-generate")
def test_generate(req: GenerateRequest):
    wg = WebsiteGenerator()
    content = wg.generate_page(req.service, req.region)
    path = wg.write_page_to_disk(req.service, req.region, content)
    return {"status": "ok", "path": path}


@router.post("/deploy")
def deploy(req: DeployRequest):
    deployer = DeployService("Turbo-89", "turboservices")
    return deployer.deploy_page(req.service, req.region)
