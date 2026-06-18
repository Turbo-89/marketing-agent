from pathlib import Path
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.integrations.ga4_client import GA4Client
from app.knowledge.google_ads_csv_ingest import GoogleAdsCsvIngest
from app.knowledge.keyword_selector import KeywordSelector
from app.knowledge.topic_pipeline import (
    build_commercial_topics,
    filter_knowledge_topics,
    dedupe_and_rank_topics,
)

router = APIRouter()


def _get_turboservices_repo() -> Path:
    base = os.getenv("TURBOSERVICES_REPO_PATH")
    if not base:
        raise RuntimeError("TURBOSERVICES_REPO_PATH ontbreekt.")
    return Path(base).resolve()


class ContentGapRequest(BaseModel):
    csv_path: str | None = None
    limit: int = 30
    min_clicks: int = 1
    ga4_top_limit: int = 100


@router.get("/analysis/content-vs-traffic")
def content_vs_traffic():
    repo = _get_turboservices_repo()
    content_dir = repo / "content" / "kennisbank-auto"

    ga = GA4Client()
    top_pages = ga.get_top_pages(50)

    results = []

    for file in content_dir.glob("*.md"):
        slug = file.stem
        path = f"/kennisbank/auto/{slug}"

        views = 0
        for p in top_pages:
            if p["page_path"] == path:
                views = p["screen_page_views"]
                break

        results.append(
            {
                "slug": slug,
                "type": "existing",
                "page_path": path,
                "views": views,
            }
        )

    return {
        "ok": True,
        "count": len(results),
        "results": sorted(results, key=lambda x: x["views"], reverse=True),
    }


@router.post("/analysis/content-gap")
def content_gap(req: ContentGapRequest):
    try:
        csv_path = req.csv_path or os.getenv("GOOGLE_ADS_CSV_PATH")
        if not csv_path:
            raise RuntimeError("csv_path ontbreekt en GOOGLE_ADS_CSV_PATH is niet ingesteld.")

        repo = _get_turboservices_repo()
        commercial_dir = repo / "content" / "commercial"
        knowledge_dir = repo / "content" / "kennisbank-auto"

        existing_commercial = {p.stem for p in commercial_dir.rglob("*.md")}
        existing_knowledge = {p.stem for p in knowledge_dir.glob("*.md")}

        ingest = GoogleAdsCsvIngest()
        selector = KeywordSelector()

        rows = ingest.load(csv_path)

        knowledge_topics = selector.select(
            rows=rows,
            limit=max(req.limit * 3, 30),
            min_clicks=req.min_clicks,
        )
        knowledge_topics = filter_knowledge_topics(knowledge_topics)

        commercial_topics = build_commercial_topics(
            rows=rows,
            min_clicks=req.min_clicks,
        )

        topics = dedupe_and_rank_topics(
            commercial_topics + knowledge_topics,
            limit=req.limit,
        )

        ga = GA4Client()
        top_pages = ga.get_top_pages(req.ga4_top_limit)
        pageviews_map = {item["page_path"]: item["screen_page_views"] for item in top_pages}

        results = []
        for topic in topics:
            slug = topic["slug"]
            intent = topic["intent"]

            if intent == "commercial":
                exists = slug in existing_commercial
                page_path = None
            else:
                exists = slug in existing_knowledge
                page_path = f"/kennisbank/auto/{slug}"

            results.append(
                {
                    "slug": slug,
                    "seed_keyword": topic["seed_keyword"],
                    "service": topic["service"],
                    "intent": intent,
                    "clicks": topic["clicks"],
                    "impressions": topic["impressions"],
                    "exists": exists,
                    "page_path": page_path,
                    "pageviews": pageviews_map.get(page_path, 0) if page_path else None,
                    "status": "existing" if exists else "missing",
                }
            )

        missing = [r for r in results if r["status"] == "missing"]
        existing = [r for r in results if r["status"] == "existing"]

        return {
            "ok": True,
            "csv_path": csv_path,
            "count": len(results),
            "missing_count": len(missing),
            "existing_count": len(existing),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))