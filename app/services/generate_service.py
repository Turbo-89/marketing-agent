# app/services/generate_service.py

from pathlib import Path
from app.tools.website import WebsiteGenerator

# ROOT = marketing-agent/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class GenerateService:
    """
    Genereert een geldige TSX-pagina én hero-afbeelding.
    Schrijft lokaal naar marketing-agent/generated/pages/...
    Wordt later door DeployService naar GitHub gestuurd.
    """

    def __init__(self):
        self.generator = WebsiteGenerator()
        self.output_dir = PROJECT_ROOT / "generated" / "pages"

    def generate(self, service: str, region: str) -> dict:
        # 1. bouw content + hero-pad + TSX
        tsx_content = self.generator.generate_page(service, region)

        # 2. schrijf lokaal naar /generated/pages
        rel_path = Path(service) / region / "page.tsx"
        target = self.output_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(tsx_content, encoding="utf-8")

        # 3. return metadata
        return {
            "status": "ok",
            "service": service,
            "region": region,
            "page_path": str(target),
        }
