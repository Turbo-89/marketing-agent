"""
Website-tools: genereren en updaten van pagina's in de turboservices-repo.
Hier wordt TSX gegenereerd voor Next.js App Router en via GitHub API weggeschreven.
"""

import json
from typing import Dict, Any

from app.models.config_models import BusinessConfig, ServiceConfig
from app.services.github_client import get_github_client_from_env
from app.tools.hero_image import ensure_hero_image_in_repo


# Mapping tussen service keys in business.yml en slug in je Next.js-app
SERVICE_SLUG_MAP = {
    "ontstopping": "ontstoppingen",
    "camera-inspectie": "camera-inspectie",
    "rioolherstelling": "gerichte-rioolherstellingen",
    # toekomstige diensten zoals "rookdetectie" kunnen gewoon 1:1 gebruikt worden
}


def get_service_slug(service_key: str) -> str:
    return SERVICE_SLUG_MAP.get(service_key, service_key)


def build_page_path(service: ServiceConfig, region: str, business_config: BusinessConfig) -> str:
    """
    Voor App Router genereren we:
    app/diensten/<service-slug>/<region>/page.tsx
    → route: /diensten/<service-slug>/<region>
    """
    slug = get_service_slug(service.key)
    region_slug = region.lower()
    return f"app/diensten/{slug}/{region_slug}/page.tsx"


def _js_string(value: str) -> str:
    """
    Maakt een geldige JS-string literal via json.dumps.
    Voorbeeld: _js_string('test "x"') → "\"test \\\"x\\\"\""
    Die string kan direct in TSX worden geplaatst.
    """
    return json.dumps(value, ensure_ascii=False)


def render_tsx(
    service: ServiceConfig,
    region: str,
    business_config: BusinessConfig,
    content: Dict,
) -> str:
    """
    Maakt de inhoud van page.tsx voor een dienst+regio,
    maar de visuele layout zit in de gedeelde DienstPageLayout-component
    in je Next.js-project (components/diensten/DienstPage.tsx).
    """
    brand = business_config.brand
    service_slug = get_service_slug(service.key)
    region_cap = region.capitalize()

    title = content.get("title", f"{service.name} in {region_cap} | {brand}")
    h1 = content.get("h1", f"{service.name} in {region_cap}")
    intro = content.get("intro", "")
    sections = content.get("sections", [])
    cta = content.get("cta", business_config.content.cta)
    meta_title = content.get("metaTitle", title)
    meta_desc = content.get("metaDescription", f"{service.name} in {region_cap} – {cta}")

    # JS-literals via json.dumps
    js_meta_title = _js_string(meta_title)
    js_meta_desc = _js_string(meta_desc)

    js_brand = _js_string(brand)
    js_region_label = _js_string(region_cap)
    js_service_name = _js_string(service.name)
    js_h1 = _js_string(h1)
    js_intro = _js_string(intro)
    js_cta = _js_string(cta)
    js_service_key = _js_string(service.key)

    # sections als JSON-literal in TSX
    js_sections = json.dumps(sections, ensure_ascii=False)

    component_name = f"{service_slug.replace('-', ' ').title().replace(' ', '')}{region_cap}Page"

    tsx = f"""import type {{ Metadata }} from "next";
import {{ DienstPageLayout }} from "@/components/diensten/DienstPage";
// Pas het importpad hierboven aan als jouw project geen "@" alias gebruikt.

export const metadata: Metadata = {{
  title: {js_meta_title},
  description: {js_meta_desc},
}};

export default function {component_name}() {{
  const props = {{
    brand: {js_brand},
    regionLabel: {js_region_label},
    serviceName: {js_service_name},
    h1: {js_h1},
    intro: {js_intro},
    sections: {js_sections},
    cta: {js_cta},
    serviceKey: {js_service_key},
  }};

  return <DienstPageLayout {{...props}} />;
}}
"""

    return tsx


def create_or_update_page_in_repo(
    service: ServiceConfig,
    region: str,
    business_config: BusinessConfig,
    content: Dict,
) -> Dict[str, Any]:
    """
    Genereert de TSX-pagina en schrijft die via GitHub API weg naar de turboservices-repo.
    Maakt nu ook automatisch een hero-afbeelding aan als die nog niet bestaat.
    """
    site_cfg = business_config.site
    owner = site_cfg.repo_owner
    repo = site_cfg.repo_name
    branch = site_cfg.default_branch

    # 1. Hero-afbeelding zeker stellen (doet niets als hij al bestaat)
    hero_result = ensure_hero_image_in_repo(service, region, business_config)

    # 2. TSX-pagina genereren
    path = build_page_path(service, region, business_config)
    tsx_content = render_tsx(service, region, business_config, content)

    client = get_github_client_from_env(owner, repo)
    message = f"feat(landing): {service.key} in {region}"

    result = client.upsert_file(
        path=path,
        content_str=tsx_content,
        message=message,
        branch=branch,
    )

    return {
        "service_key": service.key,
        "region": region,
        "path": path,
        "commit_sha": result.get("commit", {}).get("sha"),
        "html_url": result.get("content", {}).get("html_url"),
        "hero_image": hero_result,
    }
