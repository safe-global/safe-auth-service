import logging
from typing import Any

import aiohttp
from aiohttp import ClientTimeout
from safe_eth.util.http import build_full_url

from ....config import settings
from ....models import Consumer, ConsumerGroup
from ..api_gateway_client import ApiGatewayClient
from ..exceptions import ApiGatewayRequestError

logger = logging.getLogger(__name__)


class ApisixClient(ApiGatewayClient):

    def __init__(
        self, base_url: str, api_key: str | None = None, request_timeout: int = 10
    ):
        """
        :param base_url: The base URL for the Apisix API.
        :param api_key: The API key for authenticating requests.
        :param request_timeout: The timeout (in seconds) for HTTP requests.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.async_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit_per_host=100)
        )
        self.request_timeout = request_timeout

    async def _get_request(self, url: str) -> aiohttp.ClientResponse:
        """

        :param url: The URL to send the GET request to.
        :return: The response object from the GET request.
        :raises ApiGatewayRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)

        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        try:
            response = await self.async_session.get(
                full_url,
                headers=headers,
                timeout=ClientTimeout(total=self.request_timeout),
            )
        except (ValueError, IOError) as e:
            raise ApiGatewayRequestError(f"Error fetching {url} from Apisix") from e

        if not response.ok:
            raise ApiGatewayRequestError(
                f"Error fetching {url} from Apisix: {response.status} {response.content!r}"
            )

        return response

    async def _put_request(
        self, url: str, payload: dict[str, Any]
    ) -> aiohttp.ClientResponse:
        """

        :param url: The URL to send the PUT request to.
        :param payload: The data to be sent in the PUT request.
        :return: The response object from the PUT request.
        :raises ApiGatewayRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)

        headers = {"Content-type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        try:
            response = await self.async_session.put(
                full_url,
                json=payload,
                headers=headers,
                timeout=ClientTimeout(total=self.request_timeout),
            )
        except (ValueError, IOError) as e:
            raise ApiGatewayRequestError(
                f"Error creating {url} with payload {payload} in Apisix"
            ) from e

        if not response.ok:
            raise ApiGatewayRequestError(
                f"Error creating {url} with payload {payload} in Apisix: {response.status} {response.content!r}"
            )

        return response

    async def _patch_request(
        self, url: str, payload: dict[str, Any]
    ) -> aiohttp.ClientResponse:
        """

        :param url: The URL to send the PATCH request to.
        :param payload: The data to be sent in the PATCH request.
        :return: The response object from the PATCH request.
        :raises ApiGatewayRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)

        headers = {"Content-type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        try:
            response = await self.async_session.patch(
                full_url,
                json=payload,
                headers=headers,
                timeout=ClientTimeout(total=self.request_timeout),
            )
        except (ValueError, IOError) as e:
            raise ApiGatewayRequestError(
                f"Error updating {url} with payload {payload} in Apisix"
            ) from e

        if not response.ok:
            raise ApiGatewayRequestError(
                f"Error updating {url} with payload {payload} in Apisix: {response.status} {response.content!r}"
            )

        return response

    async def _delete_request(self, url: str) -> aiohttp.ClientResponse:
        """

        :param url: The URL to send the DELETE request to.
        :return: The response object from the DELETE request.
        :raises ApiGatewayRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)

        headers = {"Content-type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        try:
            response = await self.async_session.delete(
                full_url,
                headers=headers,
                timeout=ClientTimeout(total=self.request_timeout),
            )
        except (ValueError, IOError) as e:
            logger.error("Error deleting %s", url)
            raise ApiGatewayRequestError(f"Error deleting {url} in Apisix") from e

        if not response.ok:
            raise ApiGatewayRequestError(
                f"Error updating {url} in Apisix: {response.status} {response.content!r}"
            )

        return response

    def _parse_consumer_group_reponse(
        self, consumer_group_data: dict[str, Any]
    ) -> ConsumerGroup:
        consumer_group_data_value = consumer_group_data.get("value", {})
        return ConsumerGroup(
            name=consumer_group_data_value["id"],
            description=consumer_group_data_value.get("desc"),
            labels=consumer_group_data_value.get("labels"),
            plugins=consumer_group_data_value.get("plugins"),
        )

    async def get_consumer_groups(self) -> list[ConsumerGroup]:
        """
        Retrieves a list of all consumer groups.

        :return: A list of Consumer group instances.
        :raises ApiGatewayRequestError: If there is an error while fetching the consumer groups (e.g., HTTP error, invalid response).
        """
        url = "/apisix/admin/consumer_groups/"
        response = await self._get_request(url)
        consumer_groups_list = await response.json()
        return [
            self._parse_consumer_group_reponse(consumer_group_data)
            for consumer_group_data in consumer_groups_list.get("list", [])
        ]

    async def get_consumer_group(self, consumer_group_name: str) -> ConsumerGroup:
        """
        Retrieves details of a specific consumer group.

        :param consumer_group_name: The name of the consumer group.
        :return: A Consumer group instance.
        :raises ApiGatewayRequestError: If there is an error while fetching the consumer group (e.g., HTTP error, invalid response).
        """
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
        """
        Adds a new consumer group with associated labels.

        :param name: The name of the consumer group to be added.
        :param description: A description for the consumer group.
        :param labels: A dictionary of labels to be associated with the consumer group (e.g.,
                       {"version": "v1", "env": "staging"}).
        :return: `True` if the consumer group was successfully added, otherwise `False`.
        :raises ApiGatewayRequestError: If there is an error while adding the consumer group (e.g., HTTP error, invalid response).
        """

        url = f"/apisix/admin/consumer_groups/{name}"

        data: dict[str, Any] = {"plugins": {}}

        if labels is not None:
            data["labels"] = labels

        if description is not None:
            data["desc"] = description

        response = await self._put_request(url, data)
        return response.status == 201

    async def update_consumer_group(
        self, name: str, new_description: str, new_labels: dict[str, str]
    ) -> bool:
        """
        Updates the details of an existing consumer group.

        :param name: The name of the consumer group to be updated.
        :param new_description: The new description for the consumer group.
        :param new_labels: A dictionary of labels to be associated with the consumer group (e.g.,
                           {"version": "v2", "build": "16", "env": "production"}).
        :return: `True` if the consumer group was successfully updated, otherwise `False`.
        :raises ApiGatewayRequestError: If there is an error while updating the consumer group (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumer_groups/{name}"

        data = {
            "desc": new_description,
            "labels": new_labels,
        }
        response = await self._patch_request(url, data)
        return response.status == 200

    async def delete_consumer_group(self, consumer_group_name: str) -> bool:
        """
        Deletes an existing consumer group.

        :param consumer_group_name: The name of the consumer group.
        :return: `True` if the consumer group was successfully deleted, otherwise `False`.
        :raises ApiGatewayRequestError: If there is an error while deleting the consumer group (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"
        response = await self._delete_request(url)
        return response.status == 200

    async def set_rate_limit_to_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        """
        Sets a rate limit for an existing consumer group.

        :param consumer_group_name: The name of the consumer group to which the rate limit will be applied.
        :param requests_number: The maximum number of requests allowed within the time window.
        :param time_window: The time window (in seconds) within which the `requests_number` is counted.
        :return: `True` if the rate limit was successfully applied to the consumer group, otherwise `False`.
        :raises ApiGatewayRequestError: If there is an error while setting the rate limit (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"

        data = {
            "plugins": {
                "limit-count": {
                    "count": requests_number,
                    "time_window": time_window,
                    "rejected_code": 429,
                    "rejected_msg": "Too many requests",
                    "key_type": "var",
                    "key": "consumer_name",
                }
            }
        }
        response = await self._patch_request(url, data)
        return response.status == 200

    def _parse_consumer_reponse(self, consumer_data: dict[str, Any]) -> Consumer:
        consumer_data_value = consumer_data.get("value", {})
        return Consumer(
            name=consumer_data_value["username"],
            description=consumer_data_value.get("desc"),
            labels=consumer_data_value.get("labels"),
            plugins=consumer_data_value.get("plugins"),
            consumer_group_name=consumer_data_value.get("group_id"),
        )

    async def get_consumers(self) -> list[Consumer]:
        """
        Retrieves a list of all consumers.

        :return: A list of Consumer instances.
        :raises ApiGatewayRequestError: If there is an error while fetching the list of consumers (e.g., HTTP error, invalid response).
        """
        url = "/apisix/admin/consumers/"
        response = await self._get_request(url)
        consumers_list = await response.json()
        return [
            self._parse_consumer_reponse(consumer_data)
            for consumer_data in consumers_list.get("list", [])
        ]

    async def get_consumer(self, consumer_name: str) -> Consumer:
        """
        Retrieves the details of a specific consumer by name.

        :param consumer_name: The name of the consumer to retrieve.
        :return: A Consumer instance.
        :raises ApiGatewayRequestError: If there is an error while fetching the consumer (e.g., HTTP error, invalid response).
        """
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
        """
        Creates or updates a consumer. If the consumer already exists, its information will be updated;
        otherwise, a new consumer will be created.

        :param consumer_name: The name of the consumer.
        :param description: An optional description for the consumer.
        :param labels: Optional dictionary of labels to associate with the consumer.
        :param consumer_group_name: The name of the consumer group to associate the consumer with (optional).
        :return: `True` if the consumer was successfully created or updated, otherwise `False`.
        :raises ApiGatewayRequestError: If there is an error while creating or updating the consumer (e.g., HTTP error, invalid response).
        """
        url = "/apisix/admin/consumers/"

        data = {
            "username": consumer_name,
            "plugins": {
                "jwt-auth": {
                    "key": consumer_name,
                    "algorithm": "RS256",
                    "public_key": settings.JWT_PUBLIC_KEY,
                }
            },
        }

        if labels is not None:
            data["labels"] = labels

        if description is not None:
            data["desc"] = description

        if consumer_group_name is not None:
            data["group_id"] = consumer_group_name

        response = await self._put_request(url, data)
        return response.status == 201

    async def delete_consumer(self, consumer_name: str) -> bool:
        """
        Deletes a specific consumer by name.

        :param consumer_name: The name of the consumer to delete.
        :return: `True` if the consumer was successfully deleted, otherwise `False`.
        :raises ApiGatewayRequestError: If there is an error while deleting the consumer (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumers/{consumer_name}"
        response = await self._delete_request(url)
        return response.status == 200

    async def update_consumers_jwt_config(self) -> None:
        """
        Updates the JWT configuration for all consumers. For each consumer, this method will fetch its details
        and update its JWT authentication configuration with the current PUBLIC KEY configuration for JWT token validation (if changed).

        :return: None
        :raises ApiGatewayRequestError: If there is an error while fetching or updating any consumer (e.g., HTTP error, invalid response).
        """
        consumers = await self.get_consumers()

        for consumer in consumers:
            await self.upsert_consumer(
                consumer.name,
                consumer.description,
                consumer.labels,
                consumer.consumer_group_name,
            )
