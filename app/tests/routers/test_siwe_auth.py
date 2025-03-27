import re
import unittest
from unittest import mock

import pytest
from fastapi.testclient import TestClient

import siwe
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from eth_account import Account
from eth_account.messages import encode_defunct
from safe_eth.util.util import to_0x_hex_str

from ...main import app


@pytest.mark.skip(reason="Currently not using SIWE auth")
class TestSiweAuth(unittest.TestCase):
    client: TestClient

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_view_get_nonce(self):
        response = self.client.get("/api/v1/auth/nonce")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.fullmatch(r"^[A-Za-z0-9]{8,}$", response.json().get("nonce"))
        )

    def test_view_request_siwe_message(self):
        test_domain = "example.com"
        test_address = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        test_chain_id = 1
        test_uri = "https://example.com/"
        test_statement = "Test statement"

        payload = {
            "domain": test_domain,
            "address": test_address,
            "chain_id": test_chain_id,
            "uri": test_uri,
            "statement": test_statement,
        }

        response = self.client.post("/api/v1/auth/messages", json=payload)

        self.assertEqual(response.status_code, 200)
        obtained_siwe_message = siwe.SiweMessage.from_message(
            response.json().get("message")
        )
        self.assertEqual(obtained_siwe_message.domain, test_domain)
        self.assertEqual(obtained_siwe_message.address, test_address)
        self.assertEqual(obtained_siwe_message.chain_id, test_chain_id)
        self.assertEqual(obtained_siwe_message.uri, test_uri)
        self.assertEqual(obtained_siwe_message.statement, test_statement)
        self.assertTrue(re.fullmatch(r"^[A-Za-z0-9]{8,}$", obtained_siwe_message.nonce))

    def test_view_request_auth_token(self):
        account = Account.create()
        test_domain = "example.com"
        test_address = account.address
        test_chain_id = 1
        test_uri = "https://example.com/"
        test_statement = "Test statement"

        payload_request = {
            "domain": test_domain,
            "address": test_address,
            "chain_id": test_chain_id,
            "uri": test_uri,
            "statement": test_statement,
        }

        response = self.client.post("/api/v1/auth/messages", json=payload_request)
        self.assertEqual(response.status_code, 200)
        obtained_siwe_message = response.json().get("message")

        private_key = to_0x_hex_str(account.key)
        eip191_message = encode_defunct(text=obtained_siwe_message)
        signed_message = Account.sign_message(eip191_message, private_key=private_key)
        signature = to_0x_hex_str(signed_message.signature)

        jwt_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        jwt_private_key_pem = jwt_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        with mock.patch("app.config.settings.JWT_PRIVATE_KEY", jwt_private_key_pem):

            # Valid
            payload_verify = {
                "signature": signature,
                "message": obtained_siwe_message,
            }

            response = self.client.post(
                "/api/v1/auth/messages/verify", json=payload_verify
            )
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.json().get("token"))

            # Error with reusing nonce
            payload_verify = {
                "signature": signature,
                "message": obtained_siwe_message,
            }

            response = self.client.post(
                "/api/v1/auth/messages/verify", json=payload_verify
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json().get("detail"),
                "The nonce provided in the SIWE message is invalid.",
            )

            # Invalid signature
            response = self.client.post("/api/v1/auth/messages", json=payload_request)
            self.assertEqual(response.status_code, 200)
            obtained_siwe_message = response.json().get("message")

            payload_verify = {
                "signature": "0x" + "a" * 130,
                "message": obtained_siwe_message,
            }

            response = self.client.post(
                "/api/v1/auth/messages/verify", json=payload_verify
            )
            self.assertEqual(response.status_code, 401)
            self.assertEqual(
                response.json().get("detail"), "The SIWE signature is invalid."
            )

            # Invalid message format
            payload_verify = {
                "signature": signature,
                "message": "fail_message",
            }

            response = self.client.post(
                "/api/v1/auth/messages/verify", json=payload_verify
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json().get("detail"), "The SIWE message format is invalid."
            )
