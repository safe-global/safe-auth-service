import datetime
import uuid

from pydantic import TypeAdapter

from ..config import settings
from ..datasources.api_gateway.apisix.apisix_client import get_apisix_client
from ..datasources.db.models import ApiKey
from ..models.api_key import ApiKeyPublic
from ..services.jwt_service import JwtService


class ApiKeyServiceException(Exception):
    pass


class ApiKeyCreationLimitReached(ApiKeyServiceException):
    pass


async def generate_api_key(user_id: uuid.UUID, description: str) -> ApiKeyPublic:
    """
    Generate and store in database a new api key for a given user.
    Each api_key for user will contain a unique subject with user id and api key id concatenated.

    Args:
        user_id: unique user identifier.
        description: description of the api key.

    Raises:
        ApiKeyCreationLimitReached: If the user has reached the maximum number of allowed API keys.

    Returns: serialized ApiKeyPublic object.

    """
    user_api_keys = await ApiKey.get_api_keys_by_user(user_id)
    if (
        len(user_api_keys)
        >= settings.APISIX_FREEMIUM_CONSUMER_GROUP_API_KEY_CREATION_LIMIT
    ):
        raise ApiKeyCreationLimitReached("Api key creation limit reached")

    api_key_id = uuid.uuid4()
    api_key_subject = f"{user_id.hex}_{api_key_id.hex}"
    await get_apisix_client().upsert_consumer(
        api_key_subject,
        description=description,
        consumer_group_name=settings.APISIX_FREEMIUM_CONSUMER_GROUP_NAME,
    )
    access_token_expires = datetime.timedelta(days=settings.JWT_API_KEY_EXPIRE_DAYS)
    access_token = JwtService.create_access_token(
        api_key_subject, access_token_expires, settings.JWT_AUDIENCE, {}
    )
    api_key = ApiKey(
        id=api_key_id, user_id=user_id, token=access_token, description=description
    )
    await api_key.create()
    return ApiKeyPublic.model_validate(api_key)


async def delete_api_key_by_id(api_key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """
    Delete an existing api key.

    Args:
        api_key_id:
        user_id:

    Returns: True if the api key was deleted, False otherwise.

    """
    stored_api_key = await ApiKey.get_by_ids(api_key_id, user_id)

    if not stored_api_key:
        return False

    api_key_subject = f"{user_id.hex}_{api_key_id.hex}"
    await get_apisix_client().delete_consumer(api_key_subject)
    return await ApiKey.delete_by_ids(api_key_id, user_id)


async def get_api_key_by_ids(
    api_key_id: uuid.UUID, user_id: uuid.UUID
) -> ApiKeyPublic | None:
    """
    Get an existing api key by api key id.

    Args:
        api_key_id:
        user_id:

    Returns: ApiKeyPublic object.

    """
    if (api_key := await ApiKey.get_by_ids(api_key_id, user_id)) is not None:
        return ApiKeyPublic.model_validate(api_key)
    return None


async def get_api_keys_by_user(user_id: uuid.UUID) -> list["ApiKeyPublic"]:
    """
    Get all existing api keys for the authenticated user.

    Args:
        user_id:

    Returns: list with the existing api keys.

    """
    adapter = TypeAdapter(list[ApiKeyPublic])
    api_keys = await ApiKey.get_api_keys_by_user(user_id)
    return adapter.validate_python(api_keys)
