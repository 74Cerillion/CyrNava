"""Safety/lifecycle tests. Never resolve or initialize the user's data profile."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "p1_desktop", Path(__file__).with_name("desktop.py")
)
desktop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(desktop)


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop, "ROOT", tmp_path / "prototype-root")
    return desktop.ROOT


def test_workspace_is_private_and_reopens_only_explicit_marker(root):
    workspace = desktop.workspace_path()
    assert root.stat().st_mode & 0o777 == 0o700
    assert workspace.stat().st_mode & 0o777 == 0o700
    assert desktop.workspace_path(workspace) == workspace
    assert not (workspace / "data").exists()


def test_personal_profile_and_unmarked_directory_are_refused(root, tmp_path):
    personal = tmp_path / "personal" / "engage"
    personal.mkdir(parents=True)
    sentinel = personal / "engage.sqlite3"
    sentinel.write_bytes(b"must not be opened or modified")
    with pytest.raises(ValueError):
        desktop.workspace_path(personal)
    unmarked = root / "workspace-unmarked"
    unmarked.mkdir()
    with pytest.raises(FileNotFoundError):
        desktop.workspace_path(unmarked)
    assert sentinel.read_bytes() == b"must not be opened or modified"


@pytest.mark.parametrize(
    "relative",
    [
        desktop.MARKER,
        "data",
        "data/engage",
        "data/engage/engage.sqlite3",
        "data/engage/assets",
        "qt-data",
        "qt-cache",
        "config",
        "cache",
    ],
)
def test_storage_symlinks_refused(root, tmp_path, relative):
    workspace = desktop.workspace_path()
    target = tmp_path / "outside"
    target.mkdir()
    path = workspace / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    path.symlink_to(target)
    with pytest.raises(ValueError):
        desktop.workspace_path(workspace)


def test_symlink_workspace_refused(root):
    workspace = desktop.workspace_path()
    alias = root / "workspace-alias"
    alias.symlink_to(workspace, target_is_directory=True)
    with pytest.raises(ValueError):
        desktop.workspace_path(alias)


@pytest.mark.parametrize(
    "name",
    [
        "QTWEBENGINE_DISABLE_SANDBOX",
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "QTWEBENGINE_REMOTE_DEBUGGING",
        "QTWEBENGINEPROCESS_PATH",
    ],
)
def test_inherited_webengine_overrides_refused(monkeypatch, name):
    monkeypatch.setenv(name, "unsafe")
    with pytest.raises(ValueError, match=name):
        desktop.check_environment()


def test_stable_loopback_port_and_occupied_port_refusal(root):
    workspace = desktop.workspace_path()
    with desktop.bind_backend(workspace) as listener:
        address = listener.getsockname()
        assert address[0] == "127.0.0.1"
        with pytest.raises(OSError):
            desktop.bind_backend(workspace)
    with desktop.bind_backend(workspace) as reopened:
        assert reopened.getsockname() == address


@pytest.mark.parametrize("port", [True, -1, 65536, "8000"])
def test_invalid_marker_port_refused(root, port):
    workspace = desktop.workspace_path()
    desktop.write_json(
        workspace / desktop.MARKER, {"prototype": "cyrnava-p1", "port": port}
    )
    with pytest.raises(ValueError):
        desktop.bind_backend(workspace)


def test_worker_serves_existing_release_and_stops_when_parent_pipe_closes():
    # Worker CLI deliberately accepts only this hard-coded disposable root.
    workspace = desktop.workspace_path()
    child = None
    read_fd, write_fd = os.pipe()
    try:
        with desktop.bind_backend(workspace) as listener:
            origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    "-I",
                    str(Path(desktop.__file__)),
                    "--worker",
                    str(workspace),
                    str(listener.fileno()),
                    str(read_fd),
                    "synthetic-test-nonce",
                ],
                pass_fds=(listener.fileno(), read_fd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "XDG_DATA_HOME": str(workspace / "data")},
            )
        os.close(read_fd)
        read_fd = None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + 10
        while True:
            try:
                with opener.open(origin + "/api/p1-ready", timeout=0.2) as response:
                    assert json.load(response) == {
                        "prototype": "cyrnava-p1",
                        "nonce": "synthetic-test-nonce",
                    }
                break
            except OSError:
                if time.monotonic() >= deadline:
                    pytest.fail("Disposable worker failed readiness")
                time.sleep(0.05)
        with opener.open(origin + "/") as response:
            assert b"CyrNava" in response.read()
            assert "script-src 'self'" in response.headers["Content-Security-Policy"]
        request = urllib.request.Request(
            origin + "/api/notes",
            data=json.dumps(
                {
                    "title": "Temporary worker note",
                    "document_json": [{"type": "paragraph", "content": []}],
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with opener.open(request) as response:
            assert json.load(response)["revision"] == 1
        assert (workspace / "data/engage/engage.sqlite3").is_file()
        os.close(write_fd)
        write_fd = None
        assert child.wait(timeout=10) == 0
    finally:
        if read_fd is not None:
            os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)
        if child is not None:
            desktop.stop_child(child)
        shutil.rmtree(workspace)
