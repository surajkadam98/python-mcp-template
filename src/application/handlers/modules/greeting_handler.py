"""Greeting module — executes greeting tools, returns raw results."""

from dataclasses import dataclass
from typing import Any

from application.services.greeting_service import GreetingService


@dataclass(frozen=True)
class GreetingHandlerDeps:
    greeting_service: GreetingService


async def execute_greeting_tool(name: str, args: dict[str, Any], deps: GreetingHandlerDeps) -> Any:
    if name == "greet":
        greeting = deps.greeting_service.greet()
        return {"message": greeting.message, "source": greeting.source}
    raise ValueError(f"Unhandled greeting tool: {name!r}")
