import logging
from typing import Any

import requests
from exceptions import ApisixRequestError
from safe_eth.util.http import build_full_url, prepare_http_session

from ..api_gateway_client import ApiGatewayClient

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
        self.http_session = prepare_http_session(10, 100)
        self.request_timeout = request_timeout

    def _get_request(self, url: str) -> requests.Response:
        """

        :param url: The URL to send the GET request to.
        :return: The response object from the GET request.
        :raises ApisixRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)
        try:
            response = self.http_session.get(
                full_url,
                headers={"X-API-KEY": self.api_key},
                timeout=self.request_timeout,
            )
        except (ValueError, IOError) as e:
            raise ApisixRequestError(f"Error fetching {url} from Apisix") from e

        if not response.ok:
            raise ApisixRequestError(
                f"Error fetching {url} from Apisix: {response.status_code} {response.content!r}"
            )

        return response

    def _put_request(self, url: str, payload: dict[str, Any]) -> requests.Response:
        """

        :param url: The URL to send the PUT request to.
        :param payload: The data to be sent in the PUT request.
        :return: The response object from the PUT request.
        :raises ApisixRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)
        try:
            response = self.http_session.put(
                full_url,
                json=payload,
                headers={"Content-type": "application/json", "X-API-KEY": self.api_key},
                timeout=self.request_timeout,
            )
        except (ValueError, IOError) as e:
            raise ApisixRequestError(
                f"Error creating {url} with payload {payload} in Apisix"
            ) from e

        if not response.ok:
            raise ApisixRequestError(
                f"Error creating {url} with payload {payload} in Apisix: {response.status_code} {response.content!r}"
            )

        return response

    def _patch_request(self, url: str, payload: dict[str, Any]) -> requests.Response:
        """

        :param url: The URL to send the PATCH request to.
        :param payload: The data to be sent in the PATCH request.
        :return: The response object from the PATCH request.
        :raises ApisixRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)
        try:
            response = self.http_session.patch(
                full_url,
                json=payload,
                headers={"Content-type": "application/json", "X-API-KEY": self.api_key},
                timeout=self.request_timeout,
            )
        except (ValueError, IOError) as e:
            raise ApisixRequestError(
                f"Error updating {url} with payload {payload} in Apisix"
            ) from e

        if not response.ok:
            raise ApisixRequestError(
                f"Error updating {url} with payload {payload} in Apisix: {response.status_code} {response.content!r}"
            )

        return response

    def _delete_request(self, url: str) -> requests.Response:
        """

        :param url: The URL to send the DELETE request to.
        :return: The response object from the DELETE request.
        :raises ApisixRequestError: If there is an error with the request.
        """
        full_url = build_full_url(self.base_url, url)
        try:
            response = self.http_session.delete(
                full_url,
                headers={"X-API-KEY": self.api_key},
                timeout=self.request_timeout,
            )
        except (ValueError, IOError) as e:
            logger.error("Error deleting %s", url)
            raise ApisixRequestError(f"Error deleting {url} in Apisix") from e

        if not response.ok:
            raise ApisixRequestError(
                f"Error updating {url} in Apisix: {response.status_code} {response.content!r}"
            )

        return response

    def _get_consumer_group_limit_count_plugin_config(
        self, requests_number: int, time_window: int
    ) -> dict[str, Any]:
        """
        Generates the plugin configuration for a consumer group with rate limiting.

        :param requests_number: The maximum number of requests allowed.
        :param time_window: The time window (in seconds) for rate limiting.
        :return: A dictionary with the plugin configuration.
        """

        return {
            "limit-count": {
                "count": requests_number,
                "time_window": time_window,
                "rejected_code": 429,
                "rejected_msg": "Too many requests",
                "key_type": "var",
                "key": "consumer_name",
            }
        }

    def add_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        """
        Adds a new consumer group with rate limiting.

        :param consumer_group_name: The name of the consumer group.
        :param requests_number: The maximum number of requests allowed.
        :param time_window: The time window (in seconds) for rate limiting.
        :return: `True` if the consumer group was successfully added, otherwise `False`.
        :raises ApisixRequestError: If there is an error while adding the consumer group (e.g., HTTP error, invalid response).
        """

        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"

        data = {
            "plugins": self._get_consumer_group_limit_count_plugin_config(
                requests_number, time_window
            )
        }

        response = self._put_request(url, data)
        return response.status_code == 201

    def get_consumer_group(self, consumer_group_name: str) -> dict[str, Any]:
        """
        Retrieves details of a specific consumer group.

        :param consumer_group_name: The name of the consumer group.
        :return: A dictionary containing the consumer group's details.
        :raises ApisixRequestError: If there is an error while fetching the consumer group (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"
        response = self._get_request(url)
        return response.json()

    def update_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        """
        Updates the rate limit for an existing consumer group.

        :param consumer_group_name: The name of the consumer group.
        :param requests_number: The new maximum number of requests allowed.
        :param time_window: The new time window (in seconds) for rate limiting.
        :return: `True` if the consumer group was successfully updated, otherwise `False`.
        :raises ApisixRequestError: If there is an error while updating the consumer group (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"
        data = {"plugins": {"limit-count": None}}
        self._patch_request(url, data)

        data = {
            "plugins": self._get_consumer_group_limit_count_plugin_config(
                requests_number, time_window
            )
        }
        response = self._patch_request(url, data)
        return response.status_code == 200

    def delete_consumer_group(self, consumer_group_name: str) -> bool:
        """
        Deletes an existing consumer group.

        :param consumer_group_name: The name of the consumer group.
        :return: `True` if the consumer group was successfully deleted, otherwise `False`.
        :raises ApisixRequestError: If there is an error while deleting the consumer group (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumer_groups/{consumer_group_name}"
        response = self._delete_request(url)
        return response.status_code == 200

    def get_consumer_groups(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of all consumer groups.

        :return: A list of dictionaries, each containing details of a consumer group.
        :raises ApisixRequestError: If there is an error while fetching the consumer groups (e.g., HTTP error, invalid response).
        """
        url = "/apisix/admin/consumer_groups/"
        response = self._get_request(url)
        return response.json().get("list", [])
