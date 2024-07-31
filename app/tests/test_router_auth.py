import re
import unittest
from unittest import mock

from fastapi.testclient import TestClient

import siwe

from ..main import app


class TestRouterAuth(unittest.TestCase):
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

    @mock.patch("app.siwe.nonce_repository.NonceRepository.generate_nonce")
    def test_view_request_siwe_message(self, mock_generate_nonce):
        test_domain = "example.com"
        test_address = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        test_chain_id = 1
        test_uri = "https://example.com/"
        test_statement = "Test statement"
        test_nonce = "testnonce1234"

        mock_generate_nonce.return_value = test_nonce

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
        self.assertEqual(obtained_siwe_message.nonce, test_nonce)
