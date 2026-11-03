"""Synthetic-only targeted P6 contracts. No native install, runtime or Qt GUI."""

import ast
import contextlib
import copy
import io
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import historical_runtime
import native_diagnostics
import preference_contract
import targeted_b as target
import targeted_workspace as workspace


@pytest.fixture
def case(tmp_path):
    previous = os.umask(0o077)
    try:
        yield make_case(tmp_path)
    finally:
        os.umask(previous)


def make_case(root):
    migration = workspace.migration()
    from app.assets import AssetStore
    from app.database import Database
    from PIL import Image

    prepared = root / "real-pair-r2"
    r11 = root / "historical-gui-attempt-r11"
    attempt = root / "targeted-b-attempt-test"
    base = (
        r11
        / "client/home/.var/app"
        / core.APP_ID
        / "data/p4-verification"
        / ("run-" + "a" * 12)
    )
    profile = base / "desktop"
    selection = "workspaces/" + "a" * 32
    source = profile / selection
    source.mkdir(mode=0o700, parents=True)
    db = Database(source / "engage.sqlite3")
    db.initialize()
    folder = db.create_folder("Synthetic", None)
    note = db.create("P4 owner edit", [], 1, folder["id"])
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "blue").save(output, format="PNG")
    asset = AssetStore(db).upload(note["id"], output.getvalue(), "image/png")
    db.update(
        note["id"],
        1,
        {"document_json": [{"type": "image", "props": {"url": asset["url"]}}]},
    )
    (profile / ".instance.lock").write_bytes(b"")
    (profile / "active-workspace.json").write_bytes(
        core.encode({"version": 1, "workspace": selection})
    )
    (profile / ("web-profile-" + "a" * 32)).mkdir(mode=0o700)
    (profile / ("web-profile-" + "a" * 32) / "DO-NOT-COPY").write_bytes(
        b"private browser fixture"
    )
    (r11 / ".p6-gui-attempt").write_bytes(b"synthetic marked historical run")
    (r11 / "owner-result.json").write_bytes(
        core.encode({"status": "FAIL", "complete": True})
    )
    expected = copy.deepcopy(workspace.policy())
    expected["R11_marker_sha256"] = core.sha(r11 / ".p6-gui-attempt")
    expected["R11_result_sha256"] = core.sha(r11 / "owner-result.json")
    expected["R11_profile"] = workspace.snapshot(profile)
    summary = migration.inspect(source)
    expected["workspace"] = {
        "schema": 5,
        "counts": summary["counts"],
        "database_sha256": core.sha(source / "engage.sqlite3"),
        "content_fingerprint": migration.content_fingerprint(source),
        "asset_tree": workspace.snapshot(source / "assets"),
    }
    archive = root / "synthetic.zip"
    archive.write_bytes(b"synthetic identity fixture; no executable package")
    expected["B_entry"]["artifact_zip_sha256"] = core.sha(archive)
    approval = root / "approval.json"
    approval.write_bytes(
        core.encode(
            {
                "owner_approved_for_disposable_P6_update": True,
                "version": "0.1.0",
                "schema": 5,
                "entry": expected["B_entry"],
            }
        )
    )
    expected["B_approval_sha256"] = core.sha(approval)
    public = prepared / "b"
    public.mkdir(mode=0o700, parents=True)
    key = public / "staging-public.gpg"
    key.write_bytes(
        b"synthetic public key; cryptography mocked only in coordinator tests"
    )
    expected["public_key_sha256"] = core.sha(key)
    entry = expected["B_entry"]
    release = {
        "application_id": core.APP_ID,
        "version": "0.1.0",
        "source_commit": entry["source_commit"],
        "ci_run_id": entry["ci_run_id"],
        "ci_artifact_id": entry["artifact_id"],
        "bundle_sha256": entry["bundle_sha256"],
        "ostree_commit": entry["ostree_commit"],
        "architecture": "x86_64",
        "signing_fingerprint": expected["signing_fingerprint"],
        "p6_B_approval_sha256": expected["B_approval_sha256"],
        "runtime_lock": core.read_json(
            core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
        ),
    }
    (public / "release.json").write_bytes(core.encode(release))
    (prepared / ".p6-real-update").write_bytes(
        core.encode({"purpose": "disposable P6 real update"})
    )
    prepared_record = {
        "status": "PASS",
        "complete": True,
        "checks": {
            k: "PASS"
            for k in (
                "A_payload_audit_and_repository",
                "B_payload_audit",
                "disposable_signing_key_removed",
            )
        },
        "fingerprint": expected["signing_fingerprint"],
        "B": release,
    }
    (prepared / "prepared.json").write_bytes(core.encode(prepared_record))
    expected["prepared_sha256"] = core.sha(prepared / "prepared.json")
    return SimpleNamespace(
        root=root,
        prepared=prepared,
        r11=r11,
        attempt=attempt,
        archive=archive,
        approval=approval,
        expected=expected,
        profile=profile,
        source=source,
        selection=selection,
        db=db,
        note=note,
        asset=asset,
    )


def test_exact_source_copy_has_fresh_Qt_storage_and_retains_every_record(case):
    before = workspace.snapshot(case.profile)
    value = target.verify_inputs(
        case.prepared, case.r11, case.archive, case.approval, case.expected
    )
    assert value["status"] == "PASS"
    dest = case.root / "fresh/desktop"
    copied = workspace.copy_workspace(case.r11, dest, case.expected)
    assert copied["source_before"] == copied["source_after"] == before
    assert workspace.snapshot(case.profile) == before
    assert not list((dest / ("web-profile-" + "a" * 32)).iterdir())
    assert not list(dest.rglob("DO-NOT-COPY"))
    assert (
        dest / case.selection / "engage.sqlite3"
    ).read_bytes() == case.db.path.read_bytes()
    assert (
        workspace.validate_active(dest, case.expected, copied["workspace_identity"])[
            "status"
        ]
        == "PASS"
    )


@pytest.mark.parametrize(
    "field",
    [
        "source_commit",
        "ci_run_id",
        "artifact_id",
        "artifact_zip_sha256",
        "bundle_sha256",
        "ostree_commit",
        "authorization_ref",
    ],
)
def test_wrong_approval_identity_fails(case, field):
    value = core.read_json(case.approval)
    value["entry"][field] = "incorrect"
    case.approval.write_bytes(core.encode(value))
    with pytest.raises((core.Rejected, ValueError)):
        target.verify_inputs(
            case.prepared, case.r11, case.archive, case.approval, case.expected
        )


@pytest.mark.parametrize(
    "field",
    [
        "source_commit",
        "ci_run_id",
        "ci_artifact_id",
        "application_id",
        "version",
        "ostree_commit",
        "signing_fingerprint",
    ],
)
def test_wrong_prepared_release_identity_fails(case, field):
    public = case.prepared / "b/release.json"
    value = core.read_json(public)
    value[field] = "incorrect"
    public.write_bytes(core.encode(value))
    with pytest.raises(core.Rejected):
        target.verify_inputs(
            case.prepared, case.r11, case.archive, case.approval, case.expected
        )


@pytest.mark.parametrize(
    "object_name", ["archive", "approval", "prepared", "key", "R11"]
)
def test_missing_or_modified_approved_input_is_rejected(case, object_name):
    path = {
        "archive": case.archive,
        "approval": case.approval,
        "prepared": case.prepared / "prepared.json",
        "key": case.prepared / "b/staging-public.gpg",
        "R11": case.r11 / "owner-result.json",
    }[object_name]
    path.write_bytes(b"corrupt")
    with pytest.raises((core.Rejected, ValueError, KeyError)):
        target.verify_inputs(
            case.prepared, case.r11, case.archive, case.approval, case.expected
        )


@pytest.mark.parametrize(
    "bad",
    [
        "missing-db",
        "corrupt-db",
        "missing-image",
        "changed-image",
        "missing-note",
        "missing-folder",
        "future-schema",
    ],
)
def test_missing_or_corrupt_workspace_never_copies(case, bad):
    if bad == "missing-db":
        case.db.path.unlink()
    elif bad == "corrupt-db":
        case.db.path.write_bytes(b"invalid database")
    elif bad == "missing-image":
        (case.source / "assets" / case.asset["id"]).unlink()
    elif bad == "changed-image":
        (case.source / "assets" / case.asset["id"]).write_bytes(b"changed")
    else:
        with case.db.connect() as con:
            if bad == "missing-note":
                con.execute("DELETE FROM notes")
            elif bad == "missing-folder":
                con.execute("UPDATE notes SET folder_id=NULL")
                con.execute("DELETE FROM folders")
            else:
                con.execute("PRAGMA user_version=6")
    with pytest.raises((core.Rejected, ValueError, sqlite3.Error)):
        workspace.copy_workspace(case.r11, case.root / "fresh", case.expected)
    assert not (case.root / "fresh").exists()


@pytest.mark.parametrize(
    "selection", ["workspace", "../outside", "/outside", "workspaces/missing"]
)
def test_wrong_workspace_pointer_rejected_even_if_snapshot_reapproved(case, selection):
    (case.profile / "active-workspace.json").write_bytes(
        core.encode({"version": 1, "workspace": selection})
    )
    case.expected["R11_profile"] = workspace.snapshot(case.profile)
    with pytest.raises(core.Rejected):
        workspace.copy_workspace(case.r11, case.root / "fresh", case.expected)


@pytest.mark.parametrize(
    "bad", ["file-symlink", "dir-symlink", "hardlink", "permissions", "fifo"]
)
def test_unsafe_objects_rejected_without_following_them(case, bad):
    path = case.profile / "unsafe"
    if bad == "file-symlink":
        path.symlink_to(case.db.path)
    elif bad == "dir-symlink":
        path.symlink_to(case.source, target_is_directory=True)
    elif bad == "hardlink":
        os.link(case.db.path, path)
    elif bad == "permissions":
        case.db.path.chmod(0o644)
    else:
        os.mkfifo(path, 0o600)
    with pytest.raises(core.Rejected):
        workspace.snapshot(case.profile)


def test_busy_source_lock_is_not_created_or_overridden(case):
    import fcntl

    with (case.profile / ".instance.lock").open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            workspace.copy_workspace(case.r11, case.root / "fresh", case.expected)


def test_copy_interruption_keeps_source_and_partial_evidence(case, monkeypatch):
    before = workspace.snapshot(case.profile)

    def stop(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(shutil, "copytree", stop)
    with pytest.raises(KeyboardInterrupt):
        workspace.copy_workspace(case.r11, case.root / "fresh", case.expected)
    assert workspace.snapshot(case.profile) == before
    assert (case.root / "fresh").is_dir()


@pytest.mark.parametrize(
    "bad",
    [
        "existing",
        "normal-data",
        "inside-source",
        "nested-attempt",
        "traversal",
        "symlink",
    ],
)
def test_attempt_layout_never_reuses_or_targets_normal_data(case, bad):
    attempt = case.attempt
    if bad == "existing":
        attempt.mkdir()
        (attempt / "preserve").write_text("keep")
    elif bad == "normal-data":
        attempt = case.root / ".var/app" / core.APP_ID
    elif bad == "inside-source":
        attempt = core.ROOT / "targeted-b-attempt-bad"
    elif bad == "nested-attempt":
        attempt = case.r11 / "targeted-b-attempt-bad"
    elif bad == "traversal":
        attempt = case.root / ".." / case.root.name / case.attempt.name
    else:
        attempt.symlink_to(case.r11, target_is_directory=True)
    with pytest.raises(core.Rejected):
        target.layout(case.prepared, case.r11, attempt)
    if bad == "existing":
        assert (attempt / "preserve").read_text() == "keep"


def observe(probe, saved, identity, result):
    sample = {
        **saved,
        "selected": saved["appearance"] or "auto",
        "resolved": "light",
        "system_dark": False,
    }
    probe.observe(json.dumps(sample), result)
    if probe.first is probe.last:
        probe.before_owner(result, identity)


def child_result(config, required):
    result = {
        "status": "PASS",
        "complete": True,
        "workspace_identity": config["workspace_identity"],
        "checks": {k: "PASS" for k in required if k != "dark_preference_saved"},
    }
    probe = preference_contract.PreferenceContract(config)
    if config["mode"] == "reset":
        observe(
            probe,
            {"appearance": None, "theme": None},
            config["workspace_identity"],
            result,
        )
    observe(
        probe,
        {"appearance": "light", "theme": None},
        config["workspace_identity"],
        result,
    )
    probe.finish(result, config["workspace_identity"])
    return result


@pytest.fixture
def harness(case, monkeypatch):
    native_calls = []
    native = SimpleNamespace(
        root=case.attempt / "client", env={"HOME": "synthetic"}, operations=[]
    )

    def new_native(root, progress=None):
        root.mkdir(mode=0o700)
        (root / "home").mkdir(mode=0o700)
        return native

    def run_native(operation, *args):
        native_calls.append((operation, args))
        return ""

    native.run = Mock(side_effect=run_native)
    native.runtimes = Mock(return_value={"status": "PASS"})
    native.install_real = Mock(
        return_value={"status": "APP_IDENTITY_PASS_RUNTIME_DEFERRED"}
    )
    native.verify_summary = Mock()
    replay = SimpleNamespace(
        events=[], trusted=Mock(return_value={"commit_signature": "PASS"})
    )

    @contextlib.contextmanager
    def transaction(name):
        replay.events.append(
            {
                "operation": name,
                "validation": "PASS",
                "ordinary_runtime_compatible": False,
            }
        )
        yield

    replay.transaction = transaction
    monkeypatch.setattr(workspace, "policy", lambda: case.expected)
    monkeypatch.setattr(
        target.shutil, "disk_usage", lambda p: SimpleNamespace(free=10 * 1024**3)
    )
    monkeypatch.setattr(core, "extract_artifact", Mock(return_value={"status": "PASS"}))
    monkeypatch.setattr(target.native_distribution, "RuntimeClient", new_native)
    monkeypatch.setattr(target.real_update, "desktop_environment", lambda n: n.env)
    monkeypatch.setattr(target.historical_runtime, "Replay", lambda *args: replay)
    monkeypatch.setattr(
        target.historical_runtime, "probe", Mock(return_value={"status": "PASS"})
    )
    monkeypatch.setattr(target.distribution, "plan", Mock(return_value={}))
    monkeypatch.setattr(target.distribution, "publish", Mock())
    monkeypatch.setattr(
        target.trust, "verify_current_signature", Mock(return_value={"status": "PASS"})
    )
    monkeypatch.setattr(
        target.distribution,
        "loopback",
        lambda *args: contextlib.nullcontext("http://127.0.0.1:1/"),
    )
    monkeypatch.setattr(target, "installed", Mock(return_value={"status": "PASS"}))
    required = target.requirements().REQUIRED["updated"]
    real_phase = target.phase

    def successful_child(monitor, attempt, operation, command, *, env, script):
        # Execute pure observation contracts, not the native child or Qt.
        context = "post-import-baseline" if "restart" in command else "reinstall-b"
        base = next(native.root.glob("home/.var/app/*/data/p4-verification/*"))
        pointer = core.read_json(base / "desktop/active-workspace.json")["workspace"]
        import hashlib

        identity = {
            "workspace": hashlib.sha256(pointer.encode()).hexdigest(),
            "qt_profile": hashlib.sha256(
                ("web-profile-" + pointer.split("/")[1]).encode()
            ).hexdigest(),
        }
        if context == "post-import-baseline":
            config = {"mode": "reset", "workspace_identity": identity}
        else:
            config = preference_contract.preserve_config(
                core.read_json(attempt / "phase-post-import-baseline.json")
            )
        value = child_result(config, required)
        if getattr(native, "bad_check", None):
            value["checks"][native.bad_check] = "FAIL"
        (
            base
            / ("restart.json" if context == "post-import-baseline" else "updated.json")
        ).write_bytes(core.encode(value))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        target.native_diagnostics, "run", Mock(side_effect=successful_child)
    )
    return SimpleNamespace(
        case=case,
        native=native,
        calls=native_calls,
        replay=replay,
        real_phase=real_phase,
    )


def execute(harness):
    c = harness.case
    return target.run(
        c.prepared,
        c.r11,
        c.attempt,
        c.archive,
        c.approval,
        historical_runtime.COMMIT,
        target.AUTHORIZATION,
    )


def test_coordinator_runs_only_two_B_GUI_phases_with_immutable_baseline(harness):
    record = execute(harness)
    assert record["status"] == "PASS"
    assert record["GUI_launches_attempted"] == 2
    assert record["ordinary_runtime_update_compatibility"] is False
    assert record["generation_A_launch_attempted"] is False
    assert (
        record["data_before_uninstall"]
        == record["data_after_uninstall"]
        == record["data_after_reinstall"]
    )
    assert [e["operation"] for e in harness.replay.events] == [
        "install-b",
        "reinstall-b",
    ]
    assert not any("--delete-data" in args for _, args in harness.calls)
    assert (
        core.read_json(harness.case.attempt / "phase-post-import-baseline.json")[
            "preferences_snapshot"
        ]["appearance"]
        == "light"
    )
    assert (harness.case.attempt / "owner-result.json").is_file()


@pytest.mark.parametrize(
    "bad",
    [
        "renderer_sandbox",
        "backend_authentication_and_origin",
        "owned_backend_reaped",
        "single_instance_lock",
        "folder_saved",
        "screenshot_asset_saved",
        "required_title_saved",
        "production_identity_private_network_and_filesystem",
    ],
)
def test_every_native_data_and_security_failure_blocks_uninstall(harness, bad):
    harness.native.bad_check = bad
    record = execute(harness)
    assert record["status"] == "FAIL"
    assert record["GUI_launches_attempted"] == 1
    assert not any("uninstall" in args for _, args in harness.calls)


@pytest.mark.parametrize("where", ["uninstall", "reinstall"])
def test_private_data_changes_block_second_GUI(harness, where):
    original = harness.native.run.side_effect

    def change(operation, *args):
        original(operation, *args)
        if args[0] == ("uninstall" if where == "uninstall" else "install"):
            p = (
                next(harness.native.root.glob("home/.var/app/*/data/p4-verification/*"))
                / "unexpected"
            )
            p.write_bytes(b"changed")

    harness.native.run.side_effect = change
    record = execute(harness)
    assert record["status"] == "FAIL" and record["GUI_launches_attempted"] == 1


@pytest.mark.parametrize(
    "failure", ["signature", "imports", "installation", "interrupt"]
)
def test_failed_prelaunch_operation_preserves_complete_FAIL_record(
    harness, monkeypatch, failure
):
    error = (
        KeyboardInterrupt()
        if failure == "interrupt"
        else core.Rejected("synthetic fixed failure")
    )
    if failure == "signature":
        monkeypatch.setattr(target.distribution, "plan", Mock(side_effect=error))
    elif failure == "imports":
        monkeypatch.setattr(target.historical_runtime, "probe", Mock(side_effect=error))
    else:
        harness.native.install_real.side_effect = error
    record = execute(harness)
    assert record["status"] == "FAIL" and record["complete"] is True
    assert record["GUI_launches_attempted"] == 0
    assert (
        workspace.snapshot(harness.case.profile) == harness.case.expected["R11_profile"]
    )
    assert (
        core.read_json(harness.case.attempt / "owner-result.json")["complete"] is True
    )


def test_native_filesystem_failure_keeps_safe_child_stage_and_private_diagnostics(
    harness, monkeypatch
):
    def fail(monitor, attempt, operation, command, **kwargs):
        base = next(harness.native.root.glob("home/.var/app/*/data/p4-verification/*"))
        (base / "restart.json").write_bytes(
            core.encode(
                {
                    "stage": "post_close_profile_open",
                    "error_type": "FileNotFoundError",
                    "filesystem_failure": {
                        "errno": 2,
                        "path_category": "qt-web-profile",
                        "storage_frames": [
                            {"line": 60, "operation": "profile-scan-or-selection"}
                        ],
                    },
                }
            )
        )
        raise native_diagnostics.NativePhaseFailure(
            {
                "operation": operation,
                "exit_code": 1,
                "private_files": {"stderr": {"retained_sha256": "a" * 64}},
            }
        )

    monkeypatch.setattr(target.native_diagnostics, "run", fail)
    record = execute(harness)
    assert record["native_phase_failure"]["error_type"] == "FileNotFoundError"
    assert record["native_phase_failure"]["filesystem_failure"]["errno"] == 2
    assert record["native_subprocess_failure"]["private_files"]
    assert record["status"] == "FAIL"


def test_low_disk_stops_before_any_native_operation(harness, monkeypatch):
    monkeypatch.setattr(target.shutil, "disk_usage", lambda p: SimpleNamespace(free=1))
    record = execute(harness)
    assert record["status"] == "FAIL" and "5 GiB" in record["error"]
    harness.native.runtimes.assert_not_called()


def test_explicit_historical_and_targeted_authorizations_required(case):
    for runtime, authorization in [
        (None, target.AUTHORIZATION),
        ("f" * 64, target.AUTHORIZATION),
        (historical_runtime.COMMIT, "unapproved"),
    ]:
        with pytest.raises(core.Rejected):
            target.run(
                case.prepared,
                case.r11,
                case.attempt,
                case.archive,
                case.approval,
                runtime,
                authorization,
            )
        assert not case.attempt.exists()


def test_guarded_window_is_disabled_before_show_and_evidence_before_unlock():
    tree = ast.parse(
        (core.ROOT / "packaging/flatpak/production/native_check.py").read_text()
    )
    guarded = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and n.name == "GuardedWindow"
    )
    show = guarded.body[0]
    assert "setEnabled(False)" in ast.unparse(show.body[0])
    callback = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "preference"
    )
    text = ast.unparse(callback)
    assert (
        text.index("preferences.before_owner")
        < text.index("durable_json")
        < text.index("QMessageBox.information")
        < text.index("window.setEnabled(True)")
    )
    assert "if not valid:" in text and "self.quit" in text


@pytest.mark.parametrize(
    "bad",
    [
        "missing-System",
        "wrong-resolved",
        "wrong-selected",
        "wrong-Qt",
        "missing-Light",
        "reinstall-loss",
        "missing-gate",
    ],
)
def test_preinteraction_and_Light_contract_cannot_be_forged_by_later_selection(bad):
    identity = {"workspace": "a" * 64, "qt_profile": "b" * 64}
    config = {"mode": "reset", "workspace_identity": identity}
    if bad == "reinstall-loss":
        config = {
            **config,
            "mode": "preserve",
            "expected": {"appearance": "light", "theme": None},
        }
    probe = preference_contract.PreferenceContract(config)
    first = {
        "appearance": None,
        "theme": None,
        "selected": "auto",
        "resolved": "light",
        "system_dark": False,
    }
    if bad == "missing-System":
        first.update(appearance="dark", selected="dark", resolved="dark")
    if bad == "wrong-resolved":
        first["resolved"] = "dark"
    if bad == "wrong-selected":
        first["selected"] = "light"
    result = {
        "status": "PASS",
        "complete": True,
        "checks": {},
        "workspace_identity": identity,
    }
    probe.observe(json.dumps(first), result)
    if bad != "missing-gate":
        probe.before_owner(
            result,
            {**identity, "qt_profile": "c" * 64} if bad == "wrong-Qt" else identity,
        )
    if bad != "missing-Light":
        probe.observe(
            json.dumps(
                {
                    **first,
                    "appearance": "light",
                    "selected": "light",
                    "resolved": "light",
                }
            ),
            result,
        )
    probe.finish(result, identity)
    with pytest.raises(ValueError):
        preference_contract.validate_result(config, result)


@pytest.fixture
def installed_client(case):
    root = case.root / "verified-client"
    location = root / "flatpak/app/deployment"
    path = location / "files/share/cyrnava/build-inputs.json"
    path.parent.mkdir(mode=0o700, parents=True)
    inputs = {
        "app_id": core.APP_ID,
        "version": "0.1.0",
        "schema": 5,
        "runtime_lock": core.read_json(
            core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
        ),
    }
    path.write_bytes(core.encode(inputs))
    native = SimpleNamespace(
        root=root,
        commit=Mock(return_value=case.expected["B_entry"]["ostree_commit"]),
        verify_remote=Mock(return_value="p5c"),
        installed_source=Mock(),
    )

    def read(operation, *args):
        if operation == "location":
            return str(location)
        return (
            "[Context]\nshared=!network;\nsockets=wayland;\n"
            "filesystems=!home;!host;xdg-config/kdeglobals:ro;\ndevices=dri;\n"
        )

    native.run = Mock(side_effect=read)
    return SimpleNamespace(native=native, path=path, inputs=inputs)


def test_installed_identity_rechecks_source_schema_permissions_and_commit(
    case, installed_client
):
    assert target.installed(installed_client.native, case.expected)["status"] == "PASS"
    installed_client.native.installed_source.assert_called_once_with(
        case.expected["B_entry"]["source_commit"]
    )


@pytest.mark.parametrize(
    "bad",
    [
        "commit",
        "source",
        "origin",
        "application",
        "version",
        "schema",
        "runtime-lock",
        "permissions",
        "location",
    ],
)
def test_any_installed_identity_or_permission_mismatch_rejected(
    case, installed_client, bad
):
    n = installed_client.native
    if bad == "commit":
        n.commit.return_value = "f" * 64
    elif bad == "source":
        n.installed_source.side_effect = core.Rejected("wrong source")
    elif bad == "origin":
        n.verify_remote.return_value = "unexpected"
    elif bad == "permissions":
        n.run.side_effect = lambda operation, *args: (
            str(installed_client.path.parents[3])
            if operation == "location"
            else "[Context]\nshared=network;\nfilesystems=host;\n"
        )
    elif bad == "location":
        n.run.return_value = str(case.root / "outside")
        n.run.side_effect = None
    else:
        field = {"application": "app_id", "runtime-lock": "runtime_lock"}.get(bad, bad)
        installed_client.inputs[field] = "incorrect"
        installed_client.path.write_bytes(core.encode(installed_client.inputs))
    with pytest.raises(ValueError):
        target.installed(n, case.expected)


def test_missing_live_baseline_file_blocks_uninstall(harness, monkeypatch):
    original = target.phase

    def missing(*args, **kwargs):
        result = original(*args, **kwargs)
        (harness.case.attempt / "phase-post-import-baseline.json").unlink()
        return result

    monkeypatch.setattr(target, "phase", missing)
    record = execute(harness)
    assert record["status"] == "FAIL"
    assert not any("uninstall" in args for _, args in harness.calls)


def test_invalid_runtime_signature_before_first_GUI_prevents_child_execution(harness):
    harness.replay.trusted.side_effect = core.Rejected("synthetic invalid signature")
    record = execute(harness)
    assert record["status"] == "FAIL" and record["GUI_launches_attempted"] == 0
    target.native_diagnostics.run.assert_not_called()


def test_repeated_invocation_preserves_first_attempt_without_native_retry(harness):
    first = execute(harness)
    path = harness.case.attempt / "owner-result.json"
    digest = core.sha(path)
    with pytest.raises(core.Rejected):
        execute(harness)
    assert core.sha(path) == digest
    assert first["status"] == "PASS"
    assert harness.native.install_real.call_count == 1


def test_import_probes_keep_separate_before_and_after_evidence(harness):
    record = execute(harness)
    assert record["status"] == "PASS"
    calls = target.historical_runtime.probe.call_args_list
    assert len(calls) == 2
    assert calls[0].args[2] != calls[1].args[2]
    assert calls[0].args[2].name == "imports-before-baseline"
    assert calls[1].args[2].name == "imports-after-reinstall"


@pytest.mark.parametrize("name", ["install-b", "reinstall-b"])
@pytest.mark.parametrize(
    "bad",
    [
        "missing-authorization",
        "wrong-restored-commit",
        "signature",
        "restoration",
        "post-restore-drift",
    ],
)
def test_real_historical_guard_fails_closed_for_targeted_transactions(case, name, bad):
    # Exercise the actual historical control flow with simulated native effects.
    replay = historical_runtime.Replay(
        Mock(),
        case.root,
        None if bad == "missing-authorization" else historical_runtime.COMMIT,
    )
    replay.snapshot = Mock(
        side_effect=[
            historical_runtime.COMMIT,
            "f" * 64,
            "e" * 64 if bad == "wrong-restored-commit" else historical_runtime.COMMIT,
        ]
    )
    replay.origin_policy = Mock(return_value={"signature_enforcement": "PASS"})
    replay.trusted = Mock(
        side_effect=core.Rejected("synthetic signature or drift failure")
        if bad in {"signature", "post-restore-drift"}
        else None
    )
    if bad == "restoration":
        replay.native.command.side_effect = core.Rejected("synthetic restore failure")
    with pytest.raises(core.Rejected):
        with replay.transaction(name):
            pass
    assert replay.events[0]["validation"] == "FAIL"
    assert replay.events[0]["ordinary_runtime_compatible"] is False
    if bad == "missing-authorization":
        replay.native.command.assert_not_called()


@pytest.mark.parametrize("system_dark", [False, True])
def test_initial_System_option_and_resolved_OS_state_are_recorded_before_input(
    system_dark,
):
    identity = {"workspace": "a" * 64, "qt_profile": "b" * 64}
    probe = preference_contract.PreferenceContract(
        {"mode": "reset", "workspace_identity": identity}
    )
    sample = {
        "appearance": None,
        "theme": None,
        "selected": "auto",
        "system_dark": system_dark,
        "resolved": "dark" if system_dark else "light",
    }
    probe.observe(json.dumps(sample), {})
    record = {"checks": {}}
    assert probe.before_owner(record, identity)
    assert record["initial_appearance_observation"] == sample
    assert record["live_workspace_identity"] == identity


def test_no_observation_never_unblocks_owner_input():
    probe = preference_contract.PreferenceContract(
        {
            "mode": "reset",
            "workspace_identity": {"workspace": "a" * 64, "qt_profile": "b" * 64},
        }
    )
    assert not probe.before_owner({"checks": {}}, probe.config["workspace_identity"])


def test_snapshot_keeps_retained_component_order_for_Qt_profile_prefixes(tmp_path):
    import hashlib

    root = tmp_path / "profile"
    root.mkdir(mode=0o700)
    for name in ("web-profile/Preferences", "web-profile-abc/Preferences"):
        path = root / name
        path.parent.mkdir(mode=0o700)
        path.write_bytes(b"synthetic")
        path.chmod(0o600)
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(root)).encode())
            h.update(core.sha(path).encode())
    assert workspace.snapshot(root)["tree_sha256"] == h.hexdigest()


def test_key_expiry_after_baseline_stops_before_uninstall(harness):
    target.trust.verify_current_signature.side_effect = core.Rejected(
        "Expired signing identity"
    )
    record = execute(harness)
    assert record["status"] == "FAIL" and record["GUI_launches_attempted"] == 1
    assert not any("uninstall" in args for _, args in harness.calls)


def test_reselecting_Light_after_observed_loss_does_not_repair_second_phase():
    identity = {"workspace": "a" * 64, "qt_profile": "b" * 64}
    config = {
        "mode": "preserve",
        "workspace_identity": identity,
        "expected": {"appearance": "light", "theme": None},
    }
    probe = preference_contract.PreferenceContract(config)
    result = {"checks": {}, "workspace_identity": identity}
    light = {
        "appearance": "light",
        "theme": None,
        "selected": "light",
        "resolved": "light",
        "system_dark": False,
    }
    probe.observe(json.dumps(light), result)
    assert probe.before_owner(result, identity)
    probe.observe(json.dumps({**light, "appearance": None, "selected": "auto"}), result)
    probe.observe(json.dumps(light), result)
    probe.finish(result, identity)
    assert result["checks"]["imported_preferences_preserved"] == "FAIL"
    with pytest.raises(ValueError):
        preference_contract.validate_result(config, result)


def test_empty_directory_loss_also_fails_complete_tree_guard(case):
    before = workspace.data_state(case.profile)
    empty = case.profile / "empty-cache"
    empty.mkdir(mode=0o700)
    after = workspace.data_state(case.profile)
    assert before["tree_sha256"] == after["tree_sha256"]
    assert before["directory_tree_sha256"] != after["directory_tree_sha256"]


def test_world_writable_artifact_is_rejected_despite_matching_bytes(case):
    case.archive.chmod(0o666)
    with pytest.raises(core.Rejected, match="permissions"):
        target.verify_inputs(
            case.prepared, case.r11, case.archive, case.approval, case.expected
        )


def test_historical_transaction_allowlist_preserves_original_six_plus_initial_B():
    assert historical_runtime.TRANSACTIONS == {
        "install-a",
        "probe-update-b",
        "probe-rollback-a",
        "update-b",
        "rollback-a",
        "reinstall-b",
        "install-b",
    }
