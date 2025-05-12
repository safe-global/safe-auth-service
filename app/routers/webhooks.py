import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from starlette import status

from ..models.webhook import WebhookPublicPublic, WebhookRequest
from ..services.webhook_service import (
    delete_webhook_by_id,
    generate_webhook,
    get_webhook_by_ids,
    get_webhooks_by_user,
    update_webhook_by_ids,
)
from .auth import get_jwt_info_from_auth_token, get_user_id_from_jwt

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook(
    webhook_info: WebhookRequest,
    jwt_info: Annotated[dict, Depends(get_jwt_info_from_auth_token)],
):
    """
    Create a new webhook for the authenticated user.

    Args:
        webhook_info: webhook creation body

    Returns: the new webhook.

    """
    user_id = get_user_id_from_jwt(jwt_info)
    return await generate_webhook(
        user_id,
        webhook_info,
    )


@router.put("/{webhook_id}", response_model=WebhookPublicPublic)
async def update_webhook(
    webhook_id: uuid.UUID,
    webhook_info: WebhookRequest,
    jwt_info: Annotated[dict, Depends(get_jwt_info_from_auth_token)],
):
    """
    Update a webhook.

    Args:
        webhook_id: webhook id
        webhook_info: webhook update body

    Returns: the updated webhook.

    """
    user_id = get_user_id_from_jwt(jwt_info)
    if await update_webhook_by_ids(user_id, webhook_id, webhook_info) is False:
        raise HTTPException(status_code=404)

    return None  # No content response


@router.get("/{webhook_id}", response_model=WebhookPublicPublic)
async def get_webhook(
    webhook_id: uuid.UUID,
    jwt_info: Annotated[dict, Depends(get_jwt_info_from_auth_token)],
):
    """
    Get an existing webhook for the authenticated user.

    Args:
        webhook_id:

    Returns: the existing webhook.

    """
    user_id = get_user_id_from_jwt(jwt_info)
    if (webhook := await get_webhook_by_ids(webhook_id, user_id)) is None:
        raise HTTPException(status_code=404)
    return webhook


@router.get("", response_model=list[WebhookPublicPublic])
async def get_webhooks(
    jwt_info: Annotated[dict, Depends(get_jwt_info_from_auth_token)],
):
    """
    Get all existing webhooks for the authenticated user.

    Returns: list with the existing webhooks.

    """
    user_id = get_user_id_from_jwt(jwt_info)
    return get_webhooks_by_user(user_id)


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_webhook(
    webhook_id: uuid.UUID,
    jwt_info: Annotated[dict, Depends(get_jwt_info_from_auth_token)],
):
    """
    Delete an existing webhook for the authenticated user.

    Args:
        webhook_id:

    """
    user_id = get_user_id_from_jwt(jwt_info)
    if await delete_webhook_by_id(webhook_id, user_id) is False:
        raise HTTPException(status_code=404)

    return None  # No content response
