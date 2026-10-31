import json
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from app.database import Database, RevisionConflict, default_database_path
from app.main import create_app
from fastapi.testclient import TestClient


def create(client, document):
    response = client.post(
        "/api/notes",
        json={
            "title": " First note ",
            "document_json": document,
            "format_version": 1,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_retrieve_and_json_integrity(client, document):
    note = create(client, document)
    UUID(note["id"])
    assert note["title"] == "First note"
    assert note["document_json"] == document
    assert note["revision"] == note["format_version"] == 1
    assert note["folder_id"] is None
    assert note["created_at"] == note["updated_at"]
    assert client.get(f"/api/notes/{note['id']}").json() == note


def test_update_partial_fields_and_preserve_metadata(client, document):
    note = create(client, document)
    path = f"/api/notes/{note['id']}"
    changed = [
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "New paragraph", "styles": {"italic": True}}
            ],
        }
    ]
    response = client.patch(path, json={"revision": 1, "document_json": changed})
    assert response.status_code == 200
    saved = response.json()
    assert saved["revision"] == 2
    assert saved["document_json"] == changed
    assert saved["title"] == note["title"]
    assert saved["created_at"] == note["created_at"]
    assert saved["updated_at"] >= note["updated_at"]
    renamed = client.patch(path, json={"revision": 2, "title": "Renamed"}).json()
    assert renamed["revision"] == 3
    assert renamed["document_json"] == changed
    assert renamed["title"] == "Renamed"


def test_persistence_across_application_restart(database_path, document):
    with TestClient(create_app(database_path)) as first:
        note = create(first, document)
    with TestClient(create_app(database_path)) as restarted:
        assert restarted.get(f"/api/notes/{note['id']}").json() == note
    # The canonical DB representation is native JSON, not Markdown or HTML.
    with Database(database_path).connect() as connection:
        row = connection.execute("SELECT document_json FROM notes").fetchone()
        assert json.loads(row[0]) == document
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 5


def test_missing_notes_and_malformed_identifier(client):
    path = f"/api/notes/{uuid4()}"
    assert client.get(path).status_code == 404
    assert client.patch(path, json={"revision": 1, "title": "x"}).status_code == 404
    assert client.get("/api/notes/not-a-uuid").status_code == 422


@pytest.mark.parametrize(
    "changes",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {"document_json": "not JSON blocks"},
        {"document_json": []},
        {"document_json": [{"type": "video"}]},
        {"document_json": [{"type": "paragraph", "content": ["bad"]}]},
        {"document_json": [{"type": "heading", "props": {"level": 9}}]},
        {
            "document_json": [
                {"type": "paragraph", "id": "same"},
                {"type": "paragraph", "id": "same"},
            ]
        },
        {"format_version": 2},
        {"format_version": True},
        {"document_json": [{"type": []}]},
        {"document_json": [{"type": {}}]},
        {"folder_id": "reserved"},
    ],
)
def test_malformed_creation_rejected(client, document, changes):
    body = {"title": "Note", "document_json": document, **changes}
    assert client.post("/api/notes", json=body).status_code == 422


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"revision": 1},
        {"revision": 0, "title": "x"},
        {"revision": True, "title": "x"},
        {"revision": "1", "title": "x"},
        {"revision": 1, "title": None},
        {"revision": 1, "document_json": None},
        {"revision": 1, "title": "x", "format_version": 2},
    ],
)
def test_malformed_update_rejected(client, document, changes):
    note = create(client, document)
    assert client.patch(f"/api/notes/{note['id']}", json=changes).status_code == 422
    assert client.get(f"/api/notes/{note['id']}").json() == note


def test_document_size_limit(client):
    response = client.post(
        "/api/notes",
        json={
            "title": "Large",
            "document_json": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "x" * 1_048_576, "styles": {}}
                    ],
                }
            ],
        },
    )
    assert response.status_code == 422


def test_conflicting_revision_does_not_overwrite(client, document):
    note = create(client, document)
    path = f"/api/notes/{note['id']}"
    winner = client.patch(path, json={"revision": 1, "title": "Winner"}).json()
    assert client.patch(path, json={"revision": 1, "title": "Stale"}).status_code == 409
    assert client.get(path).json() == winner


def test_two_connections_competing_for_same_revision(client, document, database_path):
    note = create(client, document)

    def write(title):
        try:
            return Database(database_path).update(note["id"], 1, {"title": title})
        except RevisionConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, ["A", "B"]))
    assert sum(result == "conflict" for result in results) == 1
    assert Database(database_path).get(note["id"])["revision"] == 2


def test_parameterized_title(client, document):
    note = create(client, document)
    title = "'); DROP TABLE notes; --"
    result = client.patch(
        f"/api/notes/{note['id']}",
        json={
            "revision": 1,
            "title": title,
        },
    )
    assert result.status_code == 200
    assert result.json()["title"] == title
    assert client.get(f"/api/notes/{note['id']}").status_code == 200


def test_xdg_location(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert default_database_path() == tmp_path / "engage/engage.sqlite3"
    monkeypatch.setenv("XDG_DATA_HOME", "relative/is/ignored")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert default_database_path() == tmp_path / ".local/share/engage/engage.sqlite3"


def test_repository_data_path_rejected(monkeypatch):
    from pathlib import Path

    monkeypatch.setenv("XDG_DATA_HOME", str(Path(__file__).resolve().parents[2]))
    with pytest.raises(ValueError, match="outside the repository"):
        default_database_path()


def test_initialization_idempotent_and_future_schema_rejected(database_path):
    database = Database(database_path)
    database.initialize()
    database.initialize()
    with database.connect() as connection:
        connection.execute("PRAGMA user_version = 6")
    with pytest.raises(RuntimeError, match="newer"):
        database.initialize()
