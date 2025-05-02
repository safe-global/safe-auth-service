import datetime
import uuid

from fastapi import HTTPException

from app.config import settings
from app.datasources.db.connector import db_session_context
from app.routers.auth import (
    UserFromJWTDoesNotExist,
    get_jwt_info_from_auth_token,
    get_user_from_jwt,
)
from app.services.jwt_service import JwtService
from app.tests.datasources.db.async_db_test_case import AsyncDbTestCase
from app.tests.datasources.db.factory import generate_random_user


class TestAuth(AsyncDbTestCase):

    async def test_valid_token(self):
        token = JwtService().create_access_token(
            "user123", datetime.timedelta(minutes=5), settings.JWT_AUDIENCE, {}
        )

        user = await get_jwt_info_from_auth_token(token)
        self.assertEqual(user["sub"], "user123")
        self.assertEqual(user["key"], "user123")

    async def test_invalid_token(self):
        invalid_token = "invalid.token.value"

        with self.assertRaises(HTTPException) as context:
            await get_jwt_info_from_auth_token(invalid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Could not decode credentials")

    async def test_expired_token(self):
        token = JwtService().create_access_token(
            "user123", datetime.timedelta(minutes=-1), settings.JWT_AUDIENCE, {}
        )

        with self.assertRaises(HTTPException) as context:
            await get_jwt_info_from_auth_token(token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "The provided JWT token has expired")

    @db_session_context
    async def test_get_user_from_jwt(self):
        user_id = uuid.uuid4()
        token = JwtService().create_access_token(
            str(user_id), datetime.timedelta(minutes=5), settings.JWT_AUDIENCE, {}
        )
        jwt_info = await get_jwt_info_from_auth_token(token)
        with self.assertRaises(UserFromJWTDoesNotExist) as context:
            await get_user_from_jwt(jwt_info)

        user, password = await generate_random_user()
        token = JwtService().create_access_token(
            str(user.id), datetime.timedelta(minutes=5), settings.JWT_AUDIENCE, {}
        )
        jwt_info = await get_jwt_info_from_auth_token(token)
        self.assertEqual(jwt_info["sub"], str(user.id))
        self.assertEqual(user, await get_user_from_jwt(jwt_info))
