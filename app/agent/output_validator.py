from __future__ import annotations
import re
from typing import Dict, List, Any


FORBIDDEN_PHRASES = [
    "waarschijnlijk",
    "meestal",
    "doorgaans",
    "lijkt",
    "typisch",
    "in de sector",
    "vaak",
    "zal",
    "zou",
    "ruimte voor verbetering",
    "actief gebruik",
]

PERCENT_RE = re.compile(r"\b\d{1,3}\s*%|\b\d{1,3}\s*procent\b", re.IGNORECASE)
ABSOLUTE_CLAIM_RE = re.compile(
    r"\b(biedt|heeft|is|zijn|doet|werkt|gebruikt)\b", re.IGNORECASE
)

def validate_output(text: str, known_facts: Dict[str, Any]) -> List[str]:
    violations: List[str] = []
    low = text.lower()

    # 1) Verboden assumptie-taal
    for p in FORBIDDEN_PHRASES:
        if p in low:
            violations.append(f"Verboden assumptie/framing gedetecteerd: '{p}'")

    # 2) Percentages zonder bronvermelding (simpel en effectief)
    if PERCENT_RE.search(text):
        # accepteer alleen als er in dezelfde output ergens "bron" of "source" staat
        if "bron" not in low and "source" not in low:
            violations.append("Percentage/kwantitatieve claim zonder bronvermelding")

    # 3) Claims over diensten/doelgroep/kanalen zonder feitenbasis
    # Als facts ontbreken maar tekst doet absolute claims → fail.
    required = ["services_offered", "geographic_scope", "target_customers", "existing_channels"]
    missing = [k for k in required if k not in known_facts]

    if missing and ABSOLUTE_CLAIM_RE.search(text):
        violations.append(
            f"Output bevat stelligheden terwijl feiten ontbreken: missing={missing}"
        )

    return violations
