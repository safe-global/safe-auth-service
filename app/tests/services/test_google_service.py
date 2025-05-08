from unittest import mock

import aiohttp
import faker

from ...config import settings
from ...services.google_service import GoogleService
from ..datasources.db.async_db_test_case import AsyncDbTestCase
from ..mocks.google import google_user

fake = faker.Faker()


class TestGoogleService(AsyncDbTestCase):

    def setUp(self):
        self.google_service = GoogleService()

    async def test_is_configured(self):
        self.assertFalse(self.google_service.is_configured())
        with mock.patch.object(settings, "GOOGLE_CLIENT_ID", "4815"):
            with mock.patch.object(settings, "GOOGLE_CLIENT_SECRET", "162342"):
                self.assertTrue(self.google_service.is_configured())

    async def test_get_login_url(self):
        self.assertIn(
            settings.GOOGLE_AUTHORIZATION_URL, self.google_service.get_login_url()
        )

    async def test_get_user_info(self):
        access_token = "RANDOM-TOKEN"
        code = "12345"

        context_post_mock = mock.AsyncMock()
        mock_post = mock.AsyncMock()
        mock_post.status.return_value = 200
        mock_post.json.return_value = {"access_token": access_token}
        context_post_mock.__aenter__.return_value = mock_post

        context_get_mock = mock.AsyncMock()
        mock_get = mock.AsyncMock()
        mock_get.status.return_value = 200
        mock_get.text.return_value = google_user.model_dump_json()
        context_get_mock.__aenter__.return_value = mock_get

        with mock.patch.object(
            aiohttp.ClientSession, "post", return_value=context_post_mock
        ):
            with mock.patch.object(
                aiohttp.ClientSession, "get", return_value=context_get_mock
            ):
                user_info = await self.google_service.get_user_info(code)
                self.assertEqual(user_info, google_user)
                mock_post.json.assert_called_once()
                mock_get.text.assert_called_once()
