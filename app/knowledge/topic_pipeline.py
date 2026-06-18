from __future__ import annotations

import re
from typing import List, Dict, Any

from app.knowledge.topic_rules import (
    COMMERCIAL_TERMS,
    BRAND_BLACKLIST,
    COMPETITOR_GROUPS,
    AD_GROUP_TO_SERVICE,
)


SERVICE_HINTS = {
    "ontstoppingen": [
        "ontstop",
        "verstopping",
        "afvoer",
        "toilet",
        "wc",
        "lavabo",
        "douche",
        "gootsteen",
        "putje",
        "afvoerbuis",
    ],
    "camera-inspectie": [
        "camera inspectie",
        "camera-inspectie",
        "inspectie riolering",
        "riolering inspectie",
        "leidinginspectie",
        "camera",
    ],
    "geurdetectie": [
        "geur",
        "stank",
        "stinkt",
        "rioollucht",
        "rioolgeur",
        "geurhinder",
    ],
    "noodherstellingen": [
        "dringend",
        "spoed",
        "urgent",
        "nood",
        "lek",
        "breuk",
    ],
}


def strip_match_syntax(keyword: str) -> str:
    text = keyword.strip()
    if text.startswith("[") and text.endswith("]"):
        return text[1:-1].strip()
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1].strip()
    return text.strip()


def slugify_keyword(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"[\[\]\"]+", "", text)
    text = text.replace("&", " en ")
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def canonicalize_ad_group(ad_group: str) -> str:
    return ad_group.strip().lower()


def score_service_from_keyword(keyword: str) -> dict[str, int]:
    keyword_l = keyword.lower()
    scores: dict[str, int] = {service: 0 for service in SERVICE_HINTS.keys()}

    for service, hints in SERVICE_HINTS.items():
        for hint in hints:
            if hint in keyword_l:
                scores[service] += len(hint)

    return scores


def is_competitor(row: dict) -> bool:
    ad_group = str(row.get("ad_group") or "").strip().lower()
    return ad_group in COMPETITOR_GROUPS


def is_brand_term(keyword: str) -> bool:
    keyword_l = keyword.lower()
    return any(token in keyword_l for token in BRAND_BLACKLIST)


def guess_service(keyword: str, ad_group: str) -> str:
    ad_group_key = canonicalize_ad_group(ad_group)

    if ad_group_key in AD_GROUP_TO_SERVICE:
        ad_group_service = AD_GROUP_TO_SERVICE[ad_group_key]

        keyword_scores = score_service_from_keyword(keyword)
        best_service = max(keyword_scores, key=keyword_scores.get)
        best_score = keyword_scores[best_service]
        ad_group_score = keyword_scores.get(ad_group_service, 0)

        if best_score >= ad_group_score + 4 and best_score > 0:
            return best_service

        return ad_group_service

    keyword_scores = score_service_from_keyword(keyword)
    best_service = max(keyword_scores, key=keyword_scores.get)

    if keyword_scores[best_service] > 0:
        return best_service

    return "ontstoppingen"


def classify_intent(keyword: str) -> str:
    keyword_l = keyword.lower()
    if any(term in keyword_l for term in COMMERCIAL_TERMS):
        return "commercial"
    return "knowledge"


def build_commercial_topics(rows: List[dict], min_clicks: int) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    for row in rows:
        keyword_raw = str(row.get("keyword") or "").strip()
        keyword = strip_match_syntax(keyword_raw)

        if not keyword:
            continue

        if is_competitor(row):
            continue

        if is_brand_term(keyword):
            continue

        clicks = int(row.get("clicks") or 0)
        impressions = int(row.get("impressions") or 0)

        if clicks < min_clicks:
            continue

        if classify_intent(keyword) != "commercial":
            continue

        slug = slugify_keyword(keyword)
        if not slug:
            continue

        candidates.append(
            {
                "slug": slug,
                "seed_keyword": keyword,
                "service": guess_service(keyword, str(row.get("ad_group") or "")),
                "intent": "commercial",
                "clicks": clicks,
                "impressions": impressions,
                "campaign": str(row.get("campaign") or ""),
                "ad_group": str(row.get("ad_group") or ""),
                "match_type": str(row.get("match_type") or ""),
            }
        )

    deduped: Dict[str, Dict[str, Any]] = {}
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


def filter_knowledge_topics(topics: List[dict]) -> List[dict]:
    filtered = []
    for topic in topics:
        if classify_intent(topic["seed_keyword"]) == "commercial":
            continue
        filtered.append(topic)
    return filtered


def dedupe_and_rank_topics(topics: List[dict], limit: int) -> List[dict]:
    deduped: Dict[str, Dict[str, Any]] = {}

    for item in topics:
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
    )[:limit]