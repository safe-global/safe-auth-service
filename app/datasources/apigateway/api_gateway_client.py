from abc import ABC, abstractmethod
from typing import Any


class ApiGatewayClient(ABC):

    @abstractmethod
    async def get_consumer_groups(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of all consumer groups.

        :return: A list of dictionaries, each containing details of a consumer group.
        """
        pass

    @abstractmethod
    async def get_consumer_group(self, consumer_group_name: str) -> dict[str, Any]:
        """
        Retrieves details of a specific consumer group by its name.

        :param consumer_group_name: The name of the consumer group to retrieve.
        :return: A dictionary containing the consumer group's details (e.g., request limits, time window).
        """
        pass

    @abstractmethod
    async def add_consumer_group(
        self, name: str, description: str | None, labels: dict[str, str] | None = None
    ) -> bool:
        """
        Adds a new consumer group with specified description and labels.

        :param name: The name of the consumer group to be added.
        :param description: A description for the new consumer group.
        :param labels: A dictionary of labels to be associated with the consumer group (e.g., {"version": "v1", "env": "staging"}).
        :return: `True` if the consumer group was successfully added, otherwise `False`.
        """
        pass

    @abstractmethod
    async def update_consumer_group(
        self, name: str, new_description: str, new_labels: dict[str, str]
    ) -> bool:
        """
        Updates the details of an existing consumer group.

        :param name: The name of the consumer group to update.
        :param new_description: The new description for the consumer group.
        :param new_labels: A dictionary of labels to update the consumer group with.
        :return: `True` if the consumer group was successfully updated, otherwise `False`.
        """
        pass

    @abstractmethod
    async def delete_consumer_group(self, consumer_group_name: str) -> bool:
        """
        Deletes an existing consumer group.

        :param consumer_group_name: The name of the consumer group to delete.
        :return: `True` if the consumer group was successfully deleted, otherwise `False`.
        """
        pass

    @abstractmethod
    async def set_rate_limit_to_consumer_group(
        self, consumer_group_name: str, requests_number: int, time_window: int
    ) -> bool:
        """
        Sets a rate limit for an existing consumer group.

        :param consumer_group_name: The name of the consumer group to which the rate limit will be applied.
        :param requests_number: The maximum number of requests allowed within the time window.
        :param time_window: The time window (in seconds) within which the requests are counted.
        :return: `True` if the rate limit was successfully applied to the consumer group, otherwise `False`.
        """
        pass

    @abstractmethod
    async def get_consumers(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of all consumers.

        :return: A list of dictionaries, where each dictionary contains information about a consumer.
        Each dictionary represents a consumer and may include details like username, labels, etc.
        """
        pass

    @abstractmethod
    async def get_consumer(self, consumer_name: str) -> dict[str, Any]:
        """
        Retrieves the details of a specific consumer by name.

        :param consumer_name: The name of the consumer to retrieve.
        :return: A dictionary containing the details of the consumer (e.g., username, labels, etc.).
        """
        pass

    @abstractmethod
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
        """
        pass

    @abstractmethod
    async def delete_consumer(self, consumer_name: str) -> bool:
        """
        Deletes a specific consumer by name.

        :param consumer_name: The name of the consumer to delete.
        :return: `True` if the consumer was successfully deleted, otherwise `False`.
        """
        pass

    @abstractmethod
    async def update_consumers_jwt_config(self) -> None:
        """
        Updates the JWT configuration for all consumers. For each consumer, this method will fetch its details
        and update its JWT authentication configuration with the current PUBLIC KEY configuration for JWT token validation (if changed).

        :return: None
        """
        pass
