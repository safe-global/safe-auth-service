from fastapi import APIRouter, HTTPException

from starlette import status

from ..models.google import RedirectUrl
from ..models.users import Token
from ..services.google_service import GoogleService
from ..services.user_service import UserService

router = APIRouter(
    prefix="/google",
    tags=["Google"],
)


google_auth_not_configured_exception = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Google Auth is not configured",
)


@router.get(
    "/login",
)
async def start_google_login() -> RedirectUrl:
    google_service = GoogleService()
    if not google_service.is_configured():
        raise google_auth_not_configured_exception
    return RedirectUrl(url=google_service.get_login_url())


@router.get(
    "/callback",
)
async def callback_google_login(code: str) -> Token:
    google_service = GoogleService()
    if not google_service.is_configured():
        raise google_auth_not_configured_exception
    user_service = UserService()
    google_user = await google_service.get_user_info(code)
    token = await user_service.login_or_register(google_user.email)
    return token
