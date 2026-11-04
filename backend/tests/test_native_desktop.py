"""Synthetic profiles only. These exercise real owned backend subprocesses."""

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from desktop.native.backend import Backend  # noqa: E402
from desktop.native.policy import (  # noqa: E402
    download_allowed,
    navigation_allowed,
    resource_allowed,
)
from desktop.native.storage import Profile  # noqa: E402


def call(backend, path, body=None, token=None):
    headers = {
        "X-CyrNava-Session": backend.token if token is None else token,
        "Origin": backend.origin,
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(
        backend.origin + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=3) as response:
        return json.load(response)


def test_real_backend_restart_revokes_token_preserves_content(tmp_path):
    root = tmp_path / "profile"
    profile = Profile(root)
    backend = Backend(profile)
    try:
        backend.start()
        assert backend.child.poll() is None
        old_token, origin = backend.token, backend.origin
        assert old_token not in " ".join(backend.child.args)
        with pytest.raises(urllib.error.HTTPError) as error:
            call(backend, "/api/tree", token="missing")
        assert error.value.code == 401
        note = call(
            backend,
            "/api/notes",
            {
                "title": "Synthetic P2",
                "document_json": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Persisted privately",
                                "styles": {"bold": True},
                            }
                        ],
                    }
                ],
                "format_version": 1,
            },
        )
        backend.stop()
        assert backend.child.poll() is not None
        assert not backend.token
        assert old_token not in (root / "backend.log").read_text()
        assert old_token not in (root / "desktop.json").read_text()
    finally:
        backend.stop()
        profile.close()
    profile = Profile(root)
    backend = Backend(profile)
    try:
        backend.start()
        assert backend.origin == origin and backend.token != old_token
        with pytest.raises(urllib.error.HTTPError) as error:
            call(backend, "/api/tree", token=old_token)
        assert error.value.code == 401
        assert call(backend, "/api/notes/" + note["id"]) == note
        assert profile.database.stat().st_mode & 0o777 == 0o600
    finally:
        backend.stop()
        profile.close()


def test_duplicate_and_private_storage(tmp_path):
    root = tmp_path / "profile"
    profile = Profile(root)
    try:
        with pytest.raises(BlockingIOError):
            Profile(root)
        assert root.stat().st_mode & 0o777 == 0o700
        assert profile.qt.stat().st_mode & 0o777 == 0o700
        assert (root / ".instance.lock").stat().st_mode & 0o777 == 0o600
    finally:
        profile.close()


@pytest.mark.parametrize(
    "relative",
    [
        "workspace",
        "web-profile",
        "web-cache",
        "desktop.json",
        "workspace/engage.sqlite3",
        "workspace/engage.sqlite3-wal",
        ".instance.lock",
    ],
)
def test_rejects_symlinks(tmp_path, relative):
    root = tmp_path / "profile"
    root.mkdir()
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(tmp_path / "elsewhere")
    with pytest.raises((ValueError, OSError)):
        Profile(root)


def test_hardlink_and_special_files_refused(tmp_path):
    root = tmp_path / "profile"
    root.mkdir()
    original = tmp_path / "original"
    original.write_text("untouched")
    (root / "desktop.json").hardlink_to(original)
    with pytest.raises(ValueError):
        Profile(root)
    assert original.read_text() == "untouched"


def test_startup_failure_reaps_owned_child_and_releases_socket(tmp_path):
    profile = Profile(tmp_path / "profile")
    # Missing production assets make startup fail without touching real data.
    source = tmp_path / "empty"
    source.mkdir()
    backend = Backend(profile, source)
    try:
        with pytest.raises((RuntimeError, TimeoutError)):
            backend.start(timeout=3)
        assert backend.child.poll() is not None
        assert backend.token == ""
    finally:
        backend.stop()
        profile.close()


def test_port_collision_never_attaches_to_unknown_server(tmp_path):
    profile = Profile(tmp_path / "profile")
    backend = Backend(profile)
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        profile.remember_port(occupied.getsockname()[1])
        try:
            with pytest.raises(OSError):
                backend.start()
            assert backend.child is None
        finally:
            backend.stop()
            profile.close()


def test_parent_death_pipe_stops_worker_and_lock_survives_gui_release(tmp_path):
    profile = Profile(tmp_path / "profile")
    backend = Backend(profile)
    try:
        backend.start()
        profile.close()
        with pytest.raises(BlockingIOError):
            Profile(tmp_path / "profile")
        os.close(backend.death_write)
        backend.death_write = None
        deadline = time.monotonic() + 10
        while backend.child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert backend.child.poll() is not None
        reopened = Profile(tmp_path / "profile")
        reopened.close()
    finally:
        backend.stop()
        profile.close()


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/",
        "file:///etc/passwd",
        "http://127.0.0.1:32187.evil/",
        "http://user@127.0.0.1:32187/",
        "http://127.0.0.1:32188/",
        "http://localhost:32187/",
        "javascript:alert(1)",
        "http://127.0.0.1:32187@evil.invalid/",
        "blob:https://evil.invalid/id",
    ],
)
def test_denies_external_resources_navigation_and_downloads(url):
    origin = "http://127.0.0.1:32187"
    assert not resource_allowed(url, origin)
    assert not navigation_allowed(url, origin)
    assert not download_allowed(url, origin)


def test_policy_allows_only_app_navigation_and_own_blob_exports():
    origin = "http://127.0.0.1:32187"
    assert navigation_allowed(origin + "/#note", origin)
    assert resource_allowed(origin + "/api/assets/id", origin)
    assert not navigation_allowed(origin + "/api/notes/id", origin)
    assert resource_allowed("data:image/png;base64,AAAA", origin)
    assert download_allowed("blob:" + origin + "/id", origin)
    assert not download_allowed(origin + "/api/tree", origin)
