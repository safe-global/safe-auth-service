import uuid
from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from starlette import status

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")


async def get_jwt_info_from_user_token(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.JWT_PRIVATE_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
        )
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The provided JWT token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_user_id_from_jwt(jwt_info: dict) -> uuid.UUID:
    return jwt_info["sub"]
