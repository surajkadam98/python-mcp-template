"""
GreetingService — calls the API and returns a Greeting domain object.

This mirrors how fabricbloc-mcp services call ApiClient:
  tool_handler → GreetingService → HttpClient → API → domain model → response
"""

from domain.models import Greeting
from infrastructure.http.api_client import HttpClient
from libraries.logger import get_logger

logger = get_logger(__name__)


class GreetingService:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def greet(self) -> Greeting:
        """
        GET /greet → {"status": "success", "data": {"message": "Namaste!", "source": "/greet"}}
        HttpClient unwraps the envelope and returns the data dict directly.
        """
        logger.info("Calling GET /greet")
        # data: dict = self._http.get("/greet")
        # return Greeting(
        #     message=data["message"],
        #     source=data.get("source", "/greet"),
        # )

        # Mock API data
        return Greeting(
            message="Namaste!",
            source="",
        )
