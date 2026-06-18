# Task Planner

## Purpose

The task planner endpoint builds a read-only dry-run plan for a requested task. It combines service intent resolution, local context discovery, and the intelligence job catalog without executing commands, writing files, calling OpenAI, calling the internet, scheduling jobs, deploying, or touching GitHub.

## Endpoint

- `POST /api/tasks/plan`

Request:

```json
{
  "task": "Maak een landingspagina rookdetectie Antwerpen met SEO metadata.",
  "roots": ["marketing_agent"],
  "max_context_files": 12
}
```

Response includes service intent when detected, the local context plan, suggested intelligence jobs, execution planning steps, likely files to review, risks, validation suggestions, approval gates, and forbidden actions for the current dry-run.

## Safety

The endpoint is read-only. It does not write files, deploy, publish, change ads, merge, push to live, execute shell commands, call OpenAI, call the internet, schedule jobs, or mutate strategy.

For Turbo Services rookdetectie tasks, the planner preserves the business meaning as rooktest/geuropsporing for rioolgeur, riolering, and afvoer. It must not treat rookdetectie as rookmelders, brandveiligheid, branddetectie, or brandalarm positive context.
