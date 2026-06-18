# Landing Page Opportunities

## Purpose

The landing page opportunities integration prepares a read-only dry-run response for future landing-page opportunity planning from Google Ads and GA4 signals.

## Endpoints

- `GET /api/opportunities/status`
- `POST /api/opportunities/landing-pages`

The status endpoint reports whether the existing Google Ads and GA4 client modules are available and appear configured. It does not expose tokens, account IDs, property IDs, credential paths, or secrets.

The landing-page endpoint returns provider status, normalized inputs, signals, opportunities, approval gates, and notes. Live reads are disabled by default. Set `read_live=true` in the request and enable `ENABLE_GOOGLE_ADS_READS` or `ENABLE_GA4_READS` to attempt read-only provider calls.

When live reads are disabled or configuration is incomplete, the endpoint returns safe skipped, disabled, or not-configured statuses without crashing. Responses do not expose secrets, credential paths, account IDs, property IDs, tokens, refresh tokens, or client IDs.

For validation without live credentials, `POST /api/opportunities/landing-pages` accepts `sample_signals` only when `dry_run=true`. Sample signals are marked as sample data and are never treated as live provider data.

Available signals are grouped into scored opportunities with `score`, `priority`, and a `score_breakdown` for demand, conversion or value, content gap, local relevance, and confidence. Opportunities are sorted by score descending and always keep `approval_required=true`.

## Safety

The endpoints are read-only. They do not write files, change ads, deploy, publish, merge, push to live, execute shell commands, call OpenAI, call GitHub, schedule jobs, or make internet calls.

For `rookdetectie`, service intent is resolved as `rookdetectie_geuropsporing`: rooktest/geuropsporing for rioolgeur, riolering, riool, and afvoer. It must not be treated as rookmelders, brandveiligheid, branddetectie, or brandalarm positive context.
