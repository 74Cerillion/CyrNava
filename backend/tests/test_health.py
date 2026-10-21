def test_health_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_route_surface(client):
    assert [(route.path, route.methods) for route in client.app.routes] == [
        ("/health", {"GET"}),
        ("/api/notes", {"POST"}),
        ("/api/notes/{note_id}", {"GET"}),
        ("/api/notes/{note_id}", {"PATCH"}),
    ]
    assert client.get("/docs").status_code == 404
    assert client.post("/health").status_code == 405
