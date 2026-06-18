# LEGACY AUTH PAD
# Dit bestand gebruikt een oudere Drive-specifieke OAuth-flow met tokenopslag in:
# - config/google_drive_token.json
#
# De primaire richting voor OAuth binnen marketing-agent is nu:
# - app/auth/google_oauth.py
# - generated/tokens/{service}.json
#
# Geen nieuwe uitbreidingen meer op dit legacy pad.
# Alleen behouden tot bevestigd is dat het niet meer runtime nodig is.



import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.responses import RedirectResponse

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.auth.google_oauth import google_oauth

# Tokenbestand voor Drive, in dezelfde config map
TOKEN_PATH = os.path.join("config", "google_drive_token.json")

router = APIRouter(
    prefix="/api/auth/google/drive",
    tags=["Google Drive OAuth"],
)


def load_drive_credentials() -> Optional[Credentials]:
    """
    Laad OAuth-usercredentials voor Drive uit TOKEN_PATH.
    Retourneert None als er nog geen tokenbestand is.
    """
    if not os.path.exists(TOKEN_PATH):
        return None

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    return creds


def save_drive_credentials(creds: Credentials) -> None:
    """
    Sla OAuth-usercredentials voor Drive op in TOKEN_PATH.
    """
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def get_drive_service():
    """
    Haal een geldige Google Drive service op.
    Gooit HTTP 401 als er nog geen OAuth is uitgevoerd.
    """
    creds = load_drive_credentials()
    if not creds:
        raise HTTPException(
            status_code=401,
            detail="Google Drive is niet geautoriseerd. Start eerst de OAuth-flow.",
        )

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        save_drive_credentials(creds)

    try:
        service = build("drive", "v3", credentials=creds)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kon Google Drive service niet initialiseren: {e}",
        )

    return service


@router.get("/start")
async def start_google_drive_auth():
    flow = google_oauth.drive_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return RedirectResponse(url=authorization_url)

    """
    Start de OAuth-flow voor Google Drive.
    Retourneert een authorization_url waar de UI naartoe moet redirecten.
    """
    flow = google_oauth.drive_flow()
    from urllib.parse import quote

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )



    return RedirectResponse(url=safe_url)
  
  

@router.get("/callback")
async def google_drive_callback(request: Request):
    """
    Callback-URL die overeenkomt met redirect_uri_drive in oauth_secrets.json:
    http://localhost:8000/api/auth/google/drive/callback
    """
    # Volledige URL die Google heeft aangeroepen (incl. code & state)
    authorization_response = str(request.url)

    flow = google_oauth.drive_flow()

    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Fout bij ophalen Google Drive tokens: {e}",
        )

    creds = flow.credentials
    if not creds:
        raise HTTPException(
            status_code=400,
            detail="Geen credentials ontvangen van Google.",
        )

    save_drive_credentials(creds)

    # Na succesvolle authorisatie kun je terugkeren naar de UI
    # Pas de URL aan indien je een andere route gebruikt
    return RedirectResponse(url="http://localhost:3000/chat?drive=ok")


@router.get("/status")
async def google_drive_status():
    """
    Laat de UI/agent checken of Drive al geautoriseerd is.
    """
    creds = load_drive_credentials()
    if not creds:
        return {"authorized": False}

    return {
        "authorized": True,
        "scopes": list(creds.scopes or []),
        "expired": bool(creds.expired),
        "has_refresh_token": bool(creds.refresh_token),
    }
