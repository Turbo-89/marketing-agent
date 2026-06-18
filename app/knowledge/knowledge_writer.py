from __future__ import annotations

from app.knowledge.markdown_article_writer import MarkdownArticleWriter


class KnowledgeWriter:
    def __init__(self):
        self.writer = MarkdownArticleWriter()

    def write_article(self, topic: dict) -> str:
        return self.writer.write_article(topic)