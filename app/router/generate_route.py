# app/router/generate_route.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.generate_service import GenerateService

router = APIRouter()
service = GenerateService()

class GenerateBody(BaseModel):
    service: str
    region: str

@router.post("/agent/generate")
async def generate_page(body: GenerateBody):
    try:
        result = service.generate(body.service, body.region)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
