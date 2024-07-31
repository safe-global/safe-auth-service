import unittest

from fastapi.testclient import TestClient

from app.main import app


class TestRouterDefault(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_view_home(self):
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertTrue(response.has_redirect_location)
        self.assertEqual(response.headers["location"], "/docs")

    def test_view_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "OK")
        assert response.json() == "OK"
