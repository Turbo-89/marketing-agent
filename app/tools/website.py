from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

from app.tools.content import ContentEngine
from app.tools.hero_image import HeroImageEngine  # jouw bestaande hero engine gebruiken

# Repo root = .../marketing-agent
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class WebsiteGenerator:
    """
    Genereert de volledige Next.js TSX-pagina voor een dienst + regio.
    - Haalt content op via ContentEngine (deterministisch)
    - Zorgt voor hero-afbeelding via HeroImageEngine
    - Schrijft page.tsx naar app/diensten/{service}/{regio}/page.tsx
    """

    def __init__(self) -> None:
        self.content_engine = ContentEngine()
        self.hero_engine = HeroImageEngine()

    # ---------- Hoofdfuncties ----------

    def generate_page(self, service: str, region: str) -> str:
        """
        Gebruikt door /agent/test-generate:
        - Bouwt content dict
        - Zorgt dat hero-afbeelding bestaat
        - Rendert TSX-content (string)
        """
        data = self.content_engine.generate_content(service, region)
        hero_web_path = self.hero_engine.generate_if_missing(service, region)
        return self._render_tsx(data, hero_web_path)

    def write_page_to_disk(self, service: str, region: str, content: str) -> str:
        """
        Gebruikt door /agent/deploy:
        - Schrijft de TSX-content naar app/diensten/{service}/{region}/page.tsx
        - Geeft het absolute pad terug (handig voor logging)
        """
        target_dir = BASE_DIR / "app" / "diensten" / service / region
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "page.tsx"
        target_file.write_text(content, encoding="utf-8")
        return str(target_file)

    # ---------- Interne helpers ----------

    def _render_tsx(self, data: Dict[str, Any], hero_web_path: str) -> str:
        """
        Zet het data-dict + hero-pad om in een geldige Next.js App Router page.tsx
        die jouw bestaande DienstPageLayout gebruikt.
        """
        required_keys = [
            "service",
            "region",
            "brand",
            "serviceName",
            "regionLabel",
            "metadata_title",
            "metadata_description",
            "h1",
            "intro",
            "heroImageKey",
            "sections",
            "cta_title",
            "cta_text",
            "cta_btn",
        ]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"ContentEngine ontbrekende key: {key}")

        # eenvoudige escaping voor TSX strings
        def esc(value: str) -> str:
            if value is None:
                return ""
            return (
                str(value)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )

        # secties als literal array in TSX
        sections_literal = json.dumps(
            data["sections"], ensure_ascii=False, indent=2
        )

        # Hero wordt in layout zelf bepaald op basis van heroImageKey,
        # maar we geven heroWebPath mee voor de volledigheid indien je het later wil gebruiken.
        # Momenteel wordt heroImageKey gebruikt door jouw DienstPageLayout + hero.ts.
        tsx = f'''import type {{ Metadata }} from "next";
import DienstPageLayout from "@/components/diensten/DienstPage";

export const metadata: Metadata = {{
  title: "{esc(data["metadata_title"])}",
  description: "{esc(data["metadata_description"])}",
}};

export default function Page() {{
  const props = {{
    brand: "{esc(data["brand"])}",
    regionLabel: "{esc(data["regionLabel"])}",
    serviceName: "{esc(data["serviceName"])}",
    h1: "{esc(data["h1"])}",
    intro: "{esc(data["intro"])}",
    sections: {sections_literal},
    cta: {{
      title: "{esc(data["cta_title"])}",
      body: "{esc(data["cta_text"])}",
      button: "{esc(data["cta_btn"])}",
    }},
    serviceKey: "{esc(data["service"])}",
    heroImageKey: "{esc(data["heroImageKey"])}",
    heroImagePath: "{esc(hero_web_path)}",
  }} as const;

  return <DienstPageLayout {{...props}} />;
}}
'''
        return tsx


