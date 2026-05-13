from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "algorithm"
    assert response.headers["X-Trace-Id"]


def test_internal_ping_requires_token() -> None:
    response = TestClient(app).get("/internal/ping")

    assert response.status_code == 401
