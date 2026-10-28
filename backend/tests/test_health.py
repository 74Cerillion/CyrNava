def test_health_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_route_surface(client):
    assert [(route.path, route.methods) for route in client.app.routes] == [
        ("/api/lifecycle", {"GET"}),
        ("/api/templates", {"GET"}),
        ("/api/templates", {"POST"}),
        ("/api/templates/{template_id}", {"PATCH"}),
        ("/api/templates/{template_id}", {"DELETE"}),
        ("/api/templates/{template_id}/notes", {"POST"}),
        ("/api/tree", {"GET"}),
        ("/api/folders", {"POST"}),
        ("/api/folders/{folder_id}", {"PATCH"}),
        ("/api/folders/{folder_id}/deletion-impact", {"GET"}),
        ("/api/folders/{folder_id}", {"DELETE"}),
        ("/health", {"GET"}),
        ("/api/notes", {"POST"}),
        ("/api/notes/{note_id}", {"GET"}),
        ("/api/notes/{note_id}", {"PATCH"}),
        ("/api/notes/{note_id}", {"DELETE"}),
        ("/api/assets", {"POST"}),
        ("/api/assets/{asset_id}", {"GET"}),
    ]
    assert client.get("/docs").status_code == 404
    assert client.post("/health").status_code == 405
