from openai import OpenAI

class MetadataEngine:
    def __init__(self):
        self.client = OpenAI()

    def optimize_metadata(self, title: str, description: str, keywords: dict):
        prompt = f"""
Optimaliseer metadata:
Titel: {title}
Beschrijving: {description}
Keywords: {keywords['primary_keywords']}
Long-tail: {keywords['long_tail']}

Geef antwoord in JSON:
{{
  "title": "",
  "description": "",
  "alts": ["", ""],
  "score": 0
}}
"""
        result = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(result.choices[0].message["content"])
