import os
from typing import Any

import requests
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


def _clamped_positive_int(value: Any, default: int, hard_cap: int) -> int:
    if not isinstance(value, int) or value <= 0:
        return default
    return min(value, hard_cap)


def _add_query(queries: list[dict], seen: set[str], query: str, purpose: str, category: str) -> None:
    key = query.lower()
    if key in seen:
        return
    seen.add(key)
    queries.append({"query": query, "purpose": purpose, "category": category})


def is_online_intelligence_runner_enabled() -> bool:
    value = os.getenv("ENABLE_ONLINE_INTELLIGENCE_RUNNER", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


class OnlineSearchProvider:
    name = "provider_not_configured"
    missing_config_note = "provider_not_configured"

    def search(self, query: str, max_results: int) -> dict:
        return {
            "ok": False,
            "error": self.missing_config_note,
            "provider": self.name,
            "query": query,
            "results": [],
        }


class BraveSearchProvider:
    name = "brave"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, max_results: int) -> dict:
        try:
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key,
                },
                params={"q": query, "count": max_results},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return {
                "ok": False,
                "error": f"provider_error:{exc.__class__.__name__}",
                "provider": self.name,
                "query": query,
                "results": [],
            }

        results = []
        for item in (data.get("web") or {}).get("results", [])[:max_results]:
            results.append(
                {
                    "title": _clean_string(item.get("title")),
                    "url": _clean_string(item.get("url")),
                    "snippet": _clean_string(item.get("description")),
                    "source": self.name,
                }
            )

        return {
            "ok": True,
            "provider": self.name,
            "query": query,
            "results": results,
        }


def get_online_search_provider() -> OnlineSearchProvider:
    provider = os.getenv("ONLINE_INTELLIGENCE_PROVIDER", "none").strip().lower()
    if provider in {"", "none"}:
        return OnlineSearchProvider()
    if provider == "brave":
        api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
        if not api_key:
            missing = OnlineSearchProvider()
            missing.missing_config_note = "missing BRAVE_SEARCH_API_KEY"
            return missing
        return BraveSearchProvider(api_key)

    unknown = OnlineSearchProvider()
    unknown.missing_config_note = f"unsupported_provider:{provider}"
    return unknown


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


def run_research_plan(
    research_plan: dict,
    max_queries: int = 3,
    max_results_per_query: int = 5,
) -> dict:
    max_queries = _clamped_positive_int(max_queries, 3, 8)
    max_results_per_query = _clamped_positive_int(max_results_per_query, 5, 10)
    provider = get_online_search_provider()
    provider_configured = provider.name != "provider_not_configured"
    executed_queries = []
    notes = []
    result_count = 0

    if not provider_configured:
        notes.append("provider_not_configured")

    for item in research_plan.get("research_queries", [])[:max_queries]:
        provider_result = provider.search(item["query"], max_results_per_query)
        results = []
        for result in provider_result.get("results", [])[:max_results_per_query]:
            results.append(
                {
                    "title": _clean_string(result.get("title")),
                    "url": _clean_string(result.get("url")),
                    "snippet": _clean_string(result.get("snippet")),
                    "source": _clean_string(result.get("source") or provider.name),
                }
            )

        result_count += len(results)
        if provider_result.get("error"):
            notes.append(provider_result["error"])

        executed_queries.append(
            {
                "query": item["query"],
                "category": item["category"],
                "purpose": item["purpose"],
                "results": results,
            }
        )

    return {
        "ok": provider_configured,
        "topic": research_plan["topic"],
        "research_plan": research_plan,
        "executed_queries": executed_queries,
        "summary": {
            "result_count": result_count,
            "provider": provider.name,
            "notes": list(dict.fromkeys(notes)),
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


@router.post("/run-research")
async def run_research(request: Request):
    payload = await request.json()
    topic = _clean_string(payload.get("topic"))
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    plan = build_research_plan(
        topic=topic,
        focus=_clean_string(payload.get("focus")),
        service=_clean_string(payload.get("service")),
    )

    if not is_online_intelligence_runner_enabled():
        return {
            "ok": False,
            "error": "online_intelligence_runner_disabled",
            "research_plan": plan,
        }

    return run_research_plan(
        research_plan=plan,
        max_queries=payload.get("max_queries", 3),
        max_results_per_query=payload.get("max_results_per_query", 5),
    )
