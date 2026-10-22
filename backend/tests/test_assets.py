import io
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.assets import MAX_BYTES, AssetStore
from app.database import Database
from app.main import create_app


def raster(fmt="PNG", size=(16, 12)):
    output = io.BytesIO()
    Image.new("RGB", size, "purple").save(output, format=fmt)
    return output.getvalue()


def note(client, title="Image note", folder_id=None):
    return client.post(
        "/api/notes",
        json={
            "title": title,
            "folder_id": folder_id,
            "document_json": [{"type": "paragraph", "content": []}],
        },
    ).json()


def upload(client, identifier, data=None, mime="image/png"):
    return client.post(
        f"/api/assets?note_id={identifier}",
        content=data if data is not None else raster(),
        headers={"content-type": mime},
    )


@pytest.mark.parametrize(
    ("fmt", "mime"),
    [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")],
)
def test_upload_retrieve_metadata_and_unique_ids(client, database_path, fmt, mime):
    owner = note(client)
    data = raster(fmt)
    response = upload(client, owner["id"], data, mime)
    assert response.status_code == 201
    asset = response.json()
    assert asset["note_id"] == owner["id"] and asset["mime_type"] == mime
    assert "disk_path" not in asset
    assert upload(client, owner["id"], data, mime).json()["id"] != asset["id"]
    received = client.get(asset["url"])
    assert received.status_code == 200
    assert received.headers["content-type"] == mime
    assert received.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in received.headers["content-security-policy"]
    with Image.open(io.BytesIO(received.content)) as decoded:
        assert decoded.format == fmt and decoded.size == (16, 12)
    with Database(database_path).connect() as connection:
        row = connection.execute(
            "SELECT * FROM assets WHERE id = ?", (asset["id"],)
        ).fetchone()
        assert row["disk_path"] == asset["id"]
        assert row["byte_size"] == len(received.content)
    path = database_path.parent / "assets" / asset["id"]
    assert path.read_bytes() == received.content
    assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    ("data", "mime"),
    [
        (b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml"),
        (b"not an image", "image/png"),
        (raster("PNG"), "image/jpeg"),
        (raster("PNG")[:40], "image/png"),
        (raster("GIF"), "image/gif"),
        (b"", "image/png"),
    ],
)
def test_reject_invalid_images_without_debris(client, database_path, data, mime):
    assert upload(client, note(client)["id"], data, mime).status_code == 422
    assert list((database_path.parent / "assets").iterdir()) == []
    with Database(database_path).connect() as connection:
        assert connection.execute("SELECT count(*) FROM assets").fetchone()[0] == 0


def test_size_dimensions_and_animation(client):
    identifier = note(client)["id"]
    assert upload(client, identifier, b"x" * (MAX_BYTES + 1)).status_code == 413
    assert upload(client, identifier, raster(size=(8193, 1))).status_code == 422
    assert upload(client, identifier, raster(size=(5000, 4001))).status_code == 422
    stream = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(
        stream,
        format="PNG",
        save_all=True,
        append_images=[Image.new("RGB", (4, 4), "blue")],
    )
    assert upload(client, identifier, stream.getvalue()).status_code == 422


def test_missing_ids_traversal_and_symlink(client, database_path, tmp_path):
    assert upload(client, str(uuid4())).status_code == 404
    assert upload(client, "../../etc/passwd").status_code == 422
    assert client.get(f"/api/assets/{uuid4()}").status_code == 404
    assert client.get("/api/assets/not-a-uuid").status_code == 422
    assert client.get("/api/assets/%2e%2e%2fetc%2fpasswd").status_code != 200
    asset = upload(client, note(client)["id"]).json()
    path = database_path.parent / "assets" / asset["id"]
    path.unlink()
    secret = tmp_path / "secret"
    secret.write_bytes(b"not public")
    path.symlink_to(secret)
    assert client.get(asset["url"]).status_code == 404
    with Database(database_path).connect() as connection:
        connection.execute(
            "UPDATE assets SET disk_path = '../secret' WHERE id = ?", (asset["id"],)
        )
    assert client.get(asset["url"]).status_code == 404


def test_write_failure_and_metadata_failure_rollback(
    client, database_path, monkeypatch
):
    identifier = note(client)["id"]
    with monkeypatch.context() as patch:
        patch.setattr(
            AssetStore,
            "_write",
            staticmethod(lambda *args: (_ for _ in ()).throw(OSError("disk full"))),
        )
        assert upload(client, identifier).status_code == 503
    with Database(database_path).connect() as connection:
        connection.execute(
            """CREATE TRIGGER fail_asset BEFORE INSERT ON assets
            BEGIN SELECT RAISE(ABORT, 'disk full'); END"""
        )
    assert upload(client, identifier).status_code == 503
    assert list((database_path.parent / "assets").iterdir()) == []
    with Database(database_path).connect() as connection:
        assert connection.execute("SELECT count(*) FROM assets").fetchone()[0] == 0


def test_exclusive_creation_does_not_overwrite_or_delete(
    client, database_path, monkeypatch
):
    identifier = note(client)["id"]
    fixed = uuid4()
    path = database_path.parent / "assets" / str(fixed)
    path.write_bytes(b"existing image")
    monkeypatch.setattr("app.assets.uuid4", lambda: fixed)
    assert upload(client, identifier).status_code == 503
    assert path.read_bytes() == b"existing image"


def test_mid_write_failure_cleans_partial_file(client, database_path, monkeypatch):
    identifier = note(client)["id"]
    monkeypatch.setattr(
        "app.assets.os.fsync", lambda fd: (_ for _ in ()).throw(OSError("disk failed"))
    )
    assert upload(client, identifier).status_code == 503
    assert list((database_path.parent / "assets").iterdir()) == []


def test_reconnect_restart_and_preserve_document(client, database_path):
    original = note(client)
    asset = upload(client, original["id"]).json()
    document = [
        {"type": "heading", "props": {"level": 1}, "content": []},
        {
            "type": "image",
            "id": "image-one",
            "props": {"url": asset["url"], "caption": "Evidence", "previewWidth": 420},
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "After image", "styles": {"bold": True}}
            ],
        },
    ]
    response = client.patch(
        f"/api/notes/{original['id']}", json={"revision": 1, "document_json": document}
    )
    assert response.status_code == 200 and response.json()["document_json"] == document
    assert Database(database_path).get(original["id"])["document_json"] == document
    with TestClient(create_app(database_path)) as restarted:
        assert restarted.get(asset["url"]).status_code == 200
        assert (
            restarted.get(f"/api/notes/{original['id']}").json()["document_json"]
            == document
        )
    other = note(client)
    assert (
        client.patch(
            f"/api/notes/{other['id']}", json={"revision": 1, "document_json": document}
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/notes/{original['id']}",
            json={"revision": 1, "document_json": document},
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/a.png",
        "data:image/png;base64,a",
        "blob:temporary",
        "/etc/passwd",
        f"/api/assets/{uuid4()}/../bad",
    ],
)
def test_reject_nonlocal_document_urls(client, url):
    identifier = note(client)["id"]
    assert (
        client.patch(
            f"/api/notes/{identifier}",
            json={
                "revision": 1,
                "document_json": [{"type": "image", "props": {"url": url}}],
            },
        ).status_code
        == 422
    )


def test_delete_and_startup_cleanup_preserve_unrelated_and_pending_assets(
    client, database_path
):
    folder = client.post("/api/folders", json={"name": "Disposable"}).json()
    one, two = note(client, folder_id=folder["id"]), note(client, "Keep")
    gone, kept = upload(client, one["id"]).json(), upload(client, two["id"]).json()
    # Both are pending (not in document yet). Restart must retain live ownership.
    with TestClient(create_app(database_path)) as restarted:
        assert restarted.get(kept["url"]).status_code == 200
    impact = client.get(f"/api/folders/{folder['id']}/deletion-impact").json()
    assert (
        client.request(
            "DELETE",
            f"/api/folders/{folder['id']}",
            json={
                "recursive": True,
                "expected_descendant_folders": 0,
                "expected_notes": 1,
                "impact_token": impact["token"],
            },
        ).status_code
        == 204
    )
    assert client.get(gone["url"]).status_code == 404
    assert not (database_path.parent / "assets" / gone["id"]).exists()
    assert client.get(kept["url"]).status_code == 200
    # A crash before metadata commit leaves an unowned generated file.
    orphan = database_path.parent / "assets" / str(uuid4())
    orphan.write_bytes(b"partial")
    with TestClient(create_app(database_path)):
        assert not orphan.exists()
    assert (
        client.request(
            "DELETE", f"/api/notes/{two['id']}", json={"revision": 1}
        ).status_code
        == 204
    )
    assert list((database_path.parent / "assets").iterdir()) == []


def test_cleanup_failure_is_retried_at_startup(client, database_path, monkeypatch):
    owner = note(client)
    asset = upload(client, owner["id"]).json()
    path = database_path.parent / "assets" / asset["id"]
    original = Path.unlink
    with monkeypatch.context() as patch:

        def fail(target, *args, **kwargs):
            if target == path:
                raise PermissionError("temporarily unavailable")
            return original(target, *args, **kwargs)

        patch.setattr(Path, "unlink", fail)
        assert (
            client.request(
                "DELETE", f"/api/notes/{owner['id']}", json={"revision": 1}
            ).status_code
            == 204
        )
        assert path.exists()
    with TestClient(create_app(database_path)):
        assert not path.exists()


def test_m2_migration_preserves_every_existing_note_field(tmp_path):
    path = tmp_path / "m2.sqlite3"
    database = Database(path)
    database.initialize()
    original = database.create("Original", [{"type": "paragraph", "content": []}], 1)
    with database.connect() as connection:
        connection.execute("DROP TABLE assets")
        connection.execute("PRAGMA user_version = 2")
        before = tuple(connection.execute("SELECT * FROM notes").fetchone())
    database.initialize()
    database.initialize()
    with database.connect() as connection:
        assert tuple(connection.execute("SELECT * FROM notes").fetchone()) == before
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()
    assert database.get(original["id"]) == original
