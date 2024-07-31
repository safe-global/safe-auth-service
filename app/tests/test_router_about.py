import unittest

from fastapi.testclient import TestClient

from app import VERSION
from app.main import app


class TestRouterAbout(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_view_about(self):
        response = self.client.get("/api/v1/about")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": VERSION})
