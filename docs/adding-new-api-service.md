# Adding a New API Service

This guide walks through every file you touch to add a new API service. The example adds a `FruitService` that calls a `/fruits` endpoint and exposes it as a **`fruit` module** (registry + executor).

---

## The 7-step checklist

| Step | File | What you add |
|------|------|-------------|
| 1 | `src/domain/models.py` | The response type |
| 2 | `src/application/services/fruit_service.py` | The service class |
| 3 | `src/application/handlers/registry/fruit.py` | Tool schemas + name set |
| 4 | `src/application/handlers/registry/__init__.py` | Merge into `ALL_TOOLS` |
| 5 | `src/application/handlers/modules/fruit_handler.py` | Executor + deps dataclass |
| 6 | `src/container.py` | Wire the service |
| 7 | `src/application/handlers/tool_handler.py` | Add dependency + route to the executor |

---

## Step 1 — Domain model

Frozen dataclass in `src/domain/models.py`. No imports from other layers.

```python
@dataclass(frozen=True)
class Fruit:
    id: str
    name: str
    color: str
    season: str
```

---

## Step 2 — Service

Inject `HttpClient` via the constructor (never instantiate it inside the service) and return domain models. `HttpClient` is synchronous (stdlib `urllib`) and already unwraps the `{"status": "success", "data": ...}` envelope.

```python
# src/application/services/fruit_service.py
from domain.models import Fruit
from infrastructure.http.api_client import HttpClient
from libraries.logger import get_logger

logger = get_logger(__name__)


class FruitService:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_fruit(self, fruit_id: str) -> Fruit:
        logger.info("Fetching fruit %s", fruit_id)
        data = self._http.get(f"/fruits/{fruit_id}")
        return Fruit(id=data["id"], name=data["name"], color=data["color"], season=data["season"])

    def list_fruits(self) -> list[Fruit]:
        data = self._http.get("/fruits")
        return [Fruit(id=d["id"], name=d["name"], color=d["color"], season=d["season"]) for d in data]
```

> `HttpClient.get(endpoint)` takes no per-call headers; default headers (e.g. `X-API-Key`) are set once in the container. If an endpoint needs a per-user `Authorization` header, extend `HttpClient.get`/`_request` to accept headers first, then pass the token from `auth_service.require_auth()`.

---

## Step 3 — Registry file

```python
# src/application/handlers/registry/fruit.py
import mcp.types as types

FRUIT_TOOLS: list[types.Tool] = [
    types.Tool(
        name="get_fruit",
        description="Fetch a single fruit by ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Fruit ID"}},
            "required": ["id"],
        },
    ),
    types.Tool(
        name="list_fruits",
        description="List all available fruits.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]

FRUIT_TOOL_NAMES: frozenset[str] = frozenset(t.name for t in FRUIT_TOOLS)
```

## Step 4 — Merge into the registry

```python
# src/application/handlers/registry/__init__.py
from application.handlers.registry.fruit import FRUIT_TOOLS

ALL_TOOLS: list[types.Tool] = [*AUTH_TOOLS, *GREETING_TOOLS, *FRUIT_TOOLS, *UTILITY_TOOLS]
```

---

## Step 5 — Executor

```python
# src/application/handlers/modules/fruit_handler.py
from dataclasses import dataclass
from typing import Any

from application.services.fruit_service import FruitService
from libraries.errors import ValidationError


@dataclass(frozen=True)
class FruitHandlerDeps:
    fruit_service: FruitService


def _to_dict(f) -> dict[str, str]:
    return {"id": f.id, "name": f.name, "color": f.color, "season": f.season}


async def execute_fruit_tool(name: str, args: dict[str, Any], deps: FruitHandlerDeps) -> Any:
    if name == "get_fruit":
        fruit_id = args.get("id")
        if not isinstance(fruit_id, str) or not fruit_id.strip():
            raise ValidationError("'id' must be a non-empty string")
        return _to_dict(deps.fruit_service.get_fruit(fruit_id.strip()))
    if name == "list_fruits":
        return [_to_dict(f) for f in deps.fruit_service.list_fruits()]
    raise ValueError(f"Unhandled fruit tool: {name!r}")
```

Returning a plain value is enough — `ToolHandler.handle` JSON-serialises it into a `TextContent`. Raise `AppError` subclasses (`ValidationError`, `NotFoundError`, …) for expected failures; they are formatted as `{"error": {"code", "status_code", "message"}}`.

---

## Step 6 — Container

```python
# src/container.py
from application.services.fruit_service import FruitService

@dataclass
class Container:
    # ... existing fields ...
    fruit_service: FruitService


def create_container() -> Container:
    # ... existing wiring ...
    fruit_service = FruitService(http=http)

    tool_handler = ToolHandler(
        ToolHandlerDependencies(
            auth_service=auth_service,
            greeting_service=greeting_service,
            fruit_service=fruit_service,
            config=config,
        )
    )

    return Container(..., fruit_service=fruit_service, tool_handler=tool_handler)
```

## Step 7 — Dispatcher

```python
# src/application/handlers/tool_handler.py
from application.handlers.modules.fruit_handler import FruitHandlerDeps, execute_fruit_tool
from application.handlers.registry.fruit import FRUIT_TOOL_NAMES
from application.services.fruit_service import FruitService


@dataclass(frozen=True)
class ToolHandlerDependencies:
    auth_service: AuthService
    greeting_service: GreetingService
    fruit_service: FruitService   # <-- add
    config: AppConfig


# inside ToolHandler._execute(), next to the greeting branch (i.e. after the always-allowed ones):
if name in FRUIT_TOOL_NAMES:
    if not self._deps.auth_service.is_authenticated():
        return _AUTH_PROMPT
    return await execute_fruit_tool(name, args, FruitHandlerDeps(fruit_service=self._deps.fruit_service))
```

Place the branch **before** the `if not is_authenticated` check (as the utility branch is) to make the tools usable without login. As written above, the tools require an active session and return this prompt otherwise:

```json
{ "authenticated": false, "message": "You need to login before using this tool. Do you want to login now?", "next_step": "Just say the word and I will call the 'login' tool for you." }
```

Services calling protected upstream endpoints can additionally call `auth_service.require_auth()`, which raises `AuthError` (`AUTH_ERROR`, 401) when no session exists.

---

## Tests

Add cases to `tests/test_tools.py` and extend the `handler` fixture in `tests/conftest.py` with `fruit_service=FruitService(http=mock_http)`. Set `mock_http.get.return_value` to the unwrapped data, call `login` first, then assert on the parsed JSON of `results[0].text`.

---

## File summary

```
src/
├── domain/models.py                          ← add Fruit
├── application/
│   ├── services/fruit_service.py             ← new
│   └── handlers/
│       ├── registry/fruit.py                 ← new
│       ├── registry/__init__.py              ← merge FRUIT_TOOLS
│       ├── modules/fruit_handler.py          ← new
│       └── tool_handler.py                   ← dependency + route
└── container.py                              ← instantiate FruitService
```

## Naming conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Tool name | `snake_case` | `get_fruit` |
| Service file / class | `<domain>_service.py` / `<Domain>Service` | `fruit_service.py` |
| Registry file | `registry/<module>.py` | `registry/fruit.py` |
| Executor file | `modules/<module>_handler.py` | `modules/fruit_handler.py` |
| Constants | `<MODULE>_TOOLS`, `<MODULE>_TOOL_NAMES` | `FRUIT_TOOLS` |
| Executor / deps | `execute_<module>_tool`, `<Module>HandlerDeps` | `execute_fruit_tool` |
| Domain model | frozen `PascalCase` dataclass | `Fruit` |
