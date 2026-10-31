"""P5B deterministic trust-boundary tests. No production keys or publication."""

import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import github
import preflight
import stage
import workflow_policy


class EligibilityTests(unittest.TestCase):
    def setUp(self):
        self.policy = core.policy()
        self.entry = copy.deepcopy(self.policy["approved_staging_sources"][0])
        self.run = {
            "id": self.entry["ci_run_id"],
            "run_attempt": 1,
            "head_sha": self.entry["source_commit"],
            "head_branch": self.policy["workflow_branch"],
            "event": "push",
            "status": "completed",
            "conclusion": "success",
            "workflow_id": self.policy["ci_workflow_id"],
            "path": self.policy["ci_workflow_path"],
            "repository": {"id": self.policy["repository_id"]},
        }
        names = [
            "Workflow validation",
            "Backend and security",
            "Frontend and browser",
            "Production Flatpak and bundle audit",
            "CI required",
        ]
        self.jobs = [
            {"name": n, "status": "completed", "conclusion": "success"} for n in names
        ]
        self.artifact = {
            "id": self.entry["artifact_id"],
            "expired": False,
            "digest": "sha256:" + self.entry["artifact_zip_sha256"],
            "name": f"CyrNava-linux-x86_64-{self.entry['source_commit']}-1",
            "workflow_run": {
                "id": self.entry["ci_run_id"],
                "head_sha": self.entry["source_commit"],
            },
        }
        self.workflow = (core.ROOT / ".github/workflows/ci.yml").read_bytes()

    def verify(self):
        return core.ci_eligibility(
            self.run, self.jobs, self.artifact, self.workflow, self.entry
        )

    def test_reviewed_source_and_successful_ci(self):
        self.assertTrue(self.verify())
        self.assertEqual(
            core.approval(
                self.entry["source_commit"],
                "0.1.0",
                "staging",
                self.entry["authorization_ref"],
            ),
            self.entry,
        )

    def test_failed_or_missing_ci_jobs_rejected(self):
        for index in range(5):
            with self.subTest(job=index):
                self.jobs[index]["conclusion"] = "failure"
                with self.assertRaises(core.Rejected):
                    self.verify()
                self.jobs[index]["conclusion"] = "success"
        self.jobs.pop()
        with self.assertRaises(core.Rejected):
            self.verify()

    def test_wrong_source_run_workflow_or_repository_rejected(self):
        for key, value in [
            ("head_sha", "a" * 40),
            ("id", 1),
            ("run_attempt", 2),
            ("workflow_id", 1),
            ("event", "pull_request"),
            ("path", "evil.yml"),
            ("repository", {"id": 1}),
        ]:
            original = self.run[key]
            self.run[key] = value
            with self.subTest(key=key), self.assertRaises(core.Rejected):
                self.verify()
            self.run[key] = original

    def test_wrong_expired_or_replaced_artifact_rejected(self):
        for key, value in [
            ("id", 1),
            ("expired", True),
            ("digest", "sha256:" + "a" * 64),
            ("name", "another"),
            ("workflow_run", {"id": 1}),
        ]:
            original = self.artifact[key]
            self.artifact[key] = value
            with self.subTest(key=key), self.assertRaises(core.Rejected):
                self.verify()
            self.artifact[key] = original

    def test_unreviewed_ci_content_rejected(self):
        self.workflow += b"# changed"
        with self.assertRaises(core.Rejected):
            self.verify()

    def test_no_manual_override_of_approval_version_or_channel(self):
        args = [
            self.entry["source_commit"],
            "0.1.0",
            "staging",
            self.entry["authorization_ref"],
        ]
        for index, value in [
            (0, "main"),
            (0, "a" * 40),
            (1, "0.2.0"),
            (2, "production"),
            (3, ""),
        ]:
            changed = args.copy()
            changed[index] = value
            with (
                self.subTest(index=index, value=value),
                self.assertRaises(core.Rejected),
            ):
                core.approval(*changed)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p5b-test-")
        self.root = Path(self.temporary.name)
        self.entry = copy.deepcopy(core.policy()["approved_staging_sources"][0])
        self.source = self.root / "candidate"
        self.source.mkdir()
        (self.source / core.BUNDLE).write_bytes(b"synthetic bundle, never imported")
        digest = core.sha(self.source / core.BUNDLE)
        self.entry["bundle_sha256"] = digest
        inputs = {
            "app_id": core.APP_ID,
            "runtime_lock": core.read_json(
                core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
            ),
            "git_commit": self.entry["source_commit"],
            "version": "0.1.0",
        }
        provenance = {
            "app_id": core.APP_ID,
            "runtime": inputs["runtime_lock"],
            "source_commit": inputs["git_commit"],
            "version": "0.1.0",
            "workflow_run_id": str(self.entry["ci_run_id"]),
            "workflow_run_attempt": "1",
            "status": "PASS",
            "sha256": digest,
            "artifact_bytes": (self.source / core.BUNDLE).stat().st_size,
            "ostree_commit": self.entry["ostree_commit"],
        }
        result = {
            "app_id": core.APP_ID,
            "status": "PASS",
            "sha256": digest,
            "bytes": provenance["artifact_bytes"],
            "ostree_commit": self.entry["ostree_commit"],
        }
        for name, value in [
            ("build-inputs.json", inputs),
            ("provenance.json", provenance),
            ("result.json", result),
            ("package-inventory.json", {"status": "PASS", "files": []}),
        ]:
            (self.source / name).write_bytes(core.encode(value))
        (self.source / "SHA256SUMS").write_text(digest + "  " + core.BUNDLE + "\n")
        self.rehash()

    def tearDown(self):
        self.temporary.cleanup()

    def rehash(self):
        self.entry["inputs_sha256"] = core.sha(self.source / "build-inputs.json")
        self.entry["inventory_sha256"] = core.sha(
            self.source / "package-inventory.json"
        )

    def zip(self, extra=None):
        archive = self.root / "artifact.zip"
        with zipfile.ZipFile(archive, "w") as output:
            for path in self.source.iterdir():
                output.write(path, path.name)
            if extra:
                output.writestr(*extra)
        self.entry["artifact_zip_sha256"] = core.sha(archive)
        return archive

    def test_bounded_extraction_and_metadata_validation(self):
        result = core.extract_artifact(self.zip(), self.root / "extract", self.entry)
        self.assertEqual(result["source_commit"], self.entry["source_commit"])

    def test_archive_hash_mismatch_rejected(self):
        archive = self.zip()
        archive.write_bytes(archive.read_bytes() + b"tamper")
        with self.assertRaises(core.Rejected):
            core.extract_artifact(archive, self.root / "extract", self.entry)

    def test_unsafe_or_extra_zip_entries_rejected(self):
        for index, name in enumerate(
            ["../escape", "/absolute", "secret.key", core.BUNDLE]
        ):
            with self.subTest(name=name), self.assertRaises(core.Rejected):
                core.extract_artifact(
                    self.zip((name, b"synthetic")),
                    self.root / f"out-{index}",
                    self.entry,
                )

    def test_zip_symlink_rejected(self):
        archive = self.root / "artifact.zip"
        with zipfile.ZipFile(archive, "w") as output:
            for path in self.source.iterdir():
                if path.name == core.BUNDLE:
                    info = zipfile.ZipInfo(core.BUNDLE)
                    info.external_attr = 0o120777 << 16
                    output.writestr(info, "/etc/passwd")
                else:
                    output.write(path, path.name)
        self.entry["artifact_zip_sha256"] = core.sha(archive)
        with self.assertRaises(core.Rejected):
            core.extract_artifact(archive, self.root / "extract", self.entry)

    def test_compressed_oversized_metadata_rejected_before_extraction(self):
        (self.source / "provenance.json").write_bytes(b"0" * (4 * 1024**2 + 1))
        archive = self.root / "artifact.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for path in self.source.iterdir():
                output.write(path, path.name)
        self.entry["artifact_zip_sha256"] = core.sha(archive)
        with self.assertRaisesRegex(core.Rejected, "member exceeds"):
            core.extract_artifact(archive, self.root / "extract", self.entry)

    def test_payload_metadata_fails_closed(self):
        mutations = [
            ("provenance.json", "app_id", "evil"),
            ("provenance.json", "source_commit", "b" * 40),
            ("provenance.json", "runtime", {}),
            ("provenance.json", "status", "FAIL"),
            ("provenance.json", "version", "9.9.9"),
            ("result.json", "ostree_commit", "c" * 64),
        ]
        for name, key, value in mutations:
            path = self.source / name
            original = path.read_bytes()
            data = json.loads(original)
            data[key] = value
            path.write_bytes(core.encode(data))
            with self.subTest(name=name, key=key), self.assertRaises(core.Rejected):
                core.validate_candidate(self.source, self.entry)
            path.write_bytes(original)

    def test_candidate_symlink_and_duplicate_json_rejected(self):
        p = self.source / "provenance.json"
        p.unlink()
        p.symlink_to(self.source / "result.json")
        with self.assertRaises(core.Rejected):
            core.validate_candidate(self.source, self.entry)
        p.unlink()
        p.write_text('{"status":"PASS","status":"FAIL"}')
        with self.assertRaises(core.Rejected):
            core.read_json(p)

    def test_metadata_resource_bound(self):
        p = self.source / "provenance.json"
        p.write_bytes(b" " * (4 * 1024**2 + 1))
        with self.assertRaises(core.Rejected):
            core.read_json(p)


class TransportTests(unittest.TestCase):
    def test_download_redirect_never_forwards_api_credentials(self):
        entry = copy.deepcopy(core.policy()["approved_staging_sources"][0])
        payload = b"SYNTHETIC ARTIFACT DOWNLOAD"
        location = "https://test.blob.core.windows.net/staging?sig=synthetic"
        redirect = urllib.error.HTTPError(
            "https://api.github.com/", 302, "Found", {"Location": location}, None
        )
        opener = MagicMock()
        opener.open.side_effect = [redirect, io.BytesIO(payload)]
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"GITHUB_TOKEN": "SYNTHETIC_TOKEN_ONLY"}),
            patch.object(github.urllib.request, "build_opener", return_value=opener),
            patch.object(github, "sha", return_value=entry["artifact_zip_sha256"]),
        ):
            destination = Path(tmp) / "download.zip"
            github.download(entry, destination)
            self.assertEqual(destination.read_bytes(), payload)
        first, second = opener.open.call_args_list
        self.assertEqual(
            first.args[0].get_header("Authorization"), "Bearer SYNTHETIC_TOKEN_ONLY"
        )
        self.assertEqual(first.args[0].get_method(), "GET")
        self.assertEqual(second.args, (location,))
        self.assertEqual(second.kwargs, {"timeout": 60})

    def test_untrusted_download_redirect_is_rejected_before_following(self):
        entry = core.policy()["approved_staging_sources"][0]
        for location in (
            "http://test.blob.core.windows.net/object",
            "https://test.blob.core.windows.net.evil.invalid/object",
            "https://credential@test.blob.core.windows.net/object",
            "https://test.blob.core.windows.net:8443/object",
        ):
            redirect = urllib.error.HTTPError(
                "https://api.github.com/", 302, "Found", {"Location": location}, None
            )
            opener = MagicMock()
            opener.open.side_effect = redirect
            with (
                self.subTest(location=location),
                patch.object(
                    github.urllib.request, "build_opener", return_value=opener
                ),
                self.assertRaises(core.Rejected),
            ):
                github.download(entry, Path("never-created.zip"))
            self.assertEqual(opener.open.call_count, 1)

    def test_subprocess_diagnostics_never_echo_arguments_or_output(self):
        error = subprocess.CalledProcessError(
            1,
            ["synthetic-tool", "SENSITIVE_ARGUMENT"],
            output=b"SENSITIVE_STDOUT",
            stderr=b"SENSITIVE_STDERR",
        )
        with (
            patch.object(core.subprocess, "run", side_effect=error),
            self.assertRaises(core.Rejected) as caught,
        ):
            core.call("synthetic-tool", "SENSITIVE_ARGUMENT")
        self.assertNotIn("SENSITIVE", str(caught.exception))
        self.assertIn("CalledProcessError", str(caught.exception))


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = workflow_policy.read_workflow(
            core.ROOT / ".github/workflows/release.yml"
        )

    def test_reviewed_workflow(self):
        self.assertTrue(workflow_policy.validate(self.workflow))

    def test_unsafe_workflow_capabilities_rejected(self):
        changes = [
            lambda v: v["on"].update(push={}),
            lambda v: v["permissions"].update(contents="write"),
            lambda v: v["jobs"]["staging"].pop("environment"),
            lambda v: v["jobs"]["staging"].update(needs=[]),
            lambda v: v["jobs"]["staging"].update(**{"continue-on-error": True}),
            lambda v: v["jobs"]["staging"]["steps"][0].update(
                uses="actions/checkout@main"
            ),
            lambda v: v["jobs"]["staging"]["steps"][-1]["with"].update(
                path="/tmp/private/**"
            ),
            lambda v: v["jobs"]["staging"]["steps"][3].update(
                run="echo ${{ inputs.source_commit }}"
            ),
            lambda v: v["jobs"]["staging"]["steps"][3].update(
                env={"KEY": "${{ secrets.PROD_KEY }}"}
            ),
        ]
        for index, change in enumerate(changes):
            value = copy.deepcopy(self.workflow)
            change(value)
            with self.subTest(index=index), self.assertRaises(core.Rejected):
                workflow_policy.validate(value)

    def test_single_maintainer_environment_requires_exact_branch_not_reviewers(self):
        value = {
            "name": "p5b-staging",
            "protection_rules": [{"type": "branch_policy"}],
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            },
        }
        branches = {
            "total_count": 1,
            "branch_policies": [
                {"name": core.policy()["workflow_branch"], "type": "branch"}
            ],
        }
        self.assertTrue(github.environment_eligible(value, branches))
        for mutate in [
            lambda x: x.update(protection_rules=[{"type": "required_reviewers"}]),
            lambda x: x.update(deployment_branch_policy=None),
            lambda x: x.update(name="another-environment"),
        ]:
            changed = copy.deepcopy(value)
            mutate(changed)
            with self.assertRaises(core.Rejected):
                github.environment_eligible(changed, branches)

    def test_protection_read_error_never_claims_approval(self):
        with patch.object(github, "get", side_effect=core.Rejected("unavailable")):
            with self.assertRaises(core.Rejected):
                github.check_environment()

    def test_preflight_ref_and_inputs_are_not_shell_code(self):
        with patch.dict(
            os.environ,
            {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_REF": "refs/pull/1/merge"},
        ):
            with self.assertRaises(core.Rejected):
                preflight.main()

    def test_existing_output_is_not_overwritten_on_cli_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".p5b-disposable-root").write_text("P5B STAGING ONLY\n")
            sentinel = root / "result.json"
            sentinel.write_text("preserve")
            entry = core.policy()["approved_staging_sources"][0]
            args = [
                "stage.py",
                "--archive",
                "missing",
                "--source-commit",
                entry["source_commit"],
                "--version",
                "0.1.0",
                "--ci-run-id",
                str(entry["ci_run_id"]),
                "--channel",
                "staging",
                "--authorization-ref",
                entry["authorization_ref"],
                "--output",
                str(root),
            ]
            with patch.object(sys, "argv", args):
                self.assertEqual(stage.main(), 1)
            self.assertEqual(sentinel.read_text(), "preserve")

    def test_hosted_offline_replay_forbidden(self):
        entry = core.policy()["approved_staging_sources"][0]
        with tempfile.TemporaryDirectory() as tmp:
            args = [
                "stage.py",
                "--archive",
                "missing",
                "--source-commit",
                entry["source_commit"],
                "--version",
                "0.1.0",
                "--ci-run-id",
                str(entry["ci_run_id"]),
                "--channel",
                "staging",
                "--authorization-ref",
                entry["authorization_ref"],
                "--output",
                str(Path(tmp) / "out"),
            ]
            with (
                patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}),
                patch.object(sys, "argv", args),
            ):
                self.assertEqual(stage.main(), 1)
            result = json.loads((Path(tmp) / "out/result.json").read_text())
            self.assertIn("live CI", result["error"])

    def test_no_source_tree_outputs(self):
        with self.assertRaises(core.Rejected):
            core.outside_source(core.ROOT / "ci-output/p5b")

    def test_parent_traversal_cannot_evade_source_boundary(self):
        with self.assertRaises(core.Rejected):
            core.outside_source(
                core.ROOT.parent / ".." / core.ROOT.parent.name / core.ROOT.name
            )


class HostedExecutionTests(unittest.TestCase):
    def setUp(self):
        self.commit = "a" * 40
        self.context = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "74Cerillion/CyrNava",
            "GITHUB_REF": "refs/heads/desktop/p2-production-integration",
            "GITHUB_ACTOR": "74Cerillion",
            "GITHUB_TRIGGERING_ACTOR": "74Cerillion",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": self.commit,
            "GITHUB_WORKFLOW_SHA": self.commit,
            "GITHUB_WORKFLOW_REF": (
                "74Cerillion/CyrNava/.github/workflows/release.yml"
                "@refs/heads/desktop/p2-production-integration"
            ),
        }

    def test_owner_manual_dispatch_with_immutable_execution_identity(self):
        self.assertTrue(github.execution_eligible(self.context, self.commit))

    def test_wrong_ref_repo_actor_workflow_or_rerun_is_rejected(self):
        cases = [
            ("GITHUB_ACTIONS", "false"),
            ("GITHUB_EVENT_NAME", "push"),
            ("GITHUB_REPOSITORY", "untrusted/fork"),
            ("GITHUB_REF", "refs/heads/main"),
            ("GITHUB_REF", "refs/tags/staging"),
            ("GITHUB_REF", "refs/pull/1/merge"),
            ("GITHUB_ACTOR", "another-account"),
            ("GITHUB_TRIGGERING_ACTOR", "another-account"),
            ("GITHUB_RUN_ATTEMPT", "2"),
            ("GITHUB_SHA", "main"),
            ("GITHUB_WORKFLOW_SHA", "b" * 40),
            (
                "GITHUB_WORKFLOW_REF",
                "untrusted/fork/.github/workflows/release.yml@main",
            ),
        ]
        for name, value in cases:
            with self.subTest(name=name, value=value), self.assertRaises(core.Rejected):
                github.execution_eligible({**self.context, name: value}, self.commit)

    def test_missing_context_never_authorizes_execution(self):
        for name in self.context:
            changed = self.context.copy()
            changed.pop(name)
            with self.subTest(name=name), self.assertRaises(core.Rejected):
                github.execution_eligible(changed, self.commit)

    def test_wrong_checkout_is_rejected(self):
        with self.assertRaises(core.Rejected):
            github.execution_eligible(self.context, "b" * 40)

    def test_preflight_checks_identity_and_environment_before_live_evidence(self):
        entry = core.policy()["approved_staging_sources"][0]
        context = {
            **self.context,
            "RELEASE_SOURCE": entry["source_commit"],
            "RELEASE_VERSION": "0.1.0",
            "RELEASE_CHANNEL": "staging",
            "RELEASE_AUTHORIZATION": entry["authorization_ref"],
            "RELEASE_CI_RUN": str(entry["ci_run_id"]),
        }
        with (
            patch.dict(os.environ, context, clear=True),
            patch.object(github, "check_execution") as execution,
            patch.object(github, "check_environment") as environment,
            patch.object(
                github, "live_evidence", return_value={"status": "PASS"}
            ) as live,
        ):
            preflight.main()
            execution.assert_called_once()
            environment.assert_called_once()
            live.assert_called_once_with(entry)
        for check in ["check_execution", "check_environment"]:
            with (
                patch.dict(os.environ, context, clear=True),
                patch.object(github, "check_execution"),
                patch.object(github, "check_environment"),
                patch.object(github, check, side_effect=core.Rejected("blocked")),
                patch.object(github, "live_evidence") as live,
            ):
                with self.assertRaises(core.Rejected):
                    preflight.main()
                live.assert_not_called()


if __name__ == "__main__":
    unittest.main()
