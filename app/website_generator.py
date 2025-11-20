from app.tools.directory_engine import DirectoryEngine
from app.tools.file_writer import FileWriter
from app.tools.content_engine import ContentEngine
from app.tools.hero_image import HeroImageEngine
from app.tools.tsx_generator import TSXGenerator
from app.seo_manager import SEOManager


class WebsiteGenerator:
    def __init__(self):
        self.dir = DirectoryEngine()
        self.fw = FileWriter()
        self.content = ContentEngine()
        self.hero = HeroImageEngine()
        self.tsx = TSXGenerator()
        self.seo = SEOManager()   # <-- SEO Engine correct toegevoegd

    def generate_page(self, service: str, region: str):
        # 1. Content ophalen uit services.json & regions.json
        data = self.content.generate(service, region)

        # 2. SEO-optimalisatie toepassen op titel & beschrijving
        seo = self.seo.run(
            service=service,
            region=region,
            raw_title=data["title"],
            raw_description=data["description"]
        )

        # SEO-metagegevens overschrijven
        data["title"] = seo["optimized_metadata"]["title"]
        data["description"] = seo["optimized_metadata"]["description"]

        # 3. Hero image genereren
        hero_path = f"public/hero/{service}/{region}.webp"
        self.hero.compose(service, region, hero_path)

        # 4. TSX-bestand genereren (TurboServices-compatibel)
        tsx_output = self.tsx.render(data)
        tsx_path = f"app/diensten/{service}/{region}/page.tsx"

        # 5. Schrijven van het pagina-bestand (nooit overschrijven)
        self.fw.write(tsx_path, tsx_output, overwrite=False)

        # 6. Output teruggeven
        return {
            "status": "OK",
            "page": tsx_path,
            "hero": hero_path,
            "seo_score": seo["seo_score"],
            "keywords": seo["keywords"]
        }
