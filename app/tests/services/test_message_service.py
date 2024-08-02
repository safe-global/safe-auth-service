import unittest
from unittest import mock
from unittest.mock import MagicMock

from siwe.siwe import SiweMessage, VersionEnum

from ...config import settings
from ...services.message_service import create_siwe_message


class TestSiweMessageService(unittest.TestCase):
    @mock.patch("redis.Redis.from_url")
    @mock.patch("siwe.generate_nonce")
    def test_create_siwe_message(
        self, mock_generate_nonce: MagicMock, mock_redis_from_url: MagicMock
    ):
        test_domain = "example.com"
        test_address = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        test_chain_id = 1
        test_uri = "https://example.com"
        test_statement = "Test statement"
        test_nonce = "testnonce1234"

        mock_generate_nonce.return_value = test_nonce
        with mock.patch("app.config.settings.NONCE_TTL_SECONDS", 100):
            message_str = create_siwe_message(
                domain=test_domain,
                address=test_address,
                chain_id=test_chain_id,
                uri=test_uri,
                statement=test_statement,
            )

        mock_generate_nonce.assert_called_once()

        siwe_message = SiweMessage.from_message(message_str)
        issued_at = siwe_message.issued_at
        valid_until = siwe_message.expiration_time

        expected_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=test_statement,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            valid_until=valid_until,
        )

        self.assertEqual(message_str, expected_message.prepare_message())

    @mock.patch("redis.Redis.from_url")
    @mock.patch("siwe.generate_nonce")
    def test_create_siwe_message_without_statement(
        self, mock_generate_nonce: MagicMock, mock_redis_from_url: MagicMock
    ):
        test_domain = "example.com"
        test_address = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        test_chain_id = 1
        test_uri = "https://example.com"
        test_nonce = "testnonce1234"

        mock_generate_nonce.return_value = test_nonce
        with mock.patch("app.config.settings.NONCE_TTL_SECONDS", 100):
            message_str = create_siwe_message(
                domain=test_domain,
                address=test_address,
                chain_id=test_chain_id,
                uri=test_uri,
            )

        mock_generate_nonce.assert_called_once()

        siwe_message = SiweMessage.from_message(message_str)
        issued_at = siwe_message.issued_at
        valid_until = siwe_message.expiration_time

        expected_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=settings.DEFAULT_SIWE_MESSAGE_STATEMENT,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            valid_until=valid_until,
        )

        self.assertEqual(message_str, expected_message.prepare_message())
