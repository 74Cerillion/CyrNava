"""Production identity, package boundary and schema safety; synthetic data only."""

import hashlib
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[2]), str(HERE.parents[2] / "backend")]
from app.database import Database

from desktop.native import build_identity
from desktop.native.storage import Profile


def load(name):
    spec = importlib.util.spec_from_file_location("p4_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load("build")
payload = load("install_payload")


def test_explicit_identity_and_least_privilege_manifest():
    production = load("build_identity")
    assert production.APP_ID == build.APP_ID
    assert production.APP_ID != build_identity.APP_ID
    assert production.WINDOW_TITLE == "CyrNava"
    manifest = json.loads((HERE / (build.APP_ID + ".json")).read_text())
    development = load_development_manifest()
    assert manifest["finish-args"] == development["finish-args"]
    assert manifest["app-id"] == production.APP_ID
    assert "--share=network" not in manifest["finish-args"]
    assert manifest["branch"] == "stable"
    for name in ("runtime", "runtime-version", "sdk", "base", "base-version"):
        assert manifest[name] == development[name]


def load_development_manifest():
    spec = importlib.util.spec_from_file_location(
        "p4_devel_prepare", HERE.parent / "prepare.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.manifest()


def test_desktop_metadata_and_real_owner_artwork():
    desktop = (HERE / (build.APP_ID + ".desktop")).read_text()
    assert "Name=CyrNava\n" in desktop and "Exec=cyrnava\n" in desktop
    assert "Icon=" + build.APP_ID + "\n" in desktop
    metadata = ET.parse(HERE / (build.APP_ID + ".metainfo.xml")).getroot()
    assert metadata.findtext("id") == build.APP_ID
    assert metadata.findtext("project_license") == "LicenseRef-proprietary"
    assert metadata.findtext("metadata_license") == "CC0-1.0"
    assert metadata.find("releases") is None  # No invented public history.
    image = build.SOURCE / "frontend/public/assets/branding/DesktopLogo.png"
    assert (
        build.sha(image)
        == "0d5be626f349f83cde2dc0738242e7cccf13ed7b08c08ab85b6d6853fa69db24"
    )


def test_stage_and_install_exclude_owner_data_and_development_tools(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    build.stage(inputs)
    app = inputs / "application"
    assert not list(app.rglob("evidence"))
    assert not list(app.rglob("tests"))
    assert not list(app.rglob("requirements.txt"))
    assert not list(app.rglob("migration_benchmark.py"))
    prefix = tmp_path / "files"
    (prefix / "bin").mkdir(parents=True)
    (prefix / "bin/QtWebEngineProcess").write_text("synthetic helper")
    (prefix / "bin/pyside6-designer").write_text("development tool")
    result = payload.install(prefix, inputs)
    assert result["status"] == "PASS"
    assert (
        prefix / "share/cyrnava/desktop/native/application.py"
    ).stat().st_mode & 0o777 == 0o644
    assert (prefix / "bin/cyrnava").stat().st_mode & 0o777 == 0o755
    assert not (prefix / "bin/pyside6-designer").exists()
    assert (prefix / "bin/QtWebEngineProcess").exists()
    config = prefix / "share/cyrnava/desktop/native/build_identity.py"
    assert config.read_bytes() == (HERE / "build_identity.py").read_bytes()
    assert build_identity.APP_ID not in config.read_text()
    assert (prefix / f"share/icons/hicolor/512x512/apps/{build.APP_ID}.png").is_file()


@pytest.mark.parametrize(
    "relative",
    [
        ".env",
        "secrets.pem",
        "workspace.sqlite3",
        "notes.db",
        "diagnostic.log",
        ".git/config",
        "tests/fixture.json",
        "evidence/result.json",
        "node_modules/pkg.js",
    ],
)
def test_audit_rejects_prohibited_payload(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic prohibited content")
    with pytest.raises(ValueError, match="Prohibited"):
        payload.audit(tmp_path)


def test_audit_rejects_escaping_links(tmp_path):
    (tmp_path / "bad").symlink_to("../../etc/passwd")
    with pytest.raises(ValueError, match="Escaping"):
        payload.audit(tmp_path)


def test_runtime_lock_has_no_test_dependencies():
    requirements = (HERE / "requirements.lock").read_text()
    assert "--hash=sha256:" in requirements
    for name in ("pytest", "ruff", "httpx", "pluggy", "pygments", "iniconfig"):
        assert name not in requirements.lower()
    assert "fastapi==0.156.3" in requirements


def test_future_schema_refusal_preserves_database_bytes(tmp_path):
    profile = Profile(tmp_path / "synthetic")
    db = Database(profile.database)
    try:
        db.initialize()
        note = db.create(
            "Synthetic rollback", [{"type": "paragraph", "content": []}], 1
        )
        with db.connect() as connection:
            connection.execute("PRAGMA user_version=6")
        before = hashlib.sha256(profile.database.read_bytes()).hexdigest()
        with pytest.raises(RuntimeError, match="newer"):
            db.initialize()
        assert hashlib.sha256(profile.database.read_bytes()).hexdigest() == before
        assert db.tree()["notes"][0]["id"] == note["id"]
    finally:
        profile.close()


def test_effective_permissions_reject_overrides():
    host = load("host_verify")
    good = "[Context]\nshared=!network;\nsockets=wayland;\ndevices=dri;\nfilesystems=!home;!host;xdg-config/kdeglobals:ro;\n"
    assert host.permissions(good)
    for old, new in (
        ("!network", "network"),
        ("wayland", "wayland;x11"),
        ("!home", "home"),
        ("!host", "/etc"),
    ):
        with pytest.raises(ValueError):
            host.permissions(good.replace(old, new))
    with pytest.raises(ValueError):
        host.permissions(good + "[System Bus Policy]\norg.test=talk\n")


def test_export_refuses_post_audit_tampering(tmp_path, monkeypatch):
    directory = tmp_path / "assembled"
    files = directory / "build/files"
    files.mkdir(parents=True)
    (directory / "build/export").mkdir()
    (directory / "build-inputs.json").write_text(json.dumps({"app_id": build.APP_ID}))
    (directory / (build.APP_ID + ".json")).write_text(json.dumps({"finish-args": []}))
    (files / "module.py").write_text("original")
    (directory / "package-inventory.json").write_text(json.dumps(payload.audit(files)))
    (files / "module.py").write_text("tampered")
    monkeypatch.setattr(build, "verify_refs", dict)
    with pytest.raises(ValueError, match="changed after"):
        build.finish(directory)


@pytest.mark.parametrize("failure", [None, "missing-record", "failed-check", "nonzero"])
@pytest.mark.parametrize("resume", [False, True, "maintenance"])
def test_host_supervisor_requires_native_results_and_preserves_data(
    tmp_path, monkeypatch, failure, resume
):
    host = load("host_verify")
    a, b = tmp_path / "A", tmp_path / "B"
    a.mkdir()
    b.mkdir()
    bundle_a, bundle_b = a / "A.flatpak", b / "B.flatpak"
    bundle_a.write_bytes(b"synthetic A")
    bundle_b.write_bytes(b"synthetic B")
    monkeypatch.setattr(sys, "argv", ["host_verify", "--a", str(a), "--b", str(b)])
    monkeypatch.setattr(host.Path, "home", lambda: tmp_path / "user")
    monkeypatch.setattr(host, "uuid4", lambda: type("ID", (), {"hex": "a" * 32})())
    monkeypatch.setattr(
        host,
        "build_result",
        lambda path: (
            path,
            bundle_a if path == a else bundle_b,
            {"ostree_commit": "A" if path == a else "B"},
        ),
    )
    if resume:
        monkeypatch.setattr(sys, "argv", sys.argv + ["--resume", "run-aaaaaaaaaaaa"])
        (a / "host-run-aaaaaaaaaaaa.json").write_text(
            json.dumps(
                {
                    "run_id": "run-aaaaaaaaaaaa",
                    "status": "FAIL",
                    "complete": True,
                    "build_A": "A",
                    "build_B": "B",
                    "checks": {"fresh_install_permissions": "PASS"},
                }
            )
        )
    state = {"installed": "A" if resume else None}
    monkeypatch.setattr(
        host,
        "commit",
        lambda app: state["installed"] if app == host.APP_ID else "development-before",
    )
    monkeypatch.setattr(
        host,
        "checked",
        lambda *args: (
            "[Context]\nsockets=wayland;\ndevices=dri;\nshared=!network;\nfilesystems=!home;!host;\n"
        ),
    )
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        if command[1] == "install":
            state["installed"] = "A" if command[-1] == str(bundle_a) else "B"
        elif command[1] == "uninstall":
            state["installed"] = None
        else:
            raise AssertionError("Unexpected mutation")

    monkeypatch.setattr(host.subprocess, "run", run)
    phases = []
    root = (
        tmp_path
        / "user/.var/app"
        / host.APP_ID
        / "data/p4-verification/run-aaaaaaaaaaaa"
    )

    if resume:
        root.mkdir(parents=True)
        (root / "edit.json").write_text('{"status":"FAIL","original_failure":true}')
    if resume == "maintenance":
        monkeypatch.setattr(sys, "argv", sys.argv + ["--continue-maintenance"])
        previous_path = a / "host-run-aaaaaaaaaaaa.json"
        previous = json.loads(previous_path.read_text())
        for name in ("edit", "restart", "updated", "rollback"):
            previous["checks"][name] = "PASS"
            (root / (name + ".json")).write_text(
                json.dumps(
                    {
                        "phase": name,
                        "status": "PASS",
                        "complete": True,
                        "checks": {key: "PASS" for key in host.REQUIRED[name]},
                        "preferences_sha256": "synthetic-stable-preference",
                    }
                )
            )
        previous["checks"].update(
            local_update="PASS", compatible_binary_rollback="PASS"
        )
        previous_path.write_text(json.dumps(previous))

    class Child:
        def __init__(self, command, **kwargs):
            self.phase = command[-4]
            phases.append(self.phase)
            self.returncode = 139 if failure == "nonzero" else 0

        def communicate(self, helper, timeout):
            assert b"application.configuration()" in helper
            root.mkdir(parents=True, exist_ok=True)
            (root / "synthetic-preserved").write_text("workspace")
            if failure == "missing-record":
                return
            (root / (self.phase + ".json")).write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "complete": True,
                        "checks": {
                            name: "FAIL" if failure == "failed-check" else "PASS"
                            for name in host.REQUIRED[self.phase]
                        },
                        "preferences_sha256": "synthetic-stable-preference",
                    }
                )
            )

    monkeypatch.setattr(host.subprocess, "Popen", Child)
    assert host.main() == (0 if failure is None else 1)
    final = json.loads((a / "host-run-aaaaaaaaaaaa.json").read_text())
    assert final["complete"] is True
    assert final["status"] == ("PASS" if failure is None else "FAIL")
    assert len(phases) == (
        (2 if resume == "maintenance" else 6) if failure is None else 1
    )
    assert (root / "synthetic-preserved").read_text() == "workspace"
    assert not any("--delete-data" in command for command in commands)
    if resume == "maintenance":
        assert phases[0] == "maintenance"
        assert final["reused_phases"] == ["edit", "restart", "updated", "rollback"]
        assert (Path(final["resumed_from"]) / "rollback.json").is_file()
    elif resume:
        assert (
            json.loads((Path(final["resumed_from"]) / "edit.json").read_text())[
                "original_failure"
            ]
            is True
        )
    if failure:
        assert not any("uninstall" in command for command in commands)


def test_export_timestamp_with_real_flatpak_and_ostree(tmp_path):
    """Exercise Flatpak's actual parser, not a mock that accepts any argument.

    The synthetic fixture has no icons, application code or dependencies to run.
    No sandbox is disabled; there is simply no icon validator to invoke here.
    """
    import shutil
    import subprocess
    from datetime import datetime

    if not shutil.which("flatpak") or not shutil.which("ostree"):
        pytest.skip("Flatpak/OSTree not installed")
    assert datetime.fromisoformat(build.EXPORT_TIMESTAMP).timestamp() == 1793314800
    directory = tmp_path / "timestamp-probe"
    (directory / "files/bin").mkdir(parents=True)
    binary = directory / "files/bin/probe"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    (directory / "metadata").write_text(
        "[Application]\nname=org.cyrnava.TimestampProbe\n"
        "runtime=org.kde.Platform/x86_64/6.11\n"
        "sdk=org.kde.Sdk/x86_64/6.11\ncommand=probe\n"
    )
    subprocess.run(
        ["flatpak", "build-finish", "--command=probe", str(directory)],
        check=True,
        capture_output=True,
        text=True,
    )
    repo = tmp_path / "repo"
    subprocess.run(
        [
            "flatpak",
            "build-export",
            "--timestamp=" + build.EXPORT_TIMESTAMP,
            str(repo),
            str(directory),
            "test",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    commit = subprocess.check_output(
        [
            "ostree",
            "--repo=" + str(repo),
            "rev-parse",
            "app/org.cyrnava.TimestampProbe/x86_64/test",
        ],
        text=True,
    ).strip()
    observed = subprocess.check_output(
        ["ostree", "--repo=" + str(repo), "show", commit], text=True
    )
    assert "2026-10-29 23:00:00 +0000" in observed


def test_owner_edit_diagnostics_and_preference_serialization(tmp_path):
    # Isolate the pure helper functions from unavailable WebEngine imports.
    import ast
    from types import SimpleNamespace

    from app.migration import inspect
    from app.migration_benchmark import dataset

    tree = ast.parse((HERE / "native_check.py").read_text())
    names = {"owner_edit_state", "saved_edit", "preference_state", "maintenance_state"}
    subset = ast.Module(
        body=[
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in names
        ],
        type_ignores=[],
    )
    scope = {"inspect": inspect, "json": json, "hashlib": hashlib}
    exec(compile(subset, "p4-pure-state-functions", "exec"), scope)  # noqa: S102 - trusted internal test functions only
    db = dataset(tmp_path / "workspace", 1)
    profile = SimpleNamespace(database=db.path, data=db.path.parent)
    state = scope["owner_edit_state"](profile)
    assert state == {
        "required_title_saved": "FAIL",
        "screenshot_asset_saved": "PASS",
        "folder_saved": "PASS",
    }
    with db.connect() as connection:
        connection.execute("UPDATE notes SET title=?", ("P4 owner edit",))
    assert scope["saved_edit"](profile)
    checks, digest = scope["preference_state"]('{"appearance":"dark","theme":null}')
    assert checks == {"dark_preference_saved": "PASS"} and len(digest) == 64
    for value in (None, "not-json", "[]", '{"appearance":"light"}'):
        checks, _ = scope["preference_state"](value)
        assert checks == {"dark_preference_saved": "FAIL"}

    # Closing maintenance without import must fail even if source records remain intact.
    checks = scope["maintenance_state"](False, True, True)
    assert checks["import_activated_new_workspace"] == "FAIL"
    assert checks["import_preserved_records"] == "PASS"
    assert all(
        v == "PASS" for v in scope["maintenance_state"](True, True, True).values()
    )
    assert "FAIL" in scope["maintenance_state"](True, False, True).values()
    assert "FAIL" in scope["maintenance_state"](True, True, False).values()


@pytest.mark.parametrize(
    "defect", ["missing", "incomplete", "failed", "preferences", "host"]
)
def test_maintenance_continuation_rejects_partial_evidence(tmp_path, defect):
    host = load("host_verify")
    previous = {
        "checks": {
            name: "PASS"
            for name in (
                "fresh_install_permissions",
                "local_update",
                "compatible_binary_rollback",
                "edit",
                "restart",
                "updated",
                "rollback",
            )
        }
    }
    for phase in ("edit", "restart", "updated", "rollback"):
        (tmp_path / (phase + ".json")).write_text(
            json.dumps(
                {
                    "phase": phase,
                    "status": "PASS",
                    "complete": True,
                    "checks": {key: "PASS" for key in host.REQUIRED[phase]},
                    "preferences_sha256": "stable",
                }
            )
        )
    path = tmp_path / "rollback.json"
    record = json.loads(path.read_text())
    if defect == "missing":
        del record["checks"]["renderer_sandbox"]
    elif defect == "incomplete":
        record["complete"] = False
    elif defect == "failed":
        record["checks"]["owned_backend_reaped"] = "FAIL"
    elif defect == "preferences":
        record["preferences_sha256"] = "changed"
    else:
        previous["checks"]["local_update"] = "FAIL"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        host.maintenance_checkpoint(tmp_path, previous)
