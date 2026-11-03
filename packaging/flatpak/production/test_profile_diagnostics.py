"""Host verifier diagnostics only; synthetic profiles and no Qt/application launch."""

import ast
import errno
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path[:0] = [
    str(Path(__file__).resolve().parents[3] / "backend"),
    str(Path(__file__).resolve().parents[3]),
]
from app.migration import durable_json  # noqa: E402 - repository test bootstrap

from desktop.native import storage  # noqa: E402 - repository test bootstrap

HERE = Path(__file__).resolve().parent


def helpers():
    tree = ast.parse((HERE / "native_check.py").read_text())
    names = {"profile_filesystem_failure", "checked_profile"}
    selected = ast.Module(
        body=[
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names
        ],
        type_ignores=[],
    )
    scope = {"Path": Path, "Profile": storage.Profile, "durable_json": durable_json}
    exec(compile(selected, "p4-profile-diagnostics", "exec"), scope)  # noqa: S102 - trusted internal functions, no native imports
    return scope


def test_stage_is_persisted_before_profile_construction_fails(tmp_path):
    scope = helpers()
    result = {"status": "FAIL", "checks": {"owned_backend_reaped": "PASS"}}
    record = tmp_path / "phase.json"

    def missing(root):
        assert json.loads(record.read_text())["stage"] == "post_close_profile_open"
        raise FileNotFoundError(errno.ENOENT, "SECRET message", str(root / "SECRET"))

    scope["Profile"] = missing
    with pytest.raises(FileNotFoundError):
        scope["checked_profile"](tmp_path, result, record, "post_close_profile_open")
    assert result["checks"]["owned_backend_reaped"] == "PASS"
    assert "SECRET" not in record.read_text()


@pytest.mark.parametrize(
    ("relative", "category"),
    [
        ("web-profile/SECRET", "qt-web-profile"),
        ("web-profile-" + "a" * 32 + "/SECRET", "qt-web-profile"),
        ("web-cache/SECRET", "qt-web-cache"),
        ("workspace/SECRET", "workspace-storage"),
        ("workspaces/SECRET", "workspace-storage"),
        ("active-workspace.json", "workspace-pointer"),
        (".instance.lock", "instance-lock"),
        ("desktop.json", "desktop-configuration"),
        ("SECRET", "other-profile-entry"),
    ],
)
def test_missing_path_is_classified_without_exposing_contents(
    tmp_path, relative, category
):
    scope = helpers()
    error = FileNotFoundError(errno.ENOENT, "PRIVATE SECRET", str(tmp_path / relative))
    details = scope["profile_filesystem_failure"](error, tmp_path)
    assert details["path_category"] == category
    assert details["errno"] == errno.ENOENT
    assert "SECRET" not in json.dumps(details)
    assert str(tmp_path) not in json.dumps(details)


def test_outside_and_missing_filename_do_not_expose_paths(tmp_path):
    scope = helpers()
    error = FileNotFoundError(errno.ENOENT, "PRIVATE", "/PRIVATE/SECRET")
    details = scope["profile_filesystem_failure"](error, tmp_path)
    assert details["path_category"] == "outside-profile"
    assert "PRIVATE" not in json.dumps(details)
    details = scope["profile_filesystem_failure"](OSError("SECRET"), tmp_path)
    assert details == {
        "errno": None,
        "path_category": "unavailable",
        "storage_frames": [],
    }


def test_disappearing_Qt_file_reproduces_storage_stat_error_without_suppressing_it(
    tmp_path,
):
    # Reproduce a plausible race; this does not establish historical R9 causality.
    scope = helpers()
    root = tmp_path / "profile"
    profile = storage.Profile(root)
    profile.close()
    transient = root / "web-profile/SECRET-transient"
    transient.write_bytes(b"synthetic")
    original_walk = storage.os.walk

    def disappear(*args, **kwargs):
        for directory, dirs, files in original_walk(*args, **kwargs):
            if Path(directory) == transient.parent and transient.name in files:
                transient.unlink()
            yield directory, dirs, files

    with (
        patch.object(storage.os, "walk", side_effect=disappear),
        pytest.raises(FileNotFoundError) as caught,
    ):
        scope["checked_profile"](
            root, {}, tmp_path / "result.json", "post_close_profile_open"
        )
    details = scope["profile_filesystem_failure"](caught.value, root)
    assert details["path_category"] == "qt-web-profile"
    assert details["storage_frames"][-1]["operation"] == "profile-scan-or-selection"
    assert details["storage_frames"][-1]["line"] > 0
    assert "SECRET" not in json.dumps(details)
    # Existing lock-release behavior remains effective after failure.
    reopened = storage.Profile(root)
    reopened.close()


def test_open_private_failure_has_allowlisted_operation_and_line(tmp_path):
    scope = helpers()
    error = PermissionError(errno.EACCES, "SECRET", str(tmp_path / "desktop.json"))
    with (
        patch.object(storage.os, "open", side_effect=error),
        pytest.raises(PermissionError) as caught,
    ):
        storage.open_private(tmp_path / "desktop.json")
    details = scope["profile_filesystem_failure"](caught.value, tmp_path)
    assert details["storage_frames"][-1]["operation"] == "private-file-open"
    assert details["path_category"] == "desktop-configuration"
    assert "SECRET" not in json.dumps(details)


def test_checked_profile_does_not_accept_unsafe_storage(tmp_path):
    scope = helpers()
    root = tmp_path / "profile"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("untouched")
    (root / "desktop.json").symlink_to(outside)
    with pytest.raises(ValueError):
        scope["checked_profile"](
            root, {}, tmp_path / "result.json", "post_close_profile_open"
        )
    assert outside.read_text() == "untouched"


def test_native_checker_uses_named_boundaries_for_all_reopens():
    tree = ast.parse((HERE / "native_check.py").read_text())
    main = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"
    )
    assert not any(
        isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "profile" for t in n.targets)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name)
        and n.value.func.id == "Profile"
        for n in ast.walk(main)
    )
    stages = {
        n.args[-1].value
        for n in ast.walk(main)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "checked_profile"
    }
    assert stages == {
        "maintenance_profile_open_before_manager",
        "maintenance_profile_open_after_manager",
        "recovery_profile_open",
        "post_close_profile_open",
    }
