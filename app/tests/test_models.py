import unittest

from pydantic import ValidationError

from pydantic_core._pydantic_core import Url

from ..models import Nonce, SiweMessageRequest


class TestNonce(unittest.TestCase):
    def test_valid_nonce(self):
        valid_nonce_data = {"nonce": "abcd1234"}
        nonce_instance = Nonce(nonce=valid_nonce_data["nonce"])
        self.assertEqual(nonce_instance.nonce, valid_nonce_data["nonce"])

    def test_invalid_nonce_length(self):
        with self.assertRaises(ValidationError):
            Nonce(nonce="abc")

    def test_invalid_nonce_pattern(self):
        with self.assertRaises(ValidationError):
            Nonce(nonce="abcd-1234")


class TestSiweMessageRequest(unittest.TestCase):
    def test_valid_siwe_message_request(self):
        siwe_message_request = SiweMessageRequest(
            domain="example.com",
            address="0x32Be343B94f860124dC4fEe278FDCBD38C102D88",
            chain_id=1,
            uri=Url("https://example.com/"),
            statement="Test statement",
        )
        self.assertEqual(siwe_message_request.domain, "example.com")
        self.assertEqual(
            siwe_message_request.address, "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        )
        self.assertEqual(siwe_message_request.chain_id, 1)
        self.assertEqual(str(siwe_message_request.uri), "https://example.com/")
        self.assertEqual(siwe_message_request.statement, "Test statement")

    def test_invalid_domain(self):
        with self.assertRaises(ValidationError):
            SiweMessageRequest(
                domain="example.com/invalid",
                address="0x32Be343B94f860124dC4fEe278FDCBD38C102D88",
                chain_id=1,
                uri=Url("https://example.com"),
            )

    def test_invalid_address(self):
        with self.assertRaises(ValidationError):
            SiweMessageRequest(
                domain="example.com",
                address="0xInvalidEthereumAddress",
                chain_id=1,
                uri=Url("https://example.com"),
                statement="Test statement",
            )

    def test_invalid_uri(self):
        with self.assertRaises(ValidationError):
            SiweMessageRequest(
                domain="example.com",
                address="0x32Be343B94f860124dC4fEe278FDCBD38C102D88",
                chain_id=1,
                uri=Url("invalid-url"),
                statement="Test statement",
            )

    def test_optional_statement(self):
        siwe_message_request = SiweMessageRequest(
            domain="example.com",
            address="0x32Be343B94f860124dC4fEe278FDCBD38C102D88",
            chain_id=1,
            uri=Url("https://example.com"),
        )
        self.assertIsNone(siwe_message_request.statement)
