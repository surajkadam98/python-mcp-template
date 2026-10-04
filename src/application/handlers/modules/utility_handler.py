"""Utility module — executes stateless utility tools, returns raw results."""

from dataclasses import dataclass
from typing import Any

from libraries.config import AppConfig
from libraries.errors import ValidationError


@dataclass(frozen=True)
class UtilityHandlerDeps:
    config: AppConfig


async def execute_utility_tool(name: str, args: dict[str, Any], deps: UtilityHandlerDeps) -> Any:
    if name == "echo":
        message = args.get("message")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError("'message' must be a non-empty string")
        return {"echoed": message, "length": len(message)}
    if name == "ping":
        return {
            "status": "ok",
            "server": deps.config.server.name,
            "version": deps.config.server.version,
            "api_url": deps.config.api.base_url,
        }
    raise ValueError(f"Unhandled utility tool: {name!r}")
