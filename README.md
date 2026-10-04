# python-mcp-template

Minimal Python MCP server template — Clean Architecture, zero extra runtime dependencies.

---

## Prerequisites

- **Claude Code** — installed and authenticated
- **Python 3.11+** — required for Option A (without Docker)
- **Docker** — required for Option B (with Docker)

---

## Setup

Choose one option. Both end with the same Start step below.

### Option A — Without Docker

**Step 1 — Install and test**

```bash
cd /path/to/python-mcp-template
poetry shell                  # or: python -m venv .venv && source .venv/bin/activate
poetry install -E dev         # or: pip install -e ".[dev]"
make test   # 10 tests, all pass with mocked API
```

> Poetry-native project (`[tool.poetry]` in `pyproject.toml`, poetry-core build backend), and plain `pip install -e ".[dev]"` works too. `make test` needs `pytest` from the `dev` extra, so install it in the same shell first.

**Step 2 — Register with Claude Code**

```bash
claude mcp add python-mcp-template -s project \
  -e PYTHONPATH=src \
  -e MCP_SERVER_NAME=python-mcp-template \
  -e MCP_VERSION=0.0.1 \
  -e API_BASE_URL=https://api.example.com \
  -e API_TIMEOUT=30 \
  -e API_KEY=your-key-here \
  -- python src/main.py
```

> The server name must come **before** the `-e` flags — `-e` accepts multiple values and would otherwise swallow the name ("Invalid environment variable format"). Everything after `--` is the server command.

> `-s project` saves to `.mcp.json`. Use `-s local` to keep it out of git, or `-s user` to register globally.

Claude Code launches the server outside your shell, so use the full path to the interpreter that has `mcp` installed instead of `python`:

```bash
# last line of the command above, by environment:
#   venv:    -- /path/to/.venv/bin/python src/main.py
#   poetry:  -- "$(poetry env info -e)" src/main.py   (prints the venv's python path)
```

---

### Option B — With Docker

**Step 1 — Build the image**

```bash
make docker-build
```


**Step 2 — Register with Claude Code**

```bash
claude mcp add -s project \
  python-mcp-template -- docker run -i --rm \
  -e MCP_SERVER_NAME=python-mcp-template \
  -e MCP_VERSION=0.0.1 \
  -e API_BASE_URL=https://api.example.com \
  -e API_TIMEOUT=30 \
  -e API_KEY=your-key-here \
  python-mcp-template:latest
```

> `-i` keeps stdin open — required for stdio transport. `--rm` removes the container when the session ends. No `PYTHONPATH` needed — it is baked into the image.

**Or via `.mcp.json`:**

```bash
cp .mcp.json.example .mcp.json
```

```json
{
  "mcpServers": {
    "python-mcp-template": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_SERVER_NAME=python-mcp-template",
        "-e", "MCP_VERSION=0.0.1",
        "-e", "API_BASE_URL=https://api.example.com",
        "-e", "API_TIMEOUT=30",
        "-e", "API_KEY=your-key-here",
        "python-mcp-template:latest"
      ]
    }
  }
}
```

> `.mcp.json` is committed and shared with the team. Keep secrets out of git — add `.mcp.json` to `.gitignore` if API keys differ per developer.

---

## Start

```bash
claude
```

Claude Code reads the registered server automatically on startup. You'll see:

```
MCP server "python-mcp-template" connected
```

Run `/mcp` inside Claude Code if the server doesn't appear.

## Try the Tools

```
ping
```
```
echo "hello world"
```
```
greet me
```

`greet` needs a session — if you aren't logged in, the server replies with a prompt and Claude offers to call `login` (a mock that needs no credentials).

---

## Managing the Server

```bash
# List all registered MCP servers
claude mcp list

# Check server details and health
claude mcp get python-mcp-template

# Remove the server (only works if registered via `claude mcp add`)
claude mcp remove python-mcp-template

# If registered via .mcp.json, remove the entry from the file instead
rm .mcp.json
```

---

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Ensure `-e PYTHONPATH=src` is passed to `claude mcp add` (non-Docker only) |
| `mcp not found` / `pytest: No such file` | Install in the active env: `poetry install -E dev` or `pip install -e ".[dev]"` (non-Docker only) |
| `poetry shell`: `No such file or directory: 'python'` | Poetry has no virtualenv and can't find `python` on PATH. Create it explicitly: `poetry env use /full/path/to/python3.11`, then `poetry install -E dev` |
| Server not connected | Run `/mcp` in Claude Code to see the error |
| Wrong Python used | Use the full venv/poetry interpreter path instead of `python` in the `mcp add` command |
| `greet` only asks to log in | Expected until `login` is called; check with `auth_status` |
| Docker: server hangs | Ensure `-i` flag is present in `docker run` args |
| Docker: env vars missing | Pass each var with `-e KEY` (forwards from shell) or `-e KEY=value` |

---

## API Call Flow (greet tool)

```
Claude calls "greet"
  → ToolHandler: auth gate — not logged in? → returns "please login" prompt
  → execute_greeting_tool → GreetingService.greet()
  → HttpClient.get("/greet")                        (mocked in the service for now)
  → API: {"status":"success","data":{"message":"Namaste!","source":"/greet"}}
  → HttpClient unwraps envelope → raw dict
  → Greeting(message="Namaste!", source="/greet")
  → {"message":"Namaste!","source":"/greet"} → Claude
```

The real `HttpClient.get("/greet")` call is commented out in `greeting_service.py`; uncomment it to hit your API.

---

## Tools

| Tool | Auth | What it does |
|------|------|-------------|
| `login` | No | Mock login — stores a session token in memory (never shown to Claude) |
| `logout` | No | Clears the session |
| `auth_status` | No | Reports whether a session is active |
| `greet` | **Yes** | Calls `GET /greet` — shows full API call flow |
| `echo` | No | Echoes back the message |
| `ping` | No | Returns server name, version, API URL |

---

## Dependencies

**Runtime:** `mcp` only.
**Dev:** `pytest`, `pytest-asyncio`.
No `requests`, `httpx`, `pydantic`, `loguru`, or any other extras.

---

## Docs

| File | Contents |
|------|---------|
| `docs/architecture.md` | Folder tree, layer rules, request flow, how to add a tool |
| `docs/getting_started.md` | Install, run, Claude .mcp.json config |
| `docs/adding-new-api-service.md` | Step-by-step: add a new API service and its tools |
