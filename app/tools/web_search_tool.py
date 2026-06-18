import requests
from bs4 import BeautifulSoup

class WebSearchTool:
    name = "web_search"

    async def run(self, query: str):
        """
        Haalt zoekresultaten van Google SERP op.
        Geen scraping van accounts, enkel publieke SERP.
        Compatibel met alle bestaande tooling en router-engine.
        """

        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=10)
        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        results = []
        for block in soup.select("div.g")[:5]:
            title = block.find("h3")
            snippet = block.find("span")
            if title:
                results.append({
                    "title": title.get_text(strip=True),
                    "snippet": snippet.get_text(strip=True) if snippet else "",
                })

        return {
            "query": query,
            "results": results
        }
