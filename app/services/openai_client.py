import os
import json
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

from app.models.tool_schemas import get_tool_definitions
from app.models.config_models import BusinessConfig

load_dotenv()

# Centrale OpenAI-client (hergebruikt door andere modules zoals hero_image)
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_openai_client() -> OpenAI:
    """
    Geeft de gedeelde OpenAI-client terug.
    Wordt o.a. gebruikt door hero_image.py voor image generation.
    """
    return _client


async def call_planning_agent(goal: str, business_config: BusinessConfig) -> Dict[str, Any]:
    """
    Roept het planningsmodel aan om te beslissen welke landingspagina's
    (dienst × regio) prioriteit hebben.

    - gebruikt get_tool_definitions() als context
    - gebruikt de volledige BusinessConfig (model_dump) als input
    - geeft 1 JSON-object terug in veld "raw_response"
    """

    tools = get_tool_definitions()

    # Pydantic v2: model_dump() geeft de volledige config als dict
    cfg_dict = business_config.model_dump()
    cfg_summary = json.dumps(cfg_dict, ensure_ascii=False, indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                "Je bent een marketing-planningsagent voor Turbo Services. "
                "Op basis van de businessconfiguratie en het doel van de gebruiker "
                "maak je een concreet plan welke landingspagina's (dienst × regio) "
                "het eerst moeten worden gegenereerd. "
                "Je antwoordt ALTIJD in strikt geldige JSON."
            ),
        },
        {
            "role": "user",
            "content": f"Doel: {goal}\n\nBusinessconfig (JSON):\n{cfg_summary}",
        },
    ]

    completion = _client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=tools,
        tool_choice="none",
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    return {"raw_response": content}
