"""Legacy shim.

Bestaat enkel om oude imports te blijven ondersteunen.
De echte implementatie zit in app/router/tool_router.py
"""

from app.router.tool_router import ToolRouter

__all__ = ["ToolRouter"]
