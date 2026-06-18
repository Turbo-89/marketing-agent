# app/router/tool_router.py

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from .tool_registry import ToolRegistry


class ToolRouter:
    """
    Verantwoordelijk voor:
    - Detecteren van tool-calls in LLM-output:
        [TOOL:analytics_report()]
        [TOOL:auto_marketing(service="ontstoppingen",region="antwerpen")]
    - Uitvoeren van tools via ToolRegistry.
    - Rechtstreekse aanroep:
        await tools.run("analytics_report")
        await tools.run("auto_marketing", service="...", region="...")
    """

    # Voorbeeld: [TOOL:auto_marketing(service="ontstoppingen",region="antwerpen")]
    TOOL_PATTERN = re.compile(r"\[TOOL:(\w+)\((.*?)\)\]")

    def __init__(self) -> None:
        self.registry = ToolRegistry()

    # -------------------------------------------------
    # 1. Interface voor RouterEngine
    # -------------------------------------------------
    async def detect_and_run(self, buffer: str) -> Optional[str]:
        """
        Zoekt in de volledige buffer naar een [TOOL:...] patroon.
        Als gevonden:
          - voert de tool uit
          - retourneert de tool-output als string (wordt gestreamd)
        Als niet gevonden:
          - retourneert None
        """

        match = self.TOOL_PATTERN.search(buffer)
        if not match:
            return None

        tool_name = match.group(1)
        arg_string = match.group(2)

        args = self._parse_args(arg_string)
        result = await self.registry.run_tool(tool_name, **args)

        # Tooloutput standaard naar string (JSON voor dict/list)
        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        return str(result)

    async def run(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Directe tool-oproep (zonder [TOOL:...] in de LLM-tekst),
        bv. in RouterEngine:
            await self.tools.run("analytics_report")
        of:
            await self.tools.run("auto_marketing", service="...", region="...")
        """
        return await self.registry.run_tool(tool_name, **kwargs)

    # -------------------------------------------------
    # 2. Hulpmethoden
    # -------------------------------------------------
    def _parse_args(self, arg_string: str) -> Dict[str, Any]:
        """
        Parser voor argumenten binnen [TOOL:...(...)].

        Ondersteunt patronen zoals:
          service="ontstoppingen", region="antwerpen", days=30

        Resultaat: dict, bv. {"service": "ontstoppingen", "region": "antwerpen", "days": 30}
        """

        args: Dict[str, Any] = {}

        if not arg_string.strip():
            return args

        # Eerst key="value" paren met quotes
        quoted_pairs = re.findall(r'(\w+)\s*=\s*"([^"]*)"', arg_string)
        used_keys = set()

        for key, value in quoted_pairs:
            args[key] = value
            used_keys.add(key)

        # Daarna ruwe key=value (zonder quotes) voor integers/bools
        for part in arg_string.split(","):
            part = part.strip()
            if not part or "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key in used_keys:
                continue  # al verwerkt

            # Type-coercion: int / float / bool, anders string
            if value.isdigit():
                args[key] = int(value)
            else:
                # True/False
                if value.lower() == "true":
                    args[key] = True
                elif value.lower() == "false":
                    args[key] = False
                else:
                    args[key] = value

        return args
