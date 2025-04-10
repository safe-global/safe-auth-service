from abc import abstractmethod
from enum import Enum
from typing import Any

from ..api_gateway_metrics import ApiGatewayMetric


class ApisixMetricTagFilterEnum(Enum):
    """Metric tag filters for Apisix metrics."""

    ROUTE_NAME = "route_name"
    SERVICE_NAME = "service_name"
    CONSUMER = "consumer"
    RESPONSE_STATUS = "response_status"


class ApisixAggregationFunctionEnum(Enum):
    """Aggregation functions used for or Apisix Histogram and Timer metrics."""

    PERCENTILE_95 = "95percentile"
    AVG = "avg"
    COUNT = "count"
    MAX = "max"
    MEDIAN = "median"


class ApisixAggregatedBaseMetricEnum(Enum):
    """Base metric names available for Apisix Histogram and Timer metrics."""

    APIGATEWAY_LATENCY = "apisix.apisix.latency"
    EGRESS_SIZE = "apisix.egress.size"
    INGRESS_SIZE = "apisix.ingress.size"
    REQUEST_LATENCY = "apisix.request.latency"
    UPSTREAM_LATENCY = "apisix.upstream.latency"


class ApisixMetricBase(ApiGatewayMetric):
    """Abstract base class for Apisix metrics with optional filters."""

    def __init__(
        self, metric_filters: dict[ApisixMetricTagFilterEnum, Any] | None = None
    ):
        """

        Args:
            metric_filters: Optional filters for the metric query.
        """
        self.metric_filters = metric_filters

    def _get_filters_query(self) -> str:
        """
         Builds the query string for the metric filters.

        Returns:
            str: Formatted filter query or '*' if no filters are provided.
        """
        return (
            ",".join(
                f"{tag.value}:{value}" for tag, value in self.metric_filters.items()
            )
            if self.metric_filters
            else "*"
        )

    @abstractmethod
    def get_metric_query(self) -> str:
        pass


class ApisixAggregatedMetric(ApisixMetricBase):
    """
    Represents a Histogram or Timer Apisix metric with a base metric name and aggregation function.

    The metrics and tag filters defined here are based on the official Apisix Datadog plugin:
    https://apisix.apache.org/docs/apisix/plugins/datadog/#exported-metrics
    """

    def __init__(
        self,
        base_metric: ApisixAggregatedBaseMetricEnum,
        aggregation_function: ApisixAggregationFunctionEnum,
        metric_filters: dict[ApisixMetricTagFilterEnum, Any] | None = None,
    ):
        """

        Args:
            base_metric: The base metric.
            aggregation_function: Aggregation function.
            metric_filters: Optional filters.
        """
        super().__init__(metric_filters)
        self.base_metric = base_metric
        self.aggregation_function = aggregation_function

    def get_metric_query(self) -> str:
        """
        Builds the full query string for the aggregated metric.

        Returns:
            str: Metric query.
        """
        filters_str = self._get_filters_query()
        return f"{self.base_metric.value}.{self.aggregation_function.value}{{{filters_str}}}"


class ApisixRequestsCounterMetric(ApisixMetricBase):
    """
    Represents an Apisix requests counter metric.

    The metrics and tag filters defined here are based on the official Apisix Datadog plugin:
    https://apisix.apache.org/docs/apisix/plugins/datadog/#exported-metrics
    """

    def __init__(
        self,
        metric_filters: dict[ApisixMetricTagFilterEnum, Any] | None = None,
    ):
        """

        Args:
            metric_filters: Optional filters.
        """
        super().__init__(metric_filters)

    def get_metric_query(self) -> str:
        """
        Builds the full query string for the request counter metric.

        Returns:
            str: Metric query.
        """
        filters_str = self._get_filters_query()
        return f"apisix.request.counter{{{filters_str}}}"
