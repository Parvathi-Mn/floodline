from fastapi.testclient import TestClient

from app.main import app


def test_chat_page_is_served():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "Floodline" in response.text


def test_api_routes_still_work_with_static_mount():
    assert TestClient(app).get("/health").json() == {"status": "ok"}