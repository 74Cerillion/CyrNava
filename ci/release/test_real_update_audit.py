"""P6 B authorization/audit regressions; synthetic payloads, no native rehearsal."""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import real_update
import real_update_audit as audit


class RealUpdateAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p6-audit-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.environment = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
        self.git("init", "--quiet", self.source)
        (self.source / "synthetic.txt").write_text("synthetic B source")
        self.git("-C", self.source, "add", "synthetic.txt")
        self.git(
            "-C",
            self.source,
            "-c",
            "user.name=Synthetic",
            "-c",
            "user.email=synthetic@invalid.example",
            "commit",
            "--quiet",
            "--no-gpg-sign",
            "-m",
            "synthetic B",
        )
        self.source_sha = self.git("-C", self.source, "rev-parse", "HEAD").strip()
        self.candidate = self.root / "candidate"
        self.candidate.mkdir()
        (self.candidate / core.BUNDLE).write_bytes(b"synthetic bundle; not Flatpak")
        bundle_sha = core.sha(self.candidate / core.BUNDLE)
        runtime = core.read_json(
            core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
        )
        self.metadata = {
            "status": "PASS",
            "app_id": core.APP_ID,
            "version": "0.1.0",
            "source_commit": self.source_sha,
            "sha256": bundle_sha,
            "ostree_commit": "b" * 64,
        }
        values = {
            "build-inputs.json": {
                "app_id": core.APP_ID,
                "git_commit": self.source_sha,
                "version": "0.1.0",
                "schema": 5,
                "runtime_lock": runtime,
            },
            "provenance.json": {
                **self.metadata,
                "artifact_bytes": (self.candidate / core.BUNDLE).stat().st_size,
                "runtime": runtime,
                "workflow_run_id": "41",
                "workflow_run_attempt": "1",
            },
            "result.json": {
                **self.metadata,
                "bytes": (self.candidate / core.BUNDLE).stat().st_size,
            },
            "package-inventory.json": {"status": "PASS", "files": []},
        }
        for name, value in values.items():
            (self.candidate / name).write_bytes(core.encode(value))
        (self.candidate / "SHA256SUMS").write_text(
            bundle_sha + "  " + core.BUNDLE + "\n"
        )
        self.entry = {
            "source_commit": self.source_sha,
            "ci_run_id": 41,
            "ci_run_attempt": 1,
            "artifact_id": 42,
            "artifact_zip_sha256": "c" * 64,
            "bundle_sha256": bundle_sha,
            "inputs_sha256": core.sha(self.candidate / "build-inputs.json"),
            "inventory_sha256": core.sha(self.candidate / "package-inventory.json"),
            "ostree_commit": "b" * 64,
            "authorization_ref": "P6-synthetic-test-only",
        }
        self.proposal = {
            "owner_approved_for_disposable_P6_update": True,
            "version": "0.1.0",
            "schema": 5,
            "entry": self.entry,
        }
        self.approval = self.root / "approval.json"
        self.approval.write_bytes(core.encode(self.proposal))
        self.approval_sha = core.sha(self.approval)
        self.native_auditor = SimpleNamespace(
            ROOT=None, audit_bundle=Mock(return_value=self.metadata)
        )
        self.output = self.root / "audit"
        self.output.mkdir()

    def git(self, *args):
        return subprocess.check_output(
            ["git", *map(str, args)],
            env=self.environment,
            text=True,
            stderr=subprocess.PIPE,
            timeout=30,
        )

    def invoke(self, *, source=None, expected_sha=None):
        with (
            patch.dict(os.environ, {"GITHUB_SHA": self.source_sha}),
            patch.object(core, "p5a", return_value=self.native_auditor),
        ):
            result = audit.audit_candidate(
                source or self.source,
                self.candidate,
                self.output,
                self.approval,
                expected_sha or self.approval_sha,
            )
        self.assertEqual(core.read_json(self.output / "audit-result.json"), result)
        return result

    def assert_failed_before_native(self, stage, **kwargs):
        result = self.invoke(**kwargs)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["complete"])
        self.assertEqual(result["stage"], stage)
        self.native_auditor.audit_bundle.assert_not_called()
        return result

    def test_P5B_still_rejects_B_while_P6_owner_approved_audit_succeeds(self):
        policy_before = (core.HERE / "policy.json").read_bytes()
        with self.assertRaisesRegex(
            core.Rejected, "Source is not approved for staging"
        ):
            core.approval(self.source_sha, "0.1.0", "staging", "P6-synthetic-test-only")
        result = self.invoke()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["source_commit"], self.source_sha)
        self.assertEqual(result["B_approval_sha256"], self.approval_sha)
        self.assertEqual(self.native_auditor.ROOT, self.source)
        self.native_auditor.audit_bundle.assert_called_once_with(
            self.candidate, self.output
        )
        self.assertEqual((core.HERE / "policy.json").read_bytes(), policy_before)

    def test_unapproved_B_fails_before_source_or_payload_operations(self):
        self.proposal["owner_approved_for_disposable_P6_update"] = False
        self.approval.write_bytes(core.encode(self.proposal))
        with patch.object(core, "call") as call:
            self.assert_failed_before_native(
                "owner-approval", expected_sha=core.sha(self.approval)
            )
        call.assert_not_called()

    def test_changed_approval_bytes_rejected_before_source_operations(self):
        self.approval.write_bytes(self.approval.read_bytes() + b"\n")
        with patch.object(core, "call") as call:
            self.assert_failed_before_native("owner-approval")
        call.assert_not_called()

    def test_wrong_checkout_SHA_rejected(self):
        (self.source / "synthetic.txt").write_text("another synthetic commit")
        self.git("-C", self.source, "add", "synthetic.txt")
        self.git(
            "-C",
            self.source,
            "-c",
            "user.name=Synthetic",
            "-c",
            "user.email=synthetic@invalid.example",
            "commit",
            "--quiet",
            "--no-gpg-sign",
            "-m",
            "another commit",
        )
        self.assert_failed_before_native("source-binding")

    def test_dirty_checkout_rejected(self):
        (self.source / "synthetic.txt").write_text("uncommitted synthetic edit")
        self.assert_failed_before_native("source-cleanliness")

    def test_environment_source_binding_cannot_be_substituted(self):
        with patch.dict(os.environ, {"GITHUB_SHA": "f" * 40}):
            result = audit.audit_candidate(
                self.source,
                self.candidate,
                self.output,
                self.approval,
                self.approval_sha,
            )
        self.assertEqual(result["stage"], "source-binding")
        self.assertEqual(result["status"], "FAIL")

    def test_symlink_source_rejected(self):
        link = self.root / "source-link"
        link.symlink_to(self.source, target_is_directory=True)
        self.assert_failed_before_native("source-binding", source=link)

    def test_changed_bundle_rejected_by_unchanged_candidate_validator(self):
        (self.candidate / core.BUNDLE).write_bytes(b"tampered synthetic bundle")
        self.assert_failed_before_native("candidate-validation")

    def test_native_audit_failure_is_not_treated_as_success(self):
        self.native_auditor.audit_bundle.side_effect = ValueError("SECRET/path/token")
        result = self.invoke()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["stage"], "exported-payload-audit")
        self.assertEqual(result["category"], "invalid-data")
        self.assertNotIn("SECRET", str(result))

    def test_wrong_exported_identity_rejected_after_audit(self):
        self.native_auditor.audit_bundle.return_value = dict(
            self.metadata, source_commit="f" * 40
        )
        result = self.invoke()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["stage"], "audit-result-validation")

    def test_nonempty_output_preserved_without_overwriting_evidence(self):
        sentinel = self.output / "preserve"
        sentinel.write_bytes(b"existing synthetic evidence")
        result = audit.audit_candidate(
            self.source, self.candidate, self.output, self.approval, self.approval_sha
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["stage"], "output-guard")
        self.assertEqual(sentinel.read_bytes(), b"existing synthetic evidence")
        self.assertFalse((self.output / "audit-result.json").exists())

    def run_child(self):
        return audit.run(
            self.source,
            self.candidate,
            self.output,
            self.approval,
            self.entry,
            self.approval_sha,
        )

    def test_real_Python_child_emits_safe_failure_record_for_false_approval(self):
        self.proposal["owner_approved_for_disposable_P6_update"] = False
        self.approval.write_bytes(core.encode(self.proposal))
        self.approval_sha = core.sha(self.approval)
        with self.assertRaises(audit.AuditFailure) as caught:
            self.run_child()
        self.assertEqual(
            caught.exception.diagnostic,
            {
                "operation": audit.OPERATION,
                "category": "exit-1",
                "child_stage": "owner-approval",
            },
        )
        self.assertEqual(
            core.read_json(self.output / "audit-result.json")["status"], "FAIL"
        )
        self.assertNotIn(str(self.root), str(caught.exception))

    def test_parent_failures_never_expose_argv_stderr_or_environment(self):
        sensitive = "https://user:TOKEN_SECRET@invalid.example/private/path"
        errors = [
            (subprocess.CalledProcessError(7, [sensitive], stderr=sensitive), "exit-7"),
            (subprocess.TimeoutExpired([sensitive], 1, stderr=sensitive), "timeout"),
            (OSError(sensitive), "unavailable"),
        ]
        for error, category in errors:
            with (
                self.subTest(category=category),
                patch.object(subprocess, "run", side_effect=error),
                self.assertRaises(audit.AuditFailure) as caught,
            ):
                self.run_child()
            self.assertEqual(
                caught.exception.diagnostic,
                {
                    "operation": audit.OPERATION,
                    "category": category,
                },
            )
            self.assertNotIn("TOKEN_SECRET", str(caught.exception))
            self.assertNotIn(str(self.root), str(caught.exception))

    def test_untrusted_diagnostic_stage_is_not_copied_to_parent(self):
        (self.output / "audit-result.json").write_bytes(
            core.encode(
                {
                    "status": "FAIL",
                    "complete": True,
                    "operation": audit.OPERATION,
                    "stage": "SECRET/private/path",
                    "category": "SECRET",
                }
            )
        )
        with (
            patch.object(
                subprocess, "run", side_effect=subprocess.CalledProcessError(1, [])
            ),
            self.assertRaises(audit.AuditFailure) as caught,
        ):
            self.run_child()
        self.assertEqual(
            caught.exception.diagnostic,
            {"operation": audit.OPERATION, "category": "exit-1"},
        )

    def test_zero_exit_with_missing_evidence_fails_closed(self):
        with (
            patch.object(subprocess, "run"),
            self.assertRaises(OSError),
        ):
            self.run_child()

    def test_malformed_child_diagnostic_does_not_escape_fixed_parent_reporting(self):
        for raw in (b"[]", b"not JSON"):
            (self.output / "audit-result.json").write_bytes(raw)
            with (
                self.subTest(raw=raw),
                patch.object(
                    subprocess, "run", side_effect=subprocess.CalledProcessError(1, [])
                ),
                self.assertRaises(audit.AuditFailure) as caught,
            ):
                self.run_child()
            self.assertEqual(
                caught.exception.diagnostic,
                {"operation": audit.OPERATION, "category": "exit-1"},
            )

    def test_zero_exit_with_incorrect_evidence_fails_closed(self):
        valid = {
            **self.metadata,
            "operation": audit.OPERATION,
            "complete": True,
            "B_approval_sha256": self.approval_sha,
        }
        for field, wrong in {
            "status": "FAIL",
            "complete": False,
            "source_commit": "f" * 40,
            "sha256": "f" * 64,
            "ostree_commit": "f" * 64,
            "B_approval_sha256": "f" * 64,
            "operation": "another-operation",
        }.items():
            (self.output / "audit-result.json").write_bytes(
                core.encode(dict(valid, **{field: wrong}))
            )
            with (
                self.subTest(field=field),
                patch.object(subprocess, "run"),
                self.assertRaisesRegex(core.Rejected, "differs from approved identity"),
            ):
                self.run_child()

    def test_parent_invokes_P6_child_with_exact_source_and_approval_binding(self):
        (self.output / "audit-result.json").write_bytes(
            core.encode(
                {
                    **self.metadata,
                    "operation": audit.OPERATION,
                    "complete": True,
                    "B_approval_sha256": self.approval_sha,
                }
            )
        )
        with patch.object(subprocess, "run") as run:
            self.assertEqual(self.run_child()["source_commit"], self.source_sha)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "real_update_audit.py")
        self.assertEqual(command[command.index("--b-approval") + 1], str(self.approval))
        self.assertEqual(
            command[command.index("--approval-sha256") + 1], self.approval_sha
        )
        self.assertEqual(run.call_args.kwargs["env"]["GITHUB_SHA"], self.source_sha)

    def test_mocked_preparation_audit_failure_retains_FAIL_and_removes_partial_key_home(
        self,
    ):
        pair = self.root / "pair"

        def fake_generation(candidate, public, private, entry, url):
            (private / "key/private-keys-v1.d").mkdir(parents=True)
            (private / "key/private-keys-v1.d/synthetic").write_text("not a key")
            public.mkdir()
            for name in ("manifest.json", "manifest.json.sig"):
                (public / name).write_text("synthetic")
            return {"signing_fingerprint": "A" * 40}

        diagnostic = {
            "operation": audit.OPERATION,
            "category": "exit-1",
            "child_stage": "candidate-validation",
        }
        with (
            patch.object(core, "extract_artifact"),
            patch.object(core, "generate_repository", side_effect=fake_generation),
            patch.object(core, "seal"),
            patch.object(core, "checkout_accepted_source", return_value=self.source),
            patch.object(core, "call", return_value=self.source_sha.encode()) as call,
            patch.object(audit, "run", side_effect=audit.AuditFailure(diagnostic)),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = real_update.prepare(
                pair, self.root / "a.zip", self.root / "b.zip", self.approval
            )
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["complete"])
        self.assertEqual(result["operation"], audit.OPERATION)
        self.assertEqual(result["failure"], diagnostic)
        self.assertEqual(result["checks"]["disposable_signing_key_removed"], "PASS")
        self.assertFalse((pair / "p/key").exists())
        self.assertFalse((pair / "b").exists())
        self.assertEqual(core.read_json(pair / "prepared.json"), result)
        self.assertFalse(any(c.args[0] == "flatpak" for c in call.call_args_list))

    def test_existing_pair_cannot_be_reused_or_overwritten(self):
        pair = self.root / "failed-pair"
        pair.mkdir()
        sentinel = pair / "prepared.json"
        sentinel.write_text('{"status":"FAIL","historical":true}')
        original = sentinel.read_bytes()
        with (
            patch.object(core, "extract_artifact") as extract,
            self.assertRaises(FileExistsError),
        ):
            real_update.prepare(
                pair, self.root / "a.zip", self.root / "b.zip", self.approval
            )
        extract.assert_not_called()
        self.assertEqual(sentinel.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
