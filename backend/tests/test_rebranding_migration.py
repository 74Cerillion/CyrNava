"""Run the migration only on synthetic repositories/profiles, never this checkout."""

import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backup import validate_backup
from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "migrate_to_cyrnava.sh"
OLD = "https://github.com/74Cerillion/PEngage_Pentest-Engagement-Manager-"


@pytest.fixture
def tmp_path():
    # Standalone fixtures allow testing outside-Git guards without disabling
    # them when a developer's usual task/cache directories are Git-managed.
    with tempfile.TemporaryDirectory(prefix="cyrnava-migration-") as directory:
        yield Path(directory)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def migration(tmp_path):
    repo = tmp_path / "source with spaces"
    shutil.copytree(
        ROOT / "backend/app",
        repo / "backend/app",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (repo / "backend/.venv").symlink_to(
        ROOT / "backend/.venv", target_is_directory=True
    )
    (repo / "frontend").mkdir()
    (repo / "frontend/package.json").write_text('{"name":"cyrnava"}')
    (repo / "desktop").mkdir()
    (repo / "desktop/install.py").write_text("# synthetic installer marker\n")
    shutil.copy2(ROOT / ".gitignore", repo / ".gitignore")
    (repo / ".env").write_text("SYNTHETIC=private-config\n")
    git(repo, "init", "--initial-branch=main")
    git(repo, "config", "user.name", "Synthetic test")
    git(repo, "config", "user.email", "synthetic@example.invalid")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Synthetic source")
    git(repo, "remote", "add", "origin", OLD)
    data = tmp_path / "data/engage"
    with TestClient(create_app(data / "engage.sqlite3")) as client:
        note = client.post(
            "/api/notes",
            json={
                "title": "ENGAGE saved note",
                "document_json": [{"type": "paragraph", "content": []}],
            },
        ).json()
        image = io.BytesIO()
        Image.new("RGB", (24, 18), "blue").save(image, format="PNG")
        asset = client.post(
            f"/api/assets?note_id={note['id']}",
            content=image.getvalue(),
            headers={"Content-Type": "image/png"},
        ).json()
        note = client.patch(
            f"/api/notes/{note['id']}",
            json={
                "revision": 1,
                "document_json": [
                    *note["document_json"],
                    {"type": "image", "props": {"url": asset["url"]}},
                ],
            },
        ).json()
        template = client.post(
            "/api/templates",
            json={
                "name": "Existing custom",
                "source_note_id": note["id"],
                "source_revision": note["revision"],
            },
        ).json()
    env = {
        **os.environ,
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "HOME": str(tmp_path),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
    }

    def invoke(*args, location=None):
        return subprocess.run(
            [
                "bash",
                SCRIPT,
                str(location or repo),
                "--backup-dir",
                str(tmp_path / "backups"),
                *args,
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    return repo, data, note, template, invoke


def fingerprint(path):
    return {
        str(p.relative_to(path)): (
            hashlib.sha256(p.read_bytes()).hexdigest(),
            p.stat().st_mtime_ns,
        )
        for p in path.rglob("*")
        if p.is_file() and not any(parent.is_symlink() for parent in p.parents)
    }


def test_dry_run_does_not_modify_repository_profile_or_create_backups(
    migration, tmp_path
):
    repo, data, _, _, invoke = migration
    before_repo, before_data = fingerprint(repo), fingerprint(data)
    result = invoke("--dry-run")
    assert result.returncode == 0, result.stderr
    assert "DRY RUN" in result.stdout
    assert fingerprint(repo) == before_repo and fingerprint(data) == before_data
    assert not (tmp_path / "backups").exists() and not (tmp_path / "CyrNava").exists()
    assert git(repo, "remote", "get-url", "origin") == OLD


@pytest.mark.parametrize(
    "origin,expected",
    [
        (OLD, "https://github.com/74Cerillion/CyrNava.git"),
        (
            "git@github.com:74Cerillion/PEngage_Pentest-Engagement-Manager-.git",
            "git@github.com:74Cerillion/CyrNava.git",
        ),
        (
            "ssh://git@github.com/74Cerillion/CyrNava.git",
            "ssh://git@github.com/74Cerillion/CyrNava.git",
        ),
    ],
)
def test_verified_backup_rename_remote_and_safe_repeat(
    migration, tmp_path, origin, expected
):
    repo, data, note, template, invoke = migration
    git(repo, "remote", "set-url", "origin", origin)
    head, before_data = git(repo, "rev-parse", "HEAD"), fingerprint(data)
    result = invoke()
    assert result.returncode == 0, result.stderr
    renamed = tmp_path / "CyrNava"
    assert not repo.exists() and git(renamed, "rev-parse", "HEAD") == head
    assert git(renamed, "remote", "get-url", "origin") == expected
    assert fingerprint(data) == before_data
    backups = list((tmp_path / "backups").iterdir())
    assert len(backups) == 1
    backup = backups[0]
    assert backup.stat().st_mode & 0o077 == 0
    assert validate_backup(backup / "profile.engage-backup")
    assert json.loads((backup / "migration.json").read_text())["complete"]
    with tarfile.open(backup / "repository.tar") as archive:
        assert archive.extractfile("./.env").read() == b"SYNTHETIC=private-config\n"
        assert b"PEngage" in archive.extractfile(
            "./.git/config"
        ).read() or origin.endswith("CyrNava.git")
        assert not any(n.startswith("./backend/.venv") for n in archive.getnames())
    with TestClient(create_app(data / "engage.sqlite3")) as client:
        assert client.get(f"/api/notes/{note['id']}").json() == note
        assert template in client.get("/api/templates").json()
    repeated = invoke(location=renamed)
    assert repeated.returncode == 0 and "Already migrated" in repeated.stdout
    assert len(list((tmp_path / "backups").iterdir())) == 1


@pytest.mark.parametrize(
    "condition",
    [
        "dirty",
        "untracked",
        "destination",
        "foreign-origin",
        "push-url",
        "wal-sidecar",
        "wal-mode",
        "corrupt",
        "busy",
        "profile-in-repo",
        "backup-in-repo",
    ],
)
def test_unsafe_preflight_stops_without_mutating_repo(migration, tmp_path, condition):
    repo, data, _, _, invoke = migration
    if condition == "dirty":
        (repo / "frontend/package.json").write_text('{"name":"changed"}')
    elif condition == "untracked":
        (repo / "untracked.txt").write_text("retain")
    elif condition == "destination":
        (tmp_path / "CyrNava").mkdir()
    elif condition == "foreign-origin":
        git(
            repo,
            "remote",
            "set-url",
            "origin",
            "https://github.com/another/project.git",
        )
    elif condition == "push-url":
        git(
            repo,
            "remote",
            "set-url",
            "--push",
            "origin",
            "git@github.com:74Cerillion/CyrNava.git",
        )
    elif condition == "wal-sidecar":
        (data / "engage.sqlite3-wal").write_bytes(b"retain")
    elif condition == "wal-mode":
        with sqlite3.connect(data / "engage.sqlite3") as connection:
            connection.execute("PRAGMA journal_mode=WAL")
    elif condition == "corrupt":
        (data / "engage.sqlite3").write_bytes(b"invalid database")
    before, origin = fingerprint(repo), git(repo, "remote", "get-url", "origin")
    if condition == "busy":
        with TestClient(create_app(data / "engage.sqlite3")):
            result = invoke()
    elif condition == "profile-in-repo":
        result = invoke("--data-dir", str(repo / "data/engage"))
    elif condition == "backup-in-repo":
        result = invoke("--backup-dir", str(repo / "backups"))
    else:
        result = invoke()
    assert result.returncode != 0
    expected = {
        "dirty": "Uncommitted/untracked",
        "untracked": "Uncommitted/untracked",
        "destination": "destination already exists",
        "foreign-origin": "Unrecognized",
        "push-url": "explicit push URL",
        "wal-sidecar": "SQLite sidecars",
        "wal-mode": "WAL-mode",
        "corrupt": "Invalid or WAL-mode",
        "busy": "profile is busy",
        "profile-in-repo": "separate from the repository",
        "backup-in-repo": "separate from the repository",
    }
    assert expected[condition] in result.stderr, result.stderr
    assert (
        fingerprint(repo) == before
        and git(repo, "remote", "get-url", "origin") == origin
    )
    assert not (tmp_path / "backups").exists()
