from fastapi import FastAPI

from starlette.requests import Request
from starlette.responses import JSONResponse

from ..services.api_key_service import ApiKeyCreationLimitReached
from ..services.user_service import (
    TemporaryTokenExists,
    TemporaryTokenNotValid,
    WrongPassword,
)
from .auth import UserFromJWTDoesNotExist


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(WrongPassword)
    async def wrong_password_exception_handler(request: Request, exc: WrongPassword):
        return JSONResponse(
            status_code=403,
            content={"message": "Wrong password"},
        )

    @app.exception_handler(UserFromJWTDoesNotExist)
    async def user_from_jwt_does_not_exist_exception_handler(
        request: Request, exc: UserFromJWTDoesNotExist
    ):
        return JSONResponse(
            status_code=500,
            content={"message": "User does not exist"},
        )

    @app.exception_handler(TemporaryTokenExists)
    async def temporary_token_exists_exception_handler(
        request: Request, exc: TemporaryTokenExists
    ):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc)},
        )

    @app.exception_handler(TemporaryTokenNotValid)
    async def temporary_token_is_not_valid_exception_handler(
        request: Request, exc: TemporaryTokenNotValid
    ):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ApiKeyCreationLimitReached)
    async def api_key_creation_limit_reached_exception_handler(
        request: Request, exc: ApiKeyCreationLimitReached
    ):
        return JSONResponse(
            status_code=403,
            content={"detail": str(exc)},
        )
