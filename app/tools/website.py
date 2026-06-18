from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from app.tools.content_engine import ContentEngine
from app.tools.hero_image import HeroImageEngine

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class WebsiteGenerator:
    def __init__(self) -> None:
        self.content_engine = ContentEngine()
        self.hero_engine = HeroImageEngine()

    def generate_page(self, service: str, region: str) -> str:
        data = self.content_engine.generate_content(service, region)
        hero_web_path = self.hero_engine.generate_if_missing(service, region)
        return self._render_tsx(data, hero_web_path)

    def write_page_to_disk(self, service: str, region: str, content: str) -> str:
        target_dir = BASE_DIR / "generated" / "pages" / service / region
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "page.tsx"
        target_file.write_text(content, encoding="utf-8")
        return str(target_file)

    def _render_tsx(self, data: Dict[str, Any], hero_web_path: str) -> str:
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
            "sections",
            "cta_title",
            "cta_text",
            "cta_btn",
        ]

        for key in required_keys:
            if key not in data:
                raise KeyError(f"ContentEngine ontbrekende sleutel: {key}")

        def esc(value: str) -> str:
            if value is None:
                return ""
            return (
                str(value)
                .replace("\\\\", "\\\\\\\\")
                .replace('"', '\\"')
                .replace("\\n", "\\\\n")
            )

        sections_literal = json.dumps(data["sections"], ensure_ascii=False, indent=2)

        tsx = f'''import type {{ Metadata }} from "next";
import DienstPageLayout from "@/components/diensten/DienstPage";
import {{ REGION_CITIES }} from "@/content/regions";

export const metadata: Metadata = {{
  title: "{esc(data["metadata_title"])}",
  description: "{esc(data["metadata_description"])}",
}};

export default function Page() {{
  const municipalities = REGION_CITIES["{esc(data["region"])}"] ?? [];
  const muniText = municipalities.slice(0, 12).join(", ");

  const intro =
    "{esc(data["intro"])}" +
    (muniText ? `\\n\\nWerkgebied: ${{muniText}} en omgeving.` : "");

  const sections = {sections_literal}.map((s, idx) => {{
    if (!muniText) return s;
    if (idx === 0) {{
      return {{
        ...s,
        body: s.body + `\\n\\nActief in {esc(data["regionLabel"])}: ${{muniText}} en omgeving.`
      }};
    }}
    return s;
  }});

  const ctaBody =
    "{esc(data["cta_text"])}" +
    (muniText ? `\\n\\nWerkgebied: ${{muniText}} en omgeving.` : "");

  const props = {{
    brand: "{esc(data["brand"])}",
    regionLabel: "{esc(data["regionLabel"])}",
    serviceName: "{esc(data["serviceName"])}",
    heroTitle: "{esc(data["h1"])}",
    intro,
    sections,
    ctaTitle: "{esc(data["cta_title"])}",
    ctaBody,
    ctaButton: "{esc(data["cta_btn"])}",
    serviceKey: "{esc(data["service"])}",
    heroImagePath: "{esc(hero_web_path)}",
    municipalities,
  }} as const;

  return <DienstPageLayout {{...props}} />;
}}
'''
        return tsx
