import importlib.util
import json
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[2] / "packaging/flatpak/prepare.py"
spec = importlib.util.spec_from_file_location("p2_prepare", path)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_manifest_is_private_candidate_not_legacy_installer():
    manifest = prepare.manifest()
    assert manifest["app-id"] == "org.cyrnava.CyrNava.Devel"
    permissions = manifest["finish-args"]
    assert "--unshare=network" in permissions
    assert not any(
        p.startswith(
            ("--share=network", "--filesystem=", "--socket=session-bus", "--socket=x11")
        )
        for p in permissions
    )
    text = json.dumps(manifest)
    assert "DISABLE_SANDBOX" not in text and "--no-sandbox" not in text
    assert "prototypes/" not in text and "launcher.py" not in text
    assert "--no-index" in text and "sha256sum --check" in text
    assert "desktop.native" in text


def test_snapshot_excludes_caches_but_refuses_symlinks_and_database(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("source")
    (source / "__pycache__").mkdir()
    (source / "__pycache__/x.pyc").write_bytes(b"x")
    destination = tmp_path / "snapshot"
    prepare.snapshot(source, destination)
    assert (destination / "app.py").read_text() == "source"
    assert not (destination / "__pycache__").exists()
    (source / "personal.sqlite3").write_bytes(b"")
    with pytest.raises(ValueError):
        prepare.snapshot(source, tmp_path / "refused")
    (source / "personal.sqlite3").unlink()
    (source / "link").symlink_to(source / "app.py")
    with pytest.raises(ValueError):
        prepare.snapshot(source, tmp_path / "refused-link")


def test_preflight_requires_only_direct_refs_not_transitive_webengine_base():
    assert prepare.REFS == (
        "org.kde.Platform//6.11",
        "org.kde.Sdk//6.11",
        "io.qt.PySide.BaseApp//6.11",
    )
    commands = " ".join(prepare.manifest()["modules"][0]["build-commands"])
    assert "qWebEngineVersion" in commands


def test_snapshot_refuses_a_symlink_root(tmp_path):
    original = tmp_path / "original"
    original.mkdir()
    (original / "image.png").write_bytes(b"synthetic private file")
    link = tmp_path / "linked-root"
    link.symlink_to(original, target_is_directory=True)
    with pytest.raises(ValueError):
        prepare.snapshot(link, tmp_path / "snapshot")


def test_staging_uses_absolute_xdg_cache_and_private_permissions(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache))
    root = prepare.staging_root()
    assert root == cache / "cyrnava-builds/p2"
    assert root.stat().st_mode & 0o777 == 0o700


def test_staging_ignores_relative_xdg_cache_and_refuses_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare.Path, "home", lambda: tmp_path / "home")
    monkeypatch.setenv("XDG_CACHE_HOME", "relative-cache")
    root = prepare.staging_root()
    assert root == tmp_path / "home/.cache/cyrnava-builds/p2"
    linked = tmp_path / "linked-cache"
    linked.symlink_to(root.parent, target_is_directory=True)
    monkeypatch.setenv("XDG_CACHE_HOME", str(linked))
    with pytest.raises(ValueError, match="symbolic link"):
        prepare.staging_root()


def test_build_requires_headroom_before_creating_temporary_files(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        prepare.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(free=prepare.MIN_BUILD_FREE_BYTES - 1),
    )
    with pytest.raises(ValueError, match="4 GiB"):
        prepare.build_environment(tmp_path)
    assert not (tmp_path / "tmp").exists()


def test_build_temporary_files_stay_on_the_build_filesystem(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        prepare.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(free=prepare.MIN_BUILD_FREE_BYTES),
    )
    monkeypatch.setenv("TMPDIR", "/tmp")
    environment = prepare.build_environment(tmp_path)
    assert environment["TMPDIR"] == str(tmp_path / "tmp")
    assert (tmp_path / "tmp").stat().st_mode & 0o777 == 0o700
