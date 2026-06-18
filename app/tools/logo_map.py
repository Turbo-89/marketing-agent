# app/tools/logo_map.py
from __future__ import annotations

import os
from pathlib import Path

# Repo-root: .../marketing-agent
REPO_ROOT = Path(__file__).resolve().parents[2]

# Default: marketing-agent/public/logos
DEFAULT_LOGO_ROOT = REPO_ROOT / "public" / "logos"

# Optionele override via env (bv. als logos in turboservices repo staan)
# setx TURBO_LOGO_ROOT "C:\Projects\GitHub\turboservices\public\logos"
LOGO_ROOT = Path(os.getenv("TURBO_LOGO_ROOT", str(DEFAULT_LOGO_ROOT))).expanduser().resolve()

LOGO_MAP = {
    "ontstoppingen": LOGO_ROOT / "ontstoppingen.png",
    "camera-inspectie": LOGO_ROOT / "camera.png",
    "geurdetectie": LOGO_ROOT / "geur.png",
    "herstellingen": LOGO_ROOT / "herstelling.png",
}

def get_logo(service: str) -> str:
    key = (service or "").strip().lower()
    if key not in LOGO_MAP:
        raise KeyError(f"Geen logo gevonden voor dienst: {service}")

    path = LOGO_MAP[key]
    if not path.exists():
        raise FileNotFoundError(f"Logo-bestand bestaat niet: {path}")

    return str(path)