import asyncio
import uuid

from ..config import settings
from ..datasources.db.models import Webhook
from ..datasources.webhooks.events_service.events_service_client import (
    get_events_service_client,
)
from ..models.webhook import WebhookEventsService, WebhookPublicPublic, WebhookRequest


class WebhookServiceException(Exception):
    pass


class WebhookCreationLimitReached(WebhookServiceException):
    pass


def _parse_webhook_public(
    model_webhook: Webhook, events_service_webhook: WebhookEventsService
) -> WebhookPublicPublic:
    return WebhookPublicPublic(
        id=model_webhook.id,
        created=model_webhook.created,
        updated=model_webhook.modified,
        description=model_webhook.description,
        url=events_service_webhook.url,
        authorization=events_service_webhook.authorization,
        chains=events_service_webhook.chains,
        events=events_service_webhook.events,
        active=events_service_webhook.active,
    )


async def generate_webhook(
    user_id: uuid.UUID, webhook_request_info: WebhookRequest
) -> WebhookPublicPublic:
    user_webhooks = await Webhook.get_webhooks_by_user(user_id)

    if len(user_webhooks) >= settings.EVENTS_SERVICE_WEBHOOKS_CREATION_LIMIT:
        raise WebhookCreationLimitReached("Webhook creation limit reached")

    webhook_id = uuid.uuid4()
    events_service_webhook = await get_events_service_client().add_webhook(
        webhook_url=webhook_request_info.url,
        chains=webhook_request_info.chains,
        events=webhook_request_info.events,
        active=webhook_request_info.active,
        authorization=webhook_request_info.authorization,
        description=f"Auth Service: user {user_id} webhook {webhook_id}",
    )
    db_webhook = Webhook(
        id=webhook_id,
        user_id=user_id,
        description=webhook_request_info.description,
        external_webhook_id=events_service_webhook.id,
    )
    await db_webhook.create()
    return _parse_webhook_public(db_webhook, events_service_webhook)


async def update_webhook_by_ids(
    webhook_id: uuid.UUID, user_id: uuid.UUID, webhook_request_info: WebhookRequest
) -> bool:
    stored_webhook = await Webhook.get_by_ids(webhook_id, user_id)

    if not stored_webhook:
        return False

    await get_events_service_client().update_webhook(
        webhook_id=webhook_id,
        webhook_url=webhook_request_info.url,
        chains=webhook_request_info.chains,
        events=webhook_request_info.events,
        active=webhook_request_info.active,
        authorization=webhook_request_info.authorization,
    )
    stored_webhook.description = webhook_request_info.description
    await stored_webhook.update()
    return True


async def get_webhooks_by_user(user_id: uuid.UUID) -> list["WebhookPublicPublic"]:
    db_webhooks = await Webhook.get_webhooks_by_user(user_id)
    retrieve_events_service_webhooks_tasks = [
        get_events_service_client().get_webhook(webhook.external_webhook_id)
        for webhook in db_webhooks
    ]
    events_service_webhooks = await asyncio.gather(
        *retrieve_events_service_webhooks_tasks
    )
    return [
        _parse_webhook_public(webhook, events_service_webhook)
        for webhook, events_service_webhook in zip(db_webhooks, events_service_webhooks)
    ]


async def get_webhook_by_ids(
    webhook_id: uuid.UUID, user_id: uuid.UUID
) -> WebhookPublicPublic | None:
    if (webhook := await Webhook.get_by_ids(webhook_id, user_id)) is not None:
        events_service_webhook = await get_events_service_client().get_webhook(
            webhook.external_webhook_id
        )
        return _parse_webhook_public(webhook, events_service_webhook)
    return None


async def delete_webhook_by_id(webhook_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    stored_webhook = await Webhook.get_by_ids(webhook_id, user_id)
    if not stored_webhook:
        return False

    await get_events_service_client().delete_webhook(stored_webhook.external_webhook_id)
    return await Webhook.delete_by_ids(webhook_id, user_id)
