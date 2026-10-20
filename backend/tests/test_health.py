from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_contract():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_no_other_routes():
    assert [route.path for route in app.routes] == ["/health"]
    assert client.get("/docs").status_code == 404
    assert client.post("/health").status_code == 405
