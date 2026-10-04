"""
HTTP client — stdlib urllib only, zero external dependencies.

Unwraps the standard API envelope: {"status": "success", "data": ...}
Maps HTTP/network errors to domain exceptions.
"""

import json
import urllib.error
import urllib.request
from typing import Any

from libraries.errors import ApiError
from libraries.logger import get_logger

logger = get_logger(__name__)


class HttpClient:
    def __init__(self, base_url: str, timeout: int = 30, default_headers: dict[str, str] | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = default_headers or {}

    def _request(self, method: str, endpoint: str, *, body: Any = None) -> Any:
        url = f"{self._base_url}{endpoint}"
        headers = {"Content-Type": "application/json", "Accept": "application/json", **self._headers}
        data = json.dumps(body).encode() if body is not None else None

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode()
                if not raw:
                    return None
                result = json.loads(raw)
                # Unwrap standard envelope
                if isinstance(result, dict) and result.get("status") == "success" and "data" in result:
                    return result["data"]
                return result
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode())
                msg = payload.get("message") or str(e)
            except Exception:
                msg = str(e)
            logger.warning("HTTP %d %s: %s", e.code, endpoint, msg)
            raise ApiError(msg, e.code, endpoint) from e
        except (urllib.error.URLError, TimeoutError) as e:
            logger.error("Network error %s: %s", endpoint, e)
            raise ApiError(f"Network error: {e}", 503, endpoint) from e

    def get(self, endpoint: str) -> Any:
        return self._request("GET", endpoint)

    def post(self, endpoint: str, body: Any = None) -> Any:
        return self._request("POST", endpoint, body=body)
