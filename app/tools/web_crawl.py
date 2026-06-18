import requests
from bs4 import BeautifulSoup
from datetime import datetime


class WebCrawlExecutor:
    """
    Zeer eenvoudige, feitelijke crawler.
    GEEN interpretatie.
    GEEN samenvatting.
    """

    def crawl(self, url: str) -> dict:
        r = requests.get(url, timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        text_blocks = [
            t.strip()
            for t in soup.stripped_strings
            if len(t.strip()) > 3
        ]

        return {
            "fetched_at": datetime.utcnow().isoformat(),
            "url": url,
            "text_sample": text_blocks[:50],  # max 50 zichtbare tekstblokken
            "has_images": bool(soup.find("img")),
            "has_links": bool(soup.find("a")),
        }
