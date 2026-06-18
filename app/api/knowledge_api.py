from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.knowledge.google_ads_csv_ingest import GoogleAdsCsvIngest
from app.knowledge.google_ads_live_ingest import GoogleAdsLiveIngest
from app.knowledge.keyword_selector import KeywordSelector
from app.knowledge.knowledge_generate_preview import KnowledgeGeneratePreview
from app.knowledge.topic_pipeline import (
    build_commercial_topics,
    filter_knowledge_topics,
    dedupe_and_rank_topics,
)

router = APIRouter()


class KnowledgeGenerateRequest(BaseModel):
    source: str = "csv"  # csv | ads
    csv_path: str | None = None
    limit: int = 10
    min_clicks: int = 1
    overwrite_generated: bool = True
    overwrite_staged: bool = False
    stage: bool = False
    ads_limit: int = 500
    include_paused: bool = False


def _load_rows(req: KnowledgeGenerateRequest) -> tuple[list[dict], str]:
    if req.source == "csv":
        csv_path = req.csv_path or os.getenv("GOOGLE_ADS_CSV_PATH")
        if not csv_path:
            raise ValueError("csv_path ontbreekt en GOOGLE_ADS_CSV_PATH is niet ingesteld.")

        ingest = GoogleAdsCsvIngest()
        rows = ingest.load(csv_path)
        return rows, csv_path

    if req.source == "ads":
        ingest = GoogleAdsLiveIngest()
        rows = ingest.load(
            limit=req.ads_limit,
            min_clicks=req.min_clicks,
            include_paused=req.include_paused,
        )
        return rows, "google_ads_api"

    raise ValueError("source moet 'csv' of 'ads' zijn.")


@router.post("/knowledge/generate")
def knowledge_generate(req: KnowledgeGenerateRequest):
    try:
        selector = KeywordSelector()
        generator = KnowledgeGeneratePreview()

        rows, source_label = _load_rows(req)

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

        results = []
        for topic in topics:
            generated = generator.generate_one(
                topic=topic,
                overwrite_generated=req.overwrite_generated,
                overwrite_staged=req.overwrite_staged,
                stage=req.stage,
            )
            results.append(generated)

        return {
            "ok": True,
            "source": req.source,
            "source_label": source_label,
            "rows_loaded": len(rows),
            "count": len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/knowledge/generate-from-csv")
def knowledge_generate_from_csv(req: KnowledgeGenerateRequest):
    req.source = "csv"
    return knowledge_generate(req)