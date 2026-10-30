"""P1B packaging guards, without installing or launching a Flatpak."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load(Path(__file__).with_name("prepare.py"), "p1b_prepare")
desktop = load(Path(__file__).parents[1] / "p1_desktop/desktop.py", "p1b_desktop")


def test_manifest_keeps_network_and_filesystem_private():
    result = prepare.manifest()
    assert result["app-id"] == "org.cyrnava.P1B"
    assert result["branch"] == "p1b"
    assert result["base"] == "io.qt.PySide.BaseApp"
    assert result["runtime-version"] == result["base-version"] == "6.11"
    permissions = result["finish-args"]
    assert "--unshare=network" in permissions
    assert "--nofilesystem=home" in permissions
    assert "--nofilesystem=host" in permissions
    assert not any(
        flag.startswith(("--filesystem=", "--share=", "--talk-name="))
        for flag in permissions
    )
    assert not any(flag.startswith("--socket=x11") for flag in permissions)
    encoded = json.dumps(result)
    assert "--no-sandbox" not in encoded
    assert "QTWEBENGINE_DISABLE_SANDBOX" not in encoded
    assert "REMOTE_DEBUGGING" not in encoded
    assert "--no-index" in encoded


def test_snapshot_copies_code_and_existing_assets_only(tmp_path, monkeypatch):
    source = tmp_path / "repository"
    for relative, content in {
        "backend/app/main.py": "# code",
        "backend/app/document_format_v1.json": "{}",
        "backend/requirements.txt": "fastapi==0.156.3\n",
        "frontend/dist/index.html": "<title>Synthetic build</title>",
        "prototypes/p1_desktop/desktop.py": "# prototype",
        "personal/engage.sqlite3": "must not be copied",
        ".git/config": "must not be copied",
    }.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    monkeypatch.setattr(prepare, "SOURCE", source)
    monkeypatch.setattr(prepare, "ROOT", tmp_path / "staging")
    directory = prepare.stage()
    assert (directory / "application/backend/app/main.py").is_file()
    assert (directory / "application/frontend/dist/index.html").is_file()
    assert not (directory / "application/personal").exists()
    assert not (directory / "application/.git").exists()
    assert directory.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("kind", ["symlink", "database"])
def test_snapshot_refuses_unexpected_storage(tmp_path, kind):
    source = tmp_path / "source"
    source.mkdir()
    if kind == "symlink":
        (source / "link").symlink_to(tmp_path / "other")
    else:
        (source / "unexpected.sqlite3").write_bytes(b"synthetic")
    with pytest.raises(ValueError):
        prepare.copy_source(source, tmp_path / "output")


def test_p1b_refuses_execution_outside_its_flatpak(tmp_path, monkeypatch):
    info = tmp_path / "flatpak-info"
    info.write_text("[Application]\nname=org.cyrnava.P1B\n")
    monkeypatch.setattr(desktop, "FLATPAK_INFO", info)
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    with pytest.raises(ValueError, match="own installed Flatpak"):
        desktop.configure_flatpak()


@pytest.mark.parametrize(
    "context",
    [
        "shared=network;",
        "filesystems=home;",
        "filesystems=host:ro;",
        "filesystems=/home:ro;",
    ],
)
def test_p1b_refuses_unsafe_effective_permissions(tmp_path, monkeypatch, context):
    info = tmp_path / "flatpak-info"
    info.write_text(f"[Application]\nname=org.cyrnava.P1B\n[Context]\n{context}\n")
    monkeypatch.setattr(desktop, "FLATPAK_INFO", info)
    monkeypatch.setattr(desktop, "SOURCE", Path("/app/share/cyrnava"))
    monkeypatch.setenv("FLATPAK_ID", desktop.P1B_ID)
    with pytest.raises(ValueError, match="host networking or broad"):
        desktop.configure_flatpak()


def test_flatpak_workspace_is_stable_and_still_synthetic(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop, "ROOT", tmp_path / "private-p1b")
    first = desktop.default_flatpak_workspace()
    assert first == desktop.default_flatpak_workspace()
    assert first.name == "workspace-p1b"
    assert json.loads((first / desktop.MARKER).read_text())["prototype"] == "cyrnava-p1"
    assert not (first / "data").exists()


def test_p1b_uses_private_root_and_trusted_modules(tmp_path, monkeypatch):
    info = tmp_path / "flatpak-info"
    info.write_text("[Application]\nname=org.cyrnava.P1B\n[Context]\nshared=\n")
    monkeypatch.setattr(desktop, "FLATPAK_INFO", info)
    monkeypatch.setattr(desktop, "SOURCE", Path("/app/share/cyrnava"))
    monkeypatch.setattr(desktop, "ROOT", tmp_path / "restore-after-test")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(sys, "path", sys.path[:])
    monkeypatch.setenv("FLATPAK_ID", desktop.P1B_ID)
    desktop.configure_flatpak()
    assert desktop.ROOT == tmp_path / ".var/app/org.cyrnava.P1B/data/p1b-profiles"
    assert sys.path[0].startswith("/app/lib/python")


def test_process_evidence_reports_missing_process_without_false_pass():
    result = desktop.process_evidence(999999999)
    assert "unavailable" in result
    assert "status" not in result
