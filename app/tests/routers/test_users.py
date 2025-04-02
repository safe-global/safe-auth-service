from unittest import mock

from fastapi.testclient import TestClient

from sqlalchemy import func, select

from app.datasources.cache.redis import get_redis
from app.main import app

from ...datasources.db.connector import db_session, db_session_context
from ...datasources.db.models import Users
from ...datasources.email.email_provider import EmailProvider
from ..datasources.db.async_db_test_case import AsyncDbTestCase


class TestUsers(AsyncDbTestCase):
    client: TestClient

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        get_redis().flushall()

    def tearDown(self):
        get_redis().flushall()

    def test_pre_register(self):
        email = "testing@safe.global"
        payload = {"email": email}

        with mock.patch.object(
            EmailProvider, "send_temporary_token_email"
        ) as send_temporary_token_email_mock:
            response = self.client.post("/api/v1/users/pre-registrations", json=payload)
            self.assertEqual(response.status_code, 200)
            send_temporary_token_email_mock.assert_called_once()

        # Token will not be sent again until TTL expires
        response = self.client.post("/api/v1/users/pre-registrations", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(), {"detail": f"Temporary token exists for {email}"}
        )

    @db_session_context
    async def test_register(self):
        token = "random-token"
        password = "random-password"
        email = "testing@safe.global"

        payload = {
            "token": token,
            "password": password,
            "email": email,
        }

        response = self.client.post("/api/v1/users/registrations", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(), {"detail": f"Temporary token not valid for {email}"}
        )

        count = await db_session.execute(select(func.count(Users.id)))
        self.assertEqual(count.one()[0], 0)

        with mock.patch.object(
            EmailProvider, "send_temporary_token_email"
        ) as send_temporary_token_email_mock:
            response = self.client.post("/api/v1/users/pre-registrations", json=payload)
            self.assertEqual(response.status_code, 200)
            send_temporary_token_email_mock.assert_called_once()
            payload["token"] = send_temporary_token_email_mock.mock_calls[0].args[1]
            response = self.client.post("/api/v1/users/registrations", json=payload)
            self.assertEqual(response.status_code, 200)

        count = await db_session.execute(select(func.count(Users.id)))
        self.assertEqual(count.one()[0], 1)
