# app/tools/tsx_generator.py
import json


class TSXGenerator:
    """
    TSXGenerator V3 – Optie B
    Bouwt een volledige Next.js page.tsx voor dienst + regio,
    100% compatibel met Turboservices /components/diensten/DienstPage.tsx.
    """

    def render(self, data: dict, hero_web_path: str) -> str:
        """
        data komt van ContentEngine V3.
        hero_web_path komt van HeroImageEngine V3 (bv. /generated/assets/x.webp).
        """

        # verplichte velden
        required = [
            "brand",
            "serviceName",
            "regionLabel",
            "heroTitle",
            "intro",
            "sections",
            "cta_title",
            "cta_text",
            "cta_btn",
            "service",
            "region",
            "heroImageKey",
            "metadata_title",
            "metadata_description",
        ]
        for key in required:
            if key not in data:
                raise KeyError(f"ContentEngine ontbrekende sleutel: {key}")

        # Secties veilig naar JSON literal
        sections_literal = json.dumps(data["sections"], ensure_ascii=False, indent=2)

        # eenvoudige escape
        def esc(x: str) -> str:
            if x is None:
                return ""
            return str(x).replace("\\", "\\\\").replace('"', '\\"')

        # Volledige TSX-structuur volgens jouw turboservices-layout
        return f'''
import type {{ Metadata }} from "next";
import DienstPageLayout from "@/components/diensten/DienstPage";

export const metadata: Metadata = {{
  title: "{esc(data["metadata_title"])}",
  description: "{esc(data["metadata_description"])}",
}};

export default function Page() {{
  const props = {{
    brand: "{esc(data["brand"])}",
    serviceName: "{esc(data["serviceName"])}",
    regionLabel: "{esc(data["regionLabel"])}",
    heroTitle: "{esc(data["heroTitle"])}",
    intro: "{esc(data["intro"])}",
    sections: {sections_literal},
    ctaTitle: "{esc(data["cta_title"])}",
    ctaBody: "{esc(data["cta_text"])}",
    ctaButton: "{esc(data["cta_btn"])}",
    serviceKey: "{esc(data["service"])}",
    heroImageKey: "{esc(data["heroImageKey"])}",
    heroImagePath: "{esc(hero_web_path)}",
  }} as const;

  return <DienstPageLayout {{...props}} />;
}}
'''.strip()
