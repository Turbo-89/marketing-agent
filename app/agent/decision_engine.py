# app/agent/decision_engine.py

class DecisionEngine:
    """
    Zet SEOEngine-resultaten om in concrete acties:
    - pagina genereren
    - pagina herwerken
    - deploy uitvoeren
    """

    def decide(self, seo):
        actions = []

        # 1. Nieuwe pagina’s genereren waar regio-vraag is
        for target in seo["recommended_targets"]:
            actions.append({
                "tool": "generate",
                "args": {
                    "service": target["service"],
                    "region": target["region"]
                }
            })

        # 2. Onderscore pagina's herwerken (laag scorend)
        for lp in seo["low_pages"]:
            if lp["path"].startswith("/diensten/"):
                parts = lp["path"].split("/")
                if len(parts) >= 4:
                    service = parts[2]
                    region = parts[3]
                    actions.append({
                        "tool": "generate",
                        "args": {
                            "service": service,
                            "region": region
                        }
                    })

        # 3. Altijd deploy uitvoeren als er acties zijn
        if actions:
            actions.append({
                "tool": "deploy",
                "args": {}
            })

        return actions
