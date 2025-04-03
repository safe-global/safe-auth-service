import unittest
from datetime import UTC, datetime, timedelta
from unittest import mock

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from freezegun import freeze_time

from app.config import settings
from app.models.siwe_auth import SiweMessageInfo
from app.services.jwt_service import create_jwt_token


class TestJWTService(unittest.TestCase):

    @freeze_time("2024-01-01 01:00:0", tz_offset=0)
    def test_create_jwt_token(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_key_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )

        test_address = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        test_chain_id = 1
        siwe_message_info = SiweMessageInfo(
            chain_id=test_chain_id, signer_address=test_address
        )

        with mock.patch("app.config.settings.JWT_EXPIRATION_SECONDS", 60), mock.patch(
            "app.config.settings.JWT_PRIVATE_KEY", private_key_pem
        ):
            jwt_token = create_jwt_token(siwe_message_info)

            decoded_jwt_token = jwt.decode(
                jwt_token, public_key_pem, algorithms=["RS256"]
            )
            self.assertEqual(decoded_jwt_token.get("chain_id"), test_chain_id)
            self.assertEqual(decoded_jwt_token.get("signer_address"), test_address)
            self.assertEqual(decoded_jwt_token.get("iss"), settings.JWT_ISSUER)
            self.assertEqual(
                decoded_jwt_token.get("exp"),
                (
                    datetime.now(UTC)
                    + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
                ).timestamp(),
            )
