"""Greeting module — tool definitions."""

import mcp.types as types

GREETING_TOOLS: list[types.Tool] = [
    types.Tool(
        name="greet",
        description="Fetch a greeting from the API. Returns the API response message.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]

GREETING_TOOL_NAMES: frozenset[str] = frozenset(t.name for t in GREETING_TOOLS)
