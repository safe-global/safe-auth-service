from urllib.parse import urlencode

from fastapi import HTTPException

import aiohttp
from starlette import status

from ..config import settings
from ..models.google import GoogleUser


class GoogleService:
    def is_configured(self) -> bool:
        return bool(settings.GOOGLE_CLIENT_ID) and bool(settings.GOOGLE_CLIENT_SECRET)

    def get_login_url(self) -> str:
        authorization_url = settings.GOOGLE_AUTHORIZATION_URL
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid profile email",
            "access_type": "offline",
        }
        redirect_url = f"{authorization_url}?{urlencode(params)}"
        return redirect_url

    async def get_user_info(self, code: str) -> GoogleUser:
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
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Empty access token",
                    )
            async with session.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            ) as response:
                return GoogleUser.model_validate_json(await response.text())
