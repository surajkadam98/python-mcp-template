# Architecture

## Full Folder Structure

```
python-mcp-template/
├── src/                                  ← All Python source (PYTHONPATH root)
│   ├── application/                      ← Business logic layer
│   │   ├── handlers/
│   │   │   ├── registry/                 ← Tool schemas (the AI-visible contract), one file per module
│   │   │   │   ├── __init__.py           ← Merges module tools into ALL_TOOLS
│   │   │   │   ├── auth.py               ← AUTH_TOOLS: login, logout, auth_status
│   │   │   │   ├── greeting.py           ← GREETING_TOOLS: greet
│   │   │   │   └── utility.py            ← UTILITY_TOOLS: echo, ping
│   │   │   ├── modules/                  ← Tool executors, one file per module
│   │   │   │   ├── auth_handler.py       ← execute_auth_tool
│   │   │   │   ├── greeting_handler.py   ← execute_greeting_tool
│   │   │   │   └── utility_handler.py    ← execute_utility_tool
│   │   │   ├── tool_registry.py          ← Re-exports ALL_TOOLS for main.py
│   │   │   └── tool_handler.py           ← Thin dispatcher: auth gate + routes to module executors
│   │   └── services/
│   │       ├── auth_service.py           ← Session lifecycle (login / logout / require_auth)
│   │       └── greeting_service.py       ← Calls HttpClient, returns domain models
│   ├── domain/
│   │   └── models.py                     ← Pure value objects (frozen dataclasses)
│   ├── infrastructure/
│   │   ├── auth/
│   │   │   └── session_store.py          ← In-memory credential store (write-only to the LLM)
│   │   └── http/
│   │       └── api_client.py             ← stdlib urllib — no requests/httpx
│   ├── libraries/
│   │   ├── config.py                     ← Frozen config loaded from env vars
│   │   ├── errors.py                     ← Exception hierarchy with codes + status codes
│   │   └── logger.py                     ← Stderr-only structured logger
│   ├── container.py                      ← DI wiring — one place, all dependencies
│   └── main.py                           ← MCP server entry point
│
├── tests/
│   ├── conftest.py                       ← Fixtures: mock HttpClient, ToolHandler
│   └── test_tools.py                     ← Tool tests
│
├── docs/
│   ├── architecture.md                   ← This file
│   ├── getting_started.md                ← Setup + Claude config
│   └── adding-new-api-service.md         ← Walkthrough: add a service + tools
│
├── Dockerfile
├── pyproject.toml                        ← Deps (mcp only), pytest config
├── Makefile                              ← install/dev/test/run/docker-build shortcuts
├── .mcp.json.example
└── README.md
```

## Layer Rules

```
┌──────────────────────────────────────────┐
│  MCP Protocol (main.py + mcp SDK)        │  ← reads list_tools / call_tool requests
└──────────────────┬───────────────────────┘
                   │ calls
┌──────────────────▼───────────────────────┐
│  Application                             │  ← auth gate, module executors, services
│  (tool_handler, modules/, services/)     │
└──────────────────┬───────────────────────┘
                   │ returns domain objects
┌──────────────────▼───────────────────────┐
│  Domain (models.py)                      │  ← pure value objects, zero imports
└──────────────────┬───────────────────────┘
                   │ infrastructure used by services
┌──────────────────▼───────────────────────┐
│  Infrastructure                          │  ← I/O: HTTP (urllib), session store
│  (http/api_client.py, auth/)             │
└──────────────────┬───────────────────────┘
                   │ reads from
┌──────────────────▼───────────────────────┐
│  Libraries (config, errors, logger)      │  ← used by ALL layers
└──────────────────────────────────────────┘
```

**Direction of allowed imports:**
`main → application → domain`
`main → application → infrastructure`
`all → libraries`
`domain → nothing` (no imports from other layers)

## Tool Modules

Tools are grouped into **modules**. Each module has two files:

| Part | File | Contains |
|------|------|----------|
| Registry | `handlers/registry/<module>.py` | `<MODULE>_TOOLS` (`types.Tool` list) and `<MODULE>_TOOL_NAMES` (frozenset) |
| Executor | `handlers/modules/<module>_handler.py` | `<Module>HandlerDeps` dataclass + `execute_<module>_tool(name, args, deps)` |

`ToolHandler` ([tool_handler.py](../src/application/handlers/tool_handler.py)) is a thin dispatcher. Its `_execute` routes by name set:

| Module | Tools | Auth required? |
|--------|-------|----------------|
| auth | `login`, `logout`, `auth_status` | No — always allowed |
| utility | `echo`, `ping` | No |
| greeting | `greet` | **Yes** — otherwise returns an `authenticated: false` prompt telling the user to call `login` |

Any name not in a module's name set raises `AppError("Unknown tool", "UNKNOWN_TOOL", 400)`.

## Dependency Wiring

`container.create_container()` builds everything in order: config → `HttpClient` → `SessionStore` → `AuthService` / `GreetingService` → `ToolHandler(ToolHandlerDependencies(auth_service, greeting_service, config))`. `get_container()` returns a lazy singleton; `reset_container()` clears it (and the config cache) for tests.

## Authentication

- `AuthService.login()` is a **mock** that issues a fake token with a 1-hour expiry. The real call is left commented out inside `login()` / `logout()` — replace only those bodies to integrate a real provider.
- The token lives in `SessionStore` and is never returned to the LLM; `login` returns only `authenticated` and `expires_at`.
- The auth gate is in `ToolHandler`. Services that call protected endpoints can additionally call `AuthService.require_auth()` to get the token for headers (raises `AuthError`, 401).

## API Call Flow (greet tool)

```
Claude calls "greet"
  → main.call_tool → container.tool_handler.handle("greet", {})
  → _execute: "greet" ∈ GREETING_TOOL_NAMES
  → auth gate: AuthService.is_authenticated()?  no → return login prompt
  → execute_greeting_tool("greet", args, GreetingHandlerDeps)
  → GreetingService.greet()
  → HttpClient.get("/greet")                      (currently mocked in the service)
  → API returns: {"status": "success", "data": {"message": "Namaste!", "source": "/greet"}}
  → HttpClient unwraps envelope → {"message": ..., "source": ...}
  → Greeting(message=..., source=...)             ← domain model
  → {"message": ..., "source": ...}               ← dict
  → json.dumps → TextContent(type="text", text=...)
  → Claude receives the result
```

Errors: `AppError` → `format_error(e)`; anything else → `to_app_error(e)` then `format_error`. Both are returned as `TextContent`.

## Adding a New Tool

**New tool in an existing module**
1. Add a `types.Tool(...)` to `registry/<module>.py` (the name set updates automatically).
2. Add a branch for it in `modules/<module>_handler.py`.

**New module** (e.g. `fruit`) — see [adding-new-api-service.md](adding-new-api-service.md) for code.
1. **Domain** — add a frozen dataclass in `domain/models.py` if needed.
2. **Service** — `application/services/fruit_service.py`, inject `HttpClient` via the constructor.
3. **Registry** — `handlers/registry/fruit.py` with `FRUIT_TOOLS` + `FRUIT_TOOL_NAMES`; add `*FRUIT_TOOLS` to `ALL_TOOLS` in `registry/__init__.py`.
4. **Executor** — `handlers/modules/fruit_handler.py` with `FruitHandlerDeps` and `execute_fruit_tool`.
5. **Container** — build `FruitService` in `create_container()`, add it to `Container` and to `ToolHandlerDependencies`.
6. **Dispatcher** — in `ToolHandler._execute`, add a branch for `FRUIT_TOOL_NAMES` (after the auth check if the tools need a session).
7. **Tests** — add cases in `tests/test_tools.py` with a mocked `HttpClient`.

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Per-module registry + executor files | Adding a tool group touches its own files; the dispatcher stays small |
| Name `frozenset`s derived from the registry | Routing can't drift from the advertised tools |
| Auth gate in the dispatcher, not in each tool | One place decides which tools need a session |
| `SessionStore` isolated in infrastructure | Swap credential storage without touching the auth flow |
| Frozen dataclasses for config, deps + domain models | Immutable = no accidental mutation |
| `stdlib urllib` for HTTP | Zero extra runtime deps |
| All errors inherit `AppError` | Consistent `code` + `status_code` on every error |
| Logging to `stderr` only | `stdout` is reserved for the MCP stdio transport |
| `pythonpath = ["src"]` in pyproject.toml | Flat imports: `from libraries.config import ...` |
