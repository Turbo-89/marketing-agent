# Intelligence Research Planner

## Purpose

The intelligence research planner prepares read-only dry-run plans for AI, SEO, local SEO, structured data, ads, and content-strategy monitoring. It does not execute web searches, call OpenAI, write files, schedule tasks, deploy, or touch GitHub.

## Endpoint

- `POST /api/intelligence/research-plan`
- `POST /api/intelligence/run-research`
- `POST /api/intelligence/analyze-results`
- `GET /api/intelligence/jobs`
- `GET /api/intelligence/jobs/{job_id}`

Request:

```json
{
  "topic": "AI SEO updates voor Turbo Services",
  "focus": "optional focus",
  "service": "optional service"
}
```

Response includes the topic, focus, optional `service_intent`, research queries, source categories, Turbo Services impact questions, and a suggested weekly cadence.

`/api/intelligence/run-research` is disabled by default with `ENABLE_ONLINE_INTELLIGENCE_RUNNER`. Enabled values are `1`, `true`, `yes`, and `on`. When disabled, it returns the research plan and does not call an online provider.

When enabled, the runner executes only capped research queries and returns compact result metadata: title, URL, snippet, and source. Configure the provider with `ONLINE_INTELLIGENCE_PROVIDER`; supported values are `none` and `brave`. Brave search requires `BRAVE_SEARCH_API_KEY`. If no safe provider or key is configured, it returns `provider_not_configured` or a missing-key note without crashing. The implementation does not add paid dependencies, hardcode API keys, scrape full pages, write files, schedule tasks, call OpenAI, deploy, or touch GitHub.

`/api/intelligence/analyze-results` analyzes only compact run results already provided in the request. It treats titles, snippets, and URLs as signals rather than proven facts, returns possible Turbo Services impact areas, and proposes approval-required review actions. It does not fetch pages, call OpenAI, write files, schedule jobs, deploy, mutate strategy, or touch GitHub.

`/api/intelligence/jobs` and `/api/intelligence/jobs/{job_id}` return static read-only definitions for future periodic intelligence jobs. They do not execute jobs, schedule background tasks, call online providers, write files, mutate strategy, deploy, or touch GitHub. All jobs are disabled by default and require approval before any proposed action.

## Service Intent

When the topic, focus, or service mentions `rookdetectie`, `rook detectie`, `rooktest`, `geurdetectie`, `geuropsporing`, or `rioolgeur`, the planner treats it as Turbo Services rooktest/geuropsporing context for rioolgeur, riolering, afvoer, and ontstopping.

It must not treat Turbo Services rookdetectie as fire safety, smoke alarms, brand detection, or rookmelders.
