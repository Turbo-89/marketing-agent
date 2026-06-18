from __future__ import annotations

from app.knowledge.knowledge_planner import KnowledgePlanner
from app.knowledge.knowledge_writer import KnowledgeWriter
from app.knowledge_generator import KnowledgeGenerator


class KnowledgeAgent:
    def __init__(self):
        self.planner = KnowledgePlanner()
        self.writer = KnowledgeWriter()
        self.generator = KnowledgeGenerator()

    def run(
        self,
        csv_path: str | None = None,
        limit: int = 10,
        min_clicks: int = 1,
        overwrite: bool = False,
        stage: bool = True,
    ) -> list[dict]:
        topics = self.planner.detect_topics(
            csv_path=csv_path,
            limit=limit,
            min_clicks=min_clicks,
        )

        results = []

        for topic in topics:
            markdown = self.writer.write_article(topic)

            generated = self.generator.generate(
                slug=topic["slug"],
                markdown=markdown,
                overwrite=overwrite,
                stage=stage,
            )

            results.append(
                {
                    "seed_keyword": topic["seed_keyword"],
                    "service": topic["service"],
                    "clicks": topic["clicks"],
                    "impressions": topic["impressions"],
                    **generated,
                }
            )

        return results