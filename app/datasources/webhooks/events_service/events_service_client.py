import logging
import uuid
from functools import cache
from typing import Any, Callable

import aiohttp
from safe_eth.util.http import build_full_url

from ....config import settings
from ....models.webhook import WebhookEventsService, WebhookEventType
from .exceptions import EventsServiceRequestError

logger = logging.getLogger(__name__)


@cache
def get_events_service_client() -> "EventsServiceClient":
    """
    Creates and returns an EventsServiceClient instance.

    Returns:
        An instance of EventsServiceClient.
    """
    return EventsServiceClient(
        base_url=settings.EVENTS_SERVICE_BASE_URL,
        api_key=settings.EVENTS_SERVICE_API_KEY,
        connections_pool_size=settings.EVENTS_SERVICE_CONNECTIONS_POOL_SIZE,
        request_timeout=settings.EVENTS_SERVICE_REQUEST_TIMEOUT,
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
            headers["Authorization"] = f"Basic {self.api_key}"
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
        Sends a GET request to events service.

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
        Sends a PUT request to events service.

        Args:
            url: The URL to send the PUT request to.
            payload: The data to be sent in the PUT request.

        Returns:
            The response object from the PUT request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.put, payload)

    async def _post_request(
        self, url: str, payload: dict[str, Any]
    ) -> aiohttp.ClientResponse:
        """
        Sends a POST request to events service.

        Args:
            url: The URL to send the POST request to.
            payload: The data to be sent in the POST request.

        Returns:
            The response object from the POST request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.post, payload)

    async def _delete_request(self, url: str) -> aiohttp.ClientResponse:
        """
        Sends a DELETE request to events service.

        Args:
            url: The URL to send the DELETE request to.

        Returns:
            The response object from the DELETE request.

        Raises:
            EventsServiceRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.delete)

    def _parse_webhook_data(self, webhook_data: dict) -> WebhookEventsService:
        """
        Parses the webhook data received from the API response and converts it into a WebhookEventsService object.

        Args:
            webhook_data: The raw data of the webhook returned from the API.

        Returns:
            WebhookEventsService | None: The parsed WebhookEventsService object or None if the data is invalid.
        """
        return WebhookEventsService(
            id=webhook_data["id"],
            url=webhook_data["url"],
            authorization=webhook_data["authorization"] or None,
            chains=webhook_data["chains"],
            events=[WebhookEventType(event) for event in webhook_data["events"]],
            is_active=webhook_data["isActive"],
        )

    async def add_webhook(
        self,
        webhook_url: str,
        chains: list[int],
        events: list[WebhookEventType],
        description: str,
        is_active: bool = True,
        authorization: str | None = None,
    ) -> WebhookEventsService:
        """
        Adds a new webhook to the events service.

        Args:
            webhook_url: The URL to send webhook events to.
            chains: The list of chain IDs associated with the webhook.
            events: The list of events that trigger the webhook.
            description: A description for the webhook.
            is_active: Whether the webhook is active (default is True).
            authorization: An optional authorization token for the webhook.

        Returns:
            WebhookEventsService: The webhook object if the webhook was successfully added.

        Raises:
            ApiGatewayRequestError: If there is an error while adding the webhook (e.g., HTTP error, invalid response).
        """
        data: dict[str, Any] = {
            "url": webhook_url,
            "chains": chains,
            "events": [event.value for event in events],
            "isActive": is_active,
            "description": description,
            "authorization": authorization if authorization else "",
        }

        response = await self._post_request("/webhooks", data)
        webhook_data = await response.json()
        return self._parse_webhook_data(webhook_data)

    async def delete_webhook(
        self,
        webhook_id: uuid.UUID,
    ) -> bool:
        """
        Deletes an existing webhook by its ID.

        Args:
            webhook_id: The UUID of the webhook to delete.

        Returns:
            bool: True if the webhook was successfully deleted, False otherwise.

        Raises:
            ApiGatewayRequestError: If there is an error while deleting the webhook (e.g., HTTP error, invalid response).
        """
        url = f"/webhooks/{webhook_id}"
        response = await self._delete_request(url)
        return response.ok

    async def update_webhook(
        self,
        webhook_id: uuid.UUID,
        webhook_url: str,
        chains: list[int],
        events: list[WebhookEventType],
        description: str,
        is_active: bool = True,
        authorization: str | None = None,
    ) -> bool:
        """
        Updates an existing webhook with new information.

        Args:
            webhook_id: The UUID of the webhook to update.
            webhook_url: The new URL for the webhook.
            chains: The updated list of chain IDs associated with the webhook.
            events: The updated list of events that trigger the webhook.
            description: A description for the webhook.
            is_active: Whether the webhook is active (default is True).
            authorization: An optional new authorization token for the webhook.

        Returns:
            bool: True if the webhook was successfully updated, False otherwise.

        Raises:
            ApiGatewayRequestError: If there is an error while updating the webhook (e.g., HTTP error, invalid response).
        """

        data: dict[str, Any] = {
            "url": webhook_url,
            "chains": chains,
            "events": [event.value for event in events],
            "isActive": is_active,
            "description": description,
            "authorization": authorization if authorization else "",
        }

        response = await self._put_request(f"/webhooks/{webhook_id}", data)
        return response.ok

    async def get_webhook(self, webhook_id: uuid.UUID) -> WebhookEventsService:
        """
        Retrieves a webhook by its ID.

        Args:
            webhook_id: The UUID of the webhook to retrieve.

        Returns:
            WebhookEventsService | None: The webhook object if found, None if not found.

        Raises:
            ApiGatewayRequestError: If there is an error while retrieving the webhook (e.g., HTTP error, invalid response).
        """
        response = await self._get_request(f"/webhooks/{webhook_id}")
        webhook_data = await response.json()
        return self._parse_webhook_data(webhook_data)
