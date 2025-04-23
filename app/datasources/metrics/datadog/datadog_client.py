import datetime
from functools import cache

import aiohttp
from aiohttp import ClientTimeout
from safe_eth.util.http import build_full_url

from ....config import settings
from ....datasources.api_gateway.api_gateway_metrics import ApiGatewayMetric
from ....datasources.metrics.exceptions import MetricsRequestError
from ....models.metrics import TimeSeriesMetricData


@cache
def get_datadog_client(request_timeout: int = 10) -> "DatadogClient":
    """
    Creates and returns a DatadogClient instance.

    Args:
        request_timeout: The timeout (in seconds) for HTTP requests.

    Returns:
        An instance of DatadogClient.
    """
    return DatadogClient(
        base_url=settings.DATADOG_BASE_URL,
        api_key=settings.DATADOG_API_KEY,
        app_key=settings.DATADOG_APP_KEY,
        connections_pool_size=settings.DATADOG_CONNECTIONS_POOL_SIZE,
        request_timeout=request_timeout,
    )


class DatadogClient:
    """Client for querying metrics from Datadog."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        app_key: str,
        connections_pool_size: int = 100,
        request_timeout: int = 10,
    ):
        """

        Args:
            base_url: The base URL of the Datadog API.
            api_key: The Datadog API key.
            app_key: The Datadog application key.
            request_timeout: Timeout in seconds for API requests.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.app_key = app_key
        self.async_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_pool_size)
        )
        self.request_timeout = request_timeout

    async def _do_request(
        self,
        metric: ApiGatewayMetric,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> aiohttp.ClientResponse:
        """
        Sends a GET request to Datadog with the specified metric query.
        https://docs.datadoghq.com/api/latest/metrics/?code-lang=curl#query-timeseries-points

        Args:
            metric: The metric object with the query to send.
            from_datetime: Start of the time window.
            to_datetime: End of the time window.

        Returns:
            The response object from the HTTP request.

        Raises:
            MetricsRequestError: If there is an error with the request.
        """
        query = metric.get_metric_query()
        from_timestamp = int(from_datetime.timestamp())
        to_timestamp = int(to_datetime.timestamp())
        full_url = build_full_url(
            self.base_url,
            f"api/v1/query?from={from_timestamp}&to={to_timestamp}&query={query}",
        )

        headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
        }

        try:
            response = await self.async_session.get(
                full_url,
                headers=headers,
                timeout=ClientTimeout(total=self.request_timeout),
            )

        except (ValueError, IOError) as e:
            raise MetricsRequestError(
                f"Error while requesting metrics with query '{query}' (Start time: {from_timestamp}, End time: {to_timestamp})"
            ) from e

        if not response.ok:
            raise MetricsRequestError(
                f"Error while requesting metrics with query '{query}' (Start time: {from_timestamp}, End time: {to_timestamp}): {response.status} {response.reason}"
            )

        return response

    async def get_metric_series(
        self,
        metric: ApiGatewayMetric,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
    ) -> TimeSeriesMetricData | None:
        """
        Retrieves and parses metric data from Datadog.

        Args:
            metric: The metric to query.
            start_time: Start of the time window.
            end_time: End of the time window.

        Returns:
            A TimeSeriesMetricData object if data is found, otherwise None.
        """
        response = await self._do_request(metric, start_time, end_time)
        metric_data = await response.json()

        series = metric_data.get("series", [])
        if not series:
            return None

        series_data = series[0]
        point_list = [
            (
                datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc),
                value,
            )
            for ts, value in series_data.get("pointlist", [])
        ]

        return TimeSeriesMetricData(
            query=series_data.get("expression") or series_data.get("metric"),
            point_list_interval=series_data.get("interval"),
            point_list_length=len(point_list),
            point_list=point_list,
            point_list_start_datetime=datetime.datetime.fromtimestamp(
                series_data.get("start") / 1000, tz=datetime.timezone.utc
            ),
            point_list_end_datetime=datetime.datetime.fromtimestamp(
                series_data.get("end") / 1000, tz=datetime.timezone.utc
            ),
        )
