# app/api/agent_api.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.website import WebsiteGenerator
from app.services.deploy_service import DeployService
from app.tools.content_engine import ContentEngine


router = APIRouter(prefix="/agent", tags=["marketing-agent"])


# ---------------------------
# Modellen
# ---------------------------
class GenerateRequest(BaseModel):
    service: str
    region: str


class DeployRequest(BaseModel):
    service: str
    region: str


# ---------------------------
# 1. /agent/generate
# ---------------------------
@router.post("/generate")
def generate_page(req: GenerateRequest):
    try:
        generator = WebsiteGenerator()

        # 1) content genereren + tsx string
        tsx = generator.generate_page(req.service, req.region)

        # 2) lokaal opslaan
        page_path = generator.write_page_to_disk(
            req.service, req.region, tsx
        )

        return {
            "status": "ok",
            "service": req.service,
            "region": req.region,
            "page_file": page_path,        # lokaal pad
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------------------------
# 2. /agent/deploy
# ---------------------------
# ---------------------------
# 2. /agent/deploy
# ---------------------------
from app.services.deploy_policy import deploy_mode

@router.post("/deploy")
def deploy_page(req: DeployRequest):
    # Policy check per request
    mode = deploy_mode()
    if mode == "local":
        raise HTTPException(
            status_code=403,
            detail="Deploy mode=local: GitHub push is uitgeschakeld (stage lokaal en push manueel)"
        )

    try:
        deployer = DeployService(
            owner="Turbo-89",
            repo="turboservices",
            branch="main",
        )

        result = deployer.deploy_page(req.service, req.region)

        return {
            "status": "ok",
            "service": req.service,
            "region": req.region,
            "github_file": result["github_file"],
            "local_file": result["local_file"],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# ---------------------------
# 3. /agent/services
# ---------------------------
@router.get("/services")
def list_services():
    ce = ContentEngine()
    return {
        "services": sorted(ce.services.keys())
    }


# ---------------------------
# 4. /agent/regions
# ---------------------------
@router.get("/regions")
def list_regions():
    ce = ContentEngine()
    return {
        "regions": sorted([r["slug"] for r in ce.regions])
    }

