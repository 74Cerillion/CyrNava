import io
import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backup import BackupError, create_backup, restore_backup, validate_backup
from app.database import Database
from app.main import create_app
from app.templates import STARTERS, builtin_templates


def source(client, document):
    response = client.post(
        "/api/notes", json={"title": "Source", "document_json": document}
    )
    assert response.status_code == 201
    return response.json()


def capture(client, note, name="Custom template"):
    response = client.post(
        "/api/templates",
        json={
            "name": name,
            "source_note_id": note["id"],
            "source_revision": note["revision"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def instantiate(client, template, title="Generated", folder_id=None):
    response = client.post(
        f"/api/templates/{template['id']}/notes",
        json={"revision": template["revision"], "title": title, "folder_id": folder_id},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize("key,name,sections", STARTERS)
def test_every_builtin_has_exact_native_sections_and_independent_instances(
    client, key, name, sections
):
    template = next(
        row
        for row in client.get("/api/templates").json()
        if row["id"] == "builtin:" + key
    )
    assert template["name"] == name and template["builtin"]
    folder = client.post("/api/folders", json={"name": "Destination"}).json()
    first = instantiate(client, template, folder_id=folder["id"])
    second = instantiate(client, template)
    headings = [
        b["content"][0]["text"]
        for b in first["document_json"]
        if b["type"] == "heading"
    ]
    assert headings == list(sections)
    assert first["folder_id"] == folder["id"]
    assert second["folder_id"] is None
    assert {b["id"] for b in first["document_json"]}.isdisjoint(
        b["id"] for b in second["document_json"]
    )
    if "Commands Executed" in sections or "Commands / Payloads" in sections:
        assert any(b["type"] == "codeBlock" for b in first["document_json"])
    client.patch(
        f"/api/notes/{first['id']}",
        json={"revision": 1, "document_json": [{"type": "paragraph", "content": []}]},
    )
    assert client.get(f"/api/notes/{second['id']}").json() == second
    assert (
        builtin_templates()["builtin:" + key]["document_json"][0]["type"] == "heading"
    )


def test_custom_native_formatting_and_nested_ids_are_independent(
    client, document, database_path
):
    original = source(client, document)
    template = capture(client, original)
    first, second = instantiate(client, template), instantiate(client, template)
    assert first["document_json"][0]["content"] == document[0]["content"]
    assert (
        first["document_json"][1]["children"][0]["id"]
        != second["document_json"][1]["children"][0]["id"]
    )
    assert client.get(f"/api/notes/{original['id']}").json() == original
    with TestClient(create_app(database_path)) as restarted:
        assert restarted.get("/api/templates").json()[-1] == template
        assert restarted.get(f"/api/notes/{first['id']}").json() == first


def test_rename_delete_and_revision_checks_do_not_change_generated_notes(
    client, document
):
    template = capture(client, source(client, document))
    note = instantiate(client, template)
    renamed = client.patch(
        f"/api/templates/{template['id']}", json={"name": "Renamed", "revision": 1}
    )
    assert renamed.status_code == 200 and renamed.json()["revision"] == 2
    assert (
        client.patch(
            f"/api/templates/{template['id']}", json={"name": "Stale", "revision": 1}
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/templates/{template['id']}/notes",
            json={"title": "Stale", "revision": 1},
        ).status_code
        == 409
    )
    assert (
        client.request(
            "DELETE", f"/api/templates/{template['id']}", json={"revision": 1}
        ).status_code
        == 409
    )
    assert (
        client.request(
            "DELETE", f"/api/templates/{template['id']}", json={"revision": 2}
        ).status_code
        == 204
    )
    assert client.get(f"/api/notes/{note['id']}").json() == note
    assert (
        client.post(
            f"/api/templates/{template['id']}/notes",
            json={"title": "Missing", "revision": 2},
        ).status_code
        == 404
    )


def test_builtins_are_protected_and_missing_templates_are_404(client):
    for item in client.get("/api/templates").json():
        assert (
            client.patch(
                f"/api/templates/{item['id']}",
                json={"name": "Overwrite", "revision": 1},
            ).status_code
            == 403
        )
        assert (
            client.request(
                "DELETE", f"/api/templates/{item['id']}", json={"revision": 1}
            ).status_code
            == 403
        )
    assert (
        client.patch(
            f"/api/templates/{uuid4()}", json={"name": "Missing", "revision": 1}
        ).status_code
        == 404
    )
    assert len(client.get("/api/templates").json()) == 5


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"name": " "},
        {"name": "x" * 201},
        {"source_note_id": "invalid"},
        {"source_revision": True},
        {"document_json": []},
    ],
)
def test_malformed_capture_is_rejected_without_creating_template(
    client, document, changes
):
    note = source(client, document)
    body = {
        "name": "Valid",
        "source_note_id": note["id"],
        "source_revision": 1,
    } | changes
    assert client.post("/api/templates", json=body).status_code == 422
    assert len(client.get("/api/templates").json()) == 5


def test_capture_requires_exact_saved_source_revision(client, document):
    note = source(client, document)
    client.patch(f"/api/notes/{note['id']}", json={"revision": 1, "title": "Newer"})
    assert (
        client.post(
            "/api/templates",
            json={"name": "Stale", "source_note_id": note["id"], "source_revision": 1},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/templates",
            json={
                "name": "Missing",
                "source_note_id": str(uuid4()),
                "source_revision": 1,
            },
        ).status_code
        == 404
    )
    assert len(client.get("/api/templates").json()) == 5


def pictured(client, document):
    note = source(client, document)
    image = io.BytesIO()
    Image.new("RGB", (20, 12), "blue").save(image, format="PNG")
    upload = client.post(
        f"/api/assets?note_id={note['id']}",
        content=image.getvalue(),
        headers={"Content-Type": "image/png"},
    )
    assert upload.status_code == 201
    asset = upload.json()
    body = [
        *document,
        {
            "type": "image",
            "props": {"url": asset["url"], "caption": "Evidence", "previewWidth": 250},
            "children": [],
        },
    ]
    saved = client.patch(
        f"/api/notes/{note['id']}", json={"revision": 1, "document_json": body}
    ).json()
    return saved, asset


def test_snapshots_and_new_note_images_survive_source_and_template_deletion(
    client, document, database_path
):
    original, asset = pictured(client, document)
    before = client.get(asset["url"]).content
    template = capture(client, original)
    assert (
        client.request(
            "DELETE", f"/api/notes/{original['id']}", json={"revision": 2}
        ).status_code
        == 204
    )
    assert client.get(asset["url"]).status_code == 404
    first, second = instantiate(client, template), instantiate(client, template)
    a, b = first["document_json"][-1], second["document_json"][-1]
    assert a["props"]["caption"] == b["props"]["caption"] == "Evidence"
    assert a["props"]["url"] != b["props"]["url"] != asset["url"]
    assert (
        client.get(a["props"]["url"]).content
        == client.get(b["props"]["url"]).content
        == before
    )
    assert (
        client.request(
            "DELETE", f"/api/templates/{template['id']}", json={"revision": 1}
        ).status_code
        == 204
    )
    with Database(database_path).connect() as connection:
        assert (
            connection.execute("SELECT count(*) FROM template_images").fetchone()[0]
            == 0
        )
    assert (
        client.request(
            "DELETE", f"/api/notes/{first['id']}", json={"revision": 1}
        ).status_code
        == 204
    )
    assert client.get(b["props"]["url"]).content == before


def test_failed_image_copy_rolls_back_note_rows_and_files(
    client, document, database_path
):
    note, _ = pictured(client, document)
    template = capture(client, note)
    before = client.get("/api/tree").json()
    files = set((database_path.parent / "assets").iterdir())
    with Database(database_path).connect() as connection:
        connection.execute("""CREATE TRIGGER reject_copy BEFORE INSERT ON assets
            BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END""")
    result = client.post(
        f"/api/templates/{template['id']}/notes",
        json={"revision": 1, "title": "Must roll back"},
    )
    assert result.status_code == 503
    assert client.get("/api/tree").json() == before
    assert set((database_path.parent / "assets").iterdir()) == files


def test_missing_image_and_size_limit_fail_without_partial_templates(
    client, document, database_path, monkeypatch
):
    note, asset = pictured(client, document)
    with monkeypatch.context() as patch:
        patch.setattr("app.templates.MAX_TEMPLATE_IMAGE_BYTES", 1)
        response = client.post(
            "/api/templates",
            json={
                "name": "Too large",
                "source_note_id": note["id"],
                "source_revision": 2,
            },
        )
        assert response.status_code == 422
    (database_path.parent / "assets" / asset["id"]).unlink()
    response = client.post(
        "/api/templates",
        json={
            "name": "Missing image",
            "source_note_id": note["id"],
            "source_revision": 2,
        },
    )
    assert response.status_code == 422
    assert len(client.get("/api/templates").json()) == 5


def test_backup_restore_carries_custom_templates_and_snapshot_bytes(tmp_path, document):
    path = tmp_path / "source/engage.sqlite3"
    with TestClient(create_app(path)) as client:
        note, asset = pictured(client, document)
        before = client.get(asset["url"]).content
        template = capture(client, note)
        client.request("DELETE", f"/api/notes/{note['id']}", json={"revision": 2})
    backup, restored = tmp_path / "backup", tmp_path / "restored"
    create_backup(path.parent, backup)
    assert set(validate_backup(backup)) == {"engage.sqlite3"}
    restore_backup(backup, restored)
    with TestClient(create_app(restored / "engage.sqlite3")) as client:
        generated = instantiate(client, template)
        assert (
            client.get(generated["document_json"][-1]["props"]["url"]).content == before
        )
    assert validate_backup(backup)


def test_schema3_migration_and_old_backup_restore_preserve_existing_rows(
    tmp_path, document
):
    path = tmp_path / "old/engage.sqlite3"
    with TestClient(create_app(path)) as client:
        note, asset = pictured(client, document)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE template_images")
        connection.execute("DROP TABLE templates")
        connection.execute("PRAGMA user_version = 3")
        old_note = tuple(connection.execute("SELECT * FROM notes").fetchone())
        old_assets = connection.execute("SELECT * FROM assets").fetchall()
    backup, restored = tmp_path / "backup3", tmp_path / "restored3"
    create_backup(path.parent, backup)
    restore_backup(backup, restored)
    Database(path).initialize()
    Database(path).initialize()
    with sqlite3.connect(path) as connection:
        assert tuple(connection.execute("SELECT * FROM notes").fetchone()) == old_note
        assert connection.execute("SELECT * FROM assets").fetchall() == old_assets
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
    with TestClient(create_app(restored / "engage.sqlite3")) as client:
        assert client.get(f"/api/notes/{note['id']}").json() == note
        assert client.get(asset["url"]).status_code == 200
        assert len(client.get("/api/templates").json()) == 5
    with sqlite3.connect(backup / "engage.sqlite3") as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3


def test_backup_refuses_damaged_template_snapshot(tmp_path, document):
    path = tmp_path / "source/engage.sqlite3"
    with TestClient(create_app(path)) as client:
        note, _ = pictured(client, document)
        capture(client, note)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE template_images SET data=x'6e6f7420616e20696d616765'"
        )
    with pytest.raises(BackupError, match="A template image failed validation"):
        create_backup(path.parent, tmp_path / "invalid-backup")
    assert not (tmp_path / "invalid-backup").exists()


def test_schema4_failure_rolls_back_partial_migration(tmp_path, document):
    path = tmp_path / "migration/engage.sqlite3"
    with TestClient(create_app(path)) as client:
        note = source(client, document)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE template_images")
        connection.execute("DROP TABLE templates")
        connection.execute("PRAGMA user_version = 3")
        # Simulate a schema collision on the second DDL statement.
        connection.execute("CREATE TABLE template_images (sentinel TEXT)")
        before = connection.execute("SELECT * FROM notes").fetchall()
    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        Database(path).initialize()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        assert connection.execute("SELECT * FROM notes").fetchall() == before
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='templates'"
            ).fetchone()
            is None
        )
        assert connection.execute("SELECT id FROM notes").fetchone()[0] == note["id"]
