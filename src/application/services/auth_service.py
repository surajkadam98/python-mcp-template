"""
AuthService — manages the session lifecycle.

The public interface (login / logout / require_auth / is_authenticated) is stable.
To wire in a real auth provider, replace only the body of login() and logout().

Common replacements for login():
  - OAuth2 + PKCE:  browser flow → loopback redirect → redeem code → token
  - SSO / SAML:     redirect to IdP → callback → exchange assertion → token
"""

import time
from datetime import datetime, timedelta, timezone

from domain.models import AuthToken
from infrastructure.auth.session_store import SessionStore
from libraries.errors import AuthError
from libraries.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session_store: SessionStore) -> None:
        self._session = session_store

    async def login(self) -> AuthToken:
        # REAL — uncomment when the auth endpoint is available:
        # data = self._http.post("/auth/login")
        # response = AuthToken(token=data["token"], expires_at=data["expires_at"])

        # MOCK — mirrors the real API response shape so the rest of the code is production-ready
        response = AuthToken(
            token=f"mock_token_{int(time.time() * 1000)}",
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        )
        self._session.set(response.token)
        logger.info("Authenticated (mock)")
        return response

    async def logout(self) -> None:
        # REAL — uncomment when the auth endpoint is available:
        # self._http.post("/auth/logout")
        self._session.clear()
        logger.info("Logged out")

    def require_auth(self) -> str:
        token = self._session.get()
        if not token:
            raise AuthError("Not authenticated. Call the 'login' tool first.")
        return token

    def is_authenticated(self) -> bool:
        return self._session.is_authenticated()
