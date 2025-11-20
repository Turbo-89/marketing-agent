from app.website_generator import WebsiteGenerator

class CreateAgent:
    def __init__(self):
        self.gen = WebsiteGenerator()

    def create(self, service, region):
        result = self.gen.generate_page(service, region)
        return { "created": result }
