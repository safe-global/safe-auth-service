import datetime
import unittest

from fastapi import HTTPException

from app.config import settings
from app.routers.auth import get_user_from_jwt_token
from app.services.jwt_service import JwtService


class TestAuth(unittest.IsolatedAsyncioTestCase):

    async def test_valid_token(self):
        token = JwtService().create_access_token(
            "user123", datetime.timedelta(minutes=5), settings.JWT_AUDIENCE, {}
        )

        user = await get_user_from_jwt_token(token)
        self.assertEqual(user["sub"], "user123")

    async def test_invalid_token(self):
        invalid_token = "invalid.token.value"

        with self.assertRaises(HTTPException) as context:
            await get_user_from_jwt_token(invalid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Could not decode credentials")

    async def test_expired_token(self):
        token = JwtService().create_access_token(
            "user123", datetime.timedelta(minutes=-1), settings.JWT_AUDIENCE, {}
        )

        with self.assertRaises(HTTPException) as context:
            await get_user_from_jwt_token(token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "The provided JWT token has expired")
