import faker

from app.datasources.db.connector import db_session_context
from app.routers.auth import get_user_from_jwt_token

from ...datasources.db.models import ApiKey
from ...services.api_key_service import generate_api_key
from ..datasources.db.async_db_test_case import AsyncDbTestCase
from ..datasources.db.factory import generate_random_user

fake = faker.Faker()


class TestApiKeyService(AsyncDbTestCase):
    @db_session_context
    async def test_generate_api_key(self):
        user, _ = await generate_random_user()
        api_key = await generate_api_key(user.id)
        self.assertIsNotNone(api_key)
        stored_api_key = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertEqual(api_key.id, stored_api_key.id)
        self.assertEqual(api_key.created, stored_api_key.created)
        self.assertEqual(api_key.token, stored_api_key.token)

        # The subjects is generated correctly
        decoded_token = await get_user_from_jwt_token(api_key.token)
        self.assertEqual(f"{str(user.id)}_{str(api_key.id)}", decoded_token["sub"])
