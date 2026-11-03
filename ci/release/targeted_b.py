"""Explicit P6 B-only post-import/reinstall verification; owner execution only.

Uses existing signed B, never creates keys, prepares A/B, or alters retained R11.
No native action occurs on import. Local tests replace all native operations.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
from pathlib import Path
from uuid import uuid4

import core
import distribution
import historical_runtime
import native_diagnostics
import native_distribution
import preference_contract
import progress
import real_update
import targeted_workspace as workspace
import trust

AUTHORIZATION = "P6-owner-authorized-targeted-B-only"


def layout(prepared, r11, attempt):
    prepared, r11, attempt = map(core.outside_source, (prepared, r11, attempt))
    core.require(
        prepared.name == "real-pair-r2"
        and r11.name == "historical-gui-attempt-r11"
        and prepared.parent == r11.parent == attempt.parent
        and re.fullmatch(r"targeted-b-attempt-[a-z0-9-]+", attempt.name)
        and not attempt.exists(),
        "Fresh targeted-b attempt beside approved r2/R11 is required",
    )
    return prepared, r11, attempt


def verify_inputs(prepared, r11, archive, approval, expected):
    workspace.private_object(prepared, True)
    workspace.private_object(core.safe_path(approval))
    archive_info = core.safe_path(archive).lstat()
    core.require(
        stat.S_ISREG(archive_info.st_mode)
        and archive_info.st_uid == os.getuid()
        and archive_info.st_nlink == 1
        and stat.S_IMODE(archive_info.st_mode) in {0o600, 0o644, 0o664},
        "Unsafe public artifact object or permissions",
    )
    core.require(
        expected["app_id"] == core.APP_ID
        and expected["version"] == "0.1.0"
        and expected["schema"] == 5,
        "Targeted application policy mismatch",
    )
    entry = real_update.approved_b(approval)
    core.require(
        entry == expected["B_entry"]
        and core.sha(core.safe_path(approval)) == expected["B_approval_sha256"]
        and core.sha(core.safe_path(archive)) == entry["artifact_zip_sha256"],
        "Approved B identity, approval or ZIP changed",
    )
    core.require(
        core.sha(core.safe_path(prepared / "prepared.json"))
        == expected["prepared_sha256"],
        "Signed preparation record changed",
    )
    value = core.read_json(prepared / "prepared.json")
    core.require(
        core.read_json(prepared / ".p6-real-update")
        == {"purpose": "disposable P6 real update"}
        and value["status"] == "PASS"
        and value["complete"] is True
        and all(
            value["checks"].get(k) == "PASS"
            for k in (
                "A_payload_audit_and_repository",
                "B_payload_audit",
                "disposable_signing_key_removed",
            )
        )
        and value["fingerprint"] == expected["signing_fingerprint"],
        "Approved successful signed preparation required",
    )
    release = core.read_json(prepared / "b/release.json")
    core.require(value["B"] == release, "B release differs from preparation")
    for key, match in {
        "application_id": expected["app_id"],
        "version": expected["version"],
        "source_commit": entry["source_commit"],
        "ci_run_id": entry["ci_run_id"],
        "ci_artifact_id": entry["artifact_id"],
        "bundle_sha256": entry["bundle_sha256"],
        "ostree_commit": entry["ostree_commit"],
        "architecture": "x86_64",
        "signing_fingerprint": expected["signing_fingerprint"],
        "p6_B_approval_sha256": expected["B_approval_sha256"],
    }.items():
        core.require(release.get(key) == match, "Pinned B release identity mismatch")
    core.require(
        release["runtime_lock"]
        == core.read_json(
            core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
        )
        and release["runtime_lock"]["schema"] == expected["schema"] == 5
        and core.sha(core.safe_path(prepared / "b/staging-public.gpg"))
        == expected["public_key_sha256"],
        "Pinned B runtime, schema or signing trust mismatch",
    )
    profile, selection = workspace.retained_profile(r11, expected)
    with workspace.source_lock(profile):
        integrity = workspace.validate_workspace(
            profile / selection, expected["workspace"], exact_database=True
        )
        core.require(
            workspace.snapshot(profile) == expected["R11_profile"], "R11 changed"
        )
    return {"status": "PASS", "R11_integrity": integrity, "entry": entry}


def installed(native, expected):
    entry = expected["B_entry"]
    core.require(
        native.commit(core.APP_ID) == entry["ostree_commit"],
        "Installed B commit mismatch",
    )
    core.require(
        native.verify_remote(core.APP_ID) == "p5c", "Unexpected application origin"
    )
    native.installed_source(entry["source_commit"])
    location = Path(
        native.run("location", "info", "--show-location", core.APP_ID)
    ).resolve()
    core.require(
        location.is_relative_to(native.root / "flatpak"), "Deployment escaped client"
    )
    inputs = core.read_json(location / "files/share/cyrnava/build-inputs.json")
    core.require(
        inputs.get("app_id") == expected["app_id"] == core.APP_ID
        and inputs.get("version") == expected["version"] == "0.1.0"
        and inputs.get("schema") == expected["schema"] == 5
        and inputs.get("runtime_lock")
        == core.read_json(
            core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
        ),
        "Installed B version, schema, application or runtime identity mismatch",
    )
    permissions = native.run("list", "info", "--show-permissions", core.APP_ID)
    requirements().permissions(permissions)
    return {
        "status": "PASS",
        "application_id": core.APP_ID,
        "version": "0.1.0",
        "schema": 5,
        "source_commit": entry["source_commit"],
        "commit": entry["ostree_commit"],
        "branch": "stable",
        "architecture": "x86_64",
        "permissions_valid": True,
    }


def requirements():
    path = core.ROOT / "packaging/flatpak/production/host_verify.py"
    spec = importlib.util.spec_from_file_location("p6_targeted_requirements", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def phase(
    native,
    replay,
    monitor,
    attempt,
    env,
    data,
    run_id,
    canary,
    config,
    context,
    *,
    record,
):
    core.require(
        context in {"post-import-baseline", "reinstall-b"}, "Unreviewed targeted phase"
    )
    replay.trusted()
    script = preference_contract.script(
        (core.ROOT / "packaging/flatpak/production/native_check.py").read_bytes(),
        config,
    )
    name = "restart" if context == "post-import-baseline" else "updated"
    command = [
        "flatpak",
        "--user",
        "run",
        "--branch=stable",
        "--command=python3",
        core.APP_ID,
        "-u",
        "-",
        name,
        run_id,
        os.readlink("/proc/self/ns/net"),
        str(canary),
    ]
    print(
        "P6 " + context + ": read the native instruction dialog before interacting.",
        flush=True,
    )
    # No rewriting/removing a failed child assertion. Child source/data stay private.
    record["GUI_launches_attempted"] += 1
    native_diagnostics.run(
        monitor, attempt, "gui-" + name, command, env=env, script=script
    )
    value = core.read_json(data / (name + ".json"))
    required = (
        requirements().REQUIRED[name] - {"dark_preference_saved"}
    ) | preference_contract.required_checks(config)
    core.require(
        value.get("status") == "PASS"
        and value.get("complete") is True
        and required.issubset(value.get("checks", {}))
        and all(v == "PASS" for v in value["checks"].values()),
        "Required native B checks failed",
    )
    preference_contract.validate_result(config, value)
    # Retain original baseline bytes separately; never replace it with launch two.
    value["streamed_checker_sha256"] = hashlib.sha256(script).hexdigest()
    (attempt / ("phase-" + context + ".json")).write_bytes(core.encode(value))
    return value


def imports(native, monitor, attempt, context):
    root = attempt / context
    root.mkdir(mode=0o700)
    return historical_runtime.probe(native, monitor, root, "B")


def run(prepared, r11, attempt, archive, approval, historical_commit, authorization):
    core.require(authorization == AUTHORIZATION, "Explicit targeted scope required")
    core.require(
        historical_runtime.authorize(historical_commit),
        "Explicit historical authorization required",
    )
    prepared, r11, attempt = layout(prepared, r11, attempt)
    expected = workspace.policy()
    core.require(
        historical_commit == expected["historical_runtime"],
        "Historical policy mismatch",
    )
    attempt.mkdir(mode=0o700)  # Refuse any existing attempt; never overwrite evidence.
    record = {
        "status": "FAIL",
        "complete": False,
        "checks": {},
        "scope": "TARGETED B ONLY / HISTORICAL REPLAY",
        "authorization_ref": authorization,
        "ordinary_runtime_update_compatibility": False,
        "generation_A_launch_attempted": False,
        "GUI_launches_attempted": 0,
        "driver_code_sha256": {
            name: core.sha(core.HERE / name)
            for name in (
                "targeted_b.py",
                "targeted_workspace.py",
                "targeted-b-policy.json",
                "preference_contract.py",
                "historical_runtime.py",
                "native_distribution.py",
                "native_diagnostics.py",
                "progress.py",
            )
        },
        "native_checker_sha256": core.sha(
            core.ROOT / "packaging/flatpak/production/native_check.py"
        ),
    }
    (attempt / ".p6-targeted-B").write_bytes(core.encode(record))
    monitor = progress.Progress(attempt)
    replay = None
    data = None
    try:
        core.require(
            shutil.disk_usage(attempt).free >= 5 * 1024**3,
            "At least 5 GiB free required for isolated runtime/client copies",
        )
        with monitor.operation("source-validation"):
            record["inputs"] = verify_inputs(prepared, r11, archive, approval, expected)
        with monitor.operation("artifact-validation"):
            core.extract_artifact(archive, attempt / "candidate-b", expected["B_entry"])
            record["checks"]["approved_B_artifact"] = "PASS"
        native = native_distribution.RuntimeClient(attempt / "client", progress=monitor)
        env = real_update.desktop_environment(native)
        replay = historical_runtime.Replay(native, attempt, historical_commit)
        destination = distribution.LocalDestination(core.init_store(attempt / "store"))
        public, key = prepared / "b", prepared / "b/staging-public.gpg"
        fingerprint = expected["signing_fingerprint"]
        with monitor.operation("signed-B-validation"):
            plan = distribution.plan(public, destination, key, fingerprint, attempt)
            distribution.publish(public, destination, key, fingerprint, plan, attempt)
            record["checks"]["signed_B_repository_and_trust"] = "PASS"
        with monitor.operation("runtime-retrieval"):
            record["runtime_retrieval"] = native.runtimes()
        with distribution.loopback(destination, key, fingerprint) as base:
            with monitor.operation("install-b"), replay.transaction("install-b"):
                native.install_real(
                    base,
                    public,
                    fingerprint,
                    expected["B_entry"]["ostree_commit"],
                    expected["B_entry"]["source_commit"],
                    defer_runtime_check=True,
                )
            record["initial_B_identity"] = installed(native, expected)
            record["imports_B_before_baseline"] = imports(
                native, monitor, attempt, "imports-before-baseline"
            )
            run_id = "run-" + uuid4().hex[:12]
            data = (
                native.root
                / "home/.var/app"
                / core.APP_ID
                / "data/p4-verification"
                / run_id
            )
            profile = data / "desktop"
            with monitor.operation("workspace-copy"):
                record["workspace_copy"] = workspace.copy_workspace(
                    r11, profile, expected
                )
            identity = record["workspace_copy"]["workspace_identity"]
            canary = attempt / "host-only-canary"
            canary.write_text("Targeted P6 synthetic canary")
            config = {"mode": "reset", "workspace_identity": identity}
            record["active_native_phase"] = "post-import-baseline"
            baseline = phase(
                native,
                replay,
                monitor,
                attempt,
                env,
                data,
                run_id,
                canary,
                config,
                "post-import-baseline",
                record=record,
            )
            core.require(
                core.read_json(attempt / "phase-post-import-baseline.json") == baseline,
                "Stored baseline differs from observed baseline",
            )
            config = preference_contract.preserve_config(
                core.read_json(attempt / "phase-post-import-baseline.json")
            )
            baseline_sha = core.sha(attempt / "phase-post-import-baseline.json")
            record["preference_baseline_sha256"] = baseline_sha
            with monitor.operation("workspace-validation"):
                record["baseline_integrity"] = workspace.validate_active(
                    profile, expected, identity
                )
            record["checks"]["post_import_baseline"] = "PASS"
            record["pre_uninstall_application_trust"] = trust.verify_current_signature(
                key,
                fingerprint,
                public / "manifest.json",
                public / "manifest.json.sig",
                attempt,
            )
            record["before_uninstall_B_identity"] = installed(native, expected)
            before = workspace.data_state(data)
            record["data_before_uninstall"] = before
            with monitor.operation("uninstall-b"):
                native.run("install", "uninstall", "--noninteractive", core.APP_ID)
                record["data_after_uninstall"] = workspace.data_state(data)
                core.require(
                    record["data_after_uninstall"] == before,
                    "Uninstall changed private data",
                )
            with monitor.operation("reinstall-b"), replay.transaction("reinstall-b"):
                native.verify_summary()
                native.run("install", "install", "--noninteractive", "p5c", core.APP_ID)
                record["reinstalled_B_identity"] = installed(native, expected)
            record["data_after_reinstall"] = workspace.data_state(data)
            core.require(
                record["data_after_reinstall"] == before,
                "Reinstall changed private data",
            )
            record["post_reinstall_application_trust"] = trust.verify_current_signature(
                key,
                fingerprint,
                public / "manifest.json",
                public / "manifest.json.sig",
                attempt,
            )
            core.require(
                core.sha(attempt / "phase-post-import-baseline.json") == baseline_sha,
                "Original Light baseline changed",
            )
            record["imports_B_after_reinstall"] = imports(
                native, monitor, attempt, "imports-after-reinstall"
            )
            record["active_native_phase"] = "reinstall-b"
            phase(
                native,
                replay,
                monitor,
                attempt,
                env,
                data,
                run_id,
                canary,
                config,
                "reinstall-b",
                record=record,
            )
            core.require(
                core.sha(attempt / "phase-post-import-baseline.json") == baseline_sha,
                "Original Light baseline was replaced",
            )
            with monitor.operation("workspace-validation"):
                record["final_integrity"] = workspace.validate_active(
                    profile, expected, identity
                )
            record["checks"].update(
                reinstall_preferences_and_all_native_checks="PASS",
                synthetic_data_integrity="PASS",
            )
        record["status"] = "PASS"
    except (Exception, KeyboardInterrupt) as error:
        record.update(error_type=type(error).__name__)
        if isinstance(error, core.Rejected):
            record["error"] = str(error)
        if isinstance(error, KeyboardInterrupt):
            record.update(interrupted=True, error="Owner interruption; no retry")
        if isinstance(error, native_diagnostics.NativePhaseFailure):
            record["native_subprocess_failure"] = error.diagnostic
        if isinstance(error, native_distribution.RuntimeIdentityFailure):
            record["runtime_identity_failure"] = error.diagnostic
        if isinstance(error, OSError):
            record["errno"] = error.errno
        # Existing child file includes safe stage/errno/storage-line classification.
        if data is not None:
            name = (
                "restart"
                if record.get("active_native_phase") == "post-import-baseline"
                else "updated"
            )
            path = data / (name + ".json")
            if path.is_file() and not path.is_symlink():
                try:
                    child = core.read_json(path)
                    record["native_phase_failure"] = {
                        k: child[k]
                        for k in (
                            "stage",
                            "error_type",
                            "filesystem_failure",
                            "missing_checks",
                        )
                        if k in child
                    }
                except (ValueError, OSError, KeyError, TypeError):
                    record["native_phase_evidence_unavailable"] = True
    finally:
        try:
            source, _ = workspace.retained_profile(r11, expected)
            record["retained_R11_after"] = workspace.snapshot(source)
            record["checks"]["R11_source_preserved"] = "PASS"
        except (Exception, KeyboardInterrupt):
            record["status"] = "FAIL"
            record["checks"]["R11_source_preserved"] = "FAIL"
        try:
            for path, digest in (
                (prepared / "prepared.json", expected["prepared_sha256"]),
                (archive, expected["B_entry"]["artifact_zip_sha256"]),
                (approval, expected["B_approval_sha256"]),
            ):
                core.require(
                    core.sha(core.safe_path(path)) == digest, "Approved input changed"
                )
            record["checks"]["approved_inputs_preserved"] = "PASS"
        except (Exception, KeyboardInterrupt):
            record["status"] = "FAIL"
            record["checks"]["approved_inputs_preserved"] = "FAIL"
        record.update(
            complete=True,
            runtime_transactions=replay.events if replay else [],
            failed_operation=monitor.failure,
            operations=monitor.events,
        )
        (attempt / "owner-result.json").write_bytes(core.encode(record))
        print(json.dumps(record, indent=2), flush=True)
    return record


def execute():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "prepared-root",
        "r11-root",
        "attempt-root",
        "b-archive",
        "b-approval",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--historical-runtime", required=True)
    parser.add_argument("--authorization-ref", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    value = run(
        args.prepared_root,
        args.r11_root,
        args.attempt_root,
        args.b_archive,
        args.b_approval,
        args.historical_runtime,
        args.authorization_ref,
    )
    return 0 if value["status"] == "PASS" else 1


def main():
    try:
        return execute()
    except (Exception, KeyboardInterrupt) as error:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "complete": True,
                    "error_type": type(error).__name__,
                    "error": str(error)
                    if isinstance(error, core.Rejected)
                    else "Bootstrap failed; no retry",
                    "evidence": "stdout; no unsafe output directory created",
                }
            ),
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
