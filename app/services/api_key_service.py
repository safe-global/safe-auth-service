import datetime
import logging
import uuid

from app.datasources.db.models import ApiKey
from app.models.api_key import ApiKeyPublic


async def generate_api_key(user_id: uuid.UUID) -> ApiKeyPublic:
    """
    Generate and store in database a new api key for a given user.
    Each api_key for user will be unique.

    Args:
        user_id: unique user identifier.

    Returns: serialized ApiKeyPublic object.

    """
    api_key_id = uuid.uuid4().hex
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {"key": f"{user_id}_{api_key_id}", "created_at": now}
    logging.info(f"payload: {user_id}_{api_key_id}")
    # TODO call JwtIssuer for authservice
    token = f"Mocked token {user_id}_{api_key_id}"
    api_key = ApiKey(id=api_key_id, user_id=user_id, token=token, created_at=now)
    logging.info(f"Generated new api key {api_key.id}")
    await api_key.create()
    return ApiKeyPublic.model_validate(api_key)


async def delete_api_key_by_id(api_key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """
    Delete an existing api key.

    Args:
        api_key_id:
        user_id:

    Returns:

    """
    return await ApiKey.delete_by_ids(api_key_id, user_id)


async def get_api_key_by_ids(api_key_id: uuid.UUID, user_id: uuid.UUID) -> ApiKeyPublic:
    api_key = await ApiKey.get_by_ids(api_key_id, user_id)
    logging.info(f"ApiKey: {api_key}")
    return ApiKeyPublic.model_validate(api_key)
