import json
from openai import OpenAI

class SEOKeywords:
    def __init__(self):
        self.client = OpenAI()

    def get_keywords(self, service: str, region: str):
        prompt = f"""
Geef een JSON-array met 8 tot 12 SEO-zoekwoorden voor dienst '{service}' in regio '{region}'.
Output *enkel* een geldige JSON-array, geen tekst errond.
"""

        result = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}]
        )

        content = result.choices[0].message.content

        try:
            return json.loads(content)
        except Exception:
            return ["riool", "riolering", "ontstopping", "herstelling"]
