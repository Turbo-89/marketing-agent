from __future__ import annotations
from typing import List, Dict


QUESTION_MAP = {
    "services_offered": "Welke diensten levert Turbo Services exact (opsomming)?",
    "geographic_scope": "In welke regio’s/steden/provincies is Turbo Services actief?",
    "target_customers": "Is de doelgroep B2C, B2B of gemengd? (en welke segmenten)",
    "existing_channels": "Welke social media kanalen bestaan al? Geef URLs/profielnamen.",
}

def questions_for(missing: List[str]) -> List[str]:
    return [QUESTION_MAP.get(k, f"Vul ontbrekend feit aan: {k}") for k in missing]

def build_blocked_payload(missing: List[str]) -> Dict:
    return {
        "status": "blocked",
        "missing_information": missing,
        "questions": questions_for(missing),
    }
