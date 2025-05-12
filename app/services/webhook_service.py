import uuid

from pydantic import TypeAdapter

from ..config import settings
from ..datasources.db.models import Webhook
from ..models.webhook import WebhookPublicPublic, WebhookRequest


class WebhookServiceException(Exception):
    pass


class WebhookCreationLimitReached(WebhookServiceException):
    pass


async def generate_webhook(
    user_id: uuid.UUID, webhook_request_info: WebhookRequest
) -> WebhookPublicPublic:
    user_webhooks = await Webhook.get_webhooks_by_user(user_id)
    if len(user_webhooks) >= settings.EVENTS_SERVICE_WEBHOOKS_CREATION_LIMIT:
        raise WebhookCreationLimitReached("Webhook creation limit reached")
    webhook_id = uuid.uuid4()

    # TODO: complete from service
    # external_webhook_id = await get_events_service_client().create_webhook()

    webhook = Webhook(
        id=webhook_id,
        user_id=user_id,
        description=webhook_request_info.description,
        external_webhook_id=None,
    )

    await webhook.create()
    return WebhookPublicPublic.model_validate(webhook)


async def update_webhook_by_ids(
    webhook_id: uuid.UUID, user_id: uuid.UUID, webhook_request_info: WebhookRequest
) -> bool:
    stored_webhook = await Webhook.get_by_ids(webhook_id, user_id)

    if not stored_webhook:
        return False

    # TODO: complete from service

    stored_webhook.description = webhook_request_info.description
    await stored_webhook.update()
    return True


async def get_webhooks_by_user(user_id: uuid.UUID) -> list["WebhookPublicPublic"]:
    adapter = TypeAdapter(list[WebhookPublicPublic])
    webhooks = await Webhook.get_webhooks_by_user(user_id)
    # TODO: complete from service
    return adapter.validate_python(webhooks)


async def get_webhook_by_ids(
    webhook_id: uuid.UUID, user_id: uuid.UUID
) -> WebhookPublicPublic | None:
    if (webhook := await Webhook.get_by_ids(webhook_id, user_id)) is not None:
        # TODO: complete from service
        return WebhookPublicPublic.model_validate(webhook)
    return None


async def delete_webhook_by_id(webhook_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    stored_webhook = await Webhook.get_by_ids(webhook_id, user_id)

    if not stored_webhook:
        return False

    # TODO: complete from service
    return await Webhook.delete_by_ids(webhook_id, user_id)
