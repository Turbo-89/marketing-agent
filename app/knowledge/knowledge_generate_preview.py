from __future__ import annotations

import os
from pathlib import Path

from app.knowledge.markdown_article_writer import MarkdownArticleWriter


KNOWLEDGE_REQUIRED_SECTIONS = [
    "## Mogelijke oorzaken",
    "## Wat kan je eerst zelf controleren?",
    "## Wanneer is professionele hulp nodig?",
    "## Welke oplossing past meestal?",
    "## Gerelateerd",
]


def _yaml_quote(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
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


def _resolve_turboservices_repo() -> Path:
    repo = os.getenv("TURBOSERVICES_REPO_PATH")
    if not repo:
        raise RuntimeError("TURBOSERVICES_REPO_PATH is niet ingesteld.")
    repo_path = Path(repo).resolve()
    if not repo_path.exists():
        raise FileNotFoundError(f"TURBOSERVICES_REPO_PATH bestaat niet: {repo_path}")
    return repo_path


def _commercial_description(keyword: str) -> str:
    return (
        f"{keyword.capitalize()} nodig? Snelle interventie door Turbo Services. "
        f"24/7 bereikbaar zonder meerkost in avond en weekend."
    )


def _commercial_title(keyword: str) -> str:
    k = keyword.strip()
    if not k:
        return "Commerciële pagina"
    return k[0].upper() + k[1:]


def _commercial_links(service: str) -> str:
    links = {
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
    return "\n".join(links.get(service, links["ontstoppingen"]))


def _commercial_intro(service: str, keyword: str) -> str:
    if service == "geurdetectie":
        return (
            f"Heb je last van **{keyword}**? Turbo Services helpt snel bij aanhoudende "
            f"rioolgeur, stank uit afvoeren en verborgen geurproblemen in woning of gebouw."
        )
    if service == "camera-inspectie":
        return (
            f"Heb je een probleem rond **{keyword}**? Turbo Services gebruikt camera-inspectie "
            f"om verborgen oorzaken in afvoer of riolering exact in beeld te brengen."
        )
    if service == "noodherstellingen":
        return (
            f"Heb je dringend hulp nodig voor **{keyword}**? Turbo Services staat klaar voor "
            f"snelle interventies bij acute problemen aan afvoer of riolering."
        )
    return (
        f"Heb je dringend hulp nodig voor **{keyword}**? Turbo Services staat 24/7 klaar "
        f"voor snelle en professionele interventies bij verstoppingen en afvoerproblemen."
    )


def _commercial_problem_block(service: str) -> str:
    if service == "geurdetectie":
        return (
            "Aanhoudende geurhinder wijst vaak op een probleem met sifons, aansluitingen, "
            "verluchting of een verborgen lek. Niet elke geur betekent automatisch een verstopping."
        )
    if service == "camera-inspectie":
        return (
            "Bij terugkerende problemen is het vaak nodig om de exacte oorzaak in de leiding op "
            "te sporen. Denk aan breuken, verzakkingen, wortelgroei of verborgen blokkades."
        )
    if service == "noodherstellingen":
        return (
            "Acute problemen aan afvoer of riolering kunnen snel schade veroorzaken. Denk aan "
            "lekken, breuken, overstroming of plotse uitval van afvoer."
        )
    return (
        "Problemen zoals verstoppingen, slecht doorlopende afvoeren of terugkerende waterophoping "
        "kunnen snel escaleren. Vaak zit er meer achter dan alleen lokaal vuil in de afvoer."
    )


def _commercial_urgency_block(service: str) -> str:
    if service == "geurdetectie":
        return """- aanhoudende rioolgeur in huis
- geur komt telkens terug
- meerdere afvoeren geven geurhinder
- oorzaak is niet zichtbaar"""
    if service == "camera-inspectie":
        return """- terugkerende verstoppingen
- vermoeden van breuk of verzakking
- oorzaak blijft onduidelijk
- inspectie nodig voor gerichte herstelling"""
    if service == "noodherstellingen":
        return """- lek of breuk met schadegevaar
- plotse overstroming
- afvoer volledig buiten dienst
- dringende tijdelijke of definitieve ingreep nodig"""
    return """- water loopt niet meer weg
- terugkerende verstoppingen
- meerdere afvoeren tegelijk problemen
- klassieke huis-tuin-oplossingen helpen niet"""


def _commercial_approach_block(service: str) -> str:
    if service == "geurdetectie":
        return """Wij onderzoeken de vermoedelijke geurbron gericht en technisch:

- controle van sifons en aansluitingen
- opsporen van geurlekken
- analyse van verluchtingsproblemen
- inzet van camera-inspectie indien nodig"""
    if service == "camera-inspectie":
        return """Wij gebruiken camera-inspectie om het probleem exact te lokaliseren:

- lokalisatie van breuk of verzakking
- controle op wortelgroei of blokkades
- visuele diagnose van de leiding
- basis voor gerichte herstelling"""
    if service == "noodherstellingen":
        return """Wij grijpen snel in met focus op beveiliging en herstel:

- eerste technische inschatting ter plaatse
- tijdelijke stabilisatie indien nodig
- gerichte noodherstelling
- vervolgadvies voor definitieve oplossing"""
    return """Wij werken met professionele apparatuur om de oorzaak gericht aan te pakken:

- mechanische ontstopping
- hoge druk reiniging
- camera-inspectie indien nodig
- gericht advies bij structurele problemen"""


def _generate_commercial_markdown(topic: dict) -> str:
    keyword = topic["seed_keyword"]
    slug = topic["slug"]
    service = topic["service"]

    title = _commercial_title(keyword)
    description = _commercial_description(keyword)
    related_links = _commercial_links(service)

    markdown = f"""---
title: {_yaml_quote(title)}
description: {_yaml_quote(description)}
slug: {_yaml_quote(slug)}
service: {_yaml_quote(service)}
keywords: {_yaml_quote(keyword)}
---

{_commercial_intro(service, keyword)}

## Wat houdt dit probleem in?

{_commercial_problem_block(service)}

## Wanneer moet je ingrijpen?

{_commercial_urgency_block(service)}

## Onze aanpak

{_commercial_approach_block(service)}

## Waarom Turbo Services?

- 24/7 bereikbaar
- zelfde tarief in avond en weekend
- snelle interventie
- ervaren sinds 2009

## Direct hulp nodig?

Bel onmiddellijk of vraag online een interventie aan.

## Gerelateerd

{_commercial_links(service)}
"""
    return _normalize_text(markdown.strip()) + "\n"


class KnowledgeGeneratePreview:
    def __init__(self):
        self.writer = MarkdownArticleWriter()
        self.repo = _resolve_turboservices_repo()
        self.generated_root = Path("generated") / "content"

    def _validate_markdown(self, markdown: str, intent: str) -> None:
        if not markdown.strip():
            raise ValueError("Lege markdown-output.")

        if not markdown.startswith("---\n"):
            raise ValueError("Frontmatter ontbreekt of start niet correct.")

        if "\n---\n\n" not in markdown:
            raise ValueError("Frontmatter is niet correct afgesloten.")

        if intent == "knowledge":
            for section in KNOWLEDGE_REQUIRED_SECTIONS:
                if section not in markdown:
                    raise ValueError(f"Verplichte sectie ontbreekt: {section}")

        else:
            if "## Gerelateerd" not in markdown:
                raise ValueError("Verplichte sectie ontbreekt: ## Gerelateerd")

            if markdown.count("## ") < 5:
                raise ValueError("Commerciële markdown bevat te weinig secties.")

        if len(markdown.strip()) < 500:
            raise ValueError("Markdown-output is te kort en waarschijnlijk onbruikbaar.")

    def _target_relative_path(self, topic: dict) -> Path:
        intent = topic["intent"]
        slug = topic["slug"]
        service = topic["service"]

        if intent == "commercial":
            return Path("commercial") / service / f"{slug}.md"

        return Path("kennisbank-auto") / f"{slug}.md"

    def generate_one(
        self,
        topic: dict,
        overwrite_generated: bool = False,
        overwrite_staged: bool = False,
        stage: bool = False,
    ) -> dict:
        intent = topic["intent"]

        if intent == "commercial":
            markdown = _generate_commercial_markdown(topic)
        else:
            markdown = self.writer.write_article(topic)

        self._validate_markdown(markdown, intent=intent)

        relative_path = self._target_relative_path(topic)

        generated_path = (self.generated_root / relative_path).resolve()
        generated_path.parent.mkdir(parents=True, exist_ok=True)

        generated_exists = generated_path.exists()
        if generated_exists and not overwrite_generated:
            raise FileExistsError(f"Draft bestaat al: {generated_path}")

        generated_path.write_text(
            markdown.strip() + "\n",
            encoding="utf-8",
            newline="\n",
        )

        staged_path = None
        staged_status = "not_staged"

        if stage:
            target_path = (self.repo / "content" / relative_path).resolve()
            target_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                target_path.relative_to(self.repo)
            except Exception:
                raise PermissionError("Target pad valt buiten de turboservices repo.")

            staged_exists = target_path.exists()

            if staged_exists and not overwrite_staged:
                staged_status = "skipped_existing"
            else:
                target_path.write_text(
                    markdown.strip() + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                staged_path = str(target_path)
                staged_status = "staged"

        return {
            "slug": topic["slug"],
            "seed_keyword": topic["seed_keyword"],
            "service": topic["service"],
            "intent": intent,
            "clicks": topic["clicks"],
            "impressions": topic["impressions"],
            "generated_path": str(generated_path),
            "generated_overwritten": generated_exists and overwrite_generated,
            "staged_path": staged_path,
            "staged_status": staged_status,
            "markdown": markdown,
        }