# app/auth/google_oauth.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from google_auth_oauthlib.flow import Flow


TOKENS_DIR = Path("generated") / "tokens"
TOKENS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SECRETS_PATH = Path("config") / "oauth_secrets.json"


@dataclass(frozen=True)
class OAuthServiceConfig:
    name: str
    scopes: List[str]
    redirect_uri: str


class GoogleOAuth:
    """
    - Maakt per request een nieuwe Flow (geen cross-contaminatie van scopes)
    - Slaat tokens per service op: generated/tokens/{service}.json
    """

    def __init__(self) -> None:
        # Allow localhost OAuth (dev)
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
        # Allow scope changes without crashing oauthlib (cruciaal bij meerdere Google producten)
        os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

        secrets_path = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS_PATH")
        self.client_secrets_file = str(Path(secrets_path) if secrets_path else DEFAULT_SECRETS_PATH)

        # hard-fail als secrets ontbreken
        if not Path(self.client_secrets_file).exists():
            raise RuntimeError(
                f"OAuth secrets file ontbreekt: {self.client_secrets_file}. "
                f"Zet GOOGLE_OAUTH_CLIENT_SECRETS_PATH of plaats config/oauth_secrets.json."
            )

        self.base_url = os.getenv("OAUTH_BASE_URL", "http://localhost:8000").rstrip("/")

        self._services: Dict[str, OAuthServiceConfig] = {
            "ads": OAuthServiceConfig(
                name="ads",
                scopes=["https://www.googleapis.com/auth/adwords"],
                redirect_uri=f"{self.base_url}/api/auth/google/ads/callback",
            ),
            "sc": OAuthServiceConfig(
                name="sc",
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
                redirect_uri=f"{self.base_url}/api/auth/google/sc/callback",
            ),
            "ga4": OAuthServiceConfig(
                name="ga4",
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
                redirect_uri=f"{self.base_url}/api/auth/google/ga4/callback",
            ),
            "drive": OAuthServiceConfig(
                name="drive",
                scopes=["https://www.googleapis.com/auth/drive.file"],
                redirect_uri=f"{self.base_url}/api/auth/google/drive/callback",
            ),
        }

    def get_service(self, service: str) -> OAuthServiceConfig:
        if service not in self._services:
            raise ValueError(f"Onbekende service: {service}")
        return self._services[service]

    def _new_flow(self, service: str) -> Flow:
        cfg = self.get_service(service)
        return Flow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=cfg.scopes,
            redirect_uri=cfg.redirect_uri,
        )

    def authorization_url(self, service: str, state: str) -> Tuple[str, str]:
        flow = self._new_flow(service)
        auth_url, returned_state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=state,
        )
        return auth_url, returned_state

    def fetch_and_store_token(self, service: str, code: str) -> Dict:
        flow = self._new_flow(service)

        # oauthlib kan warnings als exceptions gooien; relax token scope is al gezet in __init__
        flow.fetch_token(code=code)

        token = flow.credentials.to_json()
        token_dict = json.loads(token)

        token_path = TOKENS_DIR / f"{service}.json"
        token_path.write_text(json.dumps(token_dict, indent=2), encoding="utf-8")

        return token_dict

    def token_path(self, service: str) -> str:
        return str(TOKENS_DIR / f"{service}.json")


google_oauth = GoogleOAuth()

__all__ = ["google_oauth", "GoogleOAuth"]
