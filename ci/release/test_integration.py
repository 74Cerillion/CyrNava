"""P5C deterministic trust boundaries. Native rehearsal is a separate CLI."""

import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import client
import core
import integration
import integration_policy
import readiness
import workflow_policy


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p5c-")
        self.root = Path(self.temp.name)
        self.c = client.Client(self.root / "c")

    def tearDown(self):
        self.temp.cleanup()

    def test_environment_does_not_inherit_owner_configuration_or_credentials(self):
        self.c.guard()
        self.assertNotIn("HOME", self.c.env)
        self.assertNotIn("GITHUB_TOKEN", self.c.env)
        self.assertNotIn("DBUS_SESSION_BUS_ADDRESS", self.c.env)
        for key in (
            "FLATPAK_USER_DIR",
            "TMPDIR",
            "GNUPGHOME",
            "XDG_CONFIG_HOME",
            "XDG_DATA_HOME",
        ):
            self.assertEqual(Path(self.c.env[key]).parent, self.c.root)

    def test_existing_profile_and_missing_marker_refused(self):
        with self.assertRaises(FileExistsError):
            client.Client(self.c.root)
        (self.c.root / ".p5c-client").unlink()
        with patch.object(subprocess, "run") as run, self.assertRaises(core.Rejected):
            self.c.run("list", "list")
        run.assert_not_called()

    def test_environment_path_escape_and_symlink_refused(self):
        self.c.env["TMPDIR"] = "/tmp"
        with self.assertRaises(core.Rejected):
            self.c.guard()
        self.c.env["TMPDIR"] = str(self.c.root / "link")
        (self.c.root / "link").symlink_to(self.root)
        with self.assertRaises(core.Rejected):
            self.c.guard()

    def test_untrusted_stderr_and_operation_are_redacted(self):
        r = subprocess.CompletedProcess(
            [], 1, b"", b"GPG signature SECRET_VALUE https://token@invalid.example"
        )
        with (
            patch.object(subprocess, "run", return_value=r),
            self.assertRaises(client.NativeFailure) as e,
        ):
            self.c.run("install", "install", "untrusted")
        self.assertEqual(e.exception.category, "signature")
        self.assertNotIn("SECRET_VALUE", str(e.exception))
        with self.assertRaisesRegex(core.Rejected, "Unreviewed"):
            self.c.run("SECRET_VALUE", "list")

    def test_installed_or_updated_commit_mismatch_rejected(self):
        with (
            patch.object(self.c, "verify_remote"),
            patch.object(self.c, "verify_summary"),
            patch.object(self.c, "run", return_value="b" * 64),
        ):
            with self.assertRaisesRegex(
                core.Rejected, "Updated application commit mismatch"
            ):
                self.c.update(client.FIXTURE_ID, "a" * 64)

    def test_deployment_outside_private_installation_is_rejected_before_read(self):
        with (
            patch.object(self.c, "run", return_value="/unapproved-workspace"),
            self.assertRaisesRegex(core.Rejected, "escaped"),
        ):
            self.c.installed_source("a" * 40)

    def test_signature_flags_must_both_be_enabled(self):
        repo = self.c.root / "flatpak/repo"
        repo.mkdir()
        for missing in ("gpg-verify", "gpg-verify-summary"):
            (repo / "config").write_text(
                '[remote "p5c"]\ngpg-verify=true\ngpg-verify-summary=true\n'.replace(
                    missing + "=true", missing + "=false"
                )
            )
            with self.subTest(missing=missing), self.assertRaises(core.Rejected):
                self.c.verify_summary()


class DescriptorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p5c-")
        self.root = Path(self.temp.name)
        self.key = self.root / "key.gpg"
        self.key.write_bytes(b"synthetic PUBLIC key bytes")
        import update_fixture

        self.path = self.root / "fixture.flatpakref"
        update_fixture.descriptor(
            self.path, "http://127.0.0.1:1234/current/repo/", self.key
        )
        self.fp = "A" * 40

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_key_and_descriptor_identity(self):
        with patch.object(client, "fingerprint", return_value=self.fp):
            self.assertTrue(
                client.validate_descriptor(
                    self.path, self.key, self.fp, self.root, client.FIXTURE_ID
                )
            )

    def test_wrong_key_external_host_or_descriptor_capability_rejected(self):
        text = self.path.read_text()
        for old, new in [
            ("127.0.0.1", "example.com"),
            (client.FIXTURE_ID, core.APP_ID),
            ("Branch=stable", "Branch=evil"),
            ("IsRuntime=false", "IsRuntime=true"),
            ("[Flatpak Ref]", "[Flatpak Ref]\nSuggestRemoteName=system"),
        ]:
            self.path.write_text(text.replace(old, new))
            with (
                self.subTest(value=new),
                patch.object(client, "fingerprint", return_value=self.fp),
                self.assertRaises(core.Rejected),
            ):
                client.validate_descriptor(
                    self.path, self.key, self.fp, self.root, client.FIXTURE_ID
                )
        self.path.write_text(text)
        with (
            patch.object(client, "fingerprint", return_value="B" * 40),
            self.assertRaisesRegex(core.Rejected, "fingerprint mismatch"),
        ):
            client.validate_descriptor(
                self.path, self.key, self.fp, self.root, client.FIXTURE_ID
            )


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p5c-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_diagnostic_whitelist_excludes_keys_and_repository(self):
        root = self.root / "r"
        root.mkdir()
        (root / ".p5c-disposable-root").write_bytes(
            core.encode({"purpose": "P5C disposable integration"})
        )
        (root / "result.json").write_bytes(
            core.encode({"status": "PASS", "complete": True})
        )
        (root / "private-key").write_text("PRIVATE KEY forbidden")
        (root / "repo").mkdir()
        integration.export_diagnostics(root, self.root / "diag")
        self.assertEqual(
            {p.name for p in (self.root / "diag").iterdir()},
            {"result.json", "SHA256SUMS.json"},
        )

    def test_diagnostic_symlink_or_missing_status_refused(self):
        root = self.root / "r"
        root.mkdir()
        (root / ".p5c-disposable-root").write_bytes(
            core.encode({"purpose": "P5C disposable integration"})
        )
        secret = self.root / "sensitive.json"
        secret.write_text('{"secret":"PRIVATE KEY"}')
        (root / "result.json").symlink_to(secret)
        with self.assertRaises(core.Rejected):
            integration.export_diagnostics(root, self.root / "diag")

    def test_unexpected_failure_always_has_redacted_complete_evidence(self):
        output = self.root / "out"
        with (
            patch.object(
                sys,
                "argv",
                ["integration.py", "--archive", "unused", "--output", str(output)],
            ),
            patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}),
            patch.object(integration, "prepare_environment", return_value={}),
            patch.object(integration, "run", side_effect=RuntimeError("SECRET_VALUE")),
            patch.object(core, "call", return_value=b"synthetic\n"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(integration.main(), 1)
        record = core.read_json(output / "result.json")
        self.assertTrue(record["complete"])
        self.assertEqual(record["status"], "FAIL")
        self.assertEqual(record["private_key_cleanup"], "PASS")
        self.assertNotIn("SECRET_VALUE", json.dumps(record))

    def test_partial_key_home_cleaned_without_success_marker(self):
        root = self.root / "out"
        (root / "p/key").mkdir(parents=True)
        (root / ".p5c-disposable-root").write_bytes(
            core.encode({"purpose": "P5C disposable integration"})
        )
        (root / "p/key/partial-secret").write_text("synthetic")
        with patch.object(core, "call"):
            integration.cleanup_keys([root / "p/key"])
        self.assertFalse((root / "p/key").exists())

    def test_setup_failure_precedes_native_processing_and_exports_final_fail(self):
        output = self.root / "setup"
        diag = self.root / "diag"
        with (
            patch.object(
                sys,
                "argv",
                [
                    "integration.py",
                    "--setup-failed",
                    "--live",
                    "--output",
                    str(output),
                    "--diagnostics",
                    str(diag),
                ],
            ),
            patch.object(integration, "run") as run,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(integration.main(), 1)
        run.assert_not_called()
        record = core.read_json(diag / "result.json")
        self.assertEqual(record["status"], "FAIL")
        self.assertTrue(record["complete"])
        self.assertFalse((output / "p").exists())

    def test_cleanup_failure_overrides_otherwise_successful_run(self):
        output = self.root / "out"

        def success(*args):
            args[-1]["status"] = "PASS"

        with (
            patch.object(
                sys,
                "argv",
                ["integration.py", "--archive", "unused", "--output", str(output)],
            ),
            patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}),
            patch.object(integration, "prepare_environment", return_value={}),
            patch.object(integration, "run", side_effect=success),
            patch.object(core, "call", return_value=b"synthetic\n"),
            patch.object(
                integration, "cleanup_keys", side_effect=core.Rejected("synthetic")
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(integration.main(), 1)
        self.assertEqual(
            core.read_json(output / "result.json")["private_key_cleanup"], "FAIL"
        )

    def test_existing_output_is_not_overwritten(self):
        output = self.root / "out"
        output.mkdir()
        (output / "result.json").write_text("preserve")
        with (
            patch.object(
                sys, "argv", ["integration.py", "--live", "--output", str(output)]
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(integration.main(), 1)
        self.assertEqual((output / "result.json").read_text(), "preserve")

    def test_insufficient_space_stops_before_repository_or_key_generation(self):
        archive = self.root / "artifact.zip"
        archive.write_bytes(b"synthetic")
        output = self.root / "out"
        output.mkdir()

        def extracted(_archive, destination, _entry):
            destination.mkdir()
            (destination / "package-inventory.json").write_bytes(
                core.encode({"logical_bytes": 100})
            )

        from types import SimpleNamespace

        with (
            patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}),
            patch.object(core, "extract_artifact", side_effect=extracted),
            patch.object(shutil, "disk_usage", return_value=SimpleNamespace(free=0)),
            patch.object(core, "generate_repository") as generate,
            self.assertRaisesRegex(core.Rejected, "Insufficient space"),
        ):
            integration.run(
                output, core.policy()["approved_staging_sources"][0], archive, False, {}
            )
        generate.assert_not_called()

    def test_cleanup_outside_marked_key_homes_rejected(self):
        wrong = self.root / "normal-profile"
        wrong.mkdir()
        with self.assertRaises(core.Rejected):
            integration.cleanup_keys([wrong])
        self.assertTrue(wrong.exists())


class WorkflowTests(unittest.TestCase):
    def test_proposed_workflow_and_every_job_dependency_history_boundary(self):
        w = workflow_policy.read_workflow(core.HERE / "p5c-workflow.yml")
        self.assertTrue(integration_policy.validate(w))
        for name in w["jobs"]:
            for defect in ("history", "dependencies"):
                changed = copy.deepcopy(w)
                job = changed["jobs"][name]
                if defect == "history":
                    job["steps"][0]["with"]["fetch-depth"] = 1
                else:
                    step = next(
                        s
                        for s in job["steps"]
                        if "--require-hashes" in s.get("run", "")
                    )
                    step["run"] = step["run"].replace("--require-hashes", "")
                with (
                    self.subTest(job=name, defect=defect),
                    self.assertRaises(core.Rejected),
                ):
                    integration_policy.validate(changed)

    def test_context_rejects_wrong_branch_owner_source_workflow_or_retry(self):
        sha = "a" * 40
        ref = "refs/heads/desktop/p2-production-integration"
        c = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "74Cerillion/CyrNava",
            "GITHUB_REF": ref,
            "GITHUB_ACTOR": "74Cerillion",
            "GITHUB_TRIGGERING_ACTOR": "74Cerillion",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": sha,
            "GITHUB_WORKFLOW_SHA": sha,
            "GITHUB_WORKFLOW_REF": "74Cerillion/CyrNava/.github/workflows/p5c.yml@"
            + ref,
            "P5C_AUTHORIZATION": "P5C-owner-authorized-disposable-integration-only",
        }
        self.assertTrue(integration_policy.context_eligible(c, sha, sha))
        for key in c:
            changed = {**c, key: "unauthorized"}
            with self.subTest(field=key), self.assertRaises(core.Rejected):
                integration_policy.context_eligible(changed, sha, sha)
        with self.assertRaises(core.Rejected):
            integration_policy.context_eligible(c, sha, "b" * 40)


class ReadinessTests(unittest.TestCase):
    def test_lock_inventory_records_partial_coverage_and_pinned_versions(self):
        sbom = readiness.inventory(core.ROOT)
        self.assertTrue(
            any(c["purl"].startswith("pkg:pypi/fastapi@") for c in sbom["components"])
        )
        self.assertTrue(
            any(c["purl"].startswith("pkg:npm/") for c in sbom["components"])
        )
        self.assertIn("not a complete", sbom["metadata"]["properties"][0]["value"])

    def test_paginated_advisories_fail_closed(self):
        import io

        response = io.BytesIO(b'{"results":[{"next_page_token":"more"}]}')
        with patch.object(readiness.urllib.request, "urlopen", return_value=response):
            result = readiness.advisories(
                {"components": [{"purl": "pkg:npm/synthetic@1"}]}
            )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["queried"], 0)

    def test_unavailable_advisories_never_claim_clearance(self):
        with patch.object(
            readiness.urllib.request, "urlopen", side_effect=OSError("SECRET")
        ):
            v = readiness.advisories({"components": [{"purl": "pkg:pypi/synthetic@1"}]})
        self.assertEqual(v["status"], "INCOMPLETE")
        self.assertNotIn("SECRET", json.dumps(v))


if __name__ == "__main__":
    unittest.main()
