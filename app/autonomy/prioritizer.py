class Prioritizer:
    def prioritize(self, analysis):
        items = []

        # 1. Bestaande pagina’s op basis van SEO-score
        for key, val in analysis["seo_data"].items():
            score = val.get("seo_score", 0)
            service, region = key.split("_", 1)

            prio = 100 - score  # lage score = hoge prio

            items.append({
                "type": "update",
                "service": service,
                "region": region,
                "priority": prio
            })

        # 2. Detecteer ontbrekende pagina’s
        existing = {f"{p['service']}_{p['region']}" for p in analysis["dienst_pages"]}

        for key in analysis["seo_data"].keys():
            if key not in existing:
                service, region = key.split("_", 1)
                items.append({
                    "type": "create",
                    "service": service,
                    "region": region,
                    "priority": 10  # zeer hoog
                })

        # sorteren op prioriteit (laag → eerst)
        items = sorted(items, key=lambda x: x["priority"])
        return items
