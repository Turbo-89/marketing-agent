# app/router/deploy_route.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.deploy_service import DeployService

# ----------------------------------------------------
# Request schema
# ----------------------------------------------------

class DeployRequest(BaseModel):
    service: str
    region: str
    page_path: str | None = None


# ----------------------------------------------------
# Router
# ----------------------------------------------------

router = APIRouter(prefix="/agent", tags=["Agent Deploy"])

@router.post("/deploy")
def deploy_page(req: DeployRequest):
    """
    Verplicht endpoint voor automatische GitHub deploy naar turboservices.
    - Vraagt service + regio
    - Laadt DeployService (die services.json en regions.json gebruikt)
    - Zoekt gegenereerde page.tsx in /generated/pages
    - Commit naar GitHub via GitHub API (upsert)
    """

    try:
        service = req.service
        region = req.region
        page_path = req.page_path  # optioneel

        # ACTUELE waarden → JA, owner en repo invullen
        deployer = DeployService(
            owner="Turbo-89",
            repo="turboservices",
            branch="main"
        )

        result = deployer.deploy_page(
            service=service,
            region=region,
            page_path=page_path
        )

        return JSONResponse({"status": "OK", "deployed": result})

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deploy fout: {str(e)}")
