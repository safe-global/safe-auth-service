from fastapi import FastAPI

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.user_service import WrongPassword


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(WrongPassword)
    async def wrong_password_exception_handler(request: Request, exc: WrongPassword):
        return JSONResponse(
            status_code=403,
            content={"message": "Wrong password"},
        )
