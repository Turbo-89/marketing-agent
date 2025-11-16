import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

from app.models.tool_schemas import get_tool_definitions
from app.models.config_models import BusinessConfig

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def call_planning_agent(goal: str, business_config: BusinessConfig) -> Dict[str, Any]:
    """
    Basis-call naar OpenAI met tool-definities.
    Voor nu: alleen een beschrijvend plan (geen echte tool-uitvoering).
    """
    tools = get_tool_definitions()

    cfg_summary = {
        "brand": business_config.brand,
        "domains": business_config.domains.model_dump(),
        "services": [s.model_dump() for s in business_config.services],
        "regions": business_config.regions,
        "limits": business_config.limits.model_dump(),
    }

    messages = [
        {
            "role": "system",
            "content": (
                "Je bent een marketing-planner voor een ontstoppingsdienst. "
                "Je maakt een concreet stappenplan (site-structuur, landingspagina's) "
                "maar voert nog niets uit. Geef resultaat in JSON-vorm."
            ),
        },
        {
            "role": "user",
            "content": f"Doel: {goal}\n\nBusinessconfig:\n{cfg_summary}",
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
