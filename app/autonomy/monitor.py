import os
import json

class Monitor:
    def __init__(self):
        # SEO data
        self.keywords_path = "generated/seo/keywords.json"
        self.seo = {}

        if os.path.exists(self.keywords_path):
            with open(self.keywords_path, encoding="utf-8") as f:
                self.seo = json.load(f)

    def get_existing_pages(self):
        pages = []
        base = "generated/app/diensten/"
        if not os.path.exists(base):
            return pages

        for service in os.listdir(base):
            service_path = os.path.join(base, service)
            if not os.path.isdir(service_path):
                continue

            for region in os.listdir(service_path):
                pages.append({
                    "service": service,
                    "region": region,
                    "path": f"{service}/{region}"
                })

        return pages

    def get_existing_knowledge(self):
        base = "generated/app/kennisbank/"
        if not os.path.exists(base):
            return []

        return [p for p in os.listdir(base)]

    def analyze(self):
        return {
            "seo_data": self.seo,
            "dienst_pages": self.get_existing_pages(),
            "kennisbank_pages": self.get_existing_knowledge()
        }
