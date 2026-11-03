"""P6 preference boundaries; synthetic samples, no Qt, native client or GUI."""

import ast
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preference_contract as contract

OLD = {"workspace": "a" * 64, "qt_profile": "b" * 64}
NEW = {"workspace": "c" * 64, "qt_profile": "d" * 64}
EMPTY = {"appearance": None, "theme": None}
LIGHT = {"appearance": "light", "theme": None}
DARK = {"appearance": "dark", "theme": None}


def reset():
    return contract.reset_config(
        {
            "status": "PASS",
            "complete": True,
            "checks": {"import_activated_new_workspace": "PASS"},
            "previous_workspace_identity": OLD,
            "workspace_identity": NEW,
        },
        {
            "status": "PASS",
            "complete": True,
            "checks": {"dark_preference_saved": "PASS"},
            "workspace_identity": OLD,
        },
    )


def observe(probe, saved, *, system_dark=False, resolved=None):
    probe.observe(
        json.dumps(
            {
                **saved,
                "system_dark": system_dark,
                "resolved": resolved
                or ("dark" if saved == DARK or system_dark else "light"),
            }
        ),
        {},
    )


def finish(probe, workspace=NEW):
    result = {
        "status": "PASS",
        "complete": True,
        "checks": {},
        "workspace_identity": workspace,
    }
    probe.finish(result, workspace)
    return result


def baseline():
    probe = contract.PreferenceContract(reset())
    observe(probe, EMPTY)
    observe(probe, LIGHT)
    result = finish(probe)
    contract.validate_result(reset(), result)
    return result


def test_retained_R11_hashes_distinguish_Dark_from_absent_override():
    assert (
        contract.digest(DARK)
        == "70992515ae26d5f17712ddff6e52182309267109d0eb035fce68d6c884bfca85"
    )
    assert (
        contract.digest(EMPTY)
        == "6c70b52b441be65cbbcbaf8b798a9127ac0ca4195d4684a175fcb607fd95f3fa"
    )
    assert contract.digest(DARK) != contract.digest(EMPTY)


@pytest.mark.parametrize("system_dark", [False, True])
def test_import_observes_System_then_requires_new_Light_preference(system_dark):
    probe = contract.PreferenceContract(reset())
    observe(probe, EMPTY, system_dark=system_dark)
    observe(probe, LIGHT, resolved="light", system_dark=system_dark)
    result = finish(probe)
    contract.validate_result(reset(), result)
    assert all(value == "PASS" for value in result["checks"].values())
    assert "dark_preference_saved" not in result["checks"]
    assert result["initial_preferences_snapshot"] == EMPTY
    assert result["preferences_snapshot"] == LIGHT


@pytest.mark.parametrize("first", [DARK, LIGHT, {"appearance": "auto", "theme": None}])
def test_import_does_not_falsely_claim_a_reset(first):
    probe = contract.PreferenceContract(reset())
    observe(probe, first)
    observe(probe, LIGHT)
    result = finish(probe)
    assert result["checks"]["post_import_preference_reset"] == "FAIL"
    with pytest.raises(ValueError):
        contract.validate_result(reset(), result)


def test_import_without_owner_chosen_preference_cannot_supply_reinstall_baseline():
    probe = contract.PreferenceContract(reset())
    observe(probe, EMPTY)
    result = finish(probe)
    assert result["checks"]["post_import_new_preference_saved"] == "FAIL"
    with pytest.raises(ValueError):
        contract.preserve_config(result)


def test_new_imported_preference_persists_during_reinstall():
    config = contract.preserve_config(baseline())
    probe = contract.PreferenceContract(config)
    observe(probe, LIGHT)
    observe(probe, LIGHT)
    result = finish(probe)
    contract.validate_result(config, result)
    assert result["checks"]["imported_preferences_preserved"] == "PASS"


@pytest.mark.parametrize("lost_at", ["first", "last", "both"])
def test_unexpected_preference_loss_on_reinstall_fails(lost_at):
    config = contract.preserve_config(baseline())
    probe = contract.PreferenceContract(config)
    observe(probe, EMPTY if lost_at in {"first", "both"} else LIGHT)
    observe(probe, EMPTY if lost_at in {"last", "both"} else LIGHT)
    result = finish(probe)
    assert result["checks"]["imported_preferences_preserved"] == "FAIL"
    with pytest.raises(ValueError):
        contract.validate_result(config, result)


def test_incorrect_DOM_resolution_is_not_accepted_as_System():
    probe = contract.PreferenceContract(reset())
    observe(probe, EMPTY, system_dark=True, resolved="light")
    observe(probe, LIGHT)
    result = finish(probe)
    assert result["checks"]["appearance_preference_valid"] == "FAIL"
    with pytest.raises(ValueError):
        contract.validate_result(reset(), result)


@pytest.mark.parametrize(
    "sample", ["{}", "not-json", '"dark"', '{"appearance":"SECRET"}']
)
def test_malformed_observation_fails_even_after_later_valid_sample(sample):
    probe = contract.PreferenceContract(reset())
    probe.observe(sample, {})
    observe(probe, EMPTY)
    observe(probe, LIGHT)
    result = finish(probe)
    assert result["checks"]["appearance_preference_valid"] == "FAIL"
    assert "SECRET" not in json.dumps(result)


def test_cancelled_callback_retains_last_valid_sample():
    probe = contract.PreferenceContract(reset())
    observe(probe, EMPTY)
    observe(probe, LIGHT)
    probe.observe(None, {})
    assert finish(probe)["preferences_snapshot"] == LIGHT


def test_missing_sample_fails():
    result = finish(contract.PreferenceContract(reset()))
    assert result["checks"]["appearance_preference_valid"] == "FAIL"


def test_same_workspace_or_Qt_profile_cannot_authorize_reset():
    for key in OLD:
        config = reset()
        maintenance = {
            "status": "PASS",
            "complete": True,
            "checks": {"import_activated_new_workspace": "PASS"},
            "previous_workspace_identity": OLD,
            "workspace_identity": {**config["workspace_identity"], key: OLD[key]},
        }
        edited = {
            "status": "PASS",
            "complete": True,
            "checks": {"dark_preference_saved": "PASS"},
            "workspace_identity": OLD,
        }
        with pytest.raises(ValueError, match="separate workspace and Qt profile"):
            contract.reset_config(maintenance, edited)


def test_preference_baseline_cannot_be_used_with_different_workspace():
    config = contract.preserve_config(baseline())
    probe = contract.PreferenceContract(config)
    observe(probe, LIGHT)
    result = finish(probe, OLD)
    assert result["checks"]["imported_workspace_bound"] == "FAIL"
    with pytest.raises(ValueError):
        contract.validate_result(config, result)


@pytest.mark.parametrize(
    "field",
    [
        "status",
        "checks",
        "preferences_sha256",
        "preference_policy",
        "initial_preferences_snapshot",
    ],
)
def test_invalid_or_unverified_baseline_rejected(field):
    value = baseline()
    value.pop(field)
    with pytest.raises(ValueError):
        contract.preserve_config(value)


def test_stream_wrapper_calls_only_explicit_test_hook():
    original = b"""def main(*, preferences=None):
    assert preferences.config["mode"] == "reset"
    return 7
if __name__ == "__main__":
    raise AssertionError("legacy main guard must not execute")
"""
    wrapped = contract.script(original, reset())
    with pytest.raises(SystemExit) as caught:
        exec(compile(wrapped, "synthetic-p6-wrapper", "exec"), {})  # noqa: S102 - synthetic trusted verifier
    assert caught.value.code == 7


def test_P4_default_remains_strict_Dark_and_has_no_environment_bypass():
    source = (
        Path(__file__).resolve().parents[2]
        / "packaging/flatpak/production/native_check.py"
    )
    tree = ast.parse(source.read_text())
    function = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "preference_state"
    )
    scope = {"json": json, "hashlib": hashlib}
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), "legacy-P4", "exec"),
        scope,
    )  # noqa: S102 - trusted isolated pure function
    assert (
        scope["preference_state"](json.dumps(DARK))[0]["dark_preference_saved"]
        == "PASS"
    )
    assert (
        scope["preference_state"](json.dumps(EMPTY))[0]["dark_preference_saved"]
        == "FAIL"
    )
    main = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"
    )
    assert main.args.kwonlyargs[0].arg == "preferences"
    assert (
        isinstance(main.args.kw_defaults[0], ast.Constant)
        and main.args.kw_defaults[0].value is None
    )
    assert "getenv" not in ast.unparse(main)


def test_workspace_binding_hashes_separate_Qt_profiles_without_private_paths():
    source = (
        Path(__file__).resolve().parents[2]
        / "packaging/flatpak/production/native_check.py"
    )
    tree = ast.parse(source.read_text())
    function = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "workspace_identity"
    )
    scope = {"hashlib": hashlib}
    exec(
        compile(
            ast.Module(body=[function], type_ignores=[]), "P4-workspace-binding", "exec"
        ),
        scope,
    )  # noqa: S102 - trusted pure helper
    root = Path("/PRIVATE/profile")
    old = scope["workspace_identity"](
        SimpleNamespace(root=root, selection="workspace", qt=root / "web-profile")
    )
    new = scope["workspace_identity"](
        SimpleNamespace(
            root=root,
            selection="workspaces/" + "a" * 32,
            qt=root / ("web-profile-" + "a" * 32),
        )
    )
    assert all(old[k] != new[k] for k in old)
    assert "PRIVATE" not in json.dumps([old, new])
