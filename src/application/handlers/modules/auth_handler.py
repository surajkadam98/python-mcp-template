"""Auth module — executes credential tools (always allowed, no session required)."""

from dataclasses import dataclass
from typing import Any

from application.services.auth_service import AuthService


@dataclass(frozen=True)
class AuthHandlerDeps:
    auth_service: AuthService


async def execute_auth_tool(name: str, args: dict[str, Any], deps: AuthHandlerDeps) -> Any:
    if name == "login":
        token = await deps.auth_service.login()
        return {"authenticated": deps.auth_service.is_authenticated(), "expires_at": token.expires_at}
    if name == "logout":
        await deps.auth_service.logout()
        return {"authenticated": False}
    if name == "auth_status":
        return {"authenticated": deps.auth_service.is_authenticated()}
    raise ValueError(f"Unhandled auth tool: {name!r}")
