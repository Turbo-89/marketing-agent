import os
from app.knowledge.knowledge_planner import KnowledgePlanner
from app.knowledge.knowledge_writer import KnowledgeWriter
from app.knowledge_generator import KnowledgeGenerator

class KnowledgeAgent:
    def __init__(self):
        self.planner = KnowledgePlanner()
        self.writer = KnowledgeWriter()
        self.generator = KnowledgeGenerator()

    def run(self):
        topics = self.planner.detect_topics()
        results = []

        for t in topics:
            slug = t["slug"]
            path = f"app/kennisbank/{slug}/page.tsx"

            # overslaan als pagina reeds bestaat
            if os.path.exists(os.path.join("generated", path)):
                continue

            article = self.writer.write_article(
                title=t["title"],
                service=t["service"],
                region=t["region"],
                intent=t["intent"]
            )

            created = self.generator.generate(
                slug=slug,
                title=t["title"],
                body=article
            )

            results.append(created)

        return results
