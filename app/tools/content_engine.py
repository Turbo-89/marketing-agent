# app/tools/content_engine.py
import json
from pathlib import Path
from app.config.region_map import get_region_communes

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"


class ContentEngine:
    def __init__(self):
        with open(CONFIG_DIR / "services.json", encoding="utf-8") as f:
            self.services = json.load(f)["services"]

        with open(CONFIG_DIR / "regions.json", encoding="utf-8") as f:
            self.regions = json.load(f)["regions"]

    def generate_content(self, service: str, region: str) -> dict:
        # -------------------------------
        # SERVICE VALIDEREN
        # -------------------------------
        if service not in self.services:
            raise KeyError(f"Dienst onbekend: {service}")

        s = self.services[service]

        # -------------------------------
        # REGIO opzoeken
        # -------------------------------
        r = next((x for x in self.regions if x["slug"] == region), None)
        if not r:
            raise KeyError(f"Regio onbekend: {region}")

        region_label = r["name"]

        # -------------------------------
        # GEMEENTEN per marketingregio
        # -------------------------------
        communes = get_region_communes(region)
        communes_text = ", ".join(communes)

        # -------------------------------
        # SECTIES opbouwen
        # -------------------------------
        sections = []

        # 1. Intro
        intro_text = s["intro"].replace("{REGIO}", region_label)
        sections.append({
            "title": s["title"],
            "body": intro_text
        })

        # 2. Bullets
        if "bullets" in s and s["bullets"]:
            bullets_text = "\n".join(f"- {b}" for b in s["bullets"])
            sections.append({
                "title": "Wat we doen",
                "body": bullets_text
            })

        # 3. Workflow
        if "workflow" in s:
            wf_text = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(s["workflow"]))
            sections.append({
                "title": "Werkwijze",
                "body": wf_text
            })

        # 4. Prijzen
        if "pricing_items" in s:
            price_text = s["pricing_intro"] + "\n\n" + "\n".join(f"- {p}" for p in s["pricing_items"])
            sections.append({
                "title": "Tarieven",
                "body": price_text
            })

        # 5. Urgentie
        if "urgency" in s:
            sections.append({
                "title": "Waarom snel ingrijpen?",
                "body": s["urgency"]
            })

        # -------------------------------
        # OUTPUT
        # -------------------------------
        return {
            "communes": communes,
            "communes_text": communes_text,
            "service": service,
            "region": region,
            "brand": "Turbo Services",
            "serviceName": s["title"],
            "regionLabel": region_label,
            "metadata_title": f"{s['title']} in {region_label}",
            "metadata_description": s["description"],
            "h1": s["hero"],
            "intro": intro_text,
            "heroImageKey": f"{service}",
            "sections": sections,
            "cta_title": s["cta_title"],
            "cta_text": s["cta_text"].replace("{REGIO}", region_label),
            "cta_btn": s["cta_btn"],
        }
