from typing import Dict, Any, List


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Geeft de tools terug zoals we ze aan OpenAI zullen aanbieden.
    Voor nu gebruiken we ze nog niet operationeel, maar de definities liggen al vast.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "propose_landing_pages",
                "description": (
                    "Bepaal op basis van businessconfig welke (service, regio) "
                    "landingspagina's er moeten bestaan en welk pad ze krijgen."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lijst van service keys waarvoor pagina's moeten gepland worden."
                        },
                        "region_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lijst van regiostrings (bijv. 'antwerpen')."
                        },
                    },
                    "required": ["service_keys", "region_keys"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_page_content",
                "description": (
                    "Genereer SEO-geschikte content voor een dienst in een regio "
                    "(H1, body, bullets, meta-title, meta-description, CTA)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_key": {"type": "string"},
                        "region": {"type": "string"},
                    },
                    "required": ["service_key", "region"],
                },
            },
        },
    ]
