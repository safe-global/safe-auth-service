import uuid

import faker

from app.datasources.db.connector import db_session_context
from app.datasources.db.models import ApiKey

from .async_db_test_case import AsyncDbTestCase
from .factory import generate_random_api_key, generate_random_user

fake = faker.Faker()


class TestModel(AsyncDbTestCase):
    @db_session_context
    async def test_user(self):
        user, _ = await generate_random_user()
        await user.create()
        result = await user.get_all()
        self.assertEqual(result[0], user)

    @db_session_context
    async def test_api_key(self):
        user, _ = await generate_random_user()
        api_key = await generate_random_api_key(user.id)
        await api_key.create()
        result = await api_key.get_all()
        self.assertEqual(result[0], api_key)

    @db_session_context
    async def test_get_api_key_by_ids(self):
        user, _ = await generate_random_user()
        wrong_user, _ = await generate_random_user()
        api_key = await generate_random_api_key(user.id)
        api_key_other = await generate_random_api_key(user.id)

        result = await ApiKey.get_by_ids(api_key.id, wrong_user.id)
        self.assertIsNone(result)

        result = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertEqual(result, api_key)

        result = await ApiKey.get_by_ids(api_key_other.id, user.id)
        self.assertEqual(result, api_key_other)

    @db_session_context
    async def test_delete_api_key_by_ids(self):
        user, _ = await generate_random_user()
        api_key = await generate_random_api_key(user.id)
        api_key_other = await generate_random_api_key(user.id)

        result = await ApiKey.delete_by_ids(api_key.id, uuid.uuid4())
        self.assertFalse(result)

        result = await ApiKey.delete_by_ids(api_key.id, user.id)
        self.assertTrue(result)

        result = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertIsNone(result)

        result = await ApiKey.get_by_ids(api_key_other.id, user.id)
        self.assertEqual(result, api_key_other)

    @db_session_context
    async def test_get_api_keys_by_user(self):
        user, _ = await generate_random_user()

        result = await ApiKey.get_api_keys_by_user(user.id)
        self.assertEqual(result, [])

        api_keys = [await generate_random_api_key(user.id) for _ in range(5)]

        result = await ApiKey.get_api_keys_by_user(user.id)
        self.assertEqual(len(result), len(api_keys))
        self.assertEqual(result, api_keys)
