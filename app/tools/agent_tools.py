from fastapi import APIRouter
from app.services.output_parser import OutputParser
from app.services.deploy_service import DeployService
from app.services.github_client import get_github_client_from_env

router = APIRouter()


# TOOL 1 — Opslaan van agent-output
@router.post("/tool/save-output")
def save_output(payload: dict):
    """
    Opslaan van:
    - landing_page (.tsx)
    - hero_image (.png)
    - marketing_plan (.json)
    """
    result = OutputParser.process(payload)
    return {"status": "ok", "result": result}


# TOOL 2 — Deploy naar GitHub
@router.post("/tool/deploy")
def deploy(payload: dict):
    slug = payload.get("slug")
    page_path = payload.get("page_path")
    image_path = payload.get("image_path")

    owner = "WimVerloo"
    repo = "turboservices-main"
    deployer = DeployService(owner, repo)

    out = {}

    if page_path:
        out["page"] = deployer.deploy_page(slug, page_path)

    if image_path:
        out["hero"] = deployer.deploy_hero(slug, image_path)

    return {"status": "ok", "result": out}
