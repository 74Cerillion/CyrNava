"""Preserve the first update PASS and distinguish a later reinstall failure."""

import ast
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
        "checks": {"saved": "PASS"},
        "preferences_sha256": "a" * 64,
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
        "run_id": "run-" + "a" * 12,
        "canary": tmp_path / "canary",
        "native_diagnostics": diagnostics,
        "monitor": Mock(),
        "attempt": tmp_path,
        "env": {},
        "data": data,
        "requirements": SimpleNamespace(REQUIRED={"updated": {"saved"}}),
    }
    exec(
        compile(ast.Module(body=[phase], type_ignores=[]), "p6-phase-context", "exec"),
        scope,
    )  # noqa: S102 - actual trusted phase logic; native child mocked
    return scope


def test_later_reinstall_record_does_not_overwrite_successful_update(tmp_path):
    scope = phase_scope(tmp_path)
    scope["phase"]("updated", "synthetic update")
    first = (tmp_path / "phase-updated.json").read_bytes()
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
