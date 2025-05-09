import uuid
from unittest import mock

import faker
from httpx import ASGITransport, AsyncClient

from app.datasources.api_gateway.apisix.apisix_client import get_apisix_client
from app.datasources.db.connector import db_session_context
from app.main import app

from ...config import settings
from ...datasources.db.models import ApiKey
from ...services.api_key_service import generate_api_key
from ...services.user_service import UserService
from ..datasources.db.async_db_test_case import AsyncDbTestCase
from ..datasources.db.factory import generate_random_user

fake = faker.Faker()


class TestApiKeys(AsyncDbTestCase):
    client: AsyncClient

    @db_session_context
    async def asyncSetUp(self):
        await super().asyncSetUp()
        user_service = UserService()
        user, password = await self._generate_random_user_with_apisix_consumer_group()
        self.user = user
        self.token = await user_service.login_user(user.email, password)
        self.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )

    def setUp(self):
        get_apisix_client.cache_clear()

    def tearDown(self):
        get_apisix_client.cache_clear()

    async def _generate_random_user_with_apisix_consumer_group(self):
        user, password = await generate_random_user()
        await get_apisix_client().add_consumer_group(user.id.hex)
        return user, password

    @db_session_context
    async def test_create_api_key(self):
        response = await self.client.post("/api/v1/api-keys")
        self.assertEqual(response.status_code, 401)
        response = await self.client.post(
            "/api/v1/api-keys",
            headers={"Authorization": "Bearer " + self.token.access_token},
            json={"description": "Api key for testing"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.json().get("id"))
        self.assertIsNotNone(response.json().get("key"))
        self.assertIsNotNone(response.json().get("created"))
        self.assertIsNotNone(response.json().get("description"))

        with mock.patch.object(
            settings, "APISIX_FREEMIUM_CONSUMER_GROUP_API_KEY_CREATION_LIMIT", 1
        ):
            response = await self.client.post(
                "/api/v1/api-keys",
                headers={"Authorization": "Bearer " + self.token.access_token},
                json={"description": "Api key for testing"},
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.json(), {"detail": "Api key creation limit reached"}
            )

    @db_session_context
    async def test_get_api_key(self):
        random_uuid = uuid.uuid4()
        response = await self.client.get(f"/api/v1/api-keys/{str(random_uuid)}")
        self.assertEqual(response.status_code, 401)

        response = await self.client.get(
            f"/api/v1/api-keys/{str(random_uuid)}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 404)

        api_keys = await ApiKey.get_api_keys_by_user(self.user.id)
        self.assertEqual(len(api_keys), 0)
        await self.test_create_api_key()
        api_keys = await ApiKey.get_api_keys_by_user(self.user.id)
        self.assertEqual(len(api_keys), 1)

        api_key = api_keys[0]
        response = await self.client.get(
            f"/api/v1/api-keys/{str(api_key.id)}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("id"), str(api_key.id))
        self.assertEqual(response.json().get("key"), api_key.key)
        self.assertEqual(
            response.json().get("created"),
            api_key.created.isoformat().replace("+00:00", "Z"),
        )
        self.assertEqual(response.json().get("description"), api_key.description)

        # Can´t get api keys from other user
        user, _ = await self._generate_random_user_with_apisix_consumer_group()
        other_api_key = await generate_api_key(
            user.id, description="Api key for testing"
        )

        response = await self.client.get(
            f"/api/v1/api-keys/{str(other_api_key.id)}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 404)

    @db_session_context
    async def test_get_api_keys(self):
        random_uuid = uuid.uuid4()
        response = await self.client.get("/api/v1/api-keys")
        self.assertEqual(response.status_code, 401)

        response = await self.client.get(
            "/api/v1/api-keys",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        api_keys = await ApiKey.get_api_keys_by_user(self.user.id)
        self.assertEqual(len(api_keys), 0)
        await self.test_create_api_key()
        api_keys = await ApiKey.get_api_keys_by_user(self.user.id)
        self.assertEqual(len(api_keys), 1)

        api_key = api_keys[0]
        response = await self.client.get(
            "/api/v1/api-keys",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        result = response.json()[0]
        self.assertEqual(result.get("id"), str(api_key.id))
        self.assertEqual(result.get("key"), api_key.key)
        self.assertEqual(
            result.get("created"), api_key.created.isoformat().replace("+00:00", "Z")
        )
        self.assertEqual(result.get("description"), api_key.description)

    @db_session_context
    async def test_delete_api_key(self):
        random_uuid = uuid.uuid4()
        response = await self.client.delete(f"/api/v1/api-keys/{str(random_uuid)}")
        self.assertEqual(response.status_code, 401)

        response = await self.client.delete(
            f"/api/v1/api-keys/{str(random_uuid)}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 404)

        api_keys = await ApiKey.get_api_keys_by_user(self.user.id)
        self.assertEqual(len(api_keys), 0)
        await self.test_create_api_key()
        api_keys = await ApiKey.get_api_keys_by_user(self.user.id)
        self.assertEqual(len(api_keys), 1)

        api_key = api_keys[0]
        response = await self.client.get(
            f"/api/v1/api-keys/{str(api_key.id)}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 200)

        response = await self.client.delete(
            f"/api/v1/api-keys/{str(api_key.id)}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 204)
        api_keys = await ApiKey.get_api_keys_by_user(self.user.id)
        self.assertEqual(len(api_keys), 0)

        # Can´t delete api keys from other user
        user, _ = await self._generate_random_user_with_apisix_consumer_group()
        other_api_key = await generate_api_key(
            user.id, description="Api key for testing"
        )

        response = await self.client.delete(
            f"/api/v1/api-keys/{str(other_api_key.id)}",
            headers={"Authorization": "Bearer " + self.token.access_token},
        )
        self.assertEqual(response.status_code, 404)
