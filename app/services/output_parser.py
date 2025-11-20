import base64
from .storage import StorageService


class OutputParser:
    """
    Verwacht strikt JSON zoals in Stap 0 gedefinieerd.
    """

    @staticmethod
    def process(output: dict) -> dict:
        result = {}

        # Landing page opslaan
        if "landing_page" in output:
            page = output["landing_page"]
            filename = page.get("file")
            content = page.get("content")

            if filename and content:
                result["page_path"] = StorageService.save_page(filename, content)

        # Marketing plan opslaan
        if "marketing_plan" in output:
            plan_filename = f"{output.get('slug')}.json"
            result["plan_path"] = StorageService.save_plan(
                plan_filename,
                output.get("marketing_plan")
            )

        # Hero image opslaan (base64)
        if "hero_image" in output:
            hero = output["hero_image"]
            filename = hero.get("file")
            base64_data = hero.get("binary")

            if filename and base64_data:
                binary = base64.b64decode(base64_data)
                result["image_path"] = StorageService.save_image(filename, binary)

        return result
