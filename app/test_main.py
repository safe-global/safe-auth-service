from fastapi.testclient import TestClient

from .main import app
from .version import VERSION

client = TestClient(app)


def test_home():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.has_redirect_location is True
    assert response.headers["location"] == "/docs"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == "OK"


def test_view_about():
    response = client.get("/v1/about")
    assert response.status_code == 200
    assert response.json() == {"version": VERSION}
