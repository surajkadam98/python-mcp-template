"""
In-memory session store — one active credential per process lifetime.

The token is write-only from the LLM's perspective: it is stored here,
used to build request headers, and never returned to the tool caller.

PRODUCTION: swap the storage backend (vault, OS keychain, encrypted file)
without touching the rest of the auth flow — this class is the only
place that knows where credentials live.
"""


class SessionStore:
    def __init__(self) -> None:
        self._token: str | None = None

    def set(self, token: str) -> None:
        self._token = token

    def get(self) -> str | None:
        return self._token

    def clear(self) -> None:
        self._token = None

    def is_authenticated(self) -> bool:
        return self._token is not None
