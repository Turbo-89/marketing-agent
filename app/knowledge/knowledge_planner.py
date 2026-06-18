from __future__ import annotations

import os
from typing import Any

from app.knowledge.google_ads_csv_ingest import GoogleAdsCsvIngest
from app.knowledge.keyword_selector import KeywordSelector


class KnowledgePlanner:
    def __init__(self):
        self.ingest = GoogleAdsCsvIngest()
        self.selector = KeywordSelector()

    def detect_topics(
        self,
        csv_path: str | None = None,
        limit: int = 10,
        min_clicks: int = 1,
    ) -> list[dict[str, Any]]:
        source = csv_path or os.getenv("GOOGLE_ADS_CSV_PATH")
        if not source:
            raise ValueError("csv_path ontbreekt en GOOGLE_ADS_CSV_PATH is niet ingesteld.")

        rows = self.ingest.load(source)
        return self.selector.select(rows=rows, limit=limit, min_clicks=min_clicks)