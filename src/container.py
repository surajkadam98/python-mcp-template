"""
Dependency injection container — wires everything together in one place.

Order:
  1. Config (from env)
  2. Infrastructure (HttpClient)
  3. Services (inject infrastructure, incl. SessionStore for auth)
  4. Handlers (inject services + config)
"""

from dataclasses import dataclass

from application.handlers.tool_handler import ToolHandler, ToolHandlerDependencies
from application.services.auth_service import AuthService
from application.services.greeting_service import GreetingService
from infrastructure.auth.session_store import SessionStore
from infrastructure.http.api_client import HttpClient
from libraries.config import AppConfig, get_config, reset_config


@dataclass
class Container:
    config: AppConfig
    http: HttpClient
    session_store: SessionStore
    auth_service: AuthService
    greeting_service: GreetingService
    tool_handler: ToolHandler


def create_container() -> Container:
    config = get_config()

    http = HttpClient(
        base_url=config.api.base_url,
        timeout=config.api.timeout,
        default_headers={"X-API-Key": config.api.api_key} if config.api.api_key else {},
    )

    session_store = SessionStore()
    auth_service = AuthService(session_store)
    greeting_service = GreetingService(http=http)
    tool_handler = ToolHandler(
        ToolHandlerDependencies(auth_service=auth_service, greeting_service=greeting_service, config=config)
    )

    return Container(
        config=config,
        http=http,
        session_store=session_store,
        auth_service=auth_service,
        greeting_service=greeting_service,
        tool_handler=tool_handler,
    )


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = create_container()
    return _container


def reset_container() -> None:
    global _container
    _container = None
    reset_config()
