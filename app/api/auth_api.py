# app/api/auth_api.py

from __future__ import annotations

import secrets
from typing import Dict

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse, JSONResponse

from app.auth.google_oauth import google_oauth

router = APIRouter(prefix="/api/auth/google", tags=["auth"])

# simpele in-memory state store voor dev
# (bij reload gaat die leeg; voor lokaal is dat OK)
STATE: Dict[str, str] = {}


def _new_state(service: str) -> str:
    s = secrets.token_urlsafe(24)
    STATE[service] = s
    return s


@router.get("/{service}/start")
def start(service: str):
    state = _new_state(service)
    auth_url, _ = google_oauth.authorization_url(service, state=state)
    return RedirectResponse(url=auth_url, status_code=307)


@router.get("/{service}/callback")
def callback(
    service: str,
    code: str = Query(...),
    state: str = Query(...),
):
    expected = STATE.get(service)
    # In dev: als uvicorn reloadt, is STATE weg. Dan blokkeren we niet hard.
    if expected and state != expected:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "state_mismatch", "expected": expected, "got": state},
        )

    token = google_oauth.fetch_and_store_token(service, code=code)

    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "service": service,
            "token_saved_to": google_oauth.token_path(service),
            "scopes": token.get("scope"),
        },
    )
