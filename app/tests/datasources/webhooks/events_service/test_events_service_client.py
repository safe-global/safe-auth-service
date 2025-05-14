import uuid
from unittest import IsolatedAsyncioTestCase, mock
from unittest.mock import AsyncMock

import aiohttp

from app.datasources.webhooks.events_service.events_service_client import (
    get_events_service_client,
)
from app.datasources.webhooks.events_service.exceptions import EventsServiceRequestError
from app.models.webhook import WebhookEventsService, WebhookEventType
from app.tests.mocks.events_service_api import events_service_api_response


class TestPrometheusClient(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.events_service_client = get_events_service_client()

    async def asyncTearDown(self):
        await self.events_service_client.async_session.close()

    @mock.patch.object(aiohttp.ClientSession, "post", new_callable=AsyncMock)
    async def test_add_webhook(self, mock_post):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=events_service_api_response)
        mock_post.return_value = mock_response

        webhook_url = "http://example.com"
        chains = [1, 2]
        events = [
            WebhookEventType.SEND_TOKEN_TRANSFERS,
            WebhookEventType.SEND_CONFIRMATIONS,
        ]
        authorization = "Bearer token"
        description = "Test webhook"

        result = await self.events_service_client.add_webhook(
            webhook_url, chains, events, description, True, authorization
        )

        mock_post.assert_called_with(
            "http:///webhooks",
            json={
                "url": "http://example.com",
                "chains": [1, 2],
                "events": ["SEND_TOKEN_TRANSFERS", "SEND_CONFIRMATIONS"],
                "isActive": True,
                "authorization": "Bearer token",
                "description": "Test webhook",
            },
            headers={"Content-Type": "application/json"},
            timeout=mock.ANY,
        )

        self.assertIsInstance(result, WebhookEventsService)
        self.assertEqual(result.url, webhook_url)
        self.assertEqual(result.authorization, authorization)
        self.assertEqual(result.chains, chains)
        self.assertEqual(result.events, events)
        self.assertTrue(result.is_active)

        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.reason = "Internal Server Error"
        mock_post.return_value = mock_response

        with self.assertRaises(EventsServiceRequestError):
            await self.events_service_client.add_webhook(
                webhook_url, chains, events, description
            )

    @mock.patch.object(aiohttp.ClientSession, "get", new_callable=AsyncMock)
    async def test_get_webhook(self, mock_get):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=events_service_api_response)
        mock_get.return_value = mock_response

        webhook_id = uuid.uuid4()

        result = await self.events_service_client.get_webhook(webhook_id)

        mock_get.assert_called_with(
            f"http:///webhooks/{webhook_id}",
            json=None,
            headers={},
            timeout=mock.ANY,
        )

        self.assertIsInstance(result, WebhookEventsService)
        self.assertEqual(result.url, "http://example.com")
        self.assertEqual(result.authorization, "Bearer token")
        self.assertEqual(result.chains, [1, 2])
        self.assertEqual(
            result.events,
            [
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
        )
        self.assertTrue(result.is_active)

    @mock.patch.object(aiohttp.ClientSession, "delete", new_callable=AsyncMock)
    async def test_delete_webhook(self, mock_delete):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_delete.return_value = mock_response

        webhook_id = uuid.uuid4()

        result = await self.events_service_client.delete_webhook(webhook_id)

        mock_delete.assert_called_with(
            f"http:///webhooks/{webhook_id}",
            json=None,
            headers={},
            timeout=mock.ANY,
        )

        self.assertTrue(result)

        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.reason = "Internal Server Error"
        mock_delete.return_value = mock_response

        webhook_id = uuid.uuid4()

        with self.assertRaises(EventsServiceRequestError):
            await self.events_service_client.delete_webhook(webhook_id)

    @mock.patch.object(aiohttp.ClientSession, "put", new_callable=AsyncMock)
    async def test_update_webhook(self, mock_put):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_put.return_value = mock_response

        webhook_id = uuid.uuid4()
        webhook_url = "http://new-url.com"
        chains = [3, 4]
        events = [WebhookEventType.SEND_TOKEN_TRANSFERS]
        is_active = False
        description = "Test webhook"

        result = await self.events_service_client.update_webhook(
            webhook_id, webhook_url, chains, events, description, is_active
        )
        mock_put.assert_called_with(
            f"http:///webhooks/{webhook_id}",
            json={
                "url": "http://new-url.com",
                "chains": [3, 4],
                "events": ["SEND_TOKEN_TRANSFERS"],
                "description": "Test webhook",
                "authorization": "",
                "isActive": False,
            },
            headers={"Content-Type": "application/json"},
            timeout=mock.ANY,
        )
        self.assertTrue(result)

        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.reason = "Internal Server Error"
        mock_put.return_value = mock_response

        with self.assertRaises(EventsServiceRequestError):
            await self.events_service_client.update_webhook(
                webhook_id, webhook_url, chains, events, description
            )
