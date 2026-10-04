"""
Shared test fixtures.

Build a ToolHandler directly from its dependencies — no singleton reset needed.
HttpClient is mocked; GreetingService currently returns a mock greeting itself.
"""

from unittest.mock import MagicMock

import pytest

from application.handlers.tool_handler import ToolHandler, ToolHandlerDependencies
from application.services.auth_service import AuthService
from application.services.greeting_service import GreetingService
from infrastructure.auth.session_store import SessionStore
from infrastructure.http.api_client import HttpClient
from libraries.config import ApiConfig, AppConfig, ServerConfig


@pytest.fixture
def mock_http() -> MagicMock:
    return MagicMock(spec=HttpClient)


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService(SessionStore())


@pytest.fixture
def handler(mock_http: MagicMock, auth_service: AuthService) -> ToolHandler:
    config = AppConfig(
        server=ServerConfig(name="test-server", version="0.0.1"),
        api=ApiConfig(base_url="http://localhost", timeout=5, api_key=None),
    )
    return ToolHandler(
        ToolHandlerDependencies(
            auth_service=auth_service,
            greeting_service=GreetingService(http=mock_http),
            config=config,
        )
    )
