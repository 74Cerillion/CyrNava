import io
import json
import shutil
import sqlite3
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.assets import AssetStore
from app.backup import BackupError, create_backup, restore_backup, validate_backup
from app.database import Database
from app.main import create_app
from app.profile import ProfileBusy, profile_lock


@pytest.fixture
def profile(tmp_path):
    source = tmp_path / "original"
    database = Database(source / "engage.sqlite3")
    database.initialize()
    folder = database.create_folder("Course", None)
    child = database.create_folder("Nested", folder["id"])
    note = database.create(
        "Formatted note", [{"type": "paragraph", "content": []}], 1, child["id"]
    )
    store = AssetStore(database)
    output = io.BytesIO()
    Image.new("RGB", (24, 18), "blue").save(output, format="PNG")
    asset = store.upload(note["id"], output.getvalue(), "image/png")
    document = [
        {
            "type": "heading",
            "props": {"level": 1},
            "content": [{"type": "text", "text": "Evidence", "styles": {"bold": True}}],
        },
        {
            "type": "image",
            "props": {"url": asset["url"], "caption": "Saved screenshot"},
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "After image", "styles": {}}],
        },
    ]
    database.update(note["id"], 1, {"document_json": document})
    return source, database, note["id"], asset


def test_complete_restoration_drill(profile, tmp_path):
    source, database, identifier, asset = profile
    backup, restored = tmp_path / "backup", tmp_path / "restored"
    before_tree, before_note = database.tree(), database.get(identifier)
    create_backup(source, backup)
    manifest = json.loads((backup / "manifest.json").read_text())
    assert set(manifest["files"]) == {"engage.sqlite3", f"assets/{asset['id']}"}
    restore_backup(backup, restored)
    with TestClient(create_app(restored / "engage.sqlite3")) as client:
        assert client.get("/api/tree").json() == before_tree
        assert client.get(f"/api/notes/{identifier}").json() == before_note
        assert (
            client.get(asset["url"]).content
            == (source / "assets" / asset["id"]).read_bytes()
        )
        assert (
            client.patch(
                f"/api/notes/{identifier}",
                json={"revision": 2, "title": "Editing restored note"},
            ).status_code
            == 200
        )
    assert database.get(identifier) == before_note
    assert validate_backup(backup) == manifest["files"]
    assert (restored / "engage.sqlite3").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "missing", ["engage.sqlite3", "assets", "manifest.json", "image"]
)
def test_restore_rejects_missing_components(profile, tmp_path, missing):
    source, _, _, asset = profile
    backup = tmp_path / "backup"
    create_backup(source, backup)
    path = backup / (f"assets/{asset['id']}" if missing == "image" else missing)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    with pytest.raises((BackupError, sqlite3.Error)):
        restore_backup(backup, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


@pytest.mark.parametrize(
    "corruption", ["manifest", "database", "checksum", "traversal"]
)
def test_malformed_backups_are_not_published(profile, tmp_path, corruption):
    source, _, _, _ = profile
    backup = tmp_path / "backup"
    create_backup(source, backup)
    if corruption == "manifest":
        (backup / "manifest.json").write_text("bad JSON")
    elif corruption == "database":
        (backup / "engage.sqlite3").write_bytes(b"not SQLite")
    else:
        manifest = json.loads((backup / "manifest.json").read_text())
        manifest["files"][
            "../../escape" if corruption == "traversal" else "engage.sqlite3"
        ] = "0" * 64
        (backup / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises((BackupError, ValueError, sqlite3.Error)):
        restore_backup(backup, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
    assert not (tmp_path.parent / "escape").exists()


def test_backup_and_restore_refuse_overwrite(profile, tmp_path):
    source, _, _, _ = profile
    backup = tmp_path / "backup"
    create_backup(source, backup)
    with pytest.raises(BackupError, match="already exists"):
        create_backup(source, backup)
    sentinel = source / "sentinel"
    sentinel.write_text("keep")
    with pytest.raises(BackupError, match="already exists"):
        restore_backup(backup, source)
    assert sentinel.read_text() == "keep"


def test_running_backend_prevents_backup_and_exclusive_tool_blocks_startup(
    profile, tmp_path
):
    source, database, _, _ = profile
    with TestClient(create_app(database.path)):
        with pytest.raises(ProfileBusy):
            create_backup(source, tmp_path / "backup")
    with profile_lock(source, offline=True):
        with pytest.raises(ProfileBusy):
            with TestClient(create_app(database.path)):
                pytest.fail("Backend started during backup")
    create_backup(source, tmp_path / "backup")


def test_copy_failure_cleans_staging_and_leaves_source_untouched(
    profile, tmp_path, monkeypatch
):
    source, database, identifier, _ = profile
    before = database.get(identifier)
    monkeypatch.setattr(
        "app.backup.shutil.copyfile",
        lambda *args: (_ for _ in ()).throw(OSError("disk full")),
    )
    with pytest.raises(OSError):
        create_backup(source, tmp_path / "backup")
    assert not (tmp_path / "backup").exists()
    assert not list(tmp_path.glob(".engage-stage-*"))
    assert database.get(identifier) == before


def test_paths_symlinks_and_sidecars_rejected(profile, tmp_path):
    source, _, _, asset = profile
    with pytest.raises(BackupError):
        create_backup(source, source / "nested")
    with pytest.raises(BackupError, match="outside Git"):
        create_backup(
            source,
            __import__("pathlib").Path(__file__).resolve().parents[2] / "backups/test",
        )
    path = source / "assets" / asset["id"]
    original = tmp_path / "external-image"
    path.rename(original)
    path.symlink_to(original)
    with pytest.raises(BackupError):
        create_backup(source, tmp_path / "backup")
    path.unlink()
    original.rename(path)
    (source / "engage.sqlite3-wal").write_bytes(b"unfinished")
    with pytest.raises(BackupError, match="sidecar"):
        create_backup(source, tmp_path / "backup")


def test_cli_errors_are_nonzero_and_do_not_expose_paths(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.backup",
            "restore",
            "--source",
            str(tmp_path / "missing"),
            "--data-dir",
            str(tmp_path / "restored"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "failed" in result.stderr
    assert str(tmp_path) not in result.stderr and "Traceback" not in result.stderr


def test_folder_cycle_is_not_backed_up(profile, tmp_path):
    source, database, identifier, _ = profile
    with database.connect() as connection:
        folder = connection.execute("SELECT id FROM folders LIMIT 1").fetchone()[0]
        connection.execute(
            "UPDATE folders SET parent_id = ? WHERE id = ?", (folder, folder)
        )
    with pytest.raises(BackupError, match="hierarchy"):
        create_backup(source, tmp_path / "backup")


def test_same_size_corrupted_image_is_not_backed_up(profile, tmp_path):
    source, _, _, asset = profile
    path = source / "assets" / asset["id"]
    path.write_bytes(b"x" * path.stat().st_size)
    with pytest.raises(BackupError, match="image failed validation"):
        create_backup(source, tmp_path / "backup")
    assert not (tmp_path / "backup").exists()


def test_restore_copy_failure_does_not_publish_partial_profile(
    profile, tmp_path, monkeypatch
):
    source, _, _, _ = profile
    backup = tmp_path / "backup"
    create_backup(source, backup)
    monkeypatch.setattr(
        "app.backup.shutil.copyfile",
        lambda *args: (_ for _ in ()).throw(OSError("disk full")),
    )
    with pytest.raises(OSError):
        restore_backup(backup, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
    assert not list(tmp_path.glob(".engage-stage-*"))
