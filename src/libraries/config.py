"""
App configuration — loaded once from env vars injected by the MCP host.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServerConfig:
    name: str
    version: str


@dataclass(frozen=True)
class ApiConfig:
    base_url: str
    timeout: int
    api_key: str | None


@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig
    api: ApiConfig


def _load() -> AppConfig:
    return AppConfig(
        server=ServerConfig(
            name=os.getenv("MCP_SERVER_NAME", "python-mcp-template"),
            version=os.getenv("MCP_VERSION", "0.0.1"),
        ),
        api=ApiConfig(
            base_url=os.getenv("API_BASE_URL", "https://api.example.com"),
            timeout=int(os.getenv("API_TIMEOUT", "30")),
            api_key=os.getenv("API_KEY"),
        ),
    )


_config: AppConfig | None = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = _load()
    return _config


def reset_config() -> None:
    global _config
    _config = None
