
# app/router/tool_registry.py

from __future__ import annotations

import inspect
from typing import Any, Dict

from app.tools.memory_search_tool import MemorySearchTool
from app.tools.web_search_tool import WebSearchTool
from app.tools.document_tools import DocsSearchTool, DocsGetTool
from app.tools.analytics_tool import AnalyticsSummaryTool
from app.tools.auto_marketing_tool import AutoMarketingTool
from app.tools.marketing_insights import MarketingInsightsTool
from app.tools.agent_tools import (
    GeneratePageTool,
    DeployPageTool,
    ListServicesTool,
    ListRegionsTool,
    AnalyticsReportTool,
)


class ToolRegistry:
    """
    Centrale registry voor alle tools van TurboAgent.

    Namen in deze registry MOETEN overeenkomen met:
    - de `name` attributen in de tools (waar aanwezig), en
    - de namen die in prompts/RouterEngine gebruikt worden, bv.:
        [TOOL:analytics_report()]
        [TOOL:auto_marketing(service="...",region="...")]
    """

    def __init__(self) -> None:
        # Instanties van alle relevante tools
        self.registry: Dict[str, Any] = {
            # Geheugen / documenten
            "memory_search": MemorySearchTool(),
            "docs_search": DocsSearchTool(),
            "docs_get": DocsGetTool(),

            # Web search
            "web_search": WebSearchTool(),

            # Analytics / marketing insights
            "analytics_summary": AnalyticsSummaryTool(),
            "analytics_report": AnalyticsReportTool(),     # GA4-engine
            "marketing_insights": MarketingInsightsTool(),

            # Auto marketing pipeline
            "auto_marketing": AutoMarketingTool(),

            # Website generatie / deploy
            "generate_page": GeneratePageTool(),
            "deploy_page": DeployPageTool(),
            "list_services": ListServicesTool(),
            "list_regions": ListRegionsTool(),
        }

    def list(self) -> list[str]:
        """Retourneert alle geregistreerde tool-namen."""
        return sorted(self.registry.keys())

    def get(self, name: str) -> Any:
        """Haalt een tool op of geeft een duidelijke fout."""
        tool = self.registry.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")
        return tool

    async def run_tool(self, name: str, **kwargs: Any) -> Any:
        """
        Voert een tool uit.

        Ondersteunt zowel:
        - async def run(...)
        - def run(...)
        """
        tool = self.get(name)

        if not hasattr(tool, "run"):
            raise ValueError(f"Tool '{name}' heeft geen 'run' methode.")

        result = tool.run(**kwargs)

        # async tool
        if inspect.isawaitable(result):
            return await result

        # sync tool
        return result
