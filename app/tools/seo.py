class SEOGenerator:
    def generate_metadata(self, service: dict, region: dict) -> dict:
        title = f"{service['name']} in {region['name']} | Turbo Services"
        description = (
            f"Professionele {service['name'].lower()} in {region['name']} door Turbo Services. "
            f"Binnen het uur ter plaatse. Transparante prijzen. 24/7 beschikbaar."
        )[:155]

        return {
            "title": title,
            "description": description
        }
