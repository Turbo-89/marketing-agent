import json
from app.website_generator import WebsiteGenerator

class GenerateManager:
    def __init__(self):
        with open("config/services.json", encoding="utf-8") as f:
            self.services = list(json.load(f)["services"].keys())

        with open("config/regions.json", encoding="utf-8") as f:
            self.regions = [x["slug"] for x in json.load(f)["regions"]]

        self.generator = WebsiteGenerator()

    def generate_all(self):
        results = []
        for service in self.services:
            for region in self.regions:
                result = self.generator.generate_page(service, region)
                results.append(result)
        return results
