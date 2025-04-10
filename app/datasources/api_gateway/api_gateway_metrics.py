from abc import ABC, abstractmethod


class ApiGatewayMetric(ABC):

    @abstractmethod
    def get_metric_query(self) -> str:
        """
        Returns the query string for the metric.

        Returns:
            str: A formatted metric query string.
        """
        pass
