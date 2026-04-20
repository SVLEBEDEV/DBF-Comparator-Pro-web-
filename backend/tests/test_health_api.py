from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_is_available() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_ready_endpoint_uses_runtime_checks(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.health.check_database", lambda db: {"status": "ok"})
    monkeypatch.setattr("app.api.v1.health.check_redis", lambda url: {"status": "ok"})
    monkeypatch.setattr("app.api.v1.health.check_storage", lambda root: {"status": "ok"})

    client = TestClient(app)
    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
