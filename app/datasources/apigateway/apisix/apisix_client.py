import logging
from typing import Any

import requests
from safe_eth.util.http import build_full_url, prepare_http_session

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
            raise ApiGatewayRequestError(f"Error fetching {url} from Apisix") from e

        if not response.ok:
            raise ApiGatewayRequestError(
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
            raise ApiGatewayRequestError(
                f"Error creating {url} with payload {payload} in Apisix"
            ) from e

        if not response.ok:
            raise ApiGatewayRequestError(
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
            raise ApiGatewayRequestError(
                f"Error updating {url} with payload {payload} in Apisix"
            ) from e

        if not response.ok:
            raise ApiGatewayRequestError(
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
            raise ApiGatewayRequestError(f"Error deleting {url} in Apisix") from e

        if not response.ok:
            raise ApiGatewayRequestError(
                f"Error updating {url} in Apisix: {response.status_code} {response.content!r}"
            )

        return response

    def get_consumer_groups(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of all consumer groups.

        :return: A list of dictionaries, each containing details of a consumer group.
        :raises ApisixRequestError: If there is an error while fetching the consumer groups (e.g., HTTP error, invalid response).
        """
        url = "/apisix/admin/consumer_groups/"
        response = self._get_request(url)
        return response.json().get("list", [])

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

    def add_consumer_group(
        self, name: str, description: str, labels: dict[str, str]
    ) -> bool:
        """
        Adds a new consumer group with associated labels.

        :param name: The name of the consumer group to be added.
        :param description: A description for the consumer group.
        :param labels: A dictionary of labels to be associated with the consumer group (e.g.,
                       {"version": "v1", "env": "staging"}).
        :return: `True` if the consumer group was successfully added, otherwise `False`.
        :raises ApisixRequestError: If there is an error while adding the consumer group (e.g., HTTP error, invalid response).
        """

        url = f"/apisix/admin/consumer_groups/{name}"

        data = {"desc": description, "labels": labels, "plugins": {}}

        response = self._put_request(url, data)
        return response.status_code == 201

    def update_consumer_group(
        self, name: str, new_description: str, new_labels: dict[str, str]
    ) -> bool:
        """
        Updates the details of an existing consumer group.

        :param name: The name of the consumer group to be updated.
        :param new_description: The new description for the consumer group.
        :param new_labels: A dictionary of labels to be associated with the consumer group (e.g.,
                           {"version": "v2", "build": "16", "env": "production"}).
        :return: `True` if the consumer group was successfully updated, otherwise `False`.
        :raises ApisixRequestError: If there is an error while updating the consumer group (e.g., HTTP error, invalid response).
        """
        url = f"/apisix/admin/consumer_groups/{name}"

        data = {
            "desc": new_description,
            "labels": new_labels,
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

    def set_rate_limit_to_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        """
        Sets a rate limit for an existing consumer group.

        :param consumer_group_name: The name of the consumer group to which the rate limit will be applied.
        :param requests_number: The maximum number of requests allowed within the time window.
        :param time_window: The time window (in seconds) within which the `requests_number` is counted.
        :return: `True` if the rate limit was successfully applied to the consumer group, otherwise `False`.
        :raises ApisixRequestError: If there is an error while setting the rate limit (e.g., HTTP error, invalid response).
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
        response = self._patch_request(url, data)
        return response.status_code == 200
