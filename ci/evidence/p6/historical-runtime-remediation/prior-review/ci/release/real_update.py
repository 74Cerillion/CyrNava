"""P6 owner-host real A/B protocol, reusing P5B signing and P4 native assertions.

No bundle-only update, synthetic app substitution, production key or normal user
installation. Generation B requires an explicit reviewed approval record.
"""

import argparse
import contextlib
import importlib.util
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import core
import distribution
import native_diagnostics
import native_distribution
import progress
import real_update_audit


def approved_b(path):
    value = core.read_json(path)
    core.require(
        value.get("owner_approved_for_disposable_P6_update") is True,
        "Generation B owner approval is pending",
    )
    entry = value["entry"]
    core.require(
        len(entry["source_commit"]) == 40
        and all(c in "0123456789abcdef" for c in entry["source_commit"])
        and entry["source_commit"]
        != core.policy()["approved_staging_sources"][0]["source_commit"],
        "Distinct immutable real B source required",
    )
    for field in (
        "artifact_zip_sha256",
        "bundle_sha256",
        "inputs_sha256",
        "inventory_sha256",
        "ostree_commit",
    ):
        core.require(
            core.SHA.fullmatch(entry[field]) is not None, "Invalid approved B digest"
        )
    core.require(
        value.get("version") == "0.1.0" and value.get("schema") == 5,
        "Version/schema change needs a separate reviewed protocol",
    )
    return entry


def prepare(root, archive_a, archive_b, approval):
    b = approved_b(approval)  # Before directories, extraction or signing.
    approval_sha256 = core.sha(approval)
    a = core.policy()["approved_staging_sources"][0]
    root = core.outside_source(root)
    root.mkdir(mode=0o700)
    (root / ".p6-real-update").write_bytes(
        core.encode({"purpose": "disposable P6 real update"})
    )
    private = root / "p"
    private.mkdir(mode=0o700)
    record = {"status": "FAIL", "complete": False, "checks": {}}
    home = private / "key"
    operation = "artifact-validation"
    try:
        store = core.init_store(root / "store")
        candidate_a, candidate_b = private / "a", private / "b"
        core.extract_artifact(archive_a, candidate_a, a)
        core.extract_artifact(archive_b, candidate_b, b)
        operation = "generation-A-repository"
        release_a = core.generate_repository(
            candidate_a, root / "a", private, a, (store / "current/repo").as_uri()
        )
        record["checks"]["A_payload_audit_and_repository"] = "PASS"
        execution = {
            "purpose": "P6 disposable real application update",
            "tooling_base_commit": core.call(
                "git", "-C", core.ROOT, "rev-parse", "HEAD"
            )
            .decode()
            .strip(),
            "tooling_state": (
                "exact worktree hashes; not an assertion of clean committed code"
            ),
            "candidate_code_sha256": {
                name: core.sha(core.HERE / name)
                for name in (
                    "real_update.py",
                    "real_update_audit.py",
                    "native_distribution.py",
                    "distribution.py",
                    "trust.py",
                )
            },
            "source_A": a["source_commit"],
            "source_B": b["source_commit"],
            "B_approval_sha256": approval_sha256,
        }
        (root / "a/p6-provenance.json").write_bytes(core.encode(execution))
        operation = "generation-A-seal"
        for name in ("manifest.json", "manifest.json.sig"):
            (root / "a" / name).unlink()
        core.seal(root / "a", home, release_a["signing_fingerprint"])
        operation = "generation-B-source-checkout"
        source_b = core.checkout_accepted_source(
            private / "source-b", b["source_commit"]
        )
        audit = private / "audit-b"
        audit.mkdir()
        operation = real_update_audit.OPERATION
        real_update_audit.run(
            source_b,
            candidate_b,
            audit,
            approval,
            b,
            approval_sha256,
        )
        record["checks"]["B_payload_audit"] = "PASS"
        operation = "generation-B-signing"
        public_b = root / "b"
        public_b.mkdir()
        shutil.copytree(root / "a/repo", public_b / "repo")
        core.call(
            "flatpak",
            "build-import-bundle",
            public_b / "repo",
            candidate_b / core.BUNDLE,
        )
        fingerprint = release_a["signing_fingerprint"]
        core.call(
            "flatpak",
            "build-sign",
            "--arch=x86_64",
            "--gpg-homedir=" + str(home),
            "--gpg-sign=" + fingerprint,
            public_b / "repo",
            core.APP_ID,
            "stable",
        )
        core.call(
            "flatpak",
            "build-update-repo",
            "--gpg-homedir=" + str(home),
            "--gpg-sign=" + fingerprint,
            public_b / "repo",
        )
        key = public_b / "staging-public.gpg"
        key.write_bytes(core.export_key(home, fingerprint))
        core.descriptors(public_b, (store / "current/repo").as_uri(), key.read_bytes())
        release_b = {
            **release_a,
            **core.validate_candidate(candidate_b, b),
            "purpose": "p5b-staging",
            "p6_B_approval_sha256": approval_sha256,
            "authorization_ref": b["authorization_ref"],
        }
        core.require(
            release_b["ostree_commit"] != release_a["ostree_commit"],
            "Real application commit did not change",
        )
        (public_b / "release.json").write_bytes(core.encode(release_b))
        (public_b / "p6-provenance.json").write_bytes(core.encode(execution))
        core.verify_repository(public_b / "repo", key, private)
        core.seal(public_b, home, fingerprint)
        operation = "pair-validation"
        destination = distribution.LocalDestination(store)
        for public in (root / "a", public_b):
            distribution.plan(public, destination, key, fingerprint, private)
        record.update(status="PASS", fingerprint=fingerprint, A=release_a, B=release_b)
    except (core.Rejected, OSError, ValueError, KeyError) as error:
        record["operation"] = operation
        if isinstance(error, real_update_audit.AuditFailure):
            record["failure"] = error.diagnostic
        record["error"] = (
            str(error) if isinstance(error, core.Rejected) else type(error).__name__
        )
    finally:
        if home.exists():
            core.call("gpgconf", "--homedir", home, "--kill", "gpg-agent")
            shutil.rmtree(home)
        record["checks"]["disposable_signing_key_removed"] = (
            "PASS" if not home.exists() else "FAIL"
        )
        record["complete"] = True
        (root / "prepared.json").write_bytes(core.encode(record))
        print(json.dumps(record, indent=2), flush=True)
    return record


def desktop_environment(native):
    native.guard()
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", ""))
    wayland = os.environ.get("WAYLAND_DISPLAY", "")
    core.require(
        runtime.is_absolute()
        and runtime.stat().st_uid == os.getuid()
        and wayland
        and Path(wayland).name == wayland
        and (runtime / wayland).is_socket(),
        "Owner Wayland desktop required; security flags will not be relaxed",
    )
    return {
        **native.env,
        "XDG_RUNTIME_DIR": str(runtime),
        "WAYLAND_DISPLAY": wayland,
        "DBUS_SESSION_BUS_ADDRESS": os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""),
    }


def exercise(root, attempt_root):
    root = core.outside_source(root)
    core.require(
        core.read_json(root / ".p6-real-update")
        == {"purpose": "disposable P6 real update"},
        "Marked P6 pair required",
    )
    prepared = core.read_json(root / "prepared.json")
    core.require(
        prepared["status"] == "PASS" and prepared["complete"],
        "Verified prepared pair required",
    )
    attempt = core.outside_source(attempt_root)
    attempt.mkdir(mode=0o700)  # A new client/store; never overwrite failed evidence.
    driver_hashes = {
        name: core.sha(core.HERE / name)
        for name in (
            "real_update.py",
            "native_distribution.py",
            "progress.py",
            "native_diagnostics.py",
        )
    }
    (attempt / ".p6-gui-attempt").write_bytes(
        core.encode(
            {
                "purpose": "P6 disposable GUI attempt",
                "prepared_sha256": core.sha(root / "prepared.json"),
                "driver_code_sha256": driver_hashes,
            }
        )
    )
    monitor = progress.Progress(attempt)
    native = native_distribution.RuntimeClient(attempt / "client", progress=monitor)
    env = desktop_environment(native)
    record = {
        "status": "FAIL",
        "complete": False,
        "checks": {},
        "source_A": prepared["A"]["source_commit"],
        "source_B": prepared["B"]["source_commit"],
        "generation_A_launch_attempted": False,
        "prepared_sha256": core.sha(root / "prepared.json"),
        "driver_code_sha256": driver_hashes,
    }
    run_id = "run-" + uuid4().hex[:12]
    data = native.root / "home/.var/app" / core.APP_ID / "data/p4-verification" / run_id
    path = core.ROOT / "packaging/flatpak/production/host_verify.py"
    spec = importlib.util.spec_from_file_location("p6_native_requirements", path)
    requirements = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(requirements)
    key, fingerprint = root / "a/staging-public.gpg", prepared["fingerprint"]
    destination = distribution.LocalDestination(core.init_store(attempt / "store"))
    canary = attempt / "host-only-canary"
    canary.write_text("P6 synthetic host canary")

    def phase(name, prompt):
        record.setdefault("runtime_checks", []).append(
            {"phase": name, **native.verify_runtime()}
        )
        print(name.upper() + ": " + prompt, flush=True)
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
        script = (path.parent / "native_check.py").read_bytes()
        if name == "edit":
            record["generation_A_launch_attempted"] = True
        result = native_diagnostics.run(
            monitor,
            attempt,
            "gui-" + name,
            command,
            env=env,
            script=script,
        )
        value = core.read_json(data / (name + ".json"))
        core.require(
            result.returncode == 0
            and value.get("status") == "PASS"
            and value.get("complete") is True
            and requirements.REQUIRED[name].issubset(value["checks"])
            and all(v == "PASS" for v in value["checks"].values()),
            "Native synthetic phase failed: " + name,
        )
        if name in {"restart", "updated", "rollback"}:
            core.require(
                value.get("preferences_sha256")
                == core.read_json(data / "edit.json").get("preferences_sha256"),
                "Preferences changed across real update/restart",
            )
        record["checks"][name] = "PASS"
        (attempt / ("phase-" + name + ".json")).write_bytes(core.encode(value))

    def activate(label):
        public = root / label
        with monitor.operation("activate-" + label):
            reviewed = distribution.plan(public, destination, key, fingerprint, attempt)
            distribution.publish(
                public, destination, key, fingerprint, reviewed, attempt
            )

    try:
        with monitor.operation("runtime-retrieval"):
            record["checks"]["runtime_retrieval"] = native.runtimes()
        activate("a")
        with contextlib.ExitStack() as stack:
            with monitor.operation("http-start"):
                base = stack.enter_context(
                    distribution.loopback(destination, key, fingerprint)
                )
            with monitor.operation("install-a"):
                record["checks"]["install_A"] = native.install_real(
                    base,
                    root / "a",
                    fingerprint,
                    prepared["A"]["ostree_commit"],
                    prepared["A"]["source_commit"],
                )
            phase(
                "edit",
                "Create a folder, title P4 owner edit, add headings/list/code. "
                "Paste ONLY a synthetic screenshot, choose Dark, wait for Saved, "
                "then close.",
            )
            phase(
                "restart",
                "Confirm synthetic rich text, image and Dark preference persist. "
                "Test keyboard navigation, then close.",
            )
            activate("b")
            native.update(core.APP_ID, prepared["B"]["ostree_commit"])
            native.installed_source(prepared["B"]["source_commit"])
            phase(
                "updated",
                "Confirm the same synthetic data after REAL application update B, "
                "then close.",
            )
            native.run(
                "update",
                "update",
                "--noninteractive",
                "--no-deps",
                "--commit=" + prepared["A"]["ostree_commit"],
                core.APP_ID,
            )
            core.require(
                native.commit(core.APP_ID) == prepared["A"]["ostree_commit"],
                "Binary rollback mismatch",
            )
            phase(
                "rollback",
                "Confirm synthetic data after compatible binary rollback A, "
                "then close. This does not roll back SQLite.",
            )
            phase(
                "maintenance",
                "Create verified backup p6-backup.cyrnava including extension. "
                "Import THE SAME file with the SECOND button. "
                "Wait for Completed and verified after BOTH actions, "
                "then close manager.",
            )
            phase(
                "recovery",
                "Automatic synthetic backup/restore and future-schema refusal.",
            )
            before = core.tree_manifest(data)
            native.run("install", "uninstall", "--noninteractive", core.APP_ID)
            core.require(core.tree_manifest(data) == before, "Uninstall modified data")
            native.run("install", "install", "--noninteractive", "p5c", core.APP_ID)
            core.require(
                native.commit(core.APP_ID) == prepared["B"]["ostree_commit"],
                "Reinstall resolved unexpected commit",
            )
            core.require(core.tree_manifest(data) == before, "Reinstall modified data")
            phase("updated", "Confirm synthetic data after reinstall B, then close.")
            record["checks"]["uninstall_reinstall_preserved_data"] = "PASS"
        record["status"] = "PASS"
    except KeyboardInterrupt:
        record.update(
            error="Owner interruption (SIGINT/KeyboardInterrupt)",
            failure_category="interrupted",
            interrupted=True,
        )
    except (
        core.Rejected,
        OSError,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
    ) as error:
        if isinstance(error, native_diagnostics.NativePhaseFailure):
            record["native_subprocess_failure"] = error.diagnostic
        if isinstance(error, native_distribution.RuntimeIdentityFailure):
            record["runtime_identity_failure"] = error.diagnostic
        record["error"] = (
            str(error) if isinstance(error, core.Rejected) else type(error).__name__
        )
    finally:
        record["complete"] = True
        record["failed_operation"] = monitor.failure
        record["operations"] = monitor.events
        record["seconds"] = round(time.monotonic() - monitor.started, 3)
        (attempt / "owner-result.json").write_bytes(core.encode(record))
        print(json.dumps(record, indent=2), flush=True)
    return record


def execute():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "gui"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--a-archive", type=Path)
    parser.add_argument("--b-archive", type=Path)
    parser.add_argument("--b-approval", type=Path)
    parser.add_argument("--attempt-root", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if args.mode == "prepare":
        core.require(
            all((args.a_archive, args.b_archive, args.b_approval)),
            "Both artifacts and explicit B approval required",
        )
        result = prepare(args.root, args.a_archive, args.b_archive, args.b_approval)
    else:
        core.require(
            args.attempt_root is not None,
            "Fresh --attempt-root required; preserve prepared and failed evidence",
        )
        result = exercise(args.root, args.attempt_root)
    return 0 if result["status"] == "PASS" else 1


def main():
    try:
        return execute()
    except (Exception, KeyboardInterrupt) as error:
        # A rejected/uncreatable output root must not be written just to report
        # its failure. Emit a final machine-readable record to stdout instead.
        print(
            core.encode(
                {
                    "status": "FAIL",
                    "complete": True,
                    "error": str(error)
                    if isinstance(error, core.Rejected)
                    else type(error).__name__,
                    "evidence": "stdout; output root not assumed safe",
                }
            ).decode(),
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
