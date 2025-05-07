import uuid
from unittest.mock import patch

import faker

from app.datasources.api_gateway.apisix.apisix_client import get_apisix_client
from app.datasources.db.connector import db_session_context
from app.routers.auth import get_jwt_info_from_auth_token

from ...datasources.api_gateway.exceptions import ApiGatewayRequestError
from ...datasources.db.models import ApiKey
from ...models.api_key import ApiKeyPublic
from ...services.api_key_service import (
    delete_api_key_by_id,
    generate_api_key,
    get_api_key_by_ids,
    get_api_keys_by_user,
)
from ..datasources.db.async_db_test_case import AsyncDbTestCase
from ..datasources.db.factory import generate_random_api_key, generate_random_user

fake = faker.Faker()


class TestApiKeyService(AsyncDbTestCase):

    def setUp(self):
        get_apisix_client.cache_clear()

    def tearDown(self):
        get_apisix_client.cache_clear()

    @db_session_context
    async def test_generate_api_key(self):
        user, _ = await generate_random_user()
        freemium_consumer_group_name = "freemium_consumer_group"
        await get_apisix_client().add_consumer_group(freemium_consumer_group_name)
        with patch(
            "app.config.settings.APISIX_FREEMIUM_CONSUMER_GROUP_NAME",
            freemium_consumer_group_name,
        ):
            api_key = await generate_api_key(user.id, description="Api key for testing")
        self.assertIsNotNone(api_key)
        stored_api_key = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertEqual(api_key.id, stored_api_key.id)
        self.assertEqual(api_key.created, stored_api_key.created)
        self.assertEqual(api_key.token, stored_api_key.token)
        self.assertEqual(api_key.description, stored_api_key.description)

        api_key_subject = f"{user.id.hex}_{api_key.id.hex}"
        apisix_consumer = await get_apisix_client().get_consumer(api_key_subject)
        self.assertIsNotNone(apisix_consumer)
        self.assertEqual(
            apisix_consumer.consumer_group_name, freemium_consumer_group_name
        )

        # The subject and key are generated correctly.
        decoded_token = await get_jwt_info_from_auth_token(api_key.token)
        self.assertEqual(api_key_subject, decoded_token["sub"])
        self.assertEqual(api_key_subject, decoded_token["key"])

    @db_session_context
    async def test_delete_api_key_by_id(self):
        user, _ = await generate_random_user()
        result = await delete_api_key_by_id(uuid.uuid4(), user.id)
        self.assertFalse(result)

        api_key = await generate_api_key(user.id, description="Api key for testing")
        stored_api_key = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertIsNotNone(stored_api_key)
        api_key_subject = f"{user.id.hex}_{api_key.id.hex}"
        apisix_consumer = await get_apisix_client().get_consumer(api_key_subject)
        self.assertIsNotNone(apisix_consumer)

        result = await delete_api_key_by_id(api_key.id, user.id)
        self.assertTrue(result)

        stored_api_key = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertIsNone(stored_api_key)
        with self.assertRaises(ApiGatewayRequestError):
            await get_apisix_client().get_consumer(api_key_subject)

    @db_session_context
    async def test_get_api_key_by_ids(self):
        user, _ = await generate_random_user()
        api_key_db = await generate_random_api_key(user.id)

        api_key_public = await get_api_key_by_ids(api_key_db.id, uuid.uuid4())
        self.assertIsNone(api_key_public)

        api_key_public = await get_api_key_by_ids(api_key_db.id, user.id)

        self.assertIsInstance(api_key_public, ApiKeyPublic)
        assert api_key_public is not None
        self.assertEqual(api_key_db.id, api_key_public.id)
        self.assertEqual(api_key_db.created, api_key_public.created)
        self.assertEqual(api_key_db.token, api_key_public.token)
        self.assertFalse(hasattr(api_key_public, "user_id"))
        self.assertEqual(api_key_db.description, api_key_public.description)

    @db_session_context
    async def test_get_api_keys_by_user(self):
        user, _ = await generate_random_user()

        self.assertEqual([], await get_api_keys_by_user(user.id))

        api_keys = [await generate_random_api_key(user.id) for _ in range(3)]

        results = await get_api_keys_by_user(user.id)

        self.assertIsInstance(results, list)
        self.assertEqual(3, len(results))

        for result, api_key in zip(results, api_keys):
            self.assertIsInstance(result, ApiKeyPublic)
            self.assertEqual(result.id, api_key.id)
            self.assertEqual(result.created, api_key.created)
            self.assertEqual(result.token, api_key.token)
            self.assertFalse(hasattr(result, "user_id"))
            self.assertEqual(result.description, api_key.description)
