import unittest
from datetime import UTC, datetime, timedelta
from unittest import mock
from unittest.mock import MagicMock

from eth_account import Account
from eth_account.messages import encode_defunct
from siwe.siwe import ISO8601Datetime, SiweMessage, VersionEnum

from ...cache import get_redis
from ...config import settings
from ...exceptions import (
    InvalidMessageFormatError,
    InvalidNonceError,
    InvalidSignatureError,
)
from ...models import SiweMessageInfo
from ...services.message_service import (
    create_siwe_message,
    get_siwe_message_info,
    verify_siwe_message,
)
from ...services.nonce_service import CACHE_NONCE_PREFIX


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
        expiration_time = siwe_message.expiration_time

        expected_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=test_statement,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            expiration_time=expiration_time,
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
        expiration_time = siwe_message.expiration_time

        expected_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=settings.DEFAULT_SIWE_MESSAGE_STATEMENT,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            expiration_time=expiration_time,
        )

        self.assertEqual(message_str, expected_message.prepare_message())

    @mock.patch("redis.Redis.from_url")
    def test_verify_siwe_message(self, mock_redis_from_url: MagicMock):
        mock_redis_instance = mock_redis_from_url.return_value
        get_redis.cache_clear()

        account = Account.create()

        test_domain = "example.com"
        test_address = account.address
        test_chain_id = 1
        test_uri = "https://example.com"
        test_statement = "Test statement"
        test_nonce = "testnonce1234"

        issued_at = ISO8601Datetime.from_datetime(datetime.now(UTC))
        expiration_time = ISO8601Datetime.from_datetime(
            datetime.now(UTC) + timedelta(seconds=settings.NONCE_TTL_SECONDS)
        )

        siwe_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=test_statement,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            expiration_time=expiration_time,
        )
        message_str = siwe_message.prepare_message()

        private_key = account.key.hex()
        eip191_message = encode_defunct(text=siwe_message.prepare_message())
        signed_message = Account.sign_message(eip191_message, private_key=private_key)
        signature = signed_message.signature.hex()

        # Valid message
        verify_siwe_message(message_str, signature)
        mock_redis_instance.delete.assert_called_once_with(
            CACHE_NONCE_PREFIX + test_nonce
        )

        # Invalid message format
        message_str = "Invalid SIWE message"

        private_key = account.key.hex()
        eip191_message = encode_defunct(text=siwe_message.prepare_message())
        signed_message = Account.sign_message(eip191_message, private_key=private_key)
        signature = signed_message.signature.hex()

        with self.assertRaises(InvalidMessageFormatError):
            verify_siwe_message(message_str, signature)

        # Invalid message nonce
        mock_redis_instance.exists.return_value = False
        siwe_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=test_statement,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            expiration_time=expiration_time,
        )
        message_str = siwe_message.prepare_message()

        private_key = account.key.hex()
        eip191_message = encode_defunct(text=siwe_message.prepare_message())
        signed_message = Account.sign_message(eip191_message, private_key=private_key)
        signature = signed_message.signature.hex()

        with self.assertRaises(InvalidNonceError):
            verify_siwe_message(message_str, signature)
        mock_redis_instance.exists.return_value = True

        # Invalid message signer
        siwe_message = SiweMessage(
            domain=test_domain,
            address="0x32Be343B94f860124dC4fEe278FDCBD38C102D88",
            statement=test_statement,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            expiration_time=expiration_time,
        )
        message_str = siwe_message.prepare_message()

        private_key = account.key.hex()
        eip191_message = encode_defunct(text=siwe_message.prepare_message())
        signed_message = Account.sign_message(eip191_message, private_key=private_key)
        signature = signed_message.signature.hex()

        with self.assertRaises(InvalidSignatureError):
            verify_siwe_message(message_str, signature)

        # Invalid signature
        siwe_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=test_statement,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            expiration_time=expiration_time,
        )
        message_str = siwe_message.prepare_message()
        signature = "0x455aaa"

        with self.assertRaises(InvalidSignatureError):
            verify_siwe_message(message_str, signature)

    def test_get_siwe_message_info(self):
        test_domain = "example.com"
        test_address = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        test_chain_id = 1
        test_uri = "https://example.com"
        test_statement = "Test statement"
        test_nonce = "testnonce1234"

        issued_at = ISO8601Datetime.from_datetime(datetime.now(UTC))
        expiration_time = ISO8601Datetime.from_datetime(
            datetime.now(UTC) + timedelta(seconds=settings.NONCE_TTL_SECONDS)
        )

        siwe_message = SiweMessage(
            domain=test_domain,
            address=test_address,
            statement=test_statement,
            uri=test_uri,
            version=VersionEnum.one,
            chain_id=test_chain_id,
            nonce=test_nonce,
            issued_at=issued_at,
            expiration_time=expiration_time,
        )
        message_str = siwe_message.prepare_message()

        # Valid message
        expected_siwe_message_info = SiweMessageInfo(
            chain_id=test_chain_id, signer_address=test_address
        )
        self.assertEqual(get_siwe_message_info(message_str), expected_siwe_message_info)

        # Invalid message format
        message_str = "Invalid SIWE message"
        with self.assertRaises(InvalidMessageFormatError):
            get_siwe_message_info(message_str)
