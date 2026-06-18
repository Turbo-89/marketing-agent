# app/tools/agent_tools.py

from __future__ import annotations

from app.tools.website import WebsiteGenerator
from app.services.deploy_service import DeployService
from app.tools.content_engine import ContentEngine


# ============================================================
# GENERATE TOOL (Optie B)
# ============================================================

class GeneratePageTool:
    """
    Tool: generate
    Genereert lokaal een pagina + hero (Optie B).
    WebsiteGenerator.generate_page() genereert TSX,
    WebsiteGenerator.write_page_to_disk() schrijft naar /generated/pages/.
    """

    def run(self, service: str, region: str):
        generator = WebsiteGenerator()

        # 1. Pagina renderen (TSX-string)
        tsx = generator.generate_page(service, region)

        # 2. Lokaal wegschrijven
        page_path = generator.write_page_to_disk(service, region, tsx)

        return (
            f"[GENERATE OK]\n"
            f"Service: {service}\n"
            f"Regio: {region}\n"
            f"TSX-bestand: {page_path}"
        )


# ============================================================
# DEPLOY TOOL (Optie B)
# ============================================================

class DeployPageTool:
    """
    Tool: deploy
    Zet een lokaal gegenereerde pagina live naar GitHub (Optie B).
    """

    def run(self, service: str, region: str):
        deployer = DeployService(
            owner="Turbo-89",
            repo="turboservices",
            branch="main",
        )

        result = deployer.deploy_page(service, region)

        return (
            f"[DEPLOY OK]\n"
            f"Service: {service}\n"
            f"Regio: {region}\n"
            f"GitHub-bestand: {result['path']}"
        )


# ============================================================
# LIST SERVICES
# ============================================================

class ListServicesTool:
    """
    Geeft alle beschikbare services uit config/services.json.
    """

    def run(self):
        ce = ContentEngine()
        return ", ".join(sorted(ce.services.keys()))


# ============================================================
# LIST REGIONS
# ============================================================

class ListRegionsTool:
    """
    Geeft alle beschikbare regio’s uit config/regions.json.
    """

    def run(self):
        ce = ContentEngine()
        return ", ".join(sorted([r["slug"] for r in ce.regions]))

# -------------------------------
# ANALYTICS REPORT TOOL
# -------------------------------

from app.agent.analytics_engine import AnalyticsEngine

class AnalyticsReportTool:
    """
    Tool die GA4-data ophaalt en combineert tot één gestructureerd rapport.
    Wordt gebruikt door RouterEngine om SEO-beslissingen te nemen.
    """

    def __init__(self, property_id="494314714"):
        self.engine = AnalyticsEngine(property_id)

    def run(self, query: str) -> dict:
        """
        query wordt genegeerd — tool levert altijd volledig rapport.
        Dit is bewust gedaan: de AI-agent moet ALTIJD volledige data krijgen.
        """

        sessions = self.engine.get_sessions()
        pageviews = self.engine.get_pageviews()
        top_pages = self.engine.get_top_pages()
        engagement = self.engine.get_engagement_by_page()

        return {
            "sessions": self._parse_metric(sessions),
            "pageviews": self._parse_metric(pageviews),
            "top_pages": self._parse_table(top_pages),
            "engagement": self._parse_table(engagement)
        }

    # -------------------------------------------------
    # Helpers om GA4 structured data om te zetten
    # -------------------------------------------------
    def _parse_metric(self, report):
        return int(report.rows[0].metric_values[0].value)

    def _parse_table(self, report):
        result = []
        for row in report.rows:
            item = {}
            for i, header in enumerate(report.dimension_headers):
                item[header.name] = row.dimension_values[i].value

            for i, header in enumerate(report.metric_headers):
                item[header.name] = row.metric_values[i].value

            result.append(item)
        return result

