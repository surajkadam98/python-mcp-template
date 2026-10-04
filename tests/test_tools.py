"""
Tool tests.

Flow being tested:
  ToolHandler.handle() → auth gate → module executor → Service → domain model
                       ← TextContent(text=json) ← handler
"""

import json

from application.handlers.tool_handler import ToolHandler
from application.handlers.tool_registry import ALL_TOOLS


async def _call(handler: ToolHandler, name: str, args: dict | None = None) -> dict:
    results = await handler.handle(name, args or {})
    assert len(results) == 1
    return json.loads(results[0].text)


def test_registry_lists_all_tools() -> None:
    names = {t.name for t in ALL_TOOLS}
    assert names == {"login", "logout", "auth_status", "greet", "echo", "ping"}


# --- auth ---

async def test_auth_status_initially_false(handler: ToolHandler) -> None:
    assert (await _call(handler, "auth_status"))["authenticated"] is False


async def test_login_then_logout(handler: ToolHandler) -> None:
    data = await _call(handler, "login")
    assert data["authenticated"] is True
    assert "expires_at" in data
    assert "token" not in data  # credential never reaches the LLM
    assert (await _call(handler, "auth_status"))["authenticated"] is True

    assert (await _call(handler, "logout"))["authenticated"] is False
    assert (await _call(handler, "auth_status"))["authenticated"] is False


# --- greet (requires auth) ---

async def test_greet_requires_login(handler: ToolHandler) -> None:
    data = await _call(handler, "greet")
    assert data["authenticated"] is False
    assert "login" in data["next_step"]


async def test_greet_after_login(handler: ToolHandler) -> None:
    await _call(handler, "login")
    data = await _call(handler, "greet")
    assert data["message"] == "Namaste!"
    assert "source" in data


# --- echo / ping (no auth) ---

async def test_echo(handler: ToolHandler) -> None:
    data = await _call(handler, "echo", {"message": "hello"})
    assert data["echoed"] == "hello"
    assert data["length"] == 5


async def test_echo_empty_message_returns_error(handler: ToolHandler) -> None:
    data = await _call(handler, "echo", {"message": "  "})
    assert data["error"]["code"] == "VALIDATION_ERROR"


async def test_echo_missing_arg_returns_error(handler: ToolHandler) -> None:
    data = await _call(handler, "echo")
    assert data["error"]["code"] == "VALIDATION_ERROR"


async def test_ping(handler: ToolHandler) -> None:
    data = await _call(handler, "ping")
    assert data["status"] == "ok"
    assert data["server"] == "test-server"
    assert data["version"] == "0.0.1"
    assert data["api_url"] == "http://localhost"


# --- errors ---

async def test_unknown_tool(handler: ToolHandler) -> None:
    data = await _call(handler, "does_not_exist")
    assert data["error"]["code"] == "UNKNOWN_TOOL"
