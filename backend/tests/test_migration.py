import hashlib
import json
import shutil
import sqlite3
import zipfile

import pytest

from app import migration as m
from app.backup import BackupError
from app.database import Database
from app.profile import profile_lock
from tests.test_backup import profile as source_profile


@pytest.fixture
def profile(tmp_path):
    return source_profile.__wrapped__(tmp_path)


def fingerprint(path):
    return {
        str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in path.rglob("*")
        if p.is_file()
    }


def archive(profile, tmp_path):
    target = tmp_path / "backup.cyrnava"
    m.pack(profile[0], target)
    return target


def test_roundtrip_preserves_source_and_all_data(profile, tmp_path):
    source, db, note, asset = profile
    before = fingerprint(source)
    backup = archive(profile, tmp_path)
    result = m.migrate(backup, tmp_path / "restored")
    assert result["status"] == "activated"
    restored = Database(tmp_path / "restored/engage.sqlite3")
    assert db.tree() == restored.tree()
    assert db.get(note) == restored.get(note)
    assert fingerprint(source) == before
    assert (source / "assets" / asset["id"]).read_bytes() == (
        tmp_path / "restored/assets" / asset["id"]
    ).read_bytes()
    restored.initialize()
    restored.update(note, restored.get(note)["revision"], {"title": "autosaved"})
    assert restored.get(note)["title"] == "autosaved"
    with pytest.raises(BackupError, match="exists"):
        m.migrate(backup, tmp_path / "restored")
    assert restored.get(note)["title"] == "autosaved"


@pytest.mark.parametrize("stage", ["extracted", "upgraded", "before-activation"])
def test_interruption_quarantines_never_activates(profile, tmp_path, stage):
    backup = archive(profile, tmp_path)
    before = fingerprint(profile[0])

    def interrupt(current):
        if current == stage:
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        m.migrate(backup, tmp_path / "restored", checkpoint=interrupt)
    assert not (tmp_path / "restored").exists()
    assert fingerprint(profile[0]) == before
    assert (
        json.loads(next(tmp_path.glob("migration-*.json")).read_text())["status"]
        == "failed-quarantined"
    )
    assert m.migrate(backup, tmp_path / "recovered")["status"] == "activated"


@pytest.mark.parametrize(
    "bad", ["database", "missing", "future", "symlink", "orphan", "trigger", "wal"]
)
def test_invalid_sources_rejected(profile, tmp_path, bad):
    source, db, _, asset = profile
    if bad == "database":
        db.path.write_bytes(b"not sqlite")
    elif bad == "missing":
        (source / "assets" / asset["id"]).unlink()
    elif bad == "future":
        with db.connect() as con:
            con.execute("PRAGMA user_version=99")
    elif bad == "trigger":
        with db.connect() as con:
            con.execute(
                "CREATE TRIGGER evil AFTER INSERT ON folders "
                "BEGIN DELETE FROM notes; END"
            )
    elif bad == "symlink":
        (source / "assets" / "link").symlink_to(db.path)
    elif bad == "orphan":
        (source / "assets" / "orphan").write_bytes(b"keep")
    else:
        (source / "engage.sqlite3-wal").write_bytes(b"pending")
    before = fingerprint(source)
    with pytest.raises((BackupError, sqlite3.Error)):
        archive(profile, tmp_path)
    assert fingerprint(source) == before
    assert not (tmp_path / "backup.cyrnava").exists()


@pytest.mark.parametrize(
    "bad",
    [
        "hash",
        "metadata",
        "version",
        "traversal",
        "duplicate",
        "symlink",
        "compressed",
        "truncated",
    ],
)
def test_untrusted_archives_fail_closed(profile, tmp_path, bad):
    original = archive(profile, tmp_path)
    candidate = tmp_path / "bad.cyrnava"
    if bad == "truncated":
        candidate.write_bytes(original.read_bytes()[:100])
    else:
        with zipfile.ZipFile(original) as src, zipfile.ZipFile(candidate, "w") as dst:
            for entry in src.infolist():
                data = src.read(entry)
                if entry.filename == "manifest.json":
                    manifest = json.loads(data)
                    if bad == "hash":
                        manifest["files"]["engage.sqlite3"] = "0" * 64
                    if bad == "version":
                        manifest["backup_format"] = 99
                    data = (
                        b"bad json"
                        if bad == "metadata"
                        else json.dumps(manifest).encode()
                    )
                if bad == "compressed":
                    entry.compress_type = zipfile.ZIP_DEFLATED
                if bad == "symlink":
                    entry.external_attr = 0o120777 << 16
                dst.writestr(entry, data)
            if bad == "traversal":
                dst.writestr("../escape", b"x")
            if bad == "duplicate":
                dst.writestr("manifest.json", b"{}")
    with pytest.raises((BackupError, ValueError, zipfile.BadZipFile)):
        m.migrate(candidate, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
    assert not (tmp_path / "escape").exists()


def test_busy_source_and_full_disk(profile, tmp_path, monkeypatch):
    with profile_lock(profile[0]):
        with pytest.raises(BackupError, match="Stop CyrNava"):
            archive(profile, tmp_path)
    monkeypatch.setattr(
        m.shutil, "disk_usage", lambda _: shutil._ntuple_diskusage(10, 10, 0)
    )
    with pytest.raises(BackupError, match="Insufficient"):
        archive(profile, tmp_path)


def test_atomic_activation_does_not_replace_concurrent_destination(profile, tmp_path):
    backup = archive(profile, tmp_path)
    target = tmp_path / "restored"

    def race(stage):
        if stage == "before-activation":
            target.mkdir()
            (target / "sentinel").write_text("preserve")

    with pytest.raises(OSError):
        m.migrate(backup, target, checkpoint=race)
    assert (target / "sentinel").read_text() == "preserve"


@pytest.mark.parametrize("version", [3, 4])
def test_upgrade_supported_schemas(profile, tmp_path, version):

    source, db, note, _ = profile
    with db.connect() as con:
        for name in ("note_search_insert", "note_search_update", "note_search_delete"):
            con.execute(f"DROP TRIGGER {name}")
        con.execute("DROP TABLE note_search")
        con.execute("DROP TABLE note_search_documents")
        if version == 3:
            con.execute("DROP TABLE template_images")
            con.execute("DROP TABLE templates")
        con.execute(f"PRAGMA user_version={version}")
    backup = archive(profile, tmp_path)
    m.migrate(backup, tmp_path / "restored")
    restored = Database(tmp_path / "restored/engage.sqlite3")
    assert restored.get(note) == db.get(note)
    assert m.inspect(tmp_path / "restored")["schema"] == 5


def test_generation_activation_and_rollback_preserve_previous(
    profile, tmp_path, monkeypatch
):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    from desktop.native.storage import Profile

    archive_path = archive(profile, tmp_path)
    native = Profile(tmp_path / "native")
    old_data = native.data
    Database(old_data / "engage.sqlite3").initialize()
    (old_data / "assets").mkdir()
    old_note = Database(old_data / "engage.sqlite3").create(
        "Previous", [{"type": "paragraph", "content": []}], 1
    )
    parent = native.root / "workspaces"
    parent.mkdir()
    selection = "workspaces/" + "a" * 32
    m.migrate(archive_path, native.root / selection)
    native.activate_workspace(selection)
    native.close()
    reopened = Profile(tmp_path / "native")
    assert reopened.selection == selection
    assert Database(reopened.database).get(profile[2]) == profile[1].get(profile[2])
    reopened.activate_workspace("workspace")
    assert Database(reopened.database).get(old_note["id"])["title"] == "Previous"
    previous_pointer = (reopened.root / "active-workspace.json").read_bytes()
    with Database(reopened.root / selection / "engage.sqlite3").connect() as con:
        con.execute("PRAGMA user_version=99")
    with pytest.raises(BackupError):
        reopened.activate_workspace(selection)
    assert (reopened.root / "active-workspace.json").read_bytes() == previous_pointer
    reopened.close()


def test_postmigration_corruption_leaves_destination_absent(profile, tmp_path):
    backup = archive(profile, tmp_path)

    def corrupt(stage):
        if stage == "upgraded":
            staged = next(tmp_path.glob(".migration-*"))
            with Database(staged / "engage.sqlite3").connect() as con:
                con.execute("UPDATE notes SET title='silently changed'")

    with pytest.raises(BackupError, match="Post-migration"):
        m.migrate(backup, tmp_path / "restored", checkpoint=corrupt)
    assert not (tmp_path / "restored").exists()


def test_old_directory_backup_can_be_packaged(profile, tmp_path):
    from app.backup import create_backup

    legacy = tmp_path / "format1"
    create_backup(profile[0], legacy)
    before = fingerprint(legacy)
    portable = tmp_path / "portable.cyrnava"
    m.pack(legacy, portable)
    m.migrate(portable, tmp_path / "restored")
    assert fingerprint(legacy) == before
    assert Database(tmp_path / "restored/engage.sqlite3").get(profile[2]) == profile[
        1
    ].get(profile[2])


def test_disk_full_during_restore_preserves_prior_workspace(
    profile, tmp_path, monkeypatch
):
    backup = archive(profile, tmp_path)
    target = tmp_path / "new"
    before = fingerprint(profile[0])
    original = m.durable_json

    def fail(path, value):
        if value.get("status") == "verified":
            raise OSError(28, "disk full")
        original(path, value)

    monkeypatch.setattr(m, "durable_json", fail)
    with pytest.raises(OSError):
        m.migrate(backup, target)
    assert not target.exists()
    assert fingerprint(profile[0]) == before


def test_resource_limits_and_hardlinks(profile, tmp_path, monkeypatch):
    import os

    image = profile[0] / "assets" / profile[3]["id"]
    os.link(image, tmp_path / "outside")
    with pytest.raises(BackupError, match="Unsafe"):
        archive(profile, tmp_path)
    (tmp_path / "outside").unlink()
    monkeypatch.setattr(m, "MAX_TOTAL", 10)
    with pytest.raises(BackupError, match="limits"):
        archive(profile, tmp_path)


def test_pointer_interruption_recovery_and_traversal(profile, tmp_path, monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    from desktop.native.storage import Profile

    root = tmp_path / "native"
    native = Profile(root)
    native.close()
    pointer = root / "active-workspace.json"
    pointer.write_text('{"version":1,"workspace":"../../outside"}')
    with pytest.raises(ValueError, match="pointer invalid"):
        Profile(root)
    maintenance = Profile(root, recovery=True)
    assert maintenance.pointer_error
    assert json.loads(pointer.read_text())["workspace"] == "../../outside"
    with pytest.raises(ValueError):
        maintenance.activate_workspace("../../outside")
    maintenance.close()


def test_portal_output_does_not_replace_existing_backup(profile, tmp_path, monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    from desktop.native.maintenance_io import export_selected

    backup = archive(profile, tmp_path)
    selected = tmp_path / "selected.cyrnava"
    selected.write_bytes(b"existing backup")
    with pytest.raises(ValueError):
        export_selected(backup, selected, tmp_path)
    assert selected.read_bytes() == b"existing backup"
    selected.unlink()
    export_selected(backup, selected, tmp_path)
    assert selected.read_bytes() == backup.read_bytes()


def test_explicit_browser_draft_recovery_preserves_original(profile, tmp_path):
    source, db, note_id, _ = profile
    note = db.get(note_id)
    before = fingerprint(source)
    draft = {
        "recovery_format": 1,
        "format_version": 1,
        "note_id": note_id,
        "base_revision": note["revision"],
        "title": "Recovered explicit draft",
        "document_json": note["document_json"],
    }
    path = tmp_path / "draft.json"
    path.write_text(json.dumps(draft))
    m.recover_draft(source, path, tmp_path / "recovered", tmp_path / "before.cyrnava")
    assert (
        Database(tmp_path / "recovered/engage.sqlite3").get(note_id)["title"]
        == draft["title"]
    )
    assert fingerprint(source) == before
    draft["base_revision"] += 10
    path.write_text(json.dumps(draft))
    with pytest.raises(BackupError, match="revision differs"):
        m.recover_draft(
            source, path, tmp_path / "conflict", tmp_path / "conflict.cyrnava"
        )
    assert not (tmp_path / "conflict").exists()


def test_migrated_api_autosave_upload_and_restart(profile, tmp_path):
    from fastapi.testclient import TestClient

    from app.main import create_app
    from tests.test_assets import raster, upload

    backup = archive(profile, tmp_path)
    destination = tmp_path / "restored"
    m.migrate(backup, destination)
    database = destination / "engage.sqlite3"
    identifier = profile[2]
    data = raster()
    with TestClient(create_app(database)) as client:
        note = client.get(f"/api/notes/{identifier}").json()
        response = upload(client, identifier, data)
        assert response.status_code == 201
        asset = response.json()
        doc = [
            *note["document_json"],
            {"type": "image", "props": {"url": asset["url"]}},
        ]
        saved = client.patch(
            f"/api/notes/{identifier}",
            json={
                "revision": note["revision"],
                "document_json": doc,
                "title": "Saved after migration",
            },
        )
        assert saved.status_code == 200
    with TestClient(create_app(database)) as client:
        assert client.get(f"/api/notes/{identifier}").json()["document_json"] == doc
        assert client.get(asset["url"]).content == data
    m.inspect(destination)


@pytest.mark.parametrize("filename", ["test", "test.zip", "test.cyrnava"])
def test_backup_import_is_independent_of_filename_extension(
    profile, tmp_path, filename
):
    source, db, note, asset = profile
    backup = tmp_path / filename
    m.pack(source, backup)
    before = hashlib.sha256(backup.read_bytes()).hexdigest()
    destination = tmp_path / "restored"
    assert m.migrate(backup, destination)["status"] == "activated"
    restored = Database(destination / "engage.sqlite3")
    assert restored.get(note) == db.get(note)
    assert (destination / "assets" / asset["id"]).read_bytes() == (
        source / "assets" / asset["id"]
    ).read_bytes()
    assert hashlib.sha256(backup.read_bytes()).hexdigest() == before
