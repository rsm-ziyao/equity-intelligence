from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import health as health_routes

client = TestClient(app)


def test_health_check(monkeypatch):
    monkeypatch.setattr(health_routes, "check_db_connection", lambda: True)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "status": "healthy",
            "service": "equity-intelligence-api",
            "version": "0.1.0",
            "database": "healthy",
        },
        "meta": {},
    }
