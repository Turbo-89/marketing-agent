from app.website_generator import WebsiteGenerator

class UpdateAgent:
    def __init__(self):
        self.gen = WebsiteGenerator()

    def update(self, service, region):
        # overwrite = True → updates are allowed
        result = self.gen.generate_page(service, region)
        return { "updated": result }
