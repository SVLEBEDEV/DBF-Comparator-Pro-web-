from fastapi.testclient import TestClient

from app.main import app


def test_ready_endpoint_skips_redis_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.health.settings.enable_redis_checks", False)
    monkeypatch.setattr("app.api.v1.health.check_database", lambda db: {"status": "ok"})
    monkeypatch.setattr("app.api.v1.health.check_storage", lambda root: {"status": "ok"})

    def fail_if_called(_: str) -> dict[str, str]:
        raise AssertionError("redis check should be skipped")

    monkeypatch.setattr("app.api.v1.health.check_redis", fail_if_called)

    client = TestClient(app)
    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "database": {"status": "ok"},
            "storage": {"status": "ok"},
        },
    }
