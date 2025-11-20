import os
from openai import OpenAI
from PIL import Image, ImageOps

from app.tools.logo_map import get_logo


class HeroImageEngine:
    """
    Hero generator volgens TurboServices-specificaties:
    
    - AI genereert alleen een silhouet (vierkant 1024×1024)
    - Daarna lokaal resize naar hero-resolutie: 1792×1024
    - Dienstlogo wordt geladen (PNG/SVG->PNG), transparant
    - Beide lagen worden correct gecomposeerd in RGBA
    - Resultaat wordt opgeslagen als WEBP
    """

    HERO_WIDTH = 1792
    HERO_HEIGHT = 1024

    def __init__(self):
        self.client = OpenAI()

    # ---------------------------------------------------------
    # 1) Silhouet genereren via OpenAI + resize naar 1792×1024
    # ---------------------------------------------------------
    def _generate_silhouette(self, region: str) -> Image.Image:
        prompt = (
            f"Maak een zwart/donker abstract silhouet van de regio {region}. "
            f"Strakke lijnen, minimalistisch, transparante achtergrond. "
            f"Geen tekst, geen labels, enkel contour."
        )

        # OpenAI ondersteunt alleen vierkante resoluties (1024×1024)
        result = self.client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        tmp_path = "/mnt/data/tmp_silhouette.png"
        result.data[0].download(tmp_path)

        img = Image.open(tmp_path).convert("RGBA")

        # Correct resize naar TurboServices Hero formaat
        img = img.resize((self.HERO_WIDTH, self.HERO_HEIGHT), Image.LANCZOS)

        return img

    # ---------------------------------------------------------
    # 2) Dienstlogo openen + schalen (maximale breedte = 700px)
    # ---------------------------------------------------------
    def _open_logo(self, service: str) -> Image.Image:
        logo_path = get_logo(service)

        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo ontbreekt: {logo_path}")

        logo = Image.open(logo_path).convert("RGBA")

        # Logo proportioneel schalen zodat het nooit te groot wordt
        max_width = 700
        if logo.width > max_width:
            ratio = max_width / logo.width
            new_size = (int(logo.width * ratio), int(logo.height * ratio))
            logo = logo.resize(new_size, Image.LANCZOS)

        return logo

    # ---------------------------------------------------------
    # 3) Compositie van silhouet + logo
    # ---------------------------------------------------------
    def compose(self, service: str, region: str, output_path: str):
        # Idempotentie: hergenereren niet vereist
        if os.path.exists(output_path):
            return output_path

        # Silhouet genereren en op hero-grootte brengen
        silhouette = self._generate_silhouette(region)

        # Dienstlogo openen
        logo = self._open_logo(service)

        # Nieuwe base canvas
        base = Image.new("RGBA", (self.HERO_WIDTH, self.HERO_HEIGHT), (0, 0, 0, 0))

        # Laag 1 = silhouet
        base.alpha_composite(silhouette, (0, 0))

        # Laag 2 = logo (positie links onder)
        logo_x = 120
        logo_y = self.HERO_HEIGHT - logo.height - 100  # margin bottom
        base.alpha_composite(logo, (logo_x, logo_y))

        # Create directory if needed
        folder = os.path.dirname(output_path)
        os.makedirs(folder, exist_ok=True)

        # Opslaan als WEBP
        base.save(output_path, "WEBP")

        return output_path

