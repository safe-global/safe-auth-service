import logging
from functools import cache
from typing import Any, Callable

import aiohttp
from safe_eth.util.http import build_full_url

from ....config import settings
from ....models.api_gateway import Consumer, ConsumerGroup
from ..api_gateway_client import ApiGatewayClient
from ..exceptions import ApiGatewayRequestError

logger = logging.getLogger(__name__)


@cache
def get_apisix_client(request_timeout: int = 10) -> "ApisixClient":
    """
    Creates and returns an ApisixClient instance.

    Args:
        request_timeout: The timeout (in seconds) for HTTP requests.

    Returns:
        An instance of ApisixClient.
    """
    return ApisixClient(
        base_url=settings.APISIX_BASE_URL,
        api_key=settings.APISIX_API_KEY,
        connections_pool_size=settings.APISIX_CONNECTIONS_POOL_SIZE,
        request_timeout=request_timeout,
    )


class ApisixClient(ApiGatewayClient):
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        connections_pool_size: int = 100,
        request_timeout: int = 10,
    ):
        """

        Args:
            base_url: The base URL for the Apisix API.
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
            ApiGatewayRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)

        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
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
            raise ApiGatewayRequestError(
                f"Error performing request to {url} with payload {payload}"
            ) from e

        if not response.ok:
            raise ApiGatewayRequestError(
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
            ApiGatewayRequestError: If there is an error with the request.
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
            ApiGatewayRequestError: If there is an error with the request.
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
            ApiGatewayRequestError: If there is an error with the request.
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
            ApiGatewayRequestError: If there is an error with the request.
        """
        return await self._do_request(url, self.async_session.delete)

    def _parse_consumer_group_reponse(
        self, consumer_group_data: dict[str, Any]
    ) -> ConsumerGroup:
        """
        Parses consumer group data from API response.

        Args:
            consumer_group_data: A dictionary containing the consumer group data from API response.

        Returns:
            A ConsumerGroup instance with the parsed data.
        """
        consumer_group_data_value = consumer_group_data["value"]
        return ConsumerGroup(
            name=consumer_group_data_value["id"],
            description=consumer_group_data_value.get("desc"),
            labels=consumer_group_data_value.get("labels"),
            plugins=consumer_group_data_value.get("plugins"),
        )

    async def get_consumer_groups(self) -> list[ConsumerGroup]:
        url = "/apisix/admin/consumer_groups/"
        response = await self._get_request(url)
        consumer_groups_list = await response.json()
        return [
            self._parse_consumer_group_reponse(consumer_group_data)
            for consumer_group_data in consumer_groups_list.get("list", [])
        ]

    async def get_consumer_group(self, consumer_group_name: str) -> ConsumerGroup:
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"
        response = await self._get_request(url)
        consumer_group_data = await response.json()

        return self._parse_consumer_group_reponse(consumer_group_data)

    async def add_consumer_group(
        self,
        name: str,
        description: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> bool:
        url = f"/apisix/admin/consumer_groups/{name}"

        data: dict[str, Any] = {"plugins": {}}

        if labels:
            data["labels"] = labels

        if description:
            data["desc"] = description

        response = await self._put_request(url, data)
        return response.ok

    async def update_consumer_group(
        self, name: str, new_description: str, new_labels: dict[str, str]
    ) -> bool:
        url = f"/apisix/admin/consumer_groups/{name}"

        data = {
            "desc": new_description,
            "labels": new_labels,
        }
        response = await self._patch_request(url, data)
        return response.ok

    async def delete_consumer_group(self, consumer_group_name: str) -> bool:
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"
        response = await self._delete_request(url)
        return response.ok

    async def set_rate_limit_to_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"

        data = {
            "plugins": {
                "limit-count": {
                    "count": requests_number,
                    "time_window": time_window,
                    "rejected_code": 429,
                    "rejected_msg": "Too many requests",
                    "key_type": "var",
                    "key": "consumer_group_id",
                }
            }
        }
        response = await self._patch_request(url, data)
        return response.ok

    def _parse_consumer_reponse(self, consumer_data: dict[str, Any]) -> Consumer:
        """
        Parses consumer data from API response.

        Args:
            consumer_data: A dictionary containing the consumer data from API response.

        Returns:
            A Consumer instance with the parsed data.
        """
        consumer_data_value = consumer_data["value"]
        return Consumer(
            name=consumer_data_value["username"],
            description=consumer_data_value.get("desc"),
            labels=consumer_data_value.get("labels"),
            plugins=consumer_data_value.get("plugins"),
            consumer_group_name=consumer_data_value.get("group_id"),
        )

    async def get_consumers(self) -> list[Consumer]:
        url = "/apisix/admin/consumers/"
        response = await self._get_request(url)
        consumers_list = await response.json()
        return [
            self._parse_consumer_reponse(consumer_data)
            for consumer_data in consumers_list.get("list", [])
        ]

    async def get_consumer(self, consumer_name: str) -> Consumer:
        url = f"/apisix/admin/consumers/{consumer_name}"
        response = await self._get_request(url)
        consumer_data = await response.json()

        return self._parse_consumer_reponse(consumer_data)

    async def upsert_consumer(
        self,
        consumer_name: str,
        description: str | None = None,
        labels: dict[str, str] | None = None,
        consumer_group_name: str | None = None,
    ) -> bool:
        url = "/apisix/admin/consumers/"

        data = {
            "username": consumer_name,
            "plugins": {
                "jwt-auth": {
                    "key": consumer_name,
                    "algorithm": settings.JWT_ALGORITHM,
                    "public_key": settings.JWT_PUBLIC_KEY,
                }
            },
        }

        if labels:
            data["labels"] = labels

        if description:
            data["desc"] = description

        if consumer_group_name:
            data["group_id"] = consumer_group_name

        response = await self._put_request(url, data)
        return response.ok

    async def delete_consumer(self, consumer_name: str) -> bool:
        url = f"/apisix/admin/consumers/{consumer_name}"
        response = await self._delete_request(url)
        return response.ok

    async def update_consumers_jwt_config(self) -> None:
        consumers = await self.get_consumers()

        for consumer in consumers:
            await self.upsert_consumer(
                consumer.name,
                consumer.description,
                consumer.labels,
                consumer.consumer_group_name,
            )
