from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.config import get_business_config
from app.services.openai_client import call_planning_agent
from app.tools.content import generate_page_content_ai
from app.tools.website import create_or_update_page_in_repo, build_page_path


router = APIRouter()


class PlanRequest(BaseModel):
    goal: str
class GeneratePagesRequest(BaseModel):
    services: Optional[List[str]] = None   # bv. ["ontstopping", "camera-inspectie"]
    regions: Optional[List[str]] = None    # bv. ["antwerpen", "mechelen"]
    execute: bool = False                  # False = alleen plan (dry-run), True = effectief committen



@router.post("/plan")
async def plan_endpoint(req: PlanRequest):
    """
    Basis-endpoint: stuurt jouw doel + businessconfig naar de planning-agent.
    Voor nu: alleen een plan terug als JSON, geen acties.
    """
    cfg = get_business_config()
    result = await call_planning_agent(goal=req.goal, business_config=cfg)
    return result
@router.post("/generate-pages")
async def generate_pages(req: GeneratePagesRequest):
    """
    Genereer content voor combinaties van diensten en regio's.
    - execute = False: alleen plan (geen GitHub-commits)
    - execute = True: pagina's worden aangemaakt/geüpdatet in turbosoervices via GitHub
    """
    cfg = get_business_config()

    # Diensten selecteren
    service_map = {s.key: s for s in cfg.services}
    if req.services:
        selected_services = [
            service_map[key]
            for key in req.services
            if key in service_map
        ]
    else:
        selected_services = cfg.services

    # Regio's selecteren
    if req.regions:
        selected_regions = req.regions
    else:
        selected_regions = cfg.regions

    results = []

    for service in selected_services:
        for region in selected_regions:
            content = generate_page_content_ai(service, region, cfg)
            path = build_page_path(service, region, cfg)

            if req.execute:
                write_result = create_or_update_page_in_repo(
                    service=service,
                    region=region,
                    business_config=cfg,
                    content=content,
                )
            else:
                write_result = None

            results.append(
                {
                    "service_key": service.key,
                    "service_name": service.name,
                    "region": region,
                    "path": path,
                    "content": content if not req.execute else None,
                    "write_result": write_result,
                }
            )

    return {
        "execute": req.execute,
        "count": len(results),
        "items": results,
    }

