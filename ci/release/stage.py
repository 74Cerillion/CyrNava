"""Explicit P5B disposable staging rehearsal. Never publishes outside local disk."""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import core
import github


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--ci-run-id", required=True, type=int)
    parser.add_argument("--channel", required=True, choices=["staging"])
    parser.add_argument("--authorization-ref", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--archive", type=Path)
    source.add_argument("--live", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--static-deltas", action="store_true")
    args = parser.parse_args()
    record = {
        "status": "FAIL",
        "complete": False,
        "purpose": "P5B disposable staging",
        "stage": "eligibility",
        "steps": [],
    }
    started = time.monotonic()
    private = None
    output = None
    created = False
    try:
        entry = core.approval(
            args.source_commit, args.version, args.channel, args.authorization_ref
        )
        core.require(
            args.ci_run_id == entry["ci_run_id"], "Wrong verification run input"
        )
        output = core.outside_source(args.output)
        output.mkdir(mode=0o700)
        created = True
        (output / ".p5b-disposable-root").write_text("P5B STAGING ONLY\n")
        private = output / "private"
        private.mkdir(mode=0o700)
        if args.live:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                core.require(
                    os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
                    and os.environ.get("GITHUB_REF")
                    == "refs/heads/" + core.policy()["workflow_branch"],
                    "Untrusted release trigger/ref",
                )
                github.check_environment()
            evidence = github.live_evidence(entry)
            (output / "eligibility.json").write_bytes(core.encode(evidence))
            archive = private / "artifact.zip"
            github.download(entry, archive)
        else:
            core.require(
                os.environ.get("GITHUB_ACTIONS") != "true",
                "Hosted workflow requires live CI evidence",
            )
            archive = args.archive
            (output / "eligibility.json").write_bytes(
                core.encode(
                    {
                        "status": "PINNED REPLAY",
                        "meaning": (
                            "Reviewed owner-accepted artifact hash; "
                            "live GitHub eligibility not checked"
                        ),
                        "ci_run_id": entry["ci_run_id"],
                        "source_commit": entry["source_commit"],
                    }
                )
            )
        record["steps"].append(
            {"eligibility": "PASS" if args.live else "PINNED REPLAY"}
        )
        record["stage"] = "candidate"
        candidate = private / "candidate"
        core.extract_artifact(archive, candidate, entry)
        record["steps"].append({"candidate": "PASS"})
        record["stage"] = "signed-repository"
        public = output / "public"
        store_path = output / "local-store"
        # Stable /current/repo/ path. Snapshot publication retains all old objects.
        url = (store_path / "current/repo").as_uri()
        report = core.generate_repository(
            candidate, public, private, entry, url, deltas=args.static_deltas
        )
        record["steps"].append({"signed_repository": "PASS"})
        record["stage"] = "negative-verification"
        wrong_home = private / "wrong-key"
        wrong = core.make_key(wrong_home)
        wrong_public = private / "wrong-public.gpg"
        wrong_public.write_bytes(core.export_key(wrong_home, wrong))
        try:
            core.verify_repository(public / "repo", wrong_public, private)
        except core.Rejected:
            record["steps"].append({"wrong_repository_key_rejected": "PASS"})
        else:
            raise core.Rejected("Repository accepted an incorrect key")
        tampered = private / "tampered"
        shutil.copytree(public, tampered)
        summary = tampered / "repo/summary"
        summary.write_bytes(summary.read_bytes() + b"TAMPER")
        try:
            core.verify_repository(
                tampered / "repo", public / "staging-public.gpg", private
            )
        except core.Rejected:
            record["steps"].append({"tampered_repository_rejected": "PASS"})
        else:
            raise core.Rejected("Repository accepted tampered metadata")
        missing = private / "missing-object"
        shutil.copytree(public, missing)
        commit = entry["ostree_commit"]
        (missing / "repo/objects" / commit[:2] / (commit[2:] + ".commit")).unlink()
        try:
            core.verify_repository(
                missing / "repo", public / "staging-public.gpg", private
            )
        except core.Rejected:
            record["steps"].append({"missing_required_object_rejected": "PASS"})
        else:
            raise core.Rejected("Repository accepted a missing commit object")
        invalid_ref = private / "invalid-ref"
        shutil.copytree(public, invalid_ref)
        (invalid_ref / "repo/refs/heads/unexpected").write_text(commit + "\n")
        try:
            core.verify_repository(
                invalid_ref / "repo", public / "staging-public.gpg", private
            )
        except core.Rejected:
            record["steps"].append({"unexpected_ref_rejected": "PASS"})
        else:
            raise core.Rejected("Repository accepted an unexpected ref")
        record["stage"] = "local-publication"
        store = core.init_store(store_path)
        publication = core.publish_local(
            public, store, public / "staging-public.gpg", report["signing_fingerprint"]
        )
        # Recheck the stable published path with a clean verifying OSTree client.
        core.verify_repository(
            (store / "current").resolve() / "repo",
            public / "staging-public.gpg",
            private,
        )
        core.verify_descriptors(public, private, entry)
        record["steps"].append({"native_flatpakrepo_descriptor_remote": "PASS"})
        drill = private / "publication-drill"
        shutil.copytree(public, drill)
        release = core.read_json(drill / "release.json")
        release["interruption_drill"] = True
        (drill / "release.json").write_bytes(core.encode(release))
        (drill / "manifest.json").unlink()
        (drill / "manifest.json.sig").unlink()
        core.seal(drill, private / "key", report["signing_fingerprint"])
        interruption = {"reached": False}

        def interrupt():
            interruption["reached"] = True
            raise core.Rejected("Intentional staging interruption before activation")

        try:
            core.publish_local(
                drill,
                store,
                public / "staging-public.gpg",
                report["signing_fingerprint"],
                before_activate=interrupt,
            )
        except core.Rejected as error:
            core.require(
                interruption["reached"]
                and str(error) == "Intentional staging interruption before activation",
                "Publication failed before reaching the intended interruption boundary",
            )
            core.require(
                core.active_generation(store).name == publication["generation"],
                "Interrupted publication changed the active repository",
            )
            record["steps"].append(
                {"interrupted_publication_preserves_previous": "PASS"}
            )
        else:
            raise core.Rejected("Interruption drill unexpectedly activated")
        files = core.tree_manifest(public)
        record.update(
            status="PASS",
            publication=publication,
            release=report,
            metrics={
                "repo_bytes": sum(
                    v["bytes"] for k, v in files.items() if k.startswith("repo/")
                ),
                "repo_files": sum(k.startswith("repo/") for k in files),
                "signed_metadata_bytes": sum(
                    v["bytes"]
                    for k, v in files.items()
                    if k.endswith((".sig", ".commitmeta"))
                ),
                "static_delta_bytes": sum(
                    v["bytes"] for k, v in files.items() if k.startswith("repo/deltas/")
                ),
            },
        )
    except (core.Rejected, OSError, ValueError, KeyError) as error:
        record["error_type"] = type(error).__name__
        record["error"] = (
            str(error)
            if isinstance(error, core.Rejected)
            else "Staging failed; no publication claimed"
        )
    finally:
        # Private keys never enter diagnostic artifacts or repository snapshots.
        if private:
            for home in (private / "key", private / "wrong-key"):
                if home.exists():
                    try:
                        core.call("gpgconf", "--homedir", home, "--kill", "gpg-agent")
                    except core.Rejected:
                        record["status"] = "FAIL"
                        record["cleanup_warning"] = (
                            "Disposable key agent shutdown failed"
                        )
                    try:
                        shutil.rmtree(home)
                    except OSError:
                        record["status"] = "FAIL"
                        record["cleanup_warning"] = (
                            "Disposable key cleanup requires operator attention"
                        )
        record.update(complete=True, seconds=round(time.monotonic() - started, 3))
        if created:
            try:
                (output / "result.json").write_bytes(core.encode(record))
            except OSError:
                record["status"] = "FAIL"
                record["evidence_warning"] = (
                    "Could not persist result; use this stdout record"
                )
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
