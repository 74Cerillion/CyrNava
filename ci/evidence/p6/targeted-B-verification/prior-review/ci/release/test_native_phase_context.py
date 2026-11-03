"""Preserve the first update PASS and distinguish a later reinstall failure."""

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import preference_contract

OLD = {"workspace": "a" * 64, "qt_profile": "b" * 64}
NEW = {"workspace": "c" * 64, "qt_profile": "d" * 64}
LIGHT = {"appearance": "light", "theme": None}
DARK = {"appearance": "dark", "theme": None}


def phase_scope(tmp_path):
    source = Path(__file__).with_name("real_update.py")
    tree = ast.parse(source.read_text())
    exercise = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "exercise"
    )
    phase = next(
        n for n in exercise.body if isinstance(n, ast.FunctionDef) and n.name == "phase"
    )
    data = tmp_path / "data"
    data.mkdir()
    state = {
        "status": "PASS",
        "complete": True,
        "checks": {"saved": "PASS", "dark_preference_saved": "PASS"},
        "preferences_sha256": preference_contract.digest(DARK),
        "workspace_identity": OLD,
    }
    (data / "updated.json").write_bytes(core.encode(state))
    (data / "edit.json").write_bytes(core.encode(state))
    diagnostics = Mock()
    diagnostics.run.return_value = subprocess.CompletedProcess([], 0)
    native = Mock()
    native.verify_runtime.return_value = {"status": "PASS", "commit": "a" * 64}
    scope = {
        "record": {"checks": {}},
        "native": native,
        "path": core.ROOT / "packaging/flatpak/production/host_verify.py",
        "os": os,
        "core": core,
        "hashlib": hashlib,
        "preference_contract": preference_contract,
        "run_id": "run-" + "a" * 12,
        "canary": tmp_path / "canary",
        "native_diagnostics": diagnostics,
        "monitor": Mock(),
        "attempt": tmp_path,
        "env": {},
        "data": data,
        "requirements": SimpleNamespace(
            REQUIRED={"updated": {"saved", "dark_preference_saved"}}
        ),
    }
    exec(
        compile(ast.Module(body=[phase], type_ignores=[]), "p6-phase-context", "exec"),
        scope,
    )  # noqa: S102 - actual trusted phase logic; native child mocked
    return scope


def imported_baseline(scope):
    config = {"mode": "reset", "workspace_identity": NEW}
    probe = preference_contract.PreferenceContract(config)
    for state in ({"appearance": None, "theme": None}, LIGHT):
        probe.observe(
            json.dumps({**state, "resolved": "light", "system_dark": False}), {}
        )
    result = {
        "status": "PASS",
        "complete": True,
        "checks": {"saved": "PASS"},
        "workspace_identity": NEW,
    }
    probe.finish(result, NEW)
    (scope["attempt"] / "phase-post-import-baseline.json").write_bytes(
        core.encode(result)
    )
    return result


def reinstall_child(scope):
    config = preference_contract.preserve_config(imported_baseline(scope))
    probe = preference_contract.PreferenceContract(config)
    probe.observe(json.dumps({**LIGHT, "resolved": "light", "system_dark": False}), {})
    result = {
        "status": "PASS",
        "complete": True,
        "checks": {"saved": "PASS"},
        "workspace_identity": NEW,
    }
    probe.finish(result, NEW)
    (scope["data"] / "updated.json").write_bytes(core.encode(result))
    return result


def test_later_reinstall_record_does_not_overwrite_successful_update(tmp_path):
    scope = phase_scope(tmp_path)
    scope["phase"]("updated", "synthetic update")
    first = (tmp_path / "phase-updated.json").read_bytes()
    reinstall_child(scope)
    scope["phase"]("updated", "synthetic reinstall", context="reinstall-b")
    assert (tmp_path / "phase-updated.json").read_bytes() == first
    assert (
        json.loads((tmp_path / "phase-reinstall-b.json").read_text())["status"]
        == "PASS"
    )
    assert [x["context"] for x in scope["record"]["completed_native_phases"]] == [
        "updated",
        "reinstall-b",
    ]


def test_reinstall_failure_retains_prior_PASS_and_exact_active_context(tmp_path):
    scope = phase_scope(tmp_path)
    scope["phase"]("updated", "synthetic update")
    first = (tmp_path / "phase-updated.json").read_bytes()
    imported_baseline(scope)
    scope["native_diagnostics"].run.side_effect = core.Rejected(
        "synthetic child failure"
    )
    with pytest.raises(core.Rejected):
        scope["phase"]("updated", "synthetic reinstall", context="reinstall-b")
    assert scope["record"]["active_native_phase"] == {
        "phase": "updated",
        "context": "reinstall-b",
    }
    assert len(scope["record"]["completed_native_phases"]) == 1
    assert (tmp_path / "phase-updated.json").read_bytes() == first
    assert not (tmp_path / "phase-reinstall-b.json").exists()


@pytest.mark.parametrize("name", ["restart", "updated", "rollback"])
def test_normal_phase_still_requires_original_preference_hash(tmp_path, name):
    scope = phase_scope(tmp_path)
    scope["requirements"].REQUIRED[name] = {"saved", "dark_preference_saved"}
    state = json.loads((scope["data"] / "updated.json").read_text())
    state["preferences_sha256"] = preference_contract.digest(LIGHT)
    (scope["data"] / (name + ".json")).write_bytes(core.encode(state))
    with pytest.raises(core.Rejected, match="Preferences changed"):
        scope["phase"](name, "synthetic normal persistence")
    assert "completed_native_phases" not in scope["record"]


def test_reinstall_without_verified_import_baseline_stops_before_child(tmp_path):
    scope = phase_scope(tmp_path)
    with pytest.raises(FileNotFoundError):
        scope["phase"]("updated", "synthetic reinstall", context="reinstall-b")
    scope["native_diagnostics"].run.assert_not_called()


def test_reinstall_preserves_all_other_assertions_and_rejects_failed_Dark(tmp_path):
    scope = phase_scope(tmp_path)
    state = reinstall_child(scope)
    state["checks"]["dark_preference_saved"] = "FAIL"
    (scope["data"] / "updated.json").write_bytes(core.encode(state))
    with pytest.raises(core.Rejected, match="Native synthetic phase failed"):
        scope["phase"]("updated", "synthetic reinstall", context="reinstall-b")


def test_missing_content_assertion_still_blocks_reinstall(tmp_path):
    scope = phase_scope(tmp_path)
    state = reinstall_child(scope)
    state["checks"].pop("saved")
    (scope["data"] / "updated.json").write_bytes(core.encode(state))
    with pytest.raises(core.Rejected, match="Native synthetic phase failed"):
        scope["phase"]("updated", "synthetic reinstall", context="reinstall-b")


def test_post_import_baseline_executes_after_recovery_and_before_uninstall():
    tree = ast.parse(Path(__file__).with_name("real_update.py").read_text())
    calls = sorted(
        (n.lineno, n)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "phase"
    )
    contexts = [
        (
            n.args[0].value,
            next((k.value.value for k in n.keywords if k.arg == "context"), None),
        )
        for _, n in calls
    ]
    assert contexts[-3:] == [
        ("recovery", None),
        ("restart", "post-import-baseline"),
        ("updated", "reinstall-b"),
    ]
    baseline_line = calls[-2][0]
    uninstall = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "run"
        and len(n.args) > 1
        and isinstance(n.args[1], ast.Constant)
        and n.args[1].value == "uninstall"
    )
    assert baseline_line < uninstall.lineno < calls[-1][0]
