"""Test-only SQL boundary and request/commit telemetry; no owner profiles."""

import importlib.util
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from app import main
from app.database import Database, RevisionConflict
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "p5a_fixture", ROOT / "ci/lifecycle_harness.py"
)
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)


@pytest.fixture
def fixture(tmp_path):
    database = harness.instrument_database(
        Database, harness.Journal(tmp_path / "events.jsonl")
    )(tmp_path / "fixture.sqlite3")
    database.initialize()
    note = database.create(
        "Synthetic private title", [{"type": "paragraph", "content": []}], 1
    )
    return database, note, harness.Journal(tmp_path / "events.jsonl")


def test_guard_rejects_preexisting_connection_and_all_note_mutations(fixture):
    database, note, journal = fixture
    pending = sqlite3.connect(database.path)
    baseline = harness.boundary(database.path, "arm", journal)
    try:
        for sql, args in [
            ("UPDATE notes SET revision=revision+1 WHERE id=?", (note["id"],)),
            ("DELETE FROM notes WHERE id=?", (note["id"],)),
            (
                "INSERT INTO notes SELECT 'synthetic-new',folder_id,title,"
                "document_json,"
                "format_version,revision,created_at,updated_at FROM notes WHERE id=?",
                (note["id"],),
            ),
        ]:
            with pytest.raises(sqlite3.IntegrityError, match="synthetic no-write"):
                pending.execute(sql, args)
            pending.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            database.update(note["id"], 1, {"title": "Must not commit"})
        assert harness.verify_boundary(database.path, baseline, journal) == baseline
    finally:
        pending.close()


def test_guard_persists_restart_and_disarm_preserves_revision_checks(fixture):
    database, note, journal = fixture
    baseline = harness.boundary(database.path, "arm", journal)
    database.initialize()
    assert harness.verify_boundary(database.path, baseline, journal) == baseline
    harness.boundary(database.path, "disarm", journal)
    saved = database.update(note["id"], 1, {"title": "Acknowledged"})
    assert saved["revision"] == 2
    with pytest.raises(RevisionConflict):
        database.update(note["id"], 1, {"title": "Stale"})


def test_unexpected_write_or_disabled_guard_fails_verification(fixture):
    database, note, journal = fixture
    baseline = harness.boundary(database.path, "arm", journal)
    harness.boundary(database.path, "disarm", journal)
    with pytest.raises(ValueError, match="guard was disarmed"):
        harness.verify_boundary(database.path, baseline, journal)
    database.update(note["id"], 1, {"title": "Unexpected canonical write"})
    harness.boundary(database.path, "arm", journal)
    with pytest.raises(ValueError, match="Canonical note changed"):
        harness.verify_boundary(database.path, baseline, journal)


def test_plain_application_has_no_test_guard(tmp_path):
    path = tmp_path / "plain.sqlite3"
    database = Database(path)
    database.initialize()
    with sqlite3.connect(path) as connection:
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE '%p5a%'"
        ).fetchall()
    with pytest.raises(sqlite3.OperationalError):
        harness.boundary(path, "arm", harness.Journal(tmp_path / "events.jsonl"))


def test_fastapi_to_sqlite_commit_and_rejection_share_correlation(
    tmp_path, monkeypatch
):
    journal = harness.Journal(tmp_path / "events.jsonl")
    monkeypatch.setattr(
        main, "Database", harness.instrument_database(Database, journal)
    )
    path = tmp_path / "fixture.sqlite3"
    app = main.create_app(path)
    app.add_middleware(harness.Correlation, journal=journal)
    with TestClient(app) as client:
        note = client.post(
            "/api/notes",
            json={
                "title": "DO NOT LOG THIS TITLE",
                "format_version": 1,
                "document_json": [{"type": "paragraph", "content": []}],
            },
        ).json()
        op = str(uuid4())
        headers = {
            "X-P5A-Operation": op,
            "X-P5A-Frontend": json.dumps(
                {
                    "perf_ms": 123,
                    "close_intent": True,
                    "visibility": "hidden",
                    "keepalive": False,
                    "service_worker": False,
                    "secret": "DO NOT LOG TOKEN",
                }
            ),
            "Authorization": "Bearer DO NOT LOG AUTH",
        }
        response = client.patch(
            f"/api/notes/{note['id']}",
            headers=headers,
            json={"revision": 1, "title": "DO NOT LOG CHANGED"},
        )
        assert response.status_code == 200
        baseline = harness.boundary(path, "arm", journal)
        denied = str(uuid4())
        response = client.patch(
            f"/api/notes/{note['id']}",
            headers={"X-P5A-Operation": denied},
            json={"revision": 2, "title": "Forbidden"},
        )
        assert response.status_code == 503
        assert harness.verify_boundary(path, baseline, journal) == baseline
    records = [json.loads(line) for line in journal.path.read_text().splitlines()]
    accepted = [r for r in records if r.get("operation") == op]
    events = [r["event"] for r in accepted]
    assert events.index("fastapi_request_enter") < events.index("database_update_enter")
    assert events.index("sqlite_commit_complete") < events.index(
        "database_update_return"
    )
    assert events.index("database_update_return") < events.index("fastapi_response")
    assert [
        r["revision"] for r in accepted if r["event"] == "database_update_return"
    ] == [2]
    assert all(a["mono_ns"] <= b["mono_ns"] for a, b in zip(accepted, accepted[1:]))
    blocked = [r for r in records if r.get("operation") == denied]
    assert any(r["event"] == "database_update_failed" for r in blocked)
    assert not any(r["event"] == "sqlite_commit_complete" for r in blocked)
    assert "DO NOT LOG" not in journal.path.read_text()


def test_production_staging_excludes_fixture_and_frontend_instrumentation(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "p5a_packager", ROOT / "packaging/flatpak/production/build.py"
    )
    packager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packager)
    packager.stage(tmp_path)
    staged = tmp_path / "application"
    assert not (staged / "ci").exists()
    assert not list(staged.rglob("*harness*"))
    for path in staged.rglob("*"):
        if path.suffix in {".py", ".js"}:
            assert "_p5a_test_guard" not in path.read_text()
            assert "X-P5A-Operation" not in path.read_text()


def test_arm_linearizes_after_an_existing_writer_and_blocks_later_requests(fixture):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    database, note, journal = fixture
    writer = sqlite3.connect(database.path)
    writer.execute("BEGIN IMMEDIATE")
    writer.execute("UPDATE notes SET revision=revision+1 WHERE id=?", (note["id"],))
    attempting = Event()

    def arm():
        attempting.set()
        return harness.boundary(database.path, "arm", journal)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(arm)
        assert attempting.wait(timeout=5)
        writer.commit()
        writer.close()
        baseline = future.result(timeout=5)
    assert baseline["notes"][0]["revision"] == 2
    with pytest.raises(sqlite3.IntegrityError):
        database.update(note["id"], 2, {"title": "Arrived after boundary"})
    assert harness.verify_boundary(database.path, baseline, journal) == baseline


def test_production_migration_rejects_guarded_fixture_profile(tmp_path):
    from app.backup import BackupError
    from app.migration import inspect

    profile = tmp_path / "synthetic-profile"
    profile.mkdir()
    (profile / "assets").mkdir()
    database = Database(profile / "engage.sqlite3")
    database.initialize()
    harness.install_guard(database.path)
    with pytest.raises(BackupError, match="Unexpected database schema"):
        inspect(profile)


def test_fixture_initialization_refuses_existing_workspace_without_modification(
    tmp_path,
):
    import hashlib

    path = tmp_path / "existing.sqlite3"
    database = Database(path)
    database.initialize()
    database.create("Synthetic existing workspace", [], 1)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    observed = harness.instrument_database(
        Database, harness.Journal(tmp_path / "events.jsonl")
    )(path)
    with pytest.raises(ValueError, match="Existing non-fixture database refused"):
        observed.initialize()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    with sqlite3.connect(path) as connection:
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE '%p5a%'"
        ).fetchall()
