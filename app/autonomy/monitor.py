# app/autonomy/monitor.py

import os
import requests
from app.seo_manager import SEOManager
from app.memory import MemoryEngine


class MonitorEngine:
    """
    Controleert systeemstatus, API-updates en gegenereerde bestanden.
    Compatibel met TurboAgent 3.0 Autonomy.
    """

    def __init__(self):
        self.memory = MemoryEngine()
        self.seo_manager = SEOManager()

        # Nieuwe paden
        self.pages_path = "generated/pages"
        self.heroes_path = "generated/images"
        self.videos_path = "generated/videos"

    # ==========================================================
    # Bestanden controleren
    # ==========================================================

    def list_pages(self):
        """
        Detecteert alle pagina’s gegenereerd door ContentEngine.
        Nieuwe structuur:
        generated/pages/{service}/{region}/page.tsx
        """
        result = []

        if not os.path.exists(self.pages_path):
            return result

        for service in os.listdir(self.pages_path):
            s_path = os.path.join(self.pages_path, service)
            if not os.path.isdir(s_path):
                continue

            for region in os.listdir(s_path):
                r_path = os.path.join(s_path, region)
                page_file = os.path.join(r_path, "page.tsx")

                if os.path.exists(page_file):
                    result.append({
                        "service": service,
                        "region": region,
                        "file": page_file
                    })

        return result

    def list_heroes(self):
        """
        Detecteert alle hero-afbeeldingen.
        """
        if not os.path.exists(self.heroes_path):
            return []

        return [f for f in os.listdir(self.heroes_path)]

    def list_videos(self):
        """
        Detecteert alle promotievideo’s.
        """
        if not os.path.exists(self.videos_path):
            return []

        return [f for f in os.listdir(self.videos_path)]

    # ==========================================================
    # Externe API-monitoring
    # ==========================================================

    def check_api_updates(self):
        """
        Controleert OpenAI, GitHub en FAL beschikbaarheid.
        """

        status = {}

        # OpenAI API
        try:
            r = requests.get("https://api.openai.com/v1/models")
            status["openai"] = r.status_code
        except:
            status["openai"] = "error"

        # GitHub API
        try:
            r = requests.get("https://api.github.com/meta")
            status["github"] = r.status_code
        except:
            status["github"] = "error"

        # FAL Queue
        try:
            r = requests.get("https://queue.fal.run")
            status["fal"] = r.status_code
        except:
            status["fal"] = "error"

        return status

    # ==========================================================
    # Integrale analyse
    # ==========================================================

    def analyze(self):
        """
        Combineert:
        - SEO data
        - bestaande pagina’s
        - hero-afbeeldingen
        - video's
        - systeemstatus (API checks)
        """

        seo_data = self.seo_manager.get_metadata_overview()

        result = {
            "seo_data": seo_data,
            "pages": self.list_pages(),
            "heroes": self.list_heroes(),
            "videos": self.list_videos(),
            "api_status": self.check_api_updates(),
        }

        # Opslaan in geheugen
        self.memory.record("monitor_snapshot", result)

        return result
