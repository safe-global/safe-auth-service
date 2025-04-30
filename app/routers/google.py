from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException

import aiohttp
from starlette import status

from ..config import settings
from ..models.google import RedirectUrl

router = APIRouter(
    prefix="/google",
    tags=["Google"],
)


@router.get(
    "/login",
)
async def start_google_login() -> RedirectUrl:
    authorization_url = settings.GOOGLE_AUTHORIZATION_URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email",
        "access_type": "offline",
    }
    redirect_url = f"{authorization_url}?{urlencode(params)}"
    return RedirectUrl(url=redirect_url)


@router.get(
    "/callback",
)
async def callback_google_login(code: str) -> dict:
    token_url = settings.GOOGLE_TOKEN_URL
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, json=data) as response:
            response_json = await response.json()
            access_token = response_json.get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Empty access token"
                )
            # TODO Maybe check access token is correctly signed by google
        async with session.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as response:
            # TODO Register and login user if it's not registered, otherwise just login
            return await response.json()
