import logging
from functools import cache
from typing import Any, Callable

import aiohttp
from safe_eth.util.http import build_full_url

from ....config import settings
from .exceptions import EventsServiceRequestError

logger = logging.getLogger(__name__)


@cache
def get_events_service_client(request_timeout: int = 10) -> "EventsServiceClient":
    """
    Creates and returns an EventsServiceClient instance.

    Args:
        request_timeout: The timeout (in seconds) for HTTP requests.

    Returns:
        An instance of EventsServiceClient.
    """
    return EventsServiceClient(
        base_url=settings.EVENTS_SERVICE_BASE_URL,
        api_key=settings.EVENTS_SERVICE_API_KEY,
        connections_pool_size=settings.EVENTS_SERVICE_CONNECTIONS_POOL_SIZE,
        request_timeout=request_timeout,
    )


class EventsServiceClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        connections_pool_size: int = 100,
        request_timeout: int = 10,
    ):
        """

        Args:
            base_url: The base URL for the Events Service API.
            api_key: The API key for authenticating requests.
            request_timeout: The timeout (in seconds) for HTTP requests.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.async_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_pool_size)
        )
        self.request_timeout = request_timeout

    async def _do_request(
        self, url: str, request_func: Callable, payload: dict[str, Any] | None = None
    ) -> aiohttp.ClientResponse:
        """
        A generic method to perform HTTP requests (GET, PUT, PATCH, DELETE).

        Args:
            url: The URL to send the request to.
            request_func: The function to execute (e.g., async_session.get, async_session.put, async_session.patch, async_session.delete).
            payload: The data to be sent in the request body.

        Returns:
            The response object from the HTTP request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)

        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key  # TODO UPDATE THIS
        if payload:
            headers["Content-Type"] = "application/json"

        try:
            response = await request_func(
                full_url,
                json=payload if payload else None,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.request_timeout),
            )

        except (ValueError, IOError) as e:
            raise EventsServiceRequestError(
                f"Error performing request to {url} with payload {payload}"
            ) from e

        if not response.ok:
            raise EventsServiceRequestError(
                f"Error performing request to {url} with payload {payload}: {response.status} {response.reason}"
            )

        return response

    async def _get_request(self, url: str) -> aiohttp.ClientResponse:
        """
        Sends a GET request.

        Args:
            url: The URL to send the GET request to.

        Returns:
            The response object from the GET request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.get)

    async def _put_request(
        self, url: str, payload: dict[str, Any]
    ) -> aiohttp.ClientResponse:
        """
        Sends a PUT request.

        Args:
            url: The URL to send the PUT request to.
            payload: The data to be sent in the PUT request.

        Returns:
            The response object from the PUT request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.put, payload)

    async def _patch_request(
        self, url: str, payload: dict[str, Any]
    ) -> aiohttp.ClientResponse:
        """
        Sends a PATCH request.

        Args:
            url: The URL to send the PATCH request to.
            payload: The data to be sent in the PATCH request.

        Returns:
            The response object from the PATCH request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.patch, payload)

    async def _delete_request(self, url: str) -> aiohttp.ClientResponse:
        """
        Sends a DELETE request.

        Args:
            url: The URL to send the DELETE request to.

        Returns:
            The response object from the DELETE request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.delete)
