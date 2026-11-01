"""P5C integrated, disposable, nonpublishing native release rehearsal."""

import argparse
import datetime
import json
import os
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path

import client
import core
import github
import readiness
import update_fixture

DIAGNOSTICS = {"result.json", "eligibility.json", "readiness.json"}


def export_diagnostics(root, destination):
    core.require(
        core.read_json(root / ".p5c-disposable-root")
        == {"purpose": "P5C disposable integration"},
        "Marked disposable integration root required",
    )
    destination = core.outside_source(destination)
    core.require(not destination.exists(), "Diagnostic destination already exists")
    payload = {}
    for name in sorted(DIAGNOSTICS):
        source = root / name
        if source.exists():
            raw = core.encode(core.read_json(source))
            core.require(
                b"PRIVATE KEY" not in raw and b"github_pat_" not in raw,
                "Unsafe diagnostic content",
            )
            payload[name] = raw
    core.require("result.json" in payload, "Final status missing from diagnostics")
    temporary = Path(tempfile.mkdtemp(prefix="diag-", dir=destination.parent))
    try:
        for name, raw in payload.items():
            (temporary / name).write_bytes(raw)
        hashes = {name: core.sha(temporary / name) for name in payload}
        (temporary / "SHA256SUMS.json").write_bytes(core.encode(hashes))
        core.require(not destination.exists(), "Diagnostic destination changed")
        os.rename(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def prepare_environment(root):
    # Short private roots also avoid GPG Unix socket path-length failures.
    core.require(
        len(os.fsencode(root)) <= 48,
        "Use a disposable output path no longer than 48 bytes",
    )
    for tool in ("git", "flatpak", "ostree", "gpg", "gpgconf"):
        core.require(
            shutil.which(tool) is not None, "Required native tool unavailable: " + tool
        )
    values = {}
    for name in (
        "TMPDIR",
        "GNUPGHOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_CACHE_HOME",
        "XDG_RUNTIME_DIR",
    ):
        path = root / name.lower()
        path.mkdir(mode=0o700)
        values[name] = str(path)
    return values


def cleanup_keys(paths):
    for path in paths:
        if path.exists():
            core.safe_path(path)
            roots = [p for p in path.parents if (p / ".p5c-disposable-root").is_file()]
            core.require(
                len(roots) == 1
                and core.read_json(roots[0] / ".p5c-disposable-root")
                == {"purpose": "P5C disposable integration"}
                and str(path.relative_to(roots[0])) in {"p/key", "fk", "wk"},
                "Refuse cleanup outside exact integration key homes",
            )
            core.call("gpgconf", "--homedir", path, "--kill", "gpg-agent", timeout=30)
            shutil.rmtree(path)
            core.require(not path.exists(), "Disposable key home remains after cleanup")


def run(root, entry, archive, scan, record):
    private = root / "p"
    private.mkdir(mode=0o700)
    if archive is None:
        evidence = github.live_evidence(entry)
        (root / "eligibility.json").write_bytes(core.encode(evidence))
        archive = private / "artifact.zip"
        github.download(entry, archive)
    else:
        core.require(
            os.environ.get("GITHUB_ACTIONS") != "true",
            "Hosted integration requires live eligibility",
        )
        (root / "eligibility.json").write_bytes(
            core.encode(
                {
                    "status": "PINNED REPLAY",
                    "source_commit": entry["source_commit"],
                    "ci_run_id": entry["ci_run_id"],
                    "artifact_id": entry["artifact_id"],
                    "artifact_zip_sha256": entry["artifact_zip_sha256"],
                    ("meaning"): (
                        "Accepted artifact replay; this execution does not claim "
                        "live hosted eligibility"
                    ),
                }
            )
        )
    record["stage"] = "candidate"
    candidate = private / "candidate"
    core.extract_artifact(archive, candidate, entry)
    logical = core.read_json(candidate / "package-inventory.json")["logical_bytes"]
    reserve = 8 * logical + 2 * Path(archive).stat().st_size
    core.require(
        shutil.disk_usage(root).free >= reserve,
        "Insufficient space for conservative audit/client/copy budget",
    )
    record["resource_budget"] = {
        "free_bytes_before_native": shutil.disk_usage(root).free,
        "required_free_bytes": reserve,
        "basis": "8x logical installed bytes plus 2x ZIP bytes",
    }
    record["stage"] = "signed-repository"
    public = root / "public"
    store = core.init_store(root / "s")
    release = core.generate_repository(
        candidate, public, private, entry, (store / "current/repo").as_uri()
    )
    record["release"] = release
    # The reused P5B release record retains its P5B reference-workflow hash.
    # Bind the distinct P5C execution in a signed sidecar rather than relabelling
    # the accepted schema or confusing source and release-tooling identities.
    workflow = core.ROOT / ".github/workflows/p5c.yml"
    execution = {
        "purpose": "P5C disposable integration provenance",
        "source_commit": entry["source_commit"],
        "source_ci_run_id": entry["ci_run_id"],
        "artifact_id": entry["artifact_id"],
        "bundle_sha256": entry["bundle_sha256"],
        "tooling_base_commit": record["tooling_base_commit"],
        "candidate_code_sha256": record["candidate_code_sha256"],
        "workflow_path": ".github/workflows/p5c.yml",
        "workflow_definition_sha256": core.sha(
            workflow if workflow.exists() else core.HERE / "p5c-workflow.yml"
        ),
        "workflow_state": "HOSTED"
        if os.environ.get("GITHUB_ACTIONS") == "true"
        else "LOCAL PROPOSAL; uncommitted candidate code",
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "p5b_reference_workflow_sha256": release["release_workflow_definition_sha256"],
    }
    (public / "integration-provenance.json").write_bytes(core.encode(execution))
    for name in ("manifest.json", "manifest.json.sig"):
        (public / name).unlink()
    core.seal(public, private / "key", release["signing_fingerprint"])
    core.verify_seal(
        public, public / "staging-public.gpg", release["signing_fingerprint"], private
    )
    record["integration_provenance"] = execution
    record["integration_provenance_sha256"] = core.sha(
        public / "integration-provenance.json"
    )
    core.publish_local(
        public, store, public / "staging-public.gpg", release["signing_fingerprint"]
    )
    core.verify_descriptors(public, private, entry)
    record["stage"] = "accepted-application-client"
    receiver = client.Client(root / "c")
    installed = receiver.install(
        public / "cyrnava-staging.flatpakref",
        public / "staging-public.gpg",
        release["signing_fingerprint"],
        core.APP_ID,
        entry["ostree_commit"],
    )
    receiver.installed_source(entry["source_commit"])
    record["accepted_client"] = {
        **installed,
        "source_commit": entry["source_commit"],
        "public_key_fingerprint_verified": release["signing_fingerprint"],
        "operations": receiver.operations,
    }
    record["stage"] = "synthetic-updates"
    key, wrong = root / "fk", root / "wk"
    fp, wrong_fp = core.make_key(key), core.make_key(wrong)
    record["updates"] = update_fixture.exercise(root / "u", key, fp, wrong, wrong_fp)
    record["stage"] = "release-readiness"
    (root / "readiness.json").write_bytes(
        core.encode(readiness.plan(private / "approved-source", release, scan))
    )
    record["status"] = "PASS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--archive", type=Path)
    source.add_argument("--live", action="store_true")
    parser.add_argument("--advisories", action="store_true")
    parser.add_argument("--diagnostics", type=Path)
    parser.add_argument("--tooling-commit")
    parser.add_argument("--setup-failed", action="store_true")
    args = parser.parse_args()
    record = {
        "status": "FAIL",
        "complete": False,
        "purpose": "P5C disposable integration",
        "stage": "setup",
        "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "application_launch": "NOT TESTED",
        "production_publication": "DISABLED",
    }
    root = None
    created = False
    previous = {}
    started = time.monotonic()

    def interrupted(_signal, _frame):
        raise core.Rejected("Integration interrupted; no release claimed")

    old_signals = {
        number: signal.signal(number, interrupted)
        for number in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        root = core.outside_source(args.output)
        root.mkdir(mode=0o700)
        created = True
        (root / ".p5c-disposable-root").write_bytes(
            core.encode({"purpose": "P5C disposable integration"})
        )
        core.require(
            not args.setup_failed,
            "Hash-locked dependency setup failed before release processing",
        )
        env = prepare_environment(root)
        previous = {key: os.environ.get(key) for key in env}
        os.environ.update(env)
        entry = core.policy()["approved_staging_sources"][0]
        core.approval(
            entry["source_commit"],
            core.policy()["version"],
            "staging",
            entry["authorization_ref"],
        )
        if os.environ.get("GITHUB_ACTIONS") == "true":
            import integration_policy

            integration_policy.check_execution(args.tooling_commit)
            github.check_environment()
        record["tooling_base_commit"] = (
            core.call("git", "-C", core.ROOT, "rev-parse", "HEAD").decode().strip()
        )
        record["candidate_code_sha256"] = {
            p.name: core.sha(p) for p in core.HERE.glob("*.py")
        }
        record["native_tools"] = {
            name: core.call(name, "--version").decode().splitlines()[0]
            for name in ("flatpak", "ostree", "gpg")
        }
        run(root, entry, args.archive, args.advisories, record)
    except (Exception, KeyboardInterrupt) as error:
        record["status"] = "FAIL"
        record["error_type"] = type(error).__name__
        record["error"] = (
            str(error)
            if isinstance(error, core.Rejected)
            else "Integration failed; sensitive details redacted"
        )
    finally:
        for number in old_signals:
            signal.signal(number, signal.SIG_IGN)
        if created:
            try:
                cleanup_keys([root / "p/key", root / "fk", root / "wk"])
                record["private_key_cleanup"] = "PASS"
            except Exception:
                record.update(status="FAIL", private_key_cleanup="FAIL")
            record.update(complete=True, seconds=round(time.monotonic() - started, 3))
            try:
                (root / "result.json").write_bytes(core.encode(record))
                if args.diagnostics:
                    export_diagnostics(root, args.diagnostics)
            except Exception:
                record.update(
                    status="FAIL",
                    evidence_warning="Could not persist/export final evidence",
                )
                try:
                    (root / "result.json").write_bytes(core.encode(record))
                except OSError:
                    pass  # stdout still carries the complete FAIL record below.
        else:
            record.update(complete=True, seconds=round(time.monotonic() - started, 3))
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        for number, handler in old_signals.items():
            signal.signal(number, handler)
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
