from fastapi import FastAPI

from starlette.requests import Request
from starlette.responses import JSONResponse

from ..services.user_service import TemporaryTokenExists, WrongPassword
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
        request: Request, exc: UserFromJWTDoesNotExist
    ):
        return JSONResponse(
            status_code=409,
            content={"message": "Temporary token exists"},
        )
