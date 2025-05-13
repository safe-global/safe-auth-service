import datetime
import uuid
from unittest import mock

from httpx import ASGITransport, AsyncClient

from ...datasources.db.connector import db_session_context
from ...main import app
from ...models.webhook import WebhookEventType, WebhookPublicPublic, WebhookRequest
from ...services.user_service import UserService
from ..datasources.db.async_db_test_case import AsyncDbTestCase
from ..datasources.db.factory import generate_random_user


class TestRouterWebhookEvents(AsyncDbTestCase):
    client: AsyncClient

    @db_session_context
    async def asyncSetUp(self):
        await super().asyncSetUp()
        user_service = UserService()
        user, password = await generate_random_user()
        self.user = user
        self.token = await user_service.login_user(user.email, password)
        self.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )

    async def test_get_webhook_events(self):
        response = await self.client.get(
            "/api/v1/webhooks/events",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )

        enum_values = {event.value for event in WebhookEventType}
        response_data_values = {event["name"] for event in response.json()}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(enum_values, response_data_values)

    @mock.patch("app.routers.webhooks.generate_webhook", new_callable=mock.AsyncMock)
    async def test_create_webhook(self, mock_generate_webhook):
        mock_generate_webhook.return_value = WebhookPublicPublic(
            id=uuid.uuid4(),
            created=datetime.datetime(2025, 5, 13, 0, 0, 0),
            updated=datetime.datetime(2025, 5, 13, 0, 0, 0),
            description="Test webhook",
            url="http://example.com",
            authorization="some-authorization",
            chains=[1, 2],
            events=[
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
            active=True,
        )

        create_webhook_request = {
            "description": "Test webhook",
            "url": "http://example.com",
            "authorization": "some-authorization",
            "chains": [1, 2],
            "events": ["SEND_TOKEN_TRANSFERS", "SEND_CONFIRMATIONS"],
            "active": True,
        }

        response = await self.client.post(
            "/api/v1/webhooks",
            headers={"Authorization": "Bearer " + self.token.access_token},
            json=create_webhook_request,
        )

        self.assertEqual(response.status_code, 201)
        webhook = response.json()
        self.assertEqual(webhook["description"], "Test webhook")
        self.assertEqual(webhook["authorization"], "some-authorization")
        self.assertEqual(webhook["url"], "http://example.com")
        self.assertEqual(webhook["chains"], [1, 2])
        self.assertEqual(
            webhook["events"], ["SEND_TOKEN_TRANSFERS", "SEND_CONFIRMATIONS"]
        )
        self.assertTrue(webhook["active"])
        mock_generate_webhook.assert_called_once()

    @mock.patch(
        "app.routers.webhooks.update_webhook_by_ids", new_callable=mock.AsyncMock
    )
    async def test_update_webhook(self, mock_update_webhook):
        mock_update_webhook.return_value = True

        webhook_id = uuid.uuid4()
        update_webhook_request = {
            "description": "Updated webhook description",
            "url": "http://new-url.com",
            "authorization": "new-authorization",
            "chains": [3, 4],
            "events": ["SEND_CONFIRMATIONS"],
            "active": False,
        }

        response = await self.client.put(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": "Bearer " + self.token.access_token},
            json=update_webhook_request,
        )

        self.assertEqual(response.status_code, 204)
        mock_update_webhook.assert_called_once_with(
            self.user.id,
            webhook_id,
            WebhookRequest(
                description="Updated webhook description",
                url="http://new-url.com",
                authorization="new-authorization",
                chains=[3, 4],
                events=[WebhookEventType.SEND_CONFIRMATIONS],
                active=False,
            ),
        )

        mock_update_webhook.return_value = False
        response = await self.client.put(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": "Bearer " + self.token.access_token},
            json=update_webhook_request,
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch(
        "app.routers.webhooks.delete_webhook_by_id", new_callable=mock.AsyncMock
    )
    async def test_delete_webhook(self, mock_delete_webhook):
        mock_delete_webhook.return_value = True

        webhook_id = uuid.uuid4()
        response = await self.client.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )

        self.assertEqual(response.status_code, 204)
        mock_delete_webhook.assert_called_once_with(webhook_id, self.user.id)

        mock_delete_webhook.return_value = False
        response = await self.client.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch("app.routers.webhooks.get_webhook_by_ids", new_callable=mock.AsyncMock)
    async def test_get_webhook(self, mock_get_webhook):
        mock_webhook = WebhookPublicPublic(
            id=uuid.uuid4(),
            created=datetime.datetime(2025, 5, 13, 0, 0, 0),  # Usar datetime
            updated=datetime.datetime(2025, 5, 13, 0, 0, 0),  # Usar datetime
            description="Test Webhook",
            url="http://example.com",
            authorization="some-authorization",
            chains=[1, 2],
            events=[
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
            active=True,
        )
        mock_get_webhook.return_value = mock_webhook

        response = await self.client.get(
            f"/api/v1/webhooks/{mock_webhook.id}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )

        self.assertEqual(response.status_code, 200)
        webhook = response.json()
        self.assertEqual(webhook["description"], "Test Webhook")
        self.assertEqual(webhook["authorization"], "some-authorization")
        self.assertEqual(webhook["url"], "http://example.com")
        self.assertEqual(webhook["chains"], [1, 2])
        self.assertEqual(
            webhook["events"], ["SEND_TOKEN_TRANSFERS", "SEND_CONFIRMATIONS"]
        )
        self.assertTrue(webhook["active"])
        mock_get_webhook.assert_called_once_with(mock_webhook.id, self.user.id)

        mock_get_webhook.return_value = None
        response = await self.client.get(
            f"/api/v1/webhooks/{mock_webhook.id}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )

        self.assertEqual(response.status_code, 404)

    @mock.patch(
        "app.routers.webhooks.get_webhooks_by_user", new_callable=mock.AsyncMock
    )
    async def test_get_webhooks(self, mock_get_webhooks_by_user):
        mock_webhooks = [
            WebhookPublicPublic(
                id=uuid.uuid4(),
                created=datetime.datetime(2025, 5, 13, 0, 0, 0),
                updated=datetime.datetime(2025, 5, 13, 0, 0, 0),
                description="Test Webhook",
                url="http://example.com",
                authorization="some-authorization",
                chains=[1, 2],
                events=[
                    WebhookEventType.SEND_TOKEN_TRANSFERS,
                    WebhookEventType.SEND_CONFIRMATIONS,
                ],
                active=True,
            )
        ]
        mock_get_webhooks_by_user.return_value = mock_webhooks

        response = await self.client.get(
            "/api/v1/webhooks",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )

        self.assertEqual(response.status_code, 200)
        webhooks = response.json()
        self.assertEqual(len(webhooks), 1)
        self.assertEqual(webhooks[0]["description"], "Test Webhook")
        self.assertEqual(webhooks[0]["authorization"], "some-authorization")
        self.assertEqual(webhooks[0]["url"], "http://example.com")
        self.assertEqual(webhooks[0]["chains"], [1, 2])
        self.assertEqual(
            webhooks[0]["events"], ["SEND_TOKEN_TRANSFERS", "SEND_CONFIRMATIONS"]
        )
        self.assertTrue(webhooks[0]["active"])
        mock_get_webhooks_by_user.assert_called_once_with(self.user.id)

        mock_get_webhooks_by_user.return_value = []

        response = await self.client.get(
            "/api/v1/webhooks",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )

        self.assertEqual(response.status_code, 200)
        webhooks = response.json()
        self.assertEqual(len(webhooks), 0)
