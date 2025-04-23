import datetime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from app.config import settings
from app.datasources.api_gateway.apisix.apisix_metrics import (
    ApisixAggregatedBaseMetricEnum,
    ApisixAggregatedMetric,
    ApisixAggregationFunctionEnum,
)
from app.datasources.metrics.datadog.datadog_client import get_datadog_client
from app.datasources.metrics.exceptions import MetricsRequestError
from app.models.metrics import TimeSeriesMetricData
from app.tests.mocks.datadog_api import (
    datadog_time_series_empty_response,
    datadog_time_series_response,
)


class TestDatadogClient(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.datadog_client = get_datadog_client()

    async def asyncTearDown(self):
        await self.datadog_client.async_session.close()

    @patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
    async def test_get_metric_series_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=datadog_time_series_response)
        mock_get.return_value = mock_response

        metric = ApisixAggregatedMetric(
            ApisixAggregatedBaseMetricEnum.REQUEST_LATENCY,
            ApisixAggregationFunctionEnum.MEDIAN,
        )
        start_time = datetime.datetime(2025, 4, 8, tzinfo=datetime.timezone.utc)
        end_time = datetime.datetime(2025, 4, 10, tzinfo=datetime.timezone.utc)

        result = await self.datadog_client.get_metric_series(
            metric, start_time, end_time
        )

        expected_url = f"{settings.DATADOG_BASE_URL}/api/v1/query?from={int(start_time.timestamp())}&to={int(end_time.timestamp())}&query={metric.get_metric_query()}"

        mock_get.assert_awaited_once()
        actual_url = mock_get.call_args[0][0]
        self.assertEqual(actual_url, expected_url)

        assert result is not None
        self.assertIsInstance(result, TimeSeriesMetricData)
        self.assertEqual(result.point_list_length, 2)
        self.assertEqual(result.query, "apisix.request.latency.median{*}")
        self.assertEqual(result.point_list_interval, 30)
        self.assertEqual(
            result.point_list,
            [
                (
                    datetime.datetime(
                        2025, 4, 9, 9, 15, 30, tzinfo=datetime.timezone.utc
                    ),
                    3.000020980835,
                ),
                (
                    datetime.datetime(2025, 4, 9, 9, 16, tzinfo=datetime.timezone.utc),
                    1.5000104904175,
                ),
            ],
        )

    @patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
    async def test_get_metric_series_returns_none_when_no_series(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=datadog_time_series_empty_response)
        mock_get.return_value = mock_response

        metric = ApisixAggregatedMetric(
            ApisixAggregatedBaseMetricEnum.REQUEST_LATENCY,
            ApisixAggregationFunctionEnum.MEDIAN,
        )
        start_time = datetime.datetime(2025, 4, 8, tzinfo=datetime.timezone.utc)
        end_time = datetime.datetime(2025, 4, 10, tzinfo=datetime.timezone.utc)

        result = await self.datadog_client.get_metric_series(
            metric, start_time, end_time
        )

        self.assertIsNone(result)

    @patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
    async def test_get_metric_series_raises_on_http_error(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.reason = "Internal Server Error"
        mock_get.return_value = mock_response

        metric = ApisixAggregatedMetric(
            ApisixAggregatedBaseMetricEnum.REQUEST_LATENCY,
            ApisixAggregationFunctionEnum.MEDIAN,
        )
        start_time = datetime.datetime(2025, 4, 8, tzinfo=datetime.timezone.utc)
        end_time = datetime.datetime(2025, 4, 10, tzinfo=datetime.timezone.utc)

        with self.assertRaises(MetricsRequestError):
            await self.datadog_client.get_metric_series(metric, start_time, end_time)
