import datetime
import logging
from functools import cache
from typing import Any

import aiohttp
from safe_eth.util.http import build_full_url

from ....config import settings
from ....datasources.metrics.exceptions import MetricsRequestError
from ....models.metrics import TimeSeriesMetricData

logger = logging.getLogger(__name__)


@cache
def get_prometheus_client(request_timeout: int = 10) -> "PrometheusClient":
    """
    Creates and returns a PrometheusClient instance.

    Args:
        request_timeout: The timeout (in seconds) for HTTP requests.

    Returns:
        An instance of PrometheusClient.
    """
    return PrometheusClient(
        base_url=settings.PROMETHEUS_BASE_URL,
        connections_pool_size=settings.PROMETHEUS_CONNECTIONS_POOL_SIZE,
        request_timeout=request_timeout,
    )


class PrometheusClient:
    """Client for querying metrics from Prometheus."""

    def __init__(
        self, base_url: str, connections_pool_size: int = 100, request_timeout: int = 10
    ):
        """

        Args:
            base_url: The base URL of the Prometheus API.
            request_timeout: Timeout in seconds for API requests.
        """
        self.base_url = base_url
        self.async_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_pool_size)
        )
        self.request_timeout = request_timeout

    async def _do_request(
        self,
        endpoint: str,
        params: dict,
    ) -> aiohttp.ClientResponse:
        full_url = build_full_url(self.base_url, endpoint)
        try:
            response = await self.async_session.get(
                full_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.request_timeout),
            )
        except (ValueError, IOError) as e:
            raise MetricsRequestError(
                f"Error while requesting metrics from {full_url} with params '{params}'"
            ) from e

        if not response.ok:
            raise MetricsRequestError(
                f"Error while requesting metrics from {full_url} with params '{params}': {response.status} {response.reason}"
            )

        return response

    def _get_raw_points(self, entry: dict[str, Any], result_type: str) -> list:
        if result_type == "vector":
            return [entry["value"]] if entry.get("value") else []
        elif result_type == "matrix":
            return entry.get("values", [])
        return []

    def _parse_api_response(
        self,
        response_json: dict[str, Any],
        query: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        step: int,
    ) -> list[TimeSeriesMetricData]:
        """
        Parses the JSON response from the Prometheus API into structured time series data.

        Args:
            response_json: The raw JSON response from the Prometheus API.
            query: The PromQL query string used for the request.
            start_time: The start time of the query range.
            end_time: The end time of the query range.
            step: The expected interval in seconds between data points.

        Returns:
            A list of parsed time series metric data objects.
        """
        result_status = response_json.get("status")
        if result_status != "success":
            logger.error(
                f"Error while parsing response from Prometheus API: {response_json}"
            )
            return []

        result_data = response_json["data"]
        result_type = result_data["resultType"]
        results = result_data["result"]

        series_list: list[TimeSeriesMetricData] = []

        for entry in results:
            point_list = [
                (
                    datetime.datetime.fromtimestamp(
                        point_timestamp, tz=datetime.timezone.utc
                    ),
                    point_value,
                )
                for point_timestamp, point_value in self._get_raw_points(
                    entry, result_type
                )
            ]

            series = TimeSeriesMetricData(
                query=query,
                point_list_interval=step,
                point_list_length=len(point_list),
                point_list=point_list,
                point_list_start_datetime=start_time,
                point_list_end_datetime=end_time,
            )
            series_list.append(series)

        return series_list

    async def query_range(
        self,
        query: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
        step: int = 30,
    ) -> list[TimeSeriesMetricData]:
        """
        Executes a range query against the Prometheus API over a specified time interval.

        Args:
            query: The PromQL query string. (https://prometheus.io/docs/prometheus/latest/querying/basics/)
            from_datetime: Start time of the query range.
            to_datetime: End time of the query range.
            step: Step in seconds between data points. Defaults to 30.

        Returns:
            A list of time series metric data results.
        """
        params = {
            "query": query,
            "start": int(from_datetime.timestamp()),
            "end": int(to_datetime.timestamp()),
            "step": step,
        }
        response = await self._do_request("api/v1/query_range", params)
        metric_data = await response.json()
        return self._parse_api_response(
            metric_data, query, from_datetime, to_datetime, step
        )

    async def query_instant(
        self, query: str, at_time: datetime.datetime
    ) -> list[TimeSeriesMetricData]:
        """
        Executes an instant query at a specific point in time.

        Args:
            query: The PromQL query string. (https://prometheus.io/docs/prometheus/latest/querying/basics/)
            at_time: The time at which to execute the query.

        Returns:
            A list containing the instant metric data result.
        """
        params = {"query": query, "time": int(at_time.timestamp())}

        response = await self._do_request("api/v1/query", params)
        metric_data = await response.json()
        return self._parse_api_response(metric_data, query, at_time, at_time, 0)
