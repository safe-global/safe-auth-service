from unittest import mock

from fastapi.testclient import TestClient

from app.main import app

from ...datasources.db.connector import db_session_context
from ...datasources.db.models import User
from ...services.google_service import GoogleService
from ..datasources.db.async_db_test_case import AsyncDbTestCase
from ..mocks.google import google_user


class TestGoogleRouter(AsyncDbTestCase):
    client: TestClient

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_start_google_login(self):
        response = self.client.get("/api/v1/google/login")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "Google Auth is not configured"})

        with mock.patch.object(GoogleService, "is_configured", return_value=True):
            response = self.client.get("/api/v1/google/login")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["url"])

    @db_session_context
    async def test_callback_google_login(self):
        response = self.client.get("/api/v1/google/callback?code=1234")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "Google Auth is not configured"})

        with mock.patch.object(GoogleService, "is_configured", return_value=True):
            with mock.patch.object(
                GoogleService, "get_user_info", return_value=google_user
            ):
                self.assertEqual(await User.count(), 0)
                response = self.client.get("/api/v1/google/callback?code=1234")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["access_token"])
                self.assertEqual(await User.count(), 1)

                response = self.client.get("/api/v1/google/callback?code=1234")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["access_token"])
                self.assertEqual(await User.count(), 1)
