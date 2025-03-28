from abc import ABC, abstractmethod
from typing import Any


class ApiGatewayClient(ABC):

    @abstractmethod
    def add_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        """
        Adds a new consumer group with specified request limits and time window.

        :param consumer_group_name: The name of the consumer group.
        :param requests_number: The maximum number of requests allowed within the time window.
        :param time_window: The time window (in seconds) for request limitation.
        :return: `True` if the consumer group was successfully added, otherwise `False`.
        """
        pass

    @abstractmethod
    def get_consumer_group(self, consumer_group_name: str) -> dict[str, Any]:
        """
        Retrieves details of a specific consumer group by its name.

        :param consumer_group_name: The name of the consumer group.
        :return: A dictionary containing the consumer group's details (e.g., request limits, time window).
        """
        pass

    @abstractmethod
    def update_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        """
        Updates the request limits and time window for an existing consumer group.

        :param consumer_group_name: The name of the consumer group to update.
        :param requests_number: The new maximum number of requests.
        :param time_window: The new time window (in seconds) for request limitation.
        :return: `True` if the consumer group was successfully updated, otherwise `False`.
        """
        pass

    @abstractmethod
    def delete_consumer_group(self, consumer_group_name: str) -> bool:
        """
        Deletes an existing consumer group.

        :param consumer_group_name: The name of the consumer group to delete.
        :return: `True` if the consumer group was successfully deleted, otherwise `False`.
        """
        pass

    @abstractmethod
    def get_consumer_groups(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of all consumer groups.

        :return: A list of dictionaries, each containing details of a consumer group.
        """
        pass
