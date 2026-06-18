from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def _to_int(value: str | None) -> int:
    if value is None:
        return 0
    raw = str(value).strip().replace(".", "").replace(",", ".")
    raw = raw.replace("%", "").replace("€", "").replace("EUR", "").strip()
    if not raw:
        return 0
    try:
        return int(float(raw))
    except ValueError:
        return 0


def _to_float(value: str | None) -> float:
    if value is None:
        return 0.0
    raw = str(value).strip()
    raw = raw.replace("€", "").replace("EUR", "").replace("%", "").strip()
    raw = raw.replace(".", "").replace(",", ".")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _clean_keyword(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _detect_match_type(row: dict[str, Any]) -> str:
    value = (row.get("Opties voor zoekwoorden") or "").strip().lower()
    if "exact" in value:
        return "exact"
    if "woordgroep" in value:
        return "phrase"
    if "breed" in value:
        return "broad"
    return value or "unknown"


class GoogleAdsCsvIngest:
    REQUIRED_HEADERS = {
        "Zoekwoord",
        "Campagne",
        "Advertentiegroep",
        "Vertoningen",
        "Aantal klikken",
    }

    def _read_rows(self, csv_path: str | Path) -> list[dict[str, str]]:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV niet gevonden: {path}")

        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as fh:
            lines = fh.readlines()

        header_index = None
        for idx, line in enumerate(lines):
            if "Zoekwoordstatus" in line and "Zoekwoord" in line and "Advertentiegroep" in line:
                header_index = idx
                break

        if header_index is None:
            raise ValueError("Headerregel van Google Ads CSV niet gevonden.")

        reader = csv.DictReader(lines[header_index:])
        if reader.fieldnames is None:
            raise ValueError("CSV bevat geen geldige kolommen.")

        missing = self.REQUIRED_HEADERS.difference(set(reader.fieldnames))
        if missing:
            raise ValueError(f"CSV mist verplichte kolommen: {sorted(missing)}")

        return list(reader)

    def load(self, csv_path: str | Path) -> list[dict[str, Any]]:
        raw_rows = self._read_rows(csv_path)
        results: list[dict[str, Any]] = []

        for row in raw_rows:
            keyword = _clean_keyword(row.get("Zoekwoord"))

            if not keyword:
                continue

            keyword_l = keyword.lower()
            if keyword_l.startswith("totaal:"):
                continue

            results.append(
                {
                    "keyword": keyword,
                    "keyword_status": (row.get("Zoekwoordstatus") or "").strip(),
                    "match_type": _detect_match_type(row),
                    "campaign": (row.get("Campagne") or "").strip(),
                    "ad_group": (row.get("Advertentiegroep") or "").strip(),
                    "status": (row.get("Status") or "").strip(),
                    "final_url": (row.get("Uiteindelijke URL") or "").strip(),
                    "interactions": _to_int(row.get("Interacties")),
                    "clicks": _to_int(row.get("Aantal klikken")),
                    "impressions": _to_int(row.get("Vertoningen")),
                    "conversions": _to_float(row.get("Conversies")),
                    "conversion_rate": _to_float(row.get("Conv. perc.")),
                    "avg_cpc": _to_float(row.get("Gem. CPC")),
                    "avg_cost": _to_float(row.get("Gem. kosten")),
                    "cost": _to_float(row.get("Kosten")),
                    "cost_per_conversion": _to_float(row.get("Kosten/conv.")),
                    "currency": (row.get("Valutacode") or "").strip(),
                }
            )

        return results