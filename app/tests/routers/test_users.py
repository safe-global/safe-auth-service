from unittest import mock

from fastapi.testclient import TestClient

import faker

from app.datasources.cache.redis import get_redis
from app.datasources.db.connector import db_session_context
from app.datasources.db.models import User
from app.main import app
from app.models.users import RegistrationUser

from ..datasources.db.async_db_test_case import AsyncDbTestCase

fake = faker.Faker()


class TestUsers(AsyncDbTestCase):
    client: TestClient

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        get_redis().flushall()

    def tearDown(self):
        get_redis().flushall()

    def get_example_registration_user(self) -> RegistrationUser:
        """
        Returns:
            The same example user so tests can be reused
        """
        token = "random-token"
        password = "random-password"
        email = "testing@safe.global"
        return RegistrationUser(token=token, password=password, email=email)

    def test_pre_register(self):
        user = self.get_example_registration_user()
        payload = {"email": user.email}

        with mock.patch(
            "app.routers.users.send_register_temporary_token_email"
        ) as send_register_temporary_token_email_mock:
            response = self.client.post("/api/v1/users/pre-registrations", json=payload)
            self.assertEqual(response.status_code, 200)
            send_register_temporary_token_email_mock.assert_called_once()

        # Token will not be sent again until TTL expires
        response = self.client.post("/api/v1/users/pre-registrations", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(), {"detail": f"Temporary token exists for {user.email}"}
        )

    @db_session_context
    async def test_register(self):
        user = self.get_example_registration_user()
        payload = {
            "token": user.token,
            "password": user.password,
            "email": user.email,
        }

        response = self.client.post("/api/v1/users/registrations", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(), {"detail": f"Temporary token not valid for {user.email}"}
        )

        count = await User.count()
        self.assertEqual(count, 0)

        with mock.patch(
            "app.routers.users.send_register_temporary_token_email"
        ) as send_register_temporary_token_email_mock:
            response = self.client.post("/api/v1/users/pre-registrations", json=payload)
            self.assertEqual(response.status_code, 200)
            send_register_temporary_token_email_mock.assert_called_once()
            payload["token"] = send_register_temporary_token_email_mock.mock_calls[
                0
            ].args[1]
            response = self.client.post("/api/v1/users/registrations", json=payload)
            self.assertEqual(response.status_code, 201)

            # Error, as user already exists
            response = self.client.post("/api/v1/users/registrations", json=payload)
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
            "password": user.password,
        }

        # User database is empty, it should not work
        response = self.client.post("/api/v1/users/login", data=payload)
        self.assertEqual(response.status_code, 401)

        await self.test_register()

        # Password is not valid
        payload_2 = {
            "username": user.email,
            "password": user.password + "not-valid",
        }
        response = self.client.post("/api/v1/users/login", data=payload_2)
        self.assertEqual(response.status_code, 401)

        response = self.client.post("/api/v1/users/login", data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertTrue(response.json()["access_token"])

        response = self.client.get(
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
            "old_password": user.password,
            "new_password": new_password,
        }
        response = self.client.post(
            "/api/v1/users/change-password",
            json=change_password_payload,
            headers={"Authorization": "Bearer " + fake.password()},
        )
        self.assertEqual(response.status_code, 401)

        login_payload = {
            "username": user.email,
            "password": user.password,
        }
        await self.test_register()
        response = self.client.post("/api/v1/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertTrue(response.json()["access_token"])
        access_token = response.json()["access_token"]

        response = self.client.post(
            "/api/v1/users/change-password",
            json=change_password_payload,
            headers={"Authorization": "Bearer " + access_token},
        )
        self.assertEqual(response.status_code, 204)

        # Should return 403 due password was changed
        response = self.client.post(
            "/api/v1/users/change-password",
            json=change_password_payload,
            headers={"Authorization": "Bearer " + access_token},
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post("/api/v1/users/login", data=login_payload)
        self.assertEqual(response.status_code, 401)

        login_payload["password"] = new_password
        response = self.client.post("/api/v1/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200)

    @db_session_context
    @mock.patch("app.services.user_service.send_reset_password_temporary_token_email")
    async def test_forgot_password(
        self, mock_send_reset_password_temporary_token_email: mock.MagicMock
    ):
        forgot_password_payload = {
            "email": fake.email(),
        }
        # Should not inform that email that not exist
        response = self.client.post(
            "/api/v1/users/forgot-password", json=forgot_password_payload
        )
        self.assertEqual(response.status_code, 204)
        mock_send_reset_password_temporary_token_email.assert_not_called()

        user = self.get_example_registration_user()
        await self.test_register()
        forgot_password_payload["email"] = user.email

        response = self.client.post(
            "/api/v1/users/forgot-password", json=forgot_password_payload
        )
        self.assertEqual(response.status_code, 204)
        mock_send_reset_password_temporary_token_email.assert_called_once()

        mock_send_reset_password_temporary_token_email.reset_mock()
        response = self.client.post(
            "/api/v1/users/forgot-password", json=forgot_password_payload
        )
        self.assertEqual(response.status_code, 409)
