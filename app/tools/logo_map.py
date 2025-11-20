LOGO_MAP = {
    "ontstoppingen": "public/logos/ontstoppingen.png",
    "camera-inspectie": "public/logos/camera.png",
    "geurdetectie": "public/logos/geur.png",
    "herstellingen": "public/logos/herstelling.png"
}

def get_logo(service: str) -> str:
    if service not in LOGO_MAP:
        raise KeyError(f"Geen logo gevonden voor dienst: {service}")
    return LOGO_MAP[service]
