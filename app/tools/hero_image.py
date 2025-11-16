# app/tools/hero_image.py

import io
from typing import Dict

from app.models.config_models import BusinessConfig, ServiceConfig
from app.services.github_client import get_github_client_from_env
from openai import OpenAI


def slugify(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "-")
        .replace("–", "-")
        .replace("—", "-")
    )


def build_hero_image_path(service: ServiceConfig, region: str) -> str:
    """
    Pad binnen de repo voor de hero-afbeelding van een dienst+regio.
    """
    service_key = slugify(service.key)
    region_slug = slugify(region)
    # dit correspondeert met /public/assets/logo/... op de live site
    return f"public/assets/logo/{service_key}-{region_slug}.png"


def generate_hero_prompt(service: ServiceConfig, region: str, business_config: BusinessConfig) -> str:
    """
    Prompt voor de AI-afbeelding. Pas desnoods verder toe aan jouw stijl.
    """
    brand = business_config.brand
    region_cap = region.capitalize()

    base = (
        f"Minimalistische vectorillustratie in de huisstijl van {brand}: "
        f"een vriendelijke rioolexpert/ontstopper met professioneel materiaal "
        f"voor een herkenbaar stadsbeeld van {region_cap} in België. "
        f"Helder, clean, platte kleuren, zachte schaduwen, zonder tekst."
    )

    # Dienstspecifieke nuance
    if "ontstopping" in service.key:
        base += " Focus op ontstopping van wc/riolering, met slang en ontstoppingsmachine."
    elif "camera" in service.key:
        base += " Focus op camera-inspectie, met inspectiecamera en scherm."
    elif "rook" in service.key:
        base += " Focus op rookdetectie van lekken in de riolering, met rookmachine."

    return base


def ensure_hero_image_in_repo(
    service: ServiceConfig,
    region: str,
    business_config: BusinessConfig,
) -> Dict:
    """
    Controleert of de hero-afbeelding al in de GitHub-repo bestaat.
    Als niet: genereert een AI-afbeelding en commit die naar public/assets/logo/.
    Retourneert info over het pad en (eventueel) de commit.
    """
    site_cfg = business_config.site
    owner = site_cfg.repo_owner
    repo = site_cfg.repo_name
    branch = site_cfg.default_branch

    client = get_github_client_from_env(owner, repo)
    path = build_hero_image_path(service, region)

    # 1. Bestaat file al?
    if client.file_exists(path, branch=branch):
        return {"path": path, "created": False, "commit_sha": None}

    # 2. Afbeelding genereren via OpenAI
    prompt = generate_hero_prompt(service, region, business_config)
    oai_client = OpenAI()  # gebruikt OPENAI_API_KEY uit omgeving

    img_resp = oai_client.images.generate(
        model="gpt-image-1",  # of ander model in jouw account
        prompt=prompt,
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )

    b64_data = img_resp.data[0].b64_json
    img_bytes = io.BytesIO()
    img_bytes.write(bytes.fromhex("") if False else __import__("base64").b64decode(b64_data))  # simpele decode
    png_bytes = img_bytes.getvalue()

    # 3. Commit naar GitHub
    commit_msg = f"feat(hero): auto hero image for {service.key} in {region}"
    result = client.upsert_binary_file(
        path=path,
        content_bytes=png_bytes,
        message=commit_msg,
        branch=branch,
    )

    return {
        "path": path,
        "created": True,
        "commit_sha": result.get("commit", {}).get("sha"),
        "content_url": result.get("content", {}).get("html_url"),
    }
