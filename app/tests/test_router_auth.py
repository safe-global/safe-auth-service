import re
import unittest

from fastapi.testclient import TestClient

from app.main import app


class TestRouterAuth(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_view_about(self):
        response = self.client.get("/api/v1/auth/nonce")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.fullmatch(r"^[A-Za-z0-9]{8,}$", response.json().get("nonce"))
        )
