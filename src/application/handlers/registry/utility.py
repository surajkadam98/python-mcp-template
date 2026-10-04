"""Utility module — tool definitions (no auth required)."""

import mcp.types as types

UTILITY_TOOLS: list[types.Tool] = [
    types.Tool(
        name="echo",
        description="Echo back the provided message.",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Text to echo back"},
            },
            "required": ["message"],
        },
    ),
    types.Tool(
        name="ping",
        description="Health check — returns server name, version, and API URL.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]

UTILITY_TOOL_NAMES: frozenset[str] = frozenset(t.name for t in UTILITY_TOOLS)
