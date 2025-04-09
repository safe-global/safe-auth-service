import uuid

from fastapi import APIRouter, HTTPException

from starlette import status

from ..services.api_key_service import (
    delete_api_key_by_id,
    generate_api_key,
    get_api_key_by_ids,
)

router = APIRouter(
    prefix="/api-keys",
    tags=["ApiKeys"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key():
    """
    Create a new api key for the authenticated user.

    Returns:

    """
    user_id = uuid.UUID("96bacde3-df6a-41ef-99ee-90aaacceed63")
    return await generate_api_key(user_id)


@router.get("/{api_key_id}")
async def get_api_key(api_key_id: uuid.UUID):
    """
    Get an existing api key for the authenticated user.

    Args:
        api_key_id:

    Returns:

    """
    user_id = uuid.UUID("96bacde3-df6a-41ef-99ee-90aaacceed63")
    if (api_key := await get_api_key_by_ids(api_key_id, user_id)) is None:
        raise HTTPException(status_code=404)
    return api_key


@router.get("/")
async def get_api_keys():
    """
    Get all existing api keys for the authenticated user.

    Returns:

    """
    return []


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_api_key(api_key_id: uuid.UUID):
    """
    Delete an existing api key for the authenticated user.

    Args:
        api_key_id:

    """
    user_id = uuid.UUID("96bacde3-df6a-41ef-99ee-90aaacceed63")
    if get_api_key_by_ids(api_key_id, user_id) is None:
        raise HTTPException(status_code=404)
    if await delete_api_key_by_id(api_key_id, user_id) is True:
        return None
