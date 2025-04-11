import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from starlette import status

from ..services.api_key_service import (
    delete_api_key_by_id,
    generate_api_key,
    get_api_key_by_ids,
    get_api_keys_by_user,
)
from .auth import get_user_from_jwt_token

router = APIRouter(
    prefix="/api-keys",
    tags=["ApiKeys"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    current_user: Annotated[dict, Depends(get_user_from_jwt_token)],
):
    """
    Create a new api key for the authenticated user.

    Returns: the new api key.

    """
    user_id = current_user["sub"]
    return await generate_api_key(user_id)


@router.get("/{api_key_id}")
async def get_api_key(
    api_key_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_user_from_jwt_token)],
):
    """
    Get an existing api key for the authenticated user.

    Args:
        api_key_id:

    Returns: the existing api key.

    """
    user_id = current_user["sub"]
    if (api_key := await get_api_key_by_ids(api_key_id, user_id)) is None:
        raise HTTPException(status_code=404)
    return api_key


@router.get("/")
async def get_api_keys(current_user: Annotated[dict, Depends(get_user_from_jwt_token)]):
    """
    Get all existing api keys for the authenticated user.

    Returns: list with the existing api keys.

    """
    user_id = current_user["sub"]
    return await get_api_keys_by_user(user_id)


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_api_key(
    api_key_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_user_from_jwt_token)],
):
    """
    Delete an existing api key for the authenticated user.

    Args:
        api_key_id:

    """
    user_id = current_user["sub"]

    if await delete_api_key_by_id(api_key_id, user_id) is False:
        raise HTTPException(status_code=404)

    return None  # No content response
