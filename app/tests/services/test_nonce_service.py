import unittest
from unittest import mock
from unittest.mock import MagicMock

from ...cache import get_redis
from ...services.nonce_service import generate_nonce


class TestNonceService(unittest.TestCase):
    @mock.patch("siwe.generate_nonce")
    @mock.patch("redis.Redis.from_url")
    def test_generate_nonce(
        self, mock_redis_from_url: MagicMock, mock_generate_nonce: MagicMock
    ):
        mock_generate_nonce.return_value = "test_nonce"
        mock_redis_instance = mock_redis_from_url.return_value
        get_redis.cache_clear()

        with mock.patch("app.config.settings.NONCE_TTL_SECONDS", 60):
            nonce = generate_nonce()

        self.assertEqual(nonce, "test_nonce")
        mock_redis_instance.set.assert_called_once_with(
            "test_nonce", "test_nonce", ex=60
        )
