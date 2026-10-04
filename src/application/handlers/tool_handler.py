"""
Tool handler — thin dispatcher that routes a tool call to the owning
module's executor. Per-module logic lives in modules/*.py.

Pattern mirrors fabricbloc-mcp:
  handle(name, args) → module executor → service call → format result → TextContent
"""

import json
from dataclasses import dataclass
from typing import Any

import mcp.types as types

from application.handlers.modules.auth_handler import AuthHandlerDeps, execute_auth_tool
from application.handlers.modules.greeting_handler import GreetingHandlerDeps, execute_greeting_tool
from application.handlers.modules.utility_handler import UtilityHandlerDeps, execute_utility_tool
from application.handlers.registry.auth import AUTH_TOOL_NAMES
from application.handlers.registry.greeting import GREETING_TOOL_NAMES
from application.handlers.registry.utility import UTILITY_TOOL_NAMES
from application.services.auth_service import AuthService
from application.services.greeting_service import GreetingService
from libraries.config import AppConfig
from libraries.errors import AppError, format_error, to_app_error
from libraries.logger import get_logger

logger = get_logger(__name__)

_AUTH_PROMPT = {
    "authenticated": False,
    "message": "You need to login before using this tool. Do you want to login now?",
    "next_step": "Just say the word and I will call the 'login' tool for you.",
}


@dataclass(frozen=True)
class ToolHandlerDependencies:
    auth_service: AuthService
    greeting_service: GreetingService
    config: AppConfig


class ToolHandler:
    def __init__(self, deps: ToolHandlerDependencies) -> None:
        self._deps = deps

    async def handle(self, name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
        args = arguments or {}
        try:
            result = await self._execute(name, args)
            text = result if isinstance(result, str) else json.dumps(result, indent=2)
            return [types.TextContent(type="text", text=text)]
        except AppError as e:
            logger.warning("Tool %r error: %s", name, e)
            return [types.TextContent(type="text", text=format_error(e))]
        except Exception as e:
            logger.exception("Unexpected error in tool %r", name)
            return [types.TextContent(type="text", text=format_error(to_app_error(e)))]

    async def _execute(self, name: str, args: dict[str, Any]) -> Any:
        # Always-allowed: credential setup tools
        if name in AUTH_TOOL_NAMES:
            return await execute_auth_tool(name, args, AuthHandlerDeps(auth_service=self._deps.auth_service))

        # Always-allowed: utility tools have no auth requirement
        if name in UTILITY_TOOL_NAMES:
            return await execute_utility_tool(name, args, UtilityHandlerDeps(config=self._deps.config))

        # Everything else requires an authenticated session
        if name in GREETING_TOOL_NAMES:
            if not self._deps.auth_service.is_authenticated():
                return _AUTH_PROMPT
            return await execute_greeting_tool(
                name, args, GreetingHandlerDeps(greeting_service=self._deps.greeting_service)
            )
        raise AppError(f"Unknown tool: {name!r}", "UNKNOWN_TOOL", 400)
