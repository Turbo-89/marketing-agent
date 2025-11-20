from openai import OpenAI

class KnowledgeWriter:
    def __init__(self):
        self.client = OpenAI()

    def write_article(self, title: str, service: str, region: str, intent: str):
        prompt = f"""
Schrijf een informatief kennisbank artikel over:
Titel: {title}
Dienst: {service}
Regio: {region}
Intentie: {intent}

Vereisten:
- korte zinnen
- technisch correct
- lokale relevantie voor regio {region}
- geen overbodige taal
- geen storytelling
- enkel feitelijke SEO-geschikte uitleg

Geef inhoud als pure tekst. Geen markdown.
"""

        result = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return result.choices[0].message["content"]
