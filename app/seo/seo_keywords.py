import json
import os
from openai import OpenAI

class KeywordEngine:
    def __init__(self, cache_path="generated/seo/keywords.json"):
        self.client = OpenAI()
        self.cache_path = cache_path
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def get_keywords(self, service: str, region: str):
        key = f"{service}_{region}"

        # Idempotentie: reeds gegenereerd
        if key in self.cache:
            return self.cache[key]

        prompt = (
            f"Genereer SEO-keywords voor dienst '{service}' "
            f"in regio '{region}'. "
            f"Geef output in JSON met velden: "
            f"primary_keywords, secondary_keywords, long_tail, intent."
        )

        result = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        keywords = json.loads(result.choices[0].message["content"])
        self.cache[key] = keywords

        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

        return keywords
