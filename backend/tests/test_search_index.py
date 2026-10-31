"""Migration/recovery tests use temporary schema copies and offline locks."""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from app.backup import create_backup, restore_backup, validate_profile
from app.database import Database
from app.main import create_app
from app.profile import ProfileBusy, profile_lock
from app.search import SearchIndexError, verify_index
from app.search_index import rebuild
from fastapi.testclient import TestClient
from search_helpers import canonical_snapshot, remove_search_schema

BACKEND = Path(__file__).resolve().parents[1]


def seed(path, document):
    with TestClient(create_app(path)) as client:
        folder = client.post("/api/folders", json={"name": "Pentesting"}).json()
        response = client.post(
            "/api/notes",
            json={
                "title": "Enumeration",
                "folder_id": folder["id"],
                "document_json": document,
            },
        )
        assert response.status_code == 201, response.text
        note = response.json()
        template = client.post(
            "/api/templates",
            json={
                "name": "Reusable",
                "source_note_id": note["id"],
                "source_revision": 1,
            },
        )
        assert template.status_code == 201
    return note


def historical(path):
    with sqlite3.connect(path) as connection:
        remove_search_schema(connection)
        connection.execute("PRAGMA user_version=4")
        # Keep deliberately non-normalized bytes; migration must not serialize them.
        document = json.loads(
            connection.execute("SELECT document_json FROM notes").fetchone()[0]
        )
        connection.execute(
            "UPDATE notes SET document_json=?",
            (json.dumps(document, indent=4, ensure_ascii=False),),
        )
        return canonical_snapshot(connection)


def snapshot(path):
    with sqlite3.connect(path) as connection:
        return canonical_snapshot(connection)


def cli(profile):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "app.search_index",
            "rebuild",
            "--data-dir",
            str(profile),
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=20,
        env={**os.environ, "PYTHONPATH": str(BACKEND)},
    )


def test_schema4_backfill_preserves_every_canonical_field_and_is_idempotent(
    database_path, document
):
    note = seed(database_path, document)
    before = historical(database_path)
    Database(database_path).initialize()
    Database(database_path).initialize()
    assert snapshot(database_path) == before
    with TestClient(create_app(database_path)) as client:
        result = client.get("/api/search", params={"q": "Engagement"}).json()
        assert [row["note_id"] for row in result["results"]] == [note["id"]]
        assert client.get(f"/api/notes/{note['id']}").json() == note
    with Database(database_path).connect() as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 5
        assert (
            connection.execute("SELECT COUNT(*) FROM note_search_documents").fetchone()[
                0
            ]
            == 1
        )
        verify_index(connection)


def test_migration_failure_rolls_back_all_index_ddl_and_version(
    database_path, document
):
    seed(database_path, document)
    before = historical(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE note_search (sentinel TEXT)")
    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        Database(database_path).initialize()
    assert snapshot(database_path) == before
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='note_search_documents'"
            ).fetchone()
            is None
        )
        connection.execute("DROP TABLE note_search")
    Database(database_path).initialize()
    assert Database(database_path).search("Engagement")["total"] == 1


def test_fts5_unavailable_migration_is_clear_and_atomic(
    database_path, document, monkeypatch
):
    seed(database_path, document)
    before = historical(database_path)
    original_connect = sqlite3.connect

    class NoFTS(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if "CREATE VIRTUAL TABLE note_search" in sql:
                raise sqlite3.OperationalError("no such module: fts5")
            return super().execute(sql, parameters)

    monkeypatch.setattr(
        sqlite3,
        "connect",
        lambda *args, **kwargs: original_connect(*args, **kwargs, factory=NoFTS),
    )
    with pytest.raises(SearchIndexError, match="requires FTS5"):
        Database(database_path).initialize()
    assert snapshot(database_path) == before
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'note_search%'"
        ).fetchall()


def test_upgrade_refuses_older_running_backend_before_touching_schema(
    database_path, document
):
    seed(database_path, document)
    before = historical(database_path)
    with profile_lock(database_path.parent):
        with pytest.raises(ProfileBusy, match="before upgrading"):
            Database(database_path).initialize()
    assert snapshot(database_path) == before
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
    Database(database_path).initialize()


def test_current_schema_startups_can_share_profile_but_rebuild_cannot(
    database_path, document
):
    seed(database_path, document)
    with TestClient(create_app(database_path)) as first:
        with TestClient(create_app(database_path)) as second:
            assert (
                first.get("/health").status_code
                == second.get("/health").status_code
                == 200
            )
            result = cli(database_path.parent)
            assert result.returncode == 1 and "Stop all" in result.stderr
            with pytest.raises(ProfileBusy):
                rebuild(database_path.parent)
    assert cli(database_path.parent).returncode == 0


@pytest.mark.parametrize("damage", ["missing", "stale", "inverted"])
def test_rebuild_restores_derived_data_without_changing_canonical_rows(
    database_path, document, damage
):
    seed(database_path, document)
    before = snapshot(database_path)
    with Database(database_path).connect() as connection:
        if damage == "missing":
            connection.execute("DROP TABLE note_search")
        elif damage == "stale":
            connection.execute(
                "UPDATE note_search_documents SET headings='stale',body='',"
                "indexed_revision=999"
            )
        else:
            connection.execute(
                "INSERT INTO note_search(note_search) VALUES('delete-all')"
            )
    if damage == "missing":
        with pytest.raises(SearchIndexError, match="missing"):
            Database(database_path).initialize()
    else:
        assert Database(database_path).search("Engagement")["total"] == 0
        with Database(database_path).connect() as connection:
            with pytest.raises((SearchIndexError, sqlite3.DatabaseError)):
                verify_index(connection)
    result = cli(database_path.parent)
    assert result.returncode == 0, result.stderr
    assert "rebuilt and verified" in result.stdout
    assert snapshot(database_path) == before
    assert Database(database_path).search("Engagement")["total"] == 1
    assert Database(database_path).search("stale")["total"] == 0
    assert cli(database_path.parent).returncode == 0
    assert snapshot(database_path) == before


def test_rebuild_error_rolls_back_previous_index_and_canonical_data(
    database_path, document, monkeypatch
):
    seed(database_path, document)
    before = snapshot(database_path)

    def fail(connection):
        connection.execute("CREATE TABLE note_search_documents(sentinel TEXT)")
        raise sqlite3.OperationalError("injected")

    monkeypatch.setattr("app.search.create_index", fail)
    with pytest.raises(sqlite3.OperationalError, match="injected"):
        rebuild(database_path.parent)
    assert snapshot(database_path) == before
    assert Database(database_path).search("Engagement")["total"] == 1


def test_rebuild_refuses_bad_paths_and_does_not_create_profiles(
    tmp_path, database_path, document
):
    missing = tmp_path / "misspelled"
    assert cli(missing).returncode == 1
    assert not missing.exists()
    seed(database_path, document)
    link = tmp_path / "symlink"
    link.symlink_to(database_path.parent, target_is_directory=True)
    assert "symbolic link" in cli(link).stderr
    assert "outside Git" in cli(BACKEND.parent / "wrong-profile").stderr
    assert not (BACKEND.parent / "wrong-profile").exists()


def test_rebuild_refuses_legacy_schema_and_invalid_canonical_data(
    database_path, document
):
    seed(database_path, document)
    historical(database_path)
    before = snapshot(database_path)
    result = cli(database_path.parent)
    assert result.returncode == 1 and "upgrade first" in result.stderr
    assert snapshot(database_path) == before
    Database(database_path).initialize()
    with sqlite3.connect(database_path) as connection:
        connection.execute("UPDATE notes SET document_json='[]'")
    before = snapshot(database_path)
    result = cli(database_path.parent)
    assert result.returncode == 1 and "canonical data was not replaced" in result.stderr
    assert snapshot(database_path) == before


def test_schema5_backup_restore_and_readonly_validation(
    database_path, document, tmp_path
):
    seed(database_path, document)
    before = database_path.read_bytes()
    assert validate_profile(database_path.parent)
    assert database_path.read_bytes() == before
    backup, restored = tmp_path / "backup", tmp_path / "restored"
    create_backup(database_path.parent, backup)
    restore_backup(backup, restored)
    assert snapshot(restored / "engage.sqlite3") == snapshot(database_path)
    with TestClient(create_app(restored / "engage.sqlite3")) as client:
        assert (
            client.get("/api/search", params={"q": "Engagement"}).json()["total"] == 1
        )
    assert database_path.read_bytes() == before


def test_schema4_backup_remains_unchanged_when_restored_profile_upgrades(
    database_path, document, tmp_path
):
    seed(database_path, document)
    before = historical(database_path)
    backup, restored = tmp_path / "backup4", tmp_path / "restored4"
    create_backup(database_path.parent, backup)
    backup_bytes = (backup / "engage.sqlite3").read_bytes()
    restore_backup(backup, restored)
    with TestClient(create_app(restored / "engage.sqlite3")) as client:
        assert (
            client.get("/api/search", params={"q": "Engagement"}).json()["total"] == 1
        )
    assert snapshot(restored / "engage.sqlite3") == before
    assert (backup / "engage.sqlite3").read_bytes() == backup_bytes


def test_rebuild_refuses_sqlite_physical_corruption(tmp_path):
    profile = tmp_path / "broken"
    profile.mkdir()
    (profile / "assets").mkdir()
    database = profile / "engage.sqlite3"
    database.write_bytes(b"not sqlite")
    result = cli(profile)
    assert result.returncode == 1
    assert database.read_bytes() == b"not sqlite"


def test_rebuild_does_not_run_inside_active_offline_lock(database_path, document):
    seed(database_path, document)
    with profile_lock(database_path.parent, offline=True):
        with pytest.raises(ProfileBusy):
            rebuild(database_path.parent)
        with pytest.raises(ProfileBusy):
            Database(database_path).initialize()
