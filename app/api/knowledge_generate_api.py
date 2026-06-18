from __future__ import annotations

import os
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.knowledge.google_ads_csv_ingest import GoogleAdsCsvIngest
from app.knowledge.keyword_selector import KeywordSelector
from app.knowledge.knowledge_generate_preview import KnowledgeGeneratePreview

router = APIRouter()


COMMERCIAL_TERMS = [
    "dienst",
    "service",
    "ontstoppen",
    "ontstoppingsdienst",
    "ruimen",
    "reinigen",
    "inspectie",
    "camera inspectie",
    "herstelling",
    "geurdetectie",
    "noodherstelling",
    "spoed",
    "dringend",
]

BRAND_BLACKLIST = [
    "turbo",
    "turboservices",
]

COMPETITOR_GROUPS = {
    "concurrenten",
}

AD_GROUP_TO_SERVICE = {
    "ontstoppingen": "ontstoppingen",
    "camera-inspectie": "camera-inspectie",
    "geurdetectie": "geurdetectie",
    "noodherstellingen": "noodherstellingen",
}


class KnowledgeGenerateRequest(BaseModel):
    csv_path: str | None = None
    limit: int = 10
    min_clicks: int = 1
    overwrite_generated: bool = True
    overwrite_staged: bool = False
    stage: bool = False


def _strip_match_syntax(keyword: str) -> str:
    text = keyword.strip()
    if text.startswith("[") and text.endswith("]"):
        return text[1:-1].strip()
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1].strip()
    return text.strip()


def _slugify(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"[\[\]\"]+", "", text)
    text = text.replace("&", " en ")
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def _is_competitor(row: dict) -> bool:
    ad_group = str(row.get("ad_group") or "").strip().lower()
    return ad_group in COMPETITOR_GROUPS


def _is_brand_term(keyword: str) -> bool:
    keyword_l = keyword.lower()
    return any(token in keyword_l for token in BRAND_BLACKLIST)


def _guess_service(keyword: str, ad_group: str) -> str:
    ad_group_key = ad_group.strip().lower()
    if ad_group_key in AD_GROUP_TO_SERVICE:
        return AD_GROUP_TO_SERVICE[ad_group_key]

    keyword_l = keyword.lower()
    if any(token in keyword_l for token in ["geur", "stank", "stinkt", "rioolgeur", "rioollucht"]):
        return "geurdetectie"
    if any(token in keyword_l for token in ["camera", "inspectie"]):
        return "camera-inspectie"
    if any(token in keyword_l for token in ["spoed", "dringend", "lek", "breuk", "nood"]):
        return "noodherstellingen"

    return "ontstoppingen"


def classify_intent(keyword: str) -> str:
    keyword_l = keyword.lower()
    if any(term in keyword_l for term in COMMERCIAL_TERMS):
        return "commercial"
    return "knowledge"


def _build_commercial_topics(rows: list[dict], min_clicks: int) -> list[dict]:
    candidates = []

    for row in rows:
        keyword_raw = str(row.get("keyword") or "").strip()
        keyword = _strip_match_syntax(keyword_raw)

        if not keyword:
            continue

        if _is_competitor(row):
            continue

        if _is_brand_term(keyword):
            continue

        clicks = int(row.get("clicks") or 0)
        impressions = int(row.get("impressions") or 0)

        if clicks < min_clicks:
            continue

        if classify_intent(keyword) != "commercial":
            continue

        slug = _slugify(keyword)
        if not slug:
            continue

        candidates.append(
            {
                "slug": slug,
                "seed_keyword": keyword,
                "service": _guess_service(keyword, str(row.get("ad_group") or "")),
                "intent": "commercial",
                "clicks": clicks,
                "impressions": impressions,
                "campaign": str(row.get("campaign") or ""),
                "ad_group": str(row.get("ad_group") or ""),
                "match_type": str(row.get("match_type") or ""),
            }
        )

    deduped = {}
    for item in candidates:
        slug = item["slug"]
        current = deduped.get(slug)
        if current is None:
            deduped[slug] = item
            continue

        if (
            item["clicks"] > current["clicks"]
            or (
                item["clicks"] == current["clicks"]
                and item["impressions"] > current["impressions"]
            )
        ):
            deduped[slug] = item

    return sorted(
        deduped.values(),
        key=lambda x: (x["clicks"], x["impressions"]),
        reverse=True,
    )


def _filter_knowledge_topics(topics: list[dict]) -> list[dict]:
    filtered = []
    for topic in topics:
        if classify_intent(topic["seed_keyword"]) == "commercial":
            continue
        filtered.append(topic)
    return filtered


@router.post("/knowledge/generate-from-csv")
def knowledge_generate_from_csv(req: KnowledgeGenerateRequest):
    try:
        csv_path = req.csv_path or os.getenv("GOOGLE_ADS_CSV_PATH")
        if not csv_path:
            raise ValueError("csv_path ontbreekt en GOOGLE_ADS_CSV_PATH is niet ingesteld.")

        ingest = GoogleAdsCsvIngest()
        selector = KeywordSelector()
        generator = KnowledgeGeneratePreview()

        rows = ingest.load(csv_path)

        knowledge_topics = selector.select(
            rows=rows,
            limit=max(req.limit * 3, 30),
            min_clicks=req.min_clicks,
        )
        knowledge_topics = _filter_knowledge_topics(knowledge_topics)

        commercial_topics = _build_commercial_topics(
            rows=rows,
            min_clicks=req.min_clicks,
        )

        combined = commercial_topics + knowledge_topics

        deduped = {}
        for item in combined:
            slug = item["slug"]
            current = deduped.get(slug)
            if current is None:
                deduped[slug] = item
                continue

            if (
                item["clicks"] > current["clicks"]
                or (
                    item["clicks"] == current["clicks"]
                    and item["impressions"] > current["impressions"]
                )
            ):
                deduped[slug] = item

        topics = sorted(
            deduped.values(),
            key=lambda x: (x["clicks"], x["impressions"]),
            reverse=True,
        )[: req.limit]

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
            "csv_path": csv_path,
            "rows_loaded": len(rows),
            "count": len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))