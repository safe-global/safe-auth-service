from fastapi import APIRouter

from ..models.google import RedirectUrl
from ..models.users import Token
from ..services.google_service import GoogleService
from ..services.user_service import UserService

router = APIRouter(
    prefix="/google",
    tags=["Google"],
)


@router.get(
    "/login",
)
async def start_google_login() -> RedirectUrl:
    google_service = GoogleService()
    return RedirectUrl(url=google_service.get_login_url())


@router.get(
    "/callback",
)
async def callback_google_login(code: str) -> Token:
    google_service = GoogleService()
    user_service = UserService()
    google_user = await google_service.get_user_info(code)
    token = await user_service.login_or_register(google_user.email)
    return token
