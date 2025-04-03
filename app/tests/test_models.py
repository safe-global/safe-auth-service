import unittest

from pydantic import HttpUrl, ValidationError

from ..models.siwe_auth import Nonce, SiweMessageVerificationRequest
from .factories import SiweMessageRequestFactory


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
        siwe_message_request = SiweMessageRequestFactory.create()
        self.assertEqual(siwe_message_request.domain, "example.com")
        self.assertEqual(
            siwe_message_request.address, "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        )
        self.assertEqual(siwe_message_request.chain_id, 1)
        self.assertEqual(str(siwe_message_request.uri), "https://valid-url.com/")
        self.assertEqual(siwe_message_request.statement, "Test statement")

    def test_invalid_domain(self):
        with self.assertRaises(ValidationError):
            SiweMessageRequestFactory.create(domain="example.com/invalid")

    def test_invalid_address(self):
        with self.assertRaises(ValidationError):
            SiweMessageRequestFactory.create(address="0xInvalidEthereumAddress")

    def test_invalid_uri(self):
        with self.assertRaises(ValidationError):
            SiweMessageRequestFactory.create(uri=HttpUrl("invalid-url"))

    def test_optional_statement(self):
        siwe_message_request = SiweMessageRequestFactory.create(statement=None)
        self.assertIsNone(siwe_message_request.statement)


class TestSiweMessageVerificationRequest(unittest.TestCase):
    def test_valid_siwe_message_verification_request(self):
        siwe_message_verification_request = SiweMessageVerificationRequest(
            message="Test",
            signature="0x" + "a" * 130,
        )
        self.assertEqual(siwe_message_verification_request.message, "Test")
        self.assertEqual(siwe_message_verification_request.signature, "0x" + "a" * 130)

    def test_invalid_signature(self):
        with self.assertRaises(ValidationError):
            SiweMessageVerificationRequest(
                message="Test",
                signature="0xa",
            )

        with self.assertRaises(ValidationError):
            SiweMessageVerificationRequest(
                message="Test",
                signature="a" * 132,
            )
