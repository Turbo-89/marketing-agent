import numpy as np

class SEOAnalyzer:
    def score_page(self, keywords: dict, metadata: dict):
        score = 0

        if keywords["primary_keywords"]:
            score += 30

        score += len(keywords["long_tail"]) * 3

        score += metadata.get("score", 0)

        # Normalisatie score 0–100
        return min(100, max(0, int(score)))
