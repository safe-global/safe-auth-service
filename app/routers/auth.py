from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from starlette import status

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")


async def get_user_from_jwt_token(
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
