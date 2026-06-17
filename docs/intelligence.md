# Intelligence Research Planner

## Purpose

The intelligence research planner prepares read-only dry-run plans for AI, SEO, local SEO, structured data, ads, and content-strategy monitoring. It does not execute web searches, call OpenAI, write files, schedule tasks, deploy, or touch GitHub.

## Endpoint

- `POST /api/intelligence/research-plan`

Request:

```json
{
  "topic": "AI SEO updates voor Turbo Services",
  "focus": "optional focus",
  "service": "optional service"
}
```

Response includes the topic, focus, optional `service_intent`, research queries, source categories, Turbo Services impact questions, and a suggested weekly cadence.

## Service Intent

When the topic, focus, or service mentions `rookdetectie`, `rook detectie`, `rooktest`, `geurdetectie`, `geuropsporing`, or `rioolgeur`, the planner treats it as Turbo Services rooktest/geuropsporing context for rioolgeur, riolering, afvoer, and ontstopping.

It must not treat Turbo Services rookdetectie as fire safety, smoke alarms, brand detection, or rookmelders.
