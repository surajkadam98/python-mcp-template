"""
Exception hierarchy — every error has a machine-readable code and HTTP status.
"""

import json
from typing import Any


class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR", 400)


class AuthError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "AUTH_ERROR", 401)


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} not found: {resource_id}", "NOT_FOUND", 404)


class ApiError(AppError):
    def __init__(self, message: str, status_code: int, endpoint: str) -> None:
        super().__init__(message, "API_ERROR", status_code, {"endpoint": endpoint})


def format_error(error: AppError) -> str:
    return json.dumps({
        "error": {
            "code": error.code,
            "status_code": error.status_code,
            "message": str(error),
        }
    })


def to_app_error(exc: Exception) -> AppError:
    if isinstance(exc, AppError):
        return exc
    return AppError(str(exc), "UNKNOWN_ERROR", 500)
