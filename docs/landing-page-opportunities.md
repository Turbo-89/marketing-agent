# Landing Page Opportunities

## Purpose

The landing page opportunities integration prepares a read-only dry-run response for future landing-page opportunity planning from Google Ads and GA4 signals.

## Endpoints

- `GET /api/opportunities/status`
- `POST /api/opportunities/landing-pages`

The status endpoint reports whether the existing Google Ads and GA4 client modules are available and appear configured. It does not expose tokens, account IDs, property IDs, credential paths, or secrets.

The landing-page endpoint returns provider status, normalized inputs, empty signals, empty opportunities, approval gates, and notes. This step does not call Google Ads or GA4 because online/provider reads are not enabled here.

## Safety

The endpoints are read-only. They do not write files, change ads, deploy, publish, merge, push to live, execute shell commands, call OpenAI, call GitHub, schedule jobs, or make internet calls.

For `rookdetectie`, service intent is resolved as `rookdetectie_geuropsporing`: rooktest/geuropsporing for rioolgeur, riolering, riool, and afvoer. It must not be treated as rookmelders, brandveiligheid, branddetectie, or brandalarm positive context.
