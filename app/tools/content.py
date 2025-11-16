from typing import Dict
import json

from dotenv import load_dotenv
from openai import OpenAI

from app.models.config_models import BusinessConfig, ServiceConfig

load_dotenv()
_client = OpenAI()  # gebruikt OPENAI_API_KEY uit .env


def generate_page_content_ai(
    service: ServiceConfig,
    region: str,
    business_config: BusinessConfig,
) -> Dict:
    """
    Genereer SEO-geschikte content voor een dienst in een regio.
    Outputstructuur blijft stabiel zodat website-tools TSX kunnen genereren.
    """
    brand = business_config.brand
    tone = business_config.content.tone
    cta = business_config.content.cta

    prompt = (
        "Je bent een gespecialiseerde copywriter voor ontstoppingsdiensten in België.\n"
        "Je schrijft SEO-landingspagina's in helder NL (Vlaams), zonder overdrijving.\n\n"
        f"MERK: {brand}\n"
        f"DIENST: {service.name} (key: {service.key})\n"
        f"REGIO: {region}\n"
        f"TONE: {tone}\n"
        f"STANDAARD CTA: {cta}\n\n"
        "GEEF UITSLUITEND ÉÉN JSON OBJECT TERUG met exact deze velden:\n"
        "{\n"
        '  "title": string,                // korte paginatitel (browser)\n'
        '  "h1": string,                   // hoofdheadline op pagina\n'
        '  "intro": string,                // korte intro-paragraaf (2-4 zinnen)\n'
        '  "sections": [\n'
        '    {\n'
        '      "heading": string,\n'
        '      "body": string\n'
        "    },\n"
        "    ... min. 2, max. 4 secties ...\n"
        "  ],\n"
        '  "cta": string,                  // 1 duidelijke call-to-action\n'
        '  "metaTitle": string,            // SEO title\n'
        '  "metaDescription": string       // meta description (max. ~160 karakters)\n'
        "}\n"
        "Gebruik geen HTML-tags in de teksten, behalve eventueel <strong> heel spaarzaam.\n"
        "Noem GEEN prijzen tenzij expliciet gevraagd (hier: NIET noemen).\n"
    )

    completion = _client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Je bent een precieze marketing- en SEO-copywriter."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw = completion.choices[0].message.content
    data = json.loads(raw)

    # minimale sanity-checks / defaulting
    data.setdefault("title", f"{service.name} in {region.capitalize()} | {brand}")
    data.setdefault("h1", f"{service.name} in {region.capitalize()}")
    data.setdefault("intro", "")
    data.setdefault("sections", [])
    data.setdefault("cta", business_config.content.cta)
    data.setdefault("metaTitle", data["title"])
    data.setdefault("metaDescription", f"{service.name} in {region.capitalize()} – {cta}")

    return data
