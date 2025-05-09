import uuid
from unittest import mock

import faker
from httpx import ASGITransport, AsyncClient

from app.datasources.api_gateway.apisix.apisix_client import get_apisix_client
from app.datasources.cache.redis import get_redis
from app.datasources.db.connector import db_session_context
from app.datasources.db.models import User
from app.main import app
from app.models.users import RegistrationUser

from ...models.types import passwordType
from ..datasources.db.async_db_test_case import AsyncDbTestCase

fake = faker.Faker()


class TestUsers(AsyncDbTestCase):
    client: AsyncClient

    @classmethod
    def setUpClass(cls):
        cls.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )
        get_redis().flushall()
        get_apisix_client.cache_clear()

    def tearDown(self):
        get_redis().flushall()
        get_apisix_client.cache_clear()

    def get_example_registration_user(self) -> RegistrationUser:
        """
        Returns:
            The same example user so tests can be reused
        """
        token = "random-token"
        password = passwordType("random-password")
        email = "testing@safe.global"
        return RegistrationUser(token=token, password=password, email=email)

    async def test_pre_register(self):
        user = self.get_example_registration_user()
        payload = {"email": user.email}

        with mock.patch(
            "app.routers.users.send_register_temporary_token_email"
        ) as send_register_temporary_token_email_mock:
            response = await self.client.post(
                "/api/v1/users/pre-registrations", json=payload
            )
            self.assertEqual(response.status_code, 204)
            send_register_temporary_token_email_mock.assert_called_once()

        # Token will not be sent again until TTL expires
        response = await self.client.post(
            "/api/v1/users/pre-registrations", json=payload
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(), {"detail": f"Temporary token exists for {user.email}"}
        )

    @db_session_context
    async def test_register(self):
        user = self.get_example_registration_user()
        payload = {
            "token": user.token,
            "password": user.password.get_secret_value(),
            "email": user.email,
        }

        response = await self.client.post("/api/v1/users/registrations", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(), {"detail": f"Temporary token not valid for {user.email}"}
        )

        count = await User.count()
        self.assertEqual(count, 0)

        with mock.patch(
            "app.routers.users.send_register_temporary_token_email"
        ) as send_register_temporary_token_email_mock:
            response = await self.client.post(
                "/api/v1/users/pre-registrations", json=payload
            )
            self.assertEqual(response.status_code, 204)
            send_register_temporary_token_email_mock.assert_called_once()
            payload["token"] = send_register_temporary_token_email_mock.mock_calls[
                0
            ].args[1]
            response = await self.client.post(
                "/api/v1/users/registrations", json=payload
            )
            self.assertEqual(response.status_code, 201)

            # Error, as user already exists
            response = await self.client.post(
                "/api/v1/users/registrations", json=payload
            )
            self.assertEqual(response.status_code, 422)
            self.assertEqual(
                response.json(),
                {"detail": f"User with email {user.email} already exists"},
            )

        count = await User.count()
        self.assertEqual(count, 1)

    async def test_login(self):
        user = self.get_example_registration_user()

        payload = {
            "username": user.email,
            "password": user.password.get_secret_value(),
        }

        # User database is empty, it should not work
        response = await self.client.post("/api/v1/users/login", data=payload)
        self.assertEqual(response.status_code, 401)

        await self.test_register()

        # Password is not valid
        payload_2 = {
            "username": user.email,
            "password": user.password.get_secret_value() + "not-valid",
        }
        response = await self.client.post("/api/v1/users/login", data=payload_2)
        self.assertEqual(response.status_code, 401)

        response = await self.client.post("/api/v1/users/login", data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertTrue(response.json()["access_token"])

        response = await self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer " + response.json()["access_token"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["iss"], "safe-auth-service")
        self.assertTrue(response.json()["sub"])
        self.assertEqual(response.json()["aud"], ["safe-auth-service"])
        self.assertIsInstance(response.json()["exp"], int)
        self.assertEqual(response.json()["data"], {})

    @db_session_context
    async def test_change_password(self):
        user = self.get_example_registration_user()
        new_password = fake.password()
        change_password_payload = {
            "old_password": user.password.get_secret_value(),
            "new_password": new_password,
        }
        response = await self.client.post(
            "/api/v1/users/change-password",
            json=change_password_payload,
            headers={"Authorization": "Bearer " + fake.password()},
        )
        self.assertEqual(response.status_code, 401)

        login_payload = {
            "username": user.email,
            "password": user.password.get_secret_value(),
        }
        await self.test_register()
        response = await self.client.post("/api/v1/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertTrue(response.json()["access_token"])
        access_token = response.json()["access_token"]

        response = await self.client.post(
            "/api/v1/users/change-password",
            json=change_password_payload,
            headers={"Authorization": "Bearer " + access_token},
        )
        self.assertEqual(response.status_code, 204)

        # Should return 403 due password was changed
        response = await self.client.post(
            "/api/v1/users/change-password",
            json=change_password_payload,
            headers={"Authorization": "Bearer " + access_token},
        )
        self.assertEqual(response.status_code, 403)

        response = await self.client.post("/api/v1/users/login", data=login_payload)
        self.assertEqual(response.status_code, 401)

        login_payload["password"] = new_password
        response = await self.client.post("/api/v1/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200)

    @db_session_context
    @mock.patch("app.routers.users.send_reset_password_temporary_token_email")
    async def test_forgot_password(
        self, mock_send_reset_password_temporary_token_email: mock.MagicMock
    ):
        forgot_password_payload = {
            "email": fake.email(),
        }
        # With wrong emails, shouldn´t return error to avoid share information about users.
        response = await self.client.post(
            "/api/v1/users/forgot-password", json=forgot_password_payload
        )
        self.assertEqual(response.status_code, 204)
        mock_send_reset_password_temporary_token_email.assert_not_called()

        user = self.get_example_registration_user()
        await self.test_register()
        forgot_password_payload["email"] = user.email

        response = await self.client.post(
            "/api/v1/users/forgot-password", json=forgot_password_payload
        )
        self.assertEqual(response.status_code, 204)
        mock_send_reset_password_temporary_token_email.assert_called_once()

        mock_send_reset_password_temporary_token_email.reset_mock()
        response = await self.client.post(
            "/api/v1/users/forgot-password", json=forgot_password_payload
        )
        self.assertEqual(response.status_code, 409)

    @db_session_context
    @mock.patch("app.routers.users.send_reset_password_temporary_token_email")
    async def test_reset_password(
        self, mock_send_reset_password_temporary_token_email: mock.MagicMock
    ):
        user = self.get_example_registration_user()
        await self.test_register()
        forgot_password_payload = {
            "email": user.email,
        }

        response = await self.client.post(
            "/api/v1/users/forgot-password", json=forgot_password_payload
        )
        self.assertEqual(response.status_code, 204)
        mock_send_reset_password_temporary_token_email.assert_called_once()
        email, token = mock_send_reset_password_temporary_token_email.call_args[0]
        self.assertEqual(email, user.email)

        new_password = fake.password()
        reset_password_payload = {
            "email": fake.email(),
            "token": str(uuid.uuid4()),
            "new_password": new_password,
        }

        response = await self.client.post(
            "/api/v1/users/reset-password", json=reset_password_payload
        )
        self.assertEqual(response.status_code, 422)

        # Set the right token but keep a wrong email
        reset_password_payload["token"] = token
        response = await self.client.post(
            "/api/v1/users/reset-password", json=reset_password_payload
        )
        self.assertEqual(response.status_code, 422)

        # Email and token are right
        reset_password_payload["email"] = user.email
        response = await self.client.post(
            "/api/v1/users/reset-password", json=reset_password_payload
        )
        self.assertEqual(response.status_code, 204)

        login_payload = {
            "username": user.email,
            "password": new_password,
        }
        response = await self.client.post("/api/v1/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200)
