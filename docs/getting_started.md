# Getting Started

## Prerequisites

- Python 3.11+
- `pip` (or `uv` for faster installs)

---

## Install

```bash
cd /path/to/python-mcp-template

# Poetry
poetry shell
poetry install -E dev

# Standard pip
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"
```

---

## Run Tests

```bash
make test
# or
pytest tests/ -v
```

---

## Run the Server

```bash
make run
# which runs: PYTHONPATH=src python src/main.py
```

The server speaks MCP over stdio. You'll see startup logs on stderr:
```
2026-06-16 [INFO] main: python-mcp-template v0.0.1 starting — API: https://api.example.com
```

Then it waits for JSON-RPC from stdin. Use Claude Desktop or Claude Code to connect.

---

## Configure Claude Code (.mcp.json)

Create `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "python-mcp-template": {
      "command": "python",
      "args": ["src/main.py"],
      "cwd": "/absolute/path/to/python-mcp-template",
      "env": {
        "PYTHONPATH": "src",
        "MCP_SERVER_NAME": "python-mcp-template",
        "MCP_VERSION": "0.0.1",
        "API_BASE_URL": "https://api.example.com",
        "API_TIMEOUT": "30",
        "API_KEY": "your-key-here"
      }
    }
  }
}
```

If using a virtualenv, use the full interpreter path:

```json
{
  "mcpServers": {
    "python-mcp-template": {
      "command": "/path/to/.venv/bin/python",
      "args": ["src/main.py"],
      "cwd": "/absolute/path/to/python-mcp-template",
      "env": {
        "PYTHONPATH": "src",
        "MCP_SERVER_NAME": "python-mcp-template",
        "MCP_VERSION": "0.0.1",
        "API_BASE_URL": "https://api.example.com",
        "API_TIMEOUT": "30",
        "API_KEY": "your-key-here"
      }
    }
  }
}
```

After saving `.mcp.json`, restart Claude Code. The server will appear in the tool panel.

---

## Environment Variables

| Variable | Default | Required | Purpose |
|----------|---------|----------|---------|
| `API_BASE_URL` | `https://api.example.com` | No | Backend API base URL |
| `API_KEY` | — | No | Sent as `X-API-Key` header |
| `API_TIMEOUT` | `30` | No | HTTP timeout in seconds |
| `MCP_SERVER_NAME` | `python-mcp-template` | No | Server name shown in Claude |
| `MCP_VERSION` | `0.0.1` | No | Server version reported in `ping` |

Values are read from the environment that the MCP host passes via the `env` block in `.mcp.json` (there is no `.env` loader).

---

## Available Tools

| Tool | Auth | Description |
|------|------|-------------|
| `login` | No | Mock login — stores a session token in memory |
| `logout` | No | Clears the session |
| `auth_status` | No | Reports whether a session is active |
| `greet` | **Yes** | Calls `GET /greet` → returns API message (prompts to log in first if needed) |
| `echo` | No | Echoes back the provided message |
| `ping` | No | Returns server name, version, API URL |

---

## Add a New Tool

Tools are organised in modules (registry file + executor file). See
[architecture.md](architecture.md#adding-a-new-tool) for the checklist and
[adding-new-api-service.md](adding-new-api-service.md) for a full walkthrough.
