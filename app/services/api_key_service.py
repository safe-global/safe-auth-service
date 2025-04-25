import datetime
import uuid

from pydantic import TypeAdapter

from app.config import settings
from app.datasources.db.models import ApiKey
from app.models.api_key import ApiKeyPublic
from app.services.jwt_service import JwtService


async def generate_api_key(user_id: uuid.UUID, description: str) -> ApiKeyPublic:
    """
    Generate and store in database a new api key for a given user.
    Each api_key for user will contain a unique subject with user id and api key id concatenated.

    Args:
        user_id: unique user identifier.
        description: description of the api key.

    Returns: serialized ApiKeyPublic object.

    """
    api_key_id = uuid.uuid4()
    access_token_expires = datetime.timedelta(days=settings.JWT_API_KEY_EXPIRE_DAYS)
    subject = f"{user_id}_{api_key_id}"
    access_token = JwtService.create_access_token(
        subject, access_token_expires, settings.JWT_AUDIENCE, {}
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
