import uuid
from unittest import mock

import faker

from ...config import settings
from ...datasources.db.connector import db_session_context
from ...datasources.db.models import Webhook
from ...datasources.webhooks.events_service.events_service_client import (
    EventsServiceClient,
)
from ...models.webhook import WebhookEventsService, WebhookEventType, WebhookRequest
from ...services.webhook_service import (
    WebhookCreationLimitReached,
    delete_webhook_by_id,
    generate_webhook,
    get_webhook_by_ids,
    get_webhooks_by_user,
    update_webhook_by_ids,
)
from ...tests.datasources.db.async_db_test_case import AsyncDbTestCase
from ...tests.datasources.db.factory import (
    generate_random_user,
    generate_random_webhook,
)

fake = faker.Faker()


class TestWebhookService(AsyncDbTestCase):

    @db_session_context
    @mock.patch.object(EventsServiceClient, "add_webhook", new_callable=mock.AsyncMock)
    async def test_generate_webhook(self, mock_add_webhook):
        user, _ = await generate_random_user()
        stored_webhooks = await Webhook.get_webhooks_by_user(user.id)
        self.assertEqual(len(stored_webhooks), 0)

        mock_events_service_webhook_id = uuid.uuid4()
        mock_add_webhook.return_value = WebhookEventsService(
            url="http://example.com",
            authorization="some-authorization",
            chains=[1, 2],
            events=[
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
            active=True,
            id=mock_events_service_webhook_id,
        )

        create_webhook_request = WebhookRequest(
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

        generated_webhook = await generate_webhook(user.id, create_webhook_request)
        self.assertIsNotNone(generated_webhook)
        stored_webhook = await Webhook.get_by_ids(generated_webhook.id, user.id)
        self.assertIsNotNone(stored_webhook)
        self.assertEqual(
            stored_webhook.external_webhook_id, mock_events_service_webhook_id
        )
        self.assertEqual(generated_webhook.id, stored_webhook.id)
        self.assertEqual(generated_webhook.description, "Test webhook")
        self.assertEqual(generated_webhook.url, "http://example.com")
        self.assertEqual(generated_webhook.authorization, "some-authorization")
        self.assertEqual(generated_webhook.chains, [1, 2])
        self.assertEqual(
            generated_webhook.events,
            [
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
        )
        self.assertTrue(generated_webhook.active)
        mock_add_webhook.assert_called_once_with(
            webhook_url="http://example.com",
            chains=[1, 2],
            events=["SEND_TOKEN_TRANSFERS", "SEND_CONFIRMATIONS"],
            active=True,
            authorization="some-authorization",
            description=f"Auth Service: user {user.id} webhook {generated_webhook.id}",
        )

        with mock.patch.object(settings, "EVENTS_SERVICE_WEBHOOKS_CREATION_LIMIT", 1):
            with self.assertRaises(WebhookCreationLimitReached):
                await generate_webhook(user.id, create_webhook_request)

    @db_session_context
    @mock.patch.object(
        EventsServiceClient, "delete_webhook", new_callable=mock.AsyncMock
    )
    async def test_delete_webhook_by_id(self, mock_delete_webhook):
        user, _ = await generate_random_user()

        deleted = await delete_webhook_by_id(uuid.uuid4(), user.id)
        self.assertFalse(deleted)

        stored_webhook = await generate_random_webhook(user.id)

        mock_delete_webhook.return_value = None

        stored_webhooks = await Webhook.get_webhooks_by_user(user.id)
        self.assertEqual(len(stored_webhooks), 1)

        success = await delete_webhook_by_id(stored_webhook.id, user.id)
        self.assertTrue(success)
        stored_webhooks = await Webhook.get_webhooks_by_user(user.id)
        self.assertEqual(len(stored_webhooks), 0)
        mock_delete_webhook.assert_called_once_with(stored_webhook.external_webhook_id)

    @db_session_context
    @mock.patch.object(
        EventsServiceClient, "update_webhook", new_callable=mock.AsyncMock
    )
    async def test_update_webhook_by_ids(self, mock_update_webhook):
        user, _ = await generate_random_user()

        updated_webhook_request = WebhookRequest(
            description="Updated webhook description",
            url="http://new-url.com",
            authorization="new-authorization",
            chains=[3, 4],
            events=[WebhookEventType.SEND_CONFIRMATIONS],
            active=False,
        )
        updated = await update_webhook_by_ids(
            uuid.uuid4(), user.id, updated_webhook_request
        )
        self.assertFalse(updated)

        generated_webhook = await generate_random_webhook(user.id)

        stored_webhook = await Webhook.get_by_ids(generated_webhook.id, user.id)
        self.assertIsNotNone(stored_webhook)
        self.assertEqual(stored_webhook.description, "Webhook for testing")

        mock_update_webhook.return_value = None

        success = await update_webhook_by_ids(
            generated_webhook.id, user.id, updated_webhook_request
        )
        self.assertTrue(success)
        mock_update_webhook.assert_called_once_with(
            webhook_id=generated_webhook.id,
            webhook_url="http://new-url.com",
            chains=[3, 4],
            events=["SEND_CONFIRMATIONS"],
            active=False,
            authorization="new-authorization",
        )
        updated_webhook = await Webhook.get_by_ids(generated_webhook.id, user.id)
        self.assertIsNotNone(updated_webhook)
        self.assertEqual(updated_webhook.description, "Updated webhook description")

    @db_session_context
    @mock.patch.object(EventsServiceClient, "get_webhook", new_callable=mock.AsyncMock)
    async def test_get_webhooks_by_user(self, mock_get_webhook):
        user, _ = await generate_random_user()
        generated_webhook = await generate_random_webhook(user.id)

        mock_get_webhook.return_value = WebhookEventsService(
            url="http://example.com",
            authorization="some-authorization",
            chains=[1, 2],
            events=[
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
            active=True,
            id=generated_webhook.external_webhook_id,
        )

        webhooks = await get_webhooks_by_user(user.id)
        self.assertEqual(len(webhooks), 1)
        self.assertEqual(webhooks[0].description, generated_webhook.description)
        self.assertEqual(webhooks[0].url, "http://example.com")
        self.assertEqual(webhooks[0].authorization, "some-authorization")
        self.assertEqual(webhooks[0].chains, [1, 2])
        self.assertEqual(
            webhooks[0].events,
            [
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
        )
        self.assertTrue(webhooks[0].active)

        mock_get_webhook.assert_called_once_with(generated_webhook.external_webhook_id)

    @db_session_context
    @mock.patch.object(EventsServiceClient, "get_webhook", new_callable=mock.AsyncMock)
    async def test_get_webhook_by_ids(self, mock_get_webhook):
        user, _ = await generate_random_user()
        retrieved_webhook = await get_webhook_by_ids(uuid.uuid4(), user.id)
        self.assertIsNone(retrieved_webhook)

        generated_webhook = await generate_random_webhook(user.id)

        mock_get_webhook.return_value = WebhookEventsService(
            url="http://example.com",
            authorization="some-authorization",
            chains=[1, 2],
            events=[
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
            active=True,
            id=generated_webhook.external_webhook_id,
        )

        retrieved_webhook = await get_webhook_by_ids(generated_webhook.id, user.id)
        assert retrieved_webhook is not None
        self.assertEqual(retrieved_webhook.id, generated_webhook.id)
        self.assertEqual(retrieved_webhook.description, "Webhook for testing")
        self.assertEqual(retrieved_webhook.url, "http://example.com")
        self.assertEqual(retrieved_webhook.authorization, "some-authorization")
        self.assertEqual(retrieved_webhook.chains, [1, 2])
        self.assertEqual(
            retrieved_webhook.events,
            [
                WebhookEventType.SEND_TOKEN_TRANSFERS,
                WebhookEventType.SEND_CONFIRMATIONS,
            ],
        )
        self.assertTrue(retrieved_webhook.active)

        mock_get_webhook.assert_called_once_with(generated_webhook.external_webhook_id)
