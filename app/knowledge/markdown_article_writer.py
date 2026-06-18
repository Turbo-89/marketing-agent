from __future__ import annotations

import os
from openai import OpenAI


TITLE_PROMPT = """Geef exact één natuurlijke Nederlandse titel terug voor een kennisbankartikel.
Geen aanhalingstekens.
Geen punt op het einde.
Geen extra uitleg.
"""

DESCRIPTION_PROMPT = """Geef exact één korte meta description terug in het Nederlands.
Maximaal ongeveer 155 tekens.
Geen aanhalingstekens.
Geen extra uitleg.
"""


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _normalize_text(value: str) -> str:
    return (
        value.replace("Ã«", "ë")
        .replace("Ã©", "é")
        .replace("Ã¨", "è")
        .replace("Ãª", "ê")
        .replace("Ã¶", "ö")
        .replace("Ã¯", "ï")
        .replace("Ã¼", "ü")
        .replace("â€™", "’")
        .replace("â€“", "–")
        .replace("â€”", "—")
        .replace("â€¦", "…")
    )


def _body_prompt_for_service(service: str) -> str:
    common = """Je schrijft een kennisbankartikel voor Turbo Services.
Schrijf in helder Nederlands.
Werk feitelijk, technisch bruikbaar en zonder opvulling.
Geen code fences.
Geen markdown tabellen.
Geen verzonnen cijfers, keurmerken of garanties.
Geef uitsluitend geldige markdown BODY terug, zonder frontmatter.

Gebruik exact deze structuur:

Korte inleiding van 1 alinea.

## Mogelijke oorzaken

## Wat kan je eerst zelf controleren?

## Wanneer is professionele hulp nodig?

## Welke oplossing past meestal?
"""

    if service == "geurdetectie":
        return common + """

Inhoudsregels voor deze dienstcluster:
- focus op rioolgeur, stank, geurhinder, droge sifon, defecte sifon, lekkende aansluiting, verluchtingsprobleem, verborgen geurbron
- schrijf NIET alsof elke geur automatisch een verstopping is
- camera-inspectie of geurdetectie mogen genoemd worden als professionele oplossing
- ontstopping alleen noemen als dat logisch volgt uit de oorzaak
"""

    if service == "camera-inspectie":
        return common + """

Inhoudsregels voor deze dienstcluster:
- focus op diagnose, lokalisatie en inspectie
- benadruk oorzaken zoals breuk, verzakking, wortelgroei, terugkerende verstopping, verborgen leidingprobleem
- schrijf NIET alsof camera-inspectie zelf de herstelling is
- vermeld camera-inspectie als methode om de exacte oorzaak vast te stellen
"""

    if service == "noodherstellingen":
        return common + """

Inhoudsregels voor deze dienstcluster:
- focus op acute problemen: lek, breuk, overstroming, plotse uitval, dringende interventie
- benadruk tijdelijke risico's en nood aan snelle inschatting
- vermijd uitgebreide algemene SEO-opvulling
"""

    return common + """

Inhoudsregels voor deze dienstcluster:
- focus op afvoer, verstopping, terugkerend slecht wegstromen, lokale blokkades en leidingproblemen
- professionele oplossing mag ontstopping, reiniging of inspectie omvatten wanneer logisch
"""


def _related_links(service: str) -> str:
    service_links = {
        "ontstoppingen": [
            "- [Ontstoppingen](/diensten/ontstoppingen)",
            "- [Camera-inspectie](/diensten/camera-inspectie)",
            "- [Geurdetectie](/diensten/geurdetectie)",
        ],
        "geurdetectie": [
            "- [Geurdetectie](/diensten/geurdetectie)",
            "- [Camera-inspectie](/diensten/camera-inspectie)",
            "- [Ontstoppingen](/diensten/ontstoppingen)",
        ],
        "camera-inspectie": [
            "- [Camera-inspectie](/diensten/camera-inspectie)",
            "- [Ontstoppingen](/diensten/ontstoppingen)",
            "- [Geurdetectie](/diensten/geurdetectie)",
        ],
        "noodherstellingen": [
            "- [Noodherstellingen](/diensten/noodherstellingen)",
            "- [Ontstoppingen](/diensten/ontstoppingen)",
            "- [Camera-inspectie](/diensten/camera-inspectie)",
        ],
    }

    return "\n".join(service_links.get(service, service_links["ontstoppingen"]))


class MarkdownArticleWriter:
    def __init__(self):
        self.client = OpenAI()
        self.model = os.getenv("KNOWLEDGE_MODEL", "gpt-4o-mini")

    @staticmethod
    def _clean_output(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```markdown"):
            cleaned = cleaned[len("```markdown"):].strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        return _normalize_text(cleaned.strip())

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        result = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return self._clean_output(result.choices[0].message.content or "")

    def write_article(self, topic: dict) -> str:
        seed_keyword = topic["seed_keyword"]
        service = topic["service"]
        slug = topic["slug"]
        clicks = topic["clicks"]
        impressions = topic["impressions"]

        shared_context = f"""
Zoekwoord: {seed_keyword}
Dienstcluster: {service}
Slug: {slug}
Intentie: kennisbank
Klikken: {clicks}
Vertoningen: {impressions}

Algemene regels:
- geen regio's verzinnen
- geen commerciële overdrijving
- wel duidelijke brug naar professionele hulp wanneer relevant
- schrijf inhoudelijk in lijn met de dienstcluster
"""

        title = self._chat(
            TITLE_PROMPT,
            shared_context + "\nGeef één titel terug.",
        )

        description = self._chat(
            DESCRIPTION_PROMPT,
            shared_context + "\nGeef één meta description terug.",
        )

        body = self._chat(
            _body_prompt_for_service(service),
            shared_context + "\nSchrijf alleen de markdown body.",
        )

        related_links = _related_links(service)

        markdown = (
            "---\n"
            f"title: {_yaml_quote(title)}\n"
            f"description: {_yaml_quote(description)}\n"
            f"slug: {_yaml_quote(slug)}\n"
            f"service: {_yaml_quote(service)}\n"
            f"keywords: {_yaml_quote(seed_keyword)}\n"
            "---\n\n"
            f"{body.strip()}\n\n"
            "## Gerelateerd\n\n"
            f"{related_links}\n"
        )

        return markdown