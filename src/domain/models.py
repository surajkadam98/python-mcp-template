"""
Domain models — pure value objects, no I/O, no framework dependencies.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Greeting:
    message: str
    source: str  # which API endpoint served it


@dataclass(frozen=True)
class AuthToken:
    """Returned by POST /auth/login — stored in SessionStore, never sent to the LLM."""

    token: str
    expires_at: str  # ISO 8601
