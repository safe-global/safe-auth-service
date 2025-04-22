import datetime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from app.datasources.metrics.exceptions import MetricsRequestError
from app.datasources.metrics.prometheus.prometheus_client import get_prometheus_client
from app.tests.mocks.prometheus_api import (
    prometheus_empty_response,
    prometheus_matrix_response,
    prometheus_vector_response,
)


class TestPrometheusClient(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.prometheus_client = get_prometheus_client()

    async def asyncTearDown(self):
        await self.prometheus_client.async_session.close()

    @patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
    async def test_query_range_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=prometheus_matrix_response)
        mock_get.return_value = mock_response

        start = datetime.datetime(2025, 4, 20, 10, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2025, 4, 20, 10, 6, tzinfo=datetime.timezone.utc)
        query = (
            'apisix_http_status{consumer="usuario1", request_uri=~"/service/hello.*"}'
        )

        result = await self.prometheus_client.query_range(query, start, end, step=30)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertTrue(
            all(
                r.query
                == 'apisix_http_status{consumer="usuario1", request_uri=~"/service/hello.*"}'
                for r in result
            )
        )
        self.assertEqual(
            result[0].point_list,
            [
                (
                    datetime.datetime.fromtimestamp(
                        1745243602.356, tz=datetime.timezone.utc
                    ),
                    1.0,
                ),
                (
                    datetime.datetime.fromtimestamp(
                        1745243659.356, tz=datetime.timezone.utc
                    ),
                    4.0,
                ),
                (
                    datetime.datetime.fromtimestamp(
                        1745243716.356, tz=datetime.timezone.utc
                    ),
                    8.0,
                ),
                (
                    datetime.datetime.fromtimestamp(
                        1745243773.356, tz=datetime.timezone.utc
                    ),
                    12.0,
                ),
                (
                    datetime.datetime.fromtimestamp(
                        1745243830.356, tz=datetime.timezone.utc
                    ),
                    16.0,
                ),
                (
                    datetime.datetime.fromtimestamp(
                        1745243887.356, tz=datetime.timezone.utc
                    ),
                    20.0,
                ),
                (
                    datetime.datetime.fromtimestamp(
                        1745243944.356, tz=datetime.timezone.utc
                    ),
                    20.0,
                ),
            ],
        )
        self.assertTrue(all(r.point_list_length == 7 for r in result))
        self.assertTrue(all(r.point_list_interval == 30 for r in result))
        self.assertTrue(all(r.point_list_start_datetime == start for r in result))
        self.assertTrue(all(r.point_list_end_datetime == end for r in result))

    @patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
    async def test_query_instant_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=prometheus_vector_response)
        mock_get.return_value = mock_response

        timestamp = datetime.datetime(2025, 4, 20, 10, 0, tzinfo=datetime.timezone.utc)
        query = (
            'apisix_http_status{consumer="usuario1", request_uri=~"/service/hello.*"}'
        )

        result = await self.prometheus_client.query_instant(query, timestamp)

        self.assertIsInstance(result, list)
        self.assertEqual(
            result[0].point_list,
            [
                (
                    datetime.datetime.fromtimestamp(
                        1745245204.461, tz=datetime.timezone.utc
                    ),
                    20.0,
                ),
            ],
        )
        self.assertEqual(
            result[1].point_list,
            [
                (
                    datetime.datetime.fromtimestamp(
                        1745245204.461, tz=datetime.timezone.utc
                    ),
                    30.0,
                ),
            ],
        )
        self.assertEqual(
            result[2].point_list,
            [
                (
                    datetime.datetime.fromtimestamp(
                        1745245204.461, tz=datetime.timezone.utc
                    ),
                    40.0,
                ),
            ],
        )
        self.assertEqual(len(result), 3)
        self.assertTrue(
            all(
                r.query
                == 'apisix_http_status{consumer="usuario1", request_uri=~"/service/hello.*"}'
                for r in result
            )
        )
        self.assertTrue(all(r.point_list_length == 1 for r in result))
        self.assertTrue(all(r.point_list_interval == 0 for r in result))
        self.assertTrue(all(r.point_list_start_datetime == timestamp for r in result))
        self.assertTrue(all(r.point_list_end_datetime == timestamp for r in result))

    @patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
    async def test_query_range_returns_empty_on_no_data(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=prometheus_empty_response)
        mock_get.return_value = mock_response

        start = datetime.datetime(2025, 4, 20, 10, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2025, 4, 20, 10, 6, tzinfo=datetime.timezone.utc)
        query = (
            'apisix_http_status{consumer="usuario1", request_uri=~"/service/hello.*"}'
        )

        result = await self.prometheus_client.query_range(query, start, end)

        self.assertEqual(result, [])

    @patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
    async def test_query_range_raises_on_error(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.reason = "Internal Server Error"
        mock_get.return_value = mock_response

        start = datetime.datetime(2025, 4, 20, 10, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2025, 4, 20, 10, 6, tzinfo=datetime.timezone.utc)
        query = (
            'apisix_http_status{consumer="usuario1", request_uri=~"/service/hello.*"}'
        )

        with self.assertRaises(MetricsRequestError):
            await self.prometheus_client.query_range(query, start, end)
