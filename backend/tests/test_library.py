import json
import shutil
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import Database, InvalidRelationship
from app.main import create_app


def folder(client, name="Folder", parent=None):
    response = client.post("/api/folders", json={"name": name, "parent_id": parent})
    assert response.status_code == 201, response.text
    return response.json()


def note(client, document, parent=None, title="Note"):
    response = client.post(
        "/api/notes",
        json={
            "title": title,
            "document_json": document,
            "folder_id": parent,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def intent(client, identifier, recursive=True):
    response = client.get(f"/api/folders/{identifier}/deletion-impact")
    assert response.status_code == 200
    impact = response.json()
    return {
        "recursive": recursive,
        "expected_descendant_folders": impact["descendant_folders"],
        "expected_notes": impact["notes"],
        "impact_token": impact["token"],
    }


def remove(client, identifier, body):
    return client.request("DELETE", f"/api/folders/{identifier}", json=body)


def test_create_nested_rename_reparent_and_retrieve(client, document):
    root = folder(client, "Root")
    child = folder(client, "Child", root["id"])
    nested = folder(client, "Deep", child["id"])
    saved = note(client, document, nested["id"])
    response = client.patch(
        f"/api/folders/{child['id']}", json={"name": "Renamed", "parent_id": None}
    )
    assert response.status_code == 200
    assert response.json()["parent_id"] is None
    assert response.json()["id"] == child["id"]
    tree = client.get("/api/tree").json()
    assert (
        next(item for item in tree["folders"] if item["id"] == child["id"])["name"]
        == "Renamed"
    )
    assert (
        next(item for item in tree["folders"] if item["id"] == nested["id"])[
            "parent_id"
        ]
        == child["id"]
    )
    assert client.get(f"/api/notes/{saved['id']}").json() == saved
    assert all("document_json" not in item for item in tree["notes"])


def test_invalid_relationships_and_folder_requests(client):
    root = folder(client)
    child = folder(client, "Child", root["id"])
    for parent in [root["id"], child["id"], str(uuid4())]:
        assert (
            client.patch(
                f"/api/folders/{root['id']}", json={"parent_id": parent}
            ).status_code
            == 422
        )
    assert (
        client.post(
            "/api/folders", json={"name": "x", "parent_id": str(uuid4())}
        ).status_code
        == 422
    )
    for body in [{}, {"name": " "}, {"name": None}, {"sort_order": 1}]:
        assert client.patch(f"/api/folders/{root['id']}", json=body).status_code == 422
    for body in [{"name": ""}, {"name": "x" * 201}, {"name": "x", "parent_id": "bad"}]:
        assert client.post("/api/folders", json=body).status_code == 422
    missing = str(uuid4())
    assert (
        client.patch(f"/api/folders/{missing}", json={"name": "x"}).status_code == 404
    )
    assert client.get(f"/api/folders/{missing}/deletion-impact").status_code == 404


def test_folder_moves_are_serialized_to_prevent_competing_cycles(client, database_path):
    a, b = folder(client, "A"), folder(client, "B")

    def move(pair):
        try:
            Database(database_path).update_folder(pair[0], {"parent_id": pair[1]})
            return "ok"
        except InvalidRelationship:
            return "invalid"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(move, [(a["id"], b["id"]), (b["id"], a["id"])]))
    assert sorted(results) == ["invalid", "ok"]


def test_note_moves_preserve_json_and_reject_stale_writes(client, document):
    a, b = folder(client, "A"), folder(client, "B")
    saved = note(client, document, a["id"])
    path = f"/api/notes/{saved['id']}"
    for revision, destination in [(1, b["id"]), (2, None)]:
        response = client.patch(
            path, json={"revision": revision, "folder_id": destination}
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["folder_id"] == destination
        assert updated["document_json"] == saved["document_json"]
        assert updated["title"] == saved["title"]
        assert updated["created_at"] == saved["created_at"]
        assert updated["id"] == saved["id"]
        assert updated["revision"] == revision + 1
    assert (
        client.patch(path, json={"revision": 1, "folder_id": a["id"]}).status_code
        == 409
    )
    assert (
        client.patch(path, json={"revision": 3, "folder_id": str(uuid4())}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/notes",
            json={"title": "x", "document_json": document, "folder_id": str(uuid4())},
        ).status_code
        == 422
    )


def test_note_delete_checks_revision(client, document):
    saved = note(client, document)
    path = f"/api/notes/{saved['id']}"
    assert client.request("DELETE", path, json={"revision": 2}).status_code == 409
    assert client.get(path).status_code == 200
    assert client.request("DELETE", path, json={"revision": 1}).status_code == 204
    assert client.get(path).status_code == 404
    assert client.request("DELETE", path, json={"revision": 1}).status_code == 404


def test_empty_and_recursive_deletion_counts_and_intent(client, document):
    empty = folder(client, "Empty")
    assert (
        remove(client, empty["id"], intent(client, empty["id"], False)).status_code
        == 204
    )
    root = folder(client, "Root")
    child = folder(client, "Child", root["id"])
    grandchild = folder(client, "Grandchild", child["id"])
    note(client, document, root["id"])
    note(client, document, grandchild["id"])
    unaffected = note(client, document, title="Keep me")
    unrelated = folder(client, "Keep folder")
    impact = client.get(f"/api/folders/{root['id']}/deletion-impact").json()
    assert impact["descendant_folders"] == 2
    assert impact["notes"] == 2
    assert remove(client, root["id"], {"recursive": True}).status_code == 422
    assert (
        remove(client, root["id"], intent(client, root["id"], False)).status_code == 409
    )
    assert remove(client, root["id"], intent(client, root["id"])).status_code == 204
    tree = client.get("/api/tree").json()
    assert [item["id"] for item in tree["folders"]] == [unrelated["id"]]
    assert [item["id"] for item in tree["notes"]] == [unaffected["id"]]
    assert client.get(f"/api/notes/{unaffected['id']}").json() == unaffected


def test_stale_counts_and_same_count_replacement_are_rejected(client, document):
    root = folder(client)
    original = note(client, document, root["id"])
    confirmed = intent(client, root["id"])
    added = note(client, document, root["id"])
    assert remove(client, root["id"], confirmed).status_code == 409
    # Restore the same COUNT but change membership: the impact token must catch it.
    client.request("DELETE", f"/api/notes/{original['id']}", json={"revision": 1})
    assert remove(client, root["id"], confirmed).status_code == 409
    assert client.get(f"/api/notes/{added['id']}").status_code == 200
    confirmed = intent(client, root["id"])
    client.patch(
        f"/api/notes/{added['id']}",
        json={"revision": 1, "title": "Changed since confirmation"},
    )
    assert remove(client, root["id"], confirmed).status_code == 409
    assert remove(client, root["id"], intent(client, root["id"])).status_code == 204


def test_recursive_delete_rolls_back_everything_if_a_statement_fails(
    client, document, database_path
):
    root = folder(client)
    child = folder(client, "Child", root["id"])
    saved = note(client, document, child["id"])
    confirmed = intent(client, root["id"])
    with Database(database_path).connect() as connection:
        connection.execute(f"""CREATE TRIGGER fail_delete BEFORE DELETE ON folders
            WHEN old.id = '{root["id"]}' BEGIN
            SELECT RAISE(ABORT, 'test failure'); END""")
    before = client.get("/api/tree").json()
    assert remove(client, root["id"], confirmed).status_code == 503
    assert client.get("/api/tree").json() == before
    assert client.get(f"/api/notes/{saved['id']}").json() == saved


def test_foreign_keys_enforced_by_sqlite(client, document, database_path):
    root = folder(client)
    child = folder(client, "Child", root["id"])
    saved = note(client, document)
    with Database(database_path).connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        for query, value in [
            ("UPDATE folders SET parent_id = ? WHERE id = ?", child["id"]),
            ("UPDATE notes SET folder_id = ? WHERE id = ?", saved["id"]),
        ]:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(query, (str(uuid4()), value))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM folders WHERE id = ?", (root["id"],))


def test_deep_hierarchy_has_no_python_or_cascade_recursion_limit(
    client, database_path, document
):
    root = folder(client, "Depth 0")
    rows = []
    parent = root["id"]
    for depth in range(1, 1201):
        identifier = str(uuid4())
        rows.append((identifier, parent, f"Depth {depth}", "now", "now"))
        parent = identifier
    with Database(database_path).connect() as connection:
        connection.executemany(
            """INSERT INTO folders (id,parent_id,name,created_at,updated_at)
               VALUES (?,?,?,?,?)""",
            rows,
        )
    leaf = folder(client, "Leaf", parent)
    saved = note(client, document, leaf["id"])
    assert len(client.get("/api/tree").json()["folders"]) == 1202
    assert (
        client.patch(
            f"/api/folders/{root['id']}", json={"parent_id": leaf["id"]}
        ).status_code
        == 422
    )
    confirmed = intent(client, root["id"])
    assert confirmed["expected_descendant_folders"] == 1201
    assert remove(client, root["id"], confirmed).status_code == 204
    assert client.get(f"/api/notes/{saved['id']}").status_code == 404


def test_deterministic_order_and_reconnection(client, document, database_path):
    folder(client, "Zulu")
    folder(client, "alpha")
    folder(client, "Alpha")
    note(client, document, title="z")
    note(client, document, title="A")
    first = client.get("/api/tree").json()
    assert [item["title"] for item in first["notes"]] == ["A", "z"]
    assert [item["name"].lower() for item in first["folders"]] == [
        "alpha",
        "alpha",
        "zulu",
    ]
    with TestClient(create_app(database_path)) as restarted:
        assert restarted.get("/api/tree").json() == first


def make_m1(path, document):
    raw = json.dumps(document, ensure_ascii=False, indent=3)
    with sqlite3.connect(path) as connection:
        connection.execute("""CREATE TABLE notes (
            id TEXT PRIMARY KEY, folder_id TEXT DEFAULT NULL CHECK (folder_id IS NULL),
            title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
            document_json TEXT NOT NULL CHECK (json_valid(document_json)),
            format_version INTEGER NOT NULL CHECK (format_version = 1),
            revision INTEGER NOT NULL CHECK (revision >= 1),
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        identifier = str(uuid4())
        connection.execute(
            "INSERT INTO notes VALUES (?,NULL,?,?,1,7,?,?)",
            (identifier, "M1 original", raw, "created", "updated"),
        )
        connection.execute("PRAGMA user_version = 1")
    return identifier, raw


def test_migration_from_copy_of_m1_preserves_every_field(tmp_path, document):
    source, migrated = tmp_path / "m1.sqlite3", tmp_path / "copy.sqlite3"
    identifier, raw = make_m1(source, document)
    shutil.copy2(source, migrated)
    with TestClient(create_app(migrated)) as upgraded:
        saved = upgraded.get(f"/api/notes/{identifier}").json()
        assert saved == {
            "id": identifier,
            "folder_id": None,
            "title": "M1 original",
            "document_json": document,
            "format_version": 1,
            "revision": 7,
            "created_at": "created",
            "updated_at": "updated",
        }
        assert upgraded.get("/api/tree").json()["notes"][0]["id"] == identifier
        destination = folder(upgraded)
        moved = upgraded.patch(
            f"/api/notes/{identifier}",
            json={"revision": 7, "folder_id": destination["id"]},
        )
        assert moved.status_code == 200
        assert moved.json()["document_json"] == document
    Database(migrated).initialize()
    with sqlite3.connect(migrated) as connection:
        assert (
            connection.execute("SELECT document_json FROM notes").fetchone()[0] == raw
        )
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 5
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()
    with sqlite3.connect(source) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert (
            connection.execute("SELECT document_json FROM notes").fetchone()[0] == raw
        )


def test_failed_migration_rolls_back_schema_and_keeps_original_data(tmp_path):
    path = tmp_path / "invalid-m1.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE notes (id TEXT PRIMARY KEY, document_json TEXT)"
        )
        connection.execute("INSERT INTO notes VALUES ('keep', 'unaltered')")
        connection.execute("PRAGMA user_version = 1")
    with pytest.raises(sqlite3.OperationalError):
        Database(path).initialize()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT * FROM notes").fetchall() == [
            ("keep", "unaltered")
        ]
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall() == [("notes",)]


def test_code_block_native_json_round_trip(client):
    document = [
        {
            "type": "codeBlock",
            "props": {"language": "text"},
            "content": [{"type": "text", "text": "nmap -sV 127.0.0.1", "styles": {}}],
            "children": [],
        }
    ]
    saved = note(client, document)
    assert client.get(f"/api/notes/{saved['id']}").json()["document_json"] == document
