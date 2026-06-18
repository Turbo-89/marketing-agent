from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.integrations.ga4_client import GA4Client

router = APIRouter()


class GA4TopPagesRequest(BaseModel):
    limit: int = 10
    start_date: str = "30daysAgo"
    end_date: str = "today"


class GA4PageViewsRequest(BaseModel):
    page_path: str
    start_date: str = "30daysAgo"
    end_date: str = "today"


@router.post("/ga4/top-pages")
def ga4_top_pages(req: GA4TopPagesRequest):
    try:
        client = GA4Client()
        results = client.get_top_pages(
            limit=req.limit,
            start_date=req.start_date,
            end_date=req.end_date,
        )
        return {
            "ok": True,
            "property_id": client.property_id,
            "count": len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ga4/pageviews")
def ga4_pageviews(req: GA4PageViewsRequest):
    try:
        client = GA4Client()
        value = client.get_pageviews(
            page_path=req.page_path,
            start_date=req.start_date,
            end_date=req.end_date,
        )
        return {
            "ok": True,
            "property_id": client.property_id,
            "page_path": req.page_path,
            "screen_page_views": value,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))