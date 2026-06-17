from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.integrations.service_intent import resolve_service_intent

router = APIRouter()

BROAD_RESEARCH_QUERIES = [
    {
        "query": "AI search updates SEO impact",
        "purpose": "Track how AI search behavior may affect organic visibility.",
        "category": "ai_search",
    },
    {
        "query": "Google AI Overviews SEO updates",
        "purpose": "Identify changes in AI Overviews that may affect landing pages.",
        "category": "ai_search",
    },
    {
        "query": "Google SEO updates local services",
        "purpose": "Monitor broad Google SEO changes for local service businesses.",
        "category": "seo",
    },
    {
        "query": "local SEO Google Business Profile updates",
        "purpose": "Find local SEO and profile changes relevant to service-area businesses.",
        "category": "local_seo",
    },
    {
        "query": "schema.org Service LocalBusiness structured data updates",
        "purpose": "Check whether Service or LocalBusiness schema should be adjusted.",
        "category": "structured_data",
    },
    {
        "query": "Google Ads changes local services keywords",
        "purpose": "Track ad platform changes that may affect service keywords and negatives.",
        "category": "ads",
    },
    {
        "query": "conversion focused landing pages local service SEO",
        "purpose": "Find content strategy patterns for higher-converting service pages.",
        "category": "content_strategy",
    },
]

SOURCE_CATEGORIES = [
    {
        "name": "Official search platform updates",
        "purpose": "Confirm changes from primary Google Search, Ads, and Business Profile sources.",
    },
    {
        "name": "Structured data references",
        "purpose": "Check schema.org and Google documentation for Service and LocalBusiness markup guidance.",
    },
    {
        "name": "Local SEO industry analysis",
        "purpose": "Compare practical local SEO interpretations and observed ranking impacts.",
    },
    {
        "name": "AI search and SERP monitoring",
        "purpose": "Watch how AI search surfaces service businesses and local landing pages.",
    },
    {
        "name": "Conversion and landing page benchmarks",
        "purpose": "Identify page patterns that may improve local service lead conversion.",
    },
]

IMPACT_QUESTIONS = [
    "Should service landing pages change?",
    "Should metadata or schema be adjusted?",
    "Are new local SEO opportunities relevant?",
    "Should Google Ads keywords or negative keywords change?",
    "Should content templates be updated?",
]


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _add_query(queries: list[dict], seen: set[str], query: str, purpose: str, category: str) -> None:
    key = query.lower()
    if key in seen:
        return
    seen.add(key)
    queries.append({"query": query, "purpose": purpose, "category": category})


def build_research_plan(topic: str, focus: str = "", service: str = "") -> dict:
    topic = topic.strip()
    focus = focus.strip()
    service = service.strip()
    service_intent = resolve_service_intent(" ".join(part for part in (topic, focus, service) if part))

    queries: list[dict] = []
    seen: set[str] = set()

    for item in BROAD_RESEARCH_QUERIES:
        _add_query(queries, seen, item["query"], item["purpose"], item["category"])

    if focus:
        _add_query(
            queries,
            seen,
            f"{focus} AI SEO updates",
            "Research the requested focus area against current AI and SEO changes.",
            "seo",
        )

    if service_intent:
        display_name = service_intent["display_name"]
        positive_terms = service_intent["positive_terms"]
        for term in positive_terms[:8]:
            _add_query(
                queries,
                seen,
                f"{term} SEO local service landing page",
                f"Research service-specific SEO opportunities for {display_name}.",
                "seo",
            )
        _add_query(
            queries,
            seen,
            "rooktest geuropsporing rioolgeur riolering SEO",
            "Keep Turbo Services rookdetectie aligned with smoke-test, sewer-odor intent.",
            "content_strategy",
        )
        _add_query(
            queries,
            seen,
            "geuropsporing riolering LocalBusiness Service schema",
            "Check structured data options for sewer-odor detection service pages.",
            "structured_data",
        )

    return {
        "ok": True,
        "topic": topic,
        "focus": focus,
        **({"service_intent": service_intent} if service_intent else {}),
        "research_queries": queries,
        "source_categories": SOURCE_CATEGORIES,
        "turbo_services_impact_questions": IMPACT_QUESTIONS,
        "suggested_cadence": {
            "frequency": "weekly",
            "reason": "AI search, SEO, local SEO, structured data, and ads guidance can shift often enough that a weekly dry-run review is useful without creating noise.",
        },
    }


@router.post("/research-plan")
async def research_plan(request: Request):
    payload = await request.json()
    topic = _clean_string(payload.get("topic"))
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    return build_research_plan(
        topic=topic,
        focus=_clean_string(payload.get("focus")),
        service=_clean_string(payload.get("service")),
    )
