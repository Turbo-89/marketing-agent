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
SIGNAL_CATEGORIES = {
    "ai_search": ("ai search", "ai overview", "ai overviews", "generative", "answer engine"),
    "seo": ("seo", "ranking", "organic", "google update", "search update"),
    "local_seo": ("local seo", "google business profile", "maps", "near me", "local pack"),
    "structured_data": ("schema", "structured data", "schema.org", "localbusiness", "service schema"),
    "ads": ("google ads", "ads", "paid search", "keyword", "negative keyword"),
    "content_strategy": ("content", "template", "landing page", "service page", "topic"),
    "conversion": ("conversion", "lead", "cta", "form", "call tracking"),
}
IMPACT_AREAS = {
    "landing_pages": ("landing page", "landing pages", "conversion", "cta"),
    "metadata": ("metadata", "title tag", "meta description", "seo title"),
    "schema": ("schema", "structured data", "localbusiness", "service schema"),
    "content_templates": ("content template", "template", "content strategy", "service page"),
    "google_business_profile": ("google business profile", "gbp", "maps", "local pack"),
    "google_ads": ("google ads", "paid search", "negative keyword", "ads"),
    "service_pages": ("service page", "service pages", "local service", "landing page"),
    "internal_strategy": ("strategy", "update", "ai search", "seo update"),
}

JOB_PIPELINE = [
    "research_plan",
    "run_research",
    "analyze_results",
    "propose_actions",
    "approval_required",
]
ALLOWED_JOB_ACTIONS = ["research", "analysis", "proposal"]
FORBIDDEN_JOB_ACTIONS = [
    "write_files",
    "deploy",
    "publish",
    "change_ads",
    "merge",
    "push_to_live",
]
JOB_DEFINITIONS = [
    {
        "job_id": "weekly_ai_seo_watch",
        "name": "Weekly AI SEO Watch",
        "description": "Review AI search and SEO update signals for Turbo Services.",
        "cadence": {
            "frequency": "weekly",
            "suggested_day": "Monday",
            "reason": "AI search and SEO changes can affect service-page visibility quickly.",
        },
        "topic": "AI SEO updates voor Turbo Services",
        "focus": "AI search, AI Overviews, Google SEO updates",
    },
    {
        "job_id": "weekly_local_seo_watch",
        "name": "Weekly Local SEO Watch",
        "description": "Review local SEO and Google Business Profile signals.",
        "cadence": {
            "frequency": "weekly",
            "suggested_day": "Tuesday",
            "reason": "Local search and Google Business Profile changes can affect service-area leads.",
        },
        "topic": "local SEO updates voor Turbo Services",
        "focus": "local SEO, Google Business Profile, Maps visibility",
    },
    {
        "job_id": "weekly_structured_data_watch",
        "name": "Weekly Structured Data Watch",
        "description": "Review structured data guidance for service and local business pages.",
        "cadence": {
            "frequency": "weekly",
            "suggested_day": "Wednesday",
            "reason": "Schema guidance can affect how service pages are interpreted by search systems.",
        },
        "topic": "structured data updates voor Turbo Services",
        "focus": "schema.org Service, LocalBusiness, structured data",
    },
    {
        "job_id": "weekly_content_strategy_watch",
        "name": "Weekly Content Strategy Watch",
        "description": "Review content and conversion signals for local service landing pages.",
        "cadence": {
            "frequency": "weekly",
            "suggested_day": "Thursday",
            "reason": "Landing-page and content strategy signals can inform future proposals.",
        },
        "topic": "content strategy updates voor lokale service landingspagina's",
        "focus": "content strategy, conversion-focused landing pages",
    },
    {
        "job_id": "monthly_google_ads_watch",
        "name": "Monthly Google Ads Watch",
        "description": "Review Google Ads signals for local service keywords and negatives.",
        "cadence": {
            "frequency": "monthly",
            "suggested_day": "First Monday",
            "reason": "Ads changes are useful to review monthly before proposing campaign updates.",
        },
        "topic": "Google Ads updates voor Turbo Services",
        "focus": "Google Ads changes, local services keywords, negative keywords",
    },
    {
        "job_id": "monthly_turbo_services_services_watch",
        "name": "Monthly Turbo Services Services Watch",
        "description": "Review broader service-page and local SEO opportunities for Turbo Services.",
        "cadence": {
            "frequency": "monthly",
            "suggested_day": "First Tuesday",
            "reason": "A monthly service catalog review can identify proposal opportunities without noise.",
        },
        "topic": "Turbo Services diensten SEO en lokale vindbaarheid",
        "focus": "service pages, local SEO, metadata, schema",
    },
    {
        "job_id": "monthly_rookdetectie_geuropsporing_watch",
        "name": "Monthly Rookdetectie Geuropsporing Watch",
        "description": "Review rookdetectie as rooktest/geuropsporing for rioolgeur and riolering context.",
        "cadence": {
            "frequency": "monthly",
            "suggested_day": "First Wednesday",
            "reason": "Rookdetectie service intent should stay aligned with geuropsporing, not fire safety.",
        },
        "topic": "rookdetectie geuropsporing SEO voor Turbo Services",
        "focus": "rooktest, rioolgeur, geuropsporing, riolering, service landing pages",
        "service": "rookdetectie",
    },
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


def _empty_category_counts() -> dict:
    return {category: 0 for category in SIGNAL_CATEGORIES}


def _iter_research_results(research_run: Any):
    if not isinstance(research_run, dict):
        return
    for item in research_run.get("executed_queries") or []:
        if not isinstance(item, dict):
            continue
        category = _clean_string(item.get("category"))
        for result in item.get("results") or []:
            if isinstance(result, dict):
                yield category, result


def _result_text(result: dict) -> str:
    return " ".join(
        _clean_string(result.get(key)).lower()
        for key in ("title", "url", "snippet")
    )


def _job_response(job: dict) -> dict:
    response = {
        **job,
        "enabled_by_default": False,
        "pipeline": JOB_PIPELINE,
        "approval_required": True,
        "allowed_actions": ALLOWED_JOB_ACTIONS,
        "forbidden_actions": FORBIDDEN_JOB_ACTIONS,
    }
    service_intent = resolve_service_intent(
        " ".join(
            _clean_string(response.get(key))
            for key in ("topic", "focus", "service")
        )
    )
    if service_intent:
        response["service_intent"] = service_intent
    return response


def list_intelligence_jobs() -> list[dict]:
    return [_job_response(job) for job in JOB_DEFINITIONS]


def get_intelligence_job(job_id: str) -> dict | None:
    for job in JOB_DEFINITIONS:
        if job["job_id"] == job_id:
            return _job_response(job)
    return None


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


def analyze_research_results(topic: str, service: str = "", research_run: Any = None) -> dict:
    topic = topic.strip()
    service = service.strip()
    service_intent = resolve_service_intent(" ".join(part for part in (topic, service) if part))
    category_counts = _empty_category_counts()
    impact_hits = {area: 0 for area in IMPACT_AREAS}
    notes = []
    total_results = 0

    if not research_run:
        notes.append("no_research_run_provided")
    else:
        for category, result in _iter_research_results(research_run):
            total_results += 1
            text = _result_text(result)

            if category in category_counts:
                category_counts[category] += 1

            for signal_category, terms in SIGNAL_CATEGORIES.items():
                if any(term in text for term in terms):
                    category_counts[signal_category] += 1

            for area, terms in IMPACT_AREAS.items():
                if any(term in text for term in terms):
                    impact_hits[area] += 1

    impact = []
    for area in IMPACT_AREAS:
        hits = impact_hits[area]
        if hits > 0:
            confidence = "medium" if hits < 3 else "high"
            reason = f"Compact search-result signals mention this area {hits} time(s). Treat as signals, not proven facts."
        elif not research_run:
            confidence = "low"
            reason = "No research run was provided, so this is a baseline review area only."
        else:
            confidence = "low"
            reason = "No direct compact-result signal found; keep as a low-priority review area."

        impact.append(
            {
                "area": area,
                "impact": "possible",
                "reason": reason,
                "confidence": confidence,
            }
        )

    recommended_actions = [
        {
            "action": "Review service landing pages against the observed AI/SEO/local SEO signals.",
            "type": "review",
            "requires_approval": True,
        },
        {
            "action": "Review metadata for affected service pages before making any copy changes.",
            "type": "content_update",
            "requires_approval": True,
        },
        {
            "action": "Review Service and LocalBusiness schema opportunities before updating markup.",
            "type": "schema_update",
            "requires_approval": True,
        },
        {
            "action": "Review Google Ads keywords and negative keywords before changing campaigns.",
            "type": "ads_review",
            "requires_approval": True,
        },
        {
            "action": "Review content templates and internal strategy notes before applying updates.",
            "type": "strategy_review",
            "requires_approval": True,
        },
    ]

    if service_intent:
        recommended_actions.insert(
            0,
            {
                "action": (
                    "Review rookdetectie pages as rooktest/geuropsporing for rioolgeur, "
                    "riolering and afvoer context, not as fire-safety content."
                ),
                "type": "review",
                "requires_approval": True,
            },
        )

    return {
        "ok": True,
        "topic": topic,
        **({"service_intent": service_intent} if service_intent else {}),
        "signal_summary": {
            "total_results": total_results,
            "categories": category_counts,
            "notes": notes,
        },
        "turbo_services_impact": impact,
        "recommended_actions": recommended_actions,
        "approval_required": True,
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


@router.get("/jobs")
def intelligence_jobs():
    return {"ok": True, "jobs": list_intelligence_jobs()}


@router.get("/jobs/{job_id}")
def intelligence_job(job_id: str):
    job = get_intelligence_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Intelligence job not found")
    return {"ok": True, "job": job}


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


@router.post("/analyze-results")
async def analyze_results(request: Request):
    payload = await request.json()
    topic = _clean_string(payload.get("topic"))
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    return analyze_research_results(
        topic=topic,
        service=_clean_string(payload.get("service")),
        research_run=payload.get("research_run"),
    )
