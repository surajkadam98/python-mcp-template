"""Auth module — tool definitions (always allowed, no session required)."""

import mcp.types as types

_EMPTY_SCHEMA = {"type": "object", "properties": {}, "required": []}

AUTH_TOOLS: list[types.Tool] = [
    types.Tool(
        name="login",
        description=(
            "Authenticate and receive a session token. MOCK — no credentials required. "
            "In production this would be replaced with a real credential flow."
        ),
        inputSchema=_EMPTY_SCHEMA,
    ),
    types.Tool(
        name="logout",
        description="Clear the current session credential from memory.",
        inputSchema=_EMPTY_SCHEMA,
    ),
    types.Tool(
        name="auth_status",
        description="Check whether the current session is authenticated.",
        inputSchema=_EMPTY_SCHEMA,
    ),
]

AUTH_TOOL_NAMES: frozenset[str] = frozenset(t.name for t in AUTH_TOOLS)
