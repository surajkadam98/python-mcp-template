"""
Tool registry — merges all per-module tool definitions.

To add a module: create registry/<module>.py, then extend ALL_TOOLS below.
"""

import mcp.types as types

from application.handlers.registry.auth import AUTH_TOOLS
from application.handlers.registry.greeting import GREETING_TOOLS
from application.handlers.registry.utility import UTILITY_TOOLS

ALL_TOOLS: list[types.Tool] = [*AUTH_TOOLS, *GREETING_TOOLS, *UTILITY_TOOLS]

__all__ = ["ALL_TOOLS"]
