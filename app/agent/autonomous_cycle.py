# app/agent/autonomous_cycle.py

from .seo_engine import SEOEngine
from .decision_engine import DecisionEngine
from .analytics_engine import AnalyticsEngine


class AutonomousCycle:
    """
    Automatische marketingcyclus:
    - Analytics ophalen
    - SEO analysetoestand bepalen
    - DecisionEngine genereert tool-acties
    """

    def __init__(self, memory, ga4_property: str):
        self.memory = memory
        self.analytics = AnalyticsEngine(ga4_property)
        self.seo = SEOEngine(self.analytics)
        self.decider = DecisionEngine()

    async def run(self):
        # 1. SEO metrics opbouwen
        seo_data = self.seo.analyze()

        # 2. Welke acties moeten uitgevoerd?
        actions = self.decider.decide(seo_data)

        # AutonomousCycle voert niet uit → RouterEngine doet dit.
        return actions

