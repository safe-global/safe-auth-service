import unittest
from unittest import mock
from unittest.mock import MagicMock

from ..siwe.nonce_repository import NonceRepository, get_nonce_repository


class TestNonceRepository(unittest.TestCase):
    @mock.patch("redis.Redis.from_url", autospec=True)
    def test_get_nonce_repository(self, mock_redis_from_url: MagicMock):
        mock_redis_client = mock_redis_from_url.return_value
        get_nonce_repository.cache_clear()
        with mock.patch("app.config.settings.REDIS_URL", "redis://localhost:port/0"):
            repository = get_nonce_repository()
        mock_redis_from_url.assert_called_once_with(
            "redis://localhost:port/0", decode_responses=True
        )
        self.assertIsInstance(repository, NonceRepository)
        self.assertEqual(repository.redis_client, mock_redis_client)

    @mock.patch("siwe.generate_nonce", return_value="test_nonce")
    @mock.patch("redis.Redis.from_url")
    def test_generate_nonce(
        self, mock_redis_from_url: MagicMock, mock_generate_nonce: MagicMock
    ):
        nonce_repository = NonceRepository(redis_client=mock_redis_from_url)

        with mock.patch("app.config.settings.NONCE_TTL_SECONDS", 100):
            nonce = nonce_repository.generate_nonce()

        mock_generate_nonce.assert_called_once()
        mock_redis_from_url.set.assert_called_once_with(
            "test_nonce", "test_nonce", ex=100
        )
        self.assertEqual(nonce, "test_nonce")
