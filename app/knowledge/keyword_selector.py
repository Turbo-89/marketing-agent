from __future__ import annotations

from typing import Any

from app.knowledge.topic_pipeline import (
    strip_match_syntax,
    slugify_keyword,
    is_competitor,
    is_brand_term,
    guess_service,
)


INFORMATIONAL_TOKENS = [
    "waarom",
    "hoe",
    "oorzaak",
    "oorzaken",
    "oplossen",
    "geur",
    "stank",
    "stinkt",
    "rioollucht",
    "rioolgeur",
    "verstopping",
    "ontstoppen",
    "afvoer",
    "riolering",
    "riool",
    "sifon",
    "putje",
    "camera inspectie",
    "camera-inspectie",
]


def is_knowledge_worthy(keyword: str) -> bool:
    keyword_l = keyword.lower()
    return any(token in keyword_l for token in INFORMATIONAL_TOKENS)


class KeywordSelector:
    def select(
        self,
        rows: list[dict[str, Any]],
        limit: int = 10,
        min_clicks: int = 1,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []

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

            if not is_knowledge_worthy(keyword):
                continue

            service = guess_service(keyword, str(row.get("ad_group") or ""))
            slug = slugify_keyword(keyword)

            if not slug:
                continue

            candidates.append(
                {
                    "slug": slug,
                    "seed_keyword": keyword,
                    "service": service,
                    "intent": "kennisbank",
                    "clicks": clicks,
                    "impressions": impressions,
                    "campaign": str(row.get("campaign") or ""),
                    "ad_group": str(row.get("ad_group") or ""),
                    "match_type": str(row.get("match_type") or ""),
                }
            )

        deduped: dict[str, dict[str, Any]] = {}
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

        ordered = sorted(
            deduped.values(),
            key=lambda x: (x["clicks"], x["impressions"]),
            reverse=True,
        )

        return ordered[:limit]