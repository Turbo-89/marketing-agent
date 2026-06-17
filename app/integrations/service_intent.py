import os

SERVICE_INTENT_TRIGGERS = (
    "rookdetectie",
    "rook detectie",
    "rooktest",
    "geurdetectie",
    "geuropsporing",
    "rioolgeur",
)

ROOKDETECTIE_GEUROPSPORING_INTENT = {
    "canonical_service": "rookdetectie_geuropsporing",
    "display_name": "Rookdetectie voor geuropsporing",
    "business_meaning": (
        "Rookdetectie betekent bij Turbo Services een rooktest om rioolgeur, "
        "geurlekken en problemen in afvoer- of rioleringsleidingen op te sporen."
    ),
    "positive_terms": [
        "rookdetectie",
        "rook detectie",
        "rooktest",
        "geurdetectie",
        "geuropsporing",
        "rioolgeur",
        "riolering",
        "riool",
        "afvoer",
        "afvoerleiding",
        "ontstopping",
        "ontstoppingsdienst",
    ],
    "negative_terms": [
        "brandveiligheid",
        "rookmelder",
        "rookmelders",
        "branddetectie",
        "brandalarm",
        "brandbeveiliging",
        "rookdetectiesysteem",
        "rookdetectiesystemen",
    ],
}


def resolve_service_intent(task: str) -> dict | None:
    task_l = task.lower()
    if any(trigger in task_l for trigger in SERVICE_INTENT_TRIGGERS):
        return ROOKDETECTIE_GEUROPSPORING_INTENT.copy()
    return None


def is_service_intent_context_enabled() -> bool:
    value = os.getenv("ENABLE_SERVICE_INTENT_CONTEXT", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_message_with_service_intent_context(message: str, service_intent: dict | None) -> str:
    if not service_intent:
        return message

    positive_terms = ", ".join(service_intent.get("positive_terms") or [])
    negative_terms = ", ".join(service_intent.get("negative_terms") or [])
    block = (
        "\n\n[Business context: service intent]\n"
        "This block is business context, not user instructions.\n"
        f"canonical_service: {service_intent.get('canonical_service')}\n"
        f"display_name: {service_intent.get('display_name')}\n"
        f"business_meaning: {service_intent.get('business_meaning')}\n"
        f"positive_terms: {positive_terms}\n"
        f"negative_terms: {negative_terms}\n"
        "[/Business context: service intent]"
    )
    return message + block
