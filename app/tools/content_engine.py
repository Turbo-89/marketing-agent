import json

class ContentEngine:
    def __init__(self):
        with open("config/services.json", encoding="utf-8") as f:
            self.services = json.load(f)["services"]

        with open("config/regions.json", encoding="utf-8") as f:
            self.regions = json.load(f)["regions"]

    def generate(self, service, region):
        if service not in self.services:
            raise KeyError(f"Dienst onbekend: {service}")

        s = self.services[service]
        r = next((x for x in self.regions if x["slug"] == region), None)

        if not r:
            raise KeyError(f"Regio onbekend: {region}")

        return {
            "title": f"{s['title']} in {r['name']}",
            "description": s["description"],
            "service": service,
            "region": region,
            "image": f"/hero/{service}/{region}.webp",
            "sections": [
                {"title": s["title"], "body": s["intro"]},
                {"title": "Wat we doen", "items": s["bullets"]}
            ]
        }
