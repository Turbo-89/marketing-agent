from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.knowledge.google_ads_csv_ingest import GoogleAdsCsvIngest
from app.knowledge.keyword_selector import KeywordSelector
from app.knowledge.topic_pipeline import filter_knowledge_topics

router = APIRouter()


class KnowledgePreviewRequest(BaseModel):
    csv_path: str | None = None
    limit: int = 10
    min_clicks: int = 1


@router.post("/knowledge/preview-from-csv")
def knowledge_preview_from_csv(req: KnowledgePreviewRequest):
    try:
        csv_path = req.csv_path or os.getenv("GOOGLE_ADS_CSV_PATH")
        if not csv_path:
            raise ValueError("csv_path ontbreekt en GOOGLE_ADS_CSV_PATH is niet ingesteld.")

        ingest = GoogleAdsCsvIngest()
        selector = KeywordSelector()

        rows = ingest.load(csv_path)
        topics = selector.select(
            rows=rows,
            limit=max(req.limit * 3, 30),
            min_clicks=req.min_clicks,
        )

        topics = filter_knowledge_topics(topics)[: req.limit]

        return {
            "ok": True,
            "csv_path": csv_path,
            "rows_loaded": len(rows),
            "count": len(topics),
            "results": topics,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))