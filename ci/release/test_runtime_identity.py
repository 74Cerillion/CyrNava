"""P6 post-transaction runtime drift regressions; no native execution."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import client
import core
import native_distribution
import progress
import real_update


class RuntimeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p6-runtime-identity-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.client = native_distribution.RuntimeClient(self.root / "client")
        self.ref = "org.kde.Platform/x86_64/6.11"
        self.expected = core.read_json(
            core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
        )["refs"]["org.kde.Platform//6.11"]
        self.drifted = (
            "fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415"
        )

    def test_exact_runtime_commit_is_verified_not_only_branch_name(self):
        with patch.object(self.client, "run", side_effect=[self.ref, self.expected]):
            self.assertEqual(
                self.client.verify_runtime(),
                {
                    "status": "PASS",
                    "runtime_ref": self.ref,
                    "commit": self.expected,
                },
            )

    def test_same_branch_changed_commit_fails_closed_without_repin_or_launch(self):
        with (
            patch.object(
                self.client, "run", side_effect=[self.ref, self.drifted]
            ) as reads,
            patch.object(self.client, "command") as mutate,
            self.assertRaises(native_distribution.RuntimeIdentityFailure) as caught,
        ):
            self.client.verify_runtime()
        self.assertEqual(
            caught.exception.diagnostic,
            {
                "category": "runtime-commit-drift",
                "runtime_ref": self.ref,
                "expected_commit": self.expected,
                "actual_commit": self.drifted,
            },
        )
        mutate.assert_not_called()
        self.assertTrue(all(c.args[1] == "info" for c in reads.call_args_list))

    def test_unexpected_runtime_ref_is_rejected_without_exposing_input(self):
        with (
            patch.object(self.client, "run", return_value="SECRET/private/path"),
            self.assertRaises(native_distribution.RuntimeIdentityFailure) as caught,
        ):
            self.client.verify_runtime()
        self.assertEqual(
            caught.exception.diagnostic["category"], "runtime-ref-mismatch"
        )
        self.assertNotIn("SECRET", str(caught.exception.diagnostic))

    def test_malformed_commit_is_rejected_without_echoing_it(self):
        with (
            patch.object(self.client, "run", side_effect=[self.ref, "SECRET"]),
            self.assertRaisesRegex(core.Rejected, "Invalid runtime commit") as caught,
        ):
            self.client.verify_runtime()
        self.assertNotIn("SECRET", str(caught.exception))

    def install(self, runtime_commit):
        public = self.root / "public"
        public.mkdir()
        (public / "staging-public.gpg").write_bytes(b"synthetic public key")
        location = self.client.root / "flatpak/synthetic-deployment"
        inputs = location / "files/share/cyrnava/build-inputs.json"
        inputs.parent.mkdir(parents=True)
        inputs.write_bytes(core.encode({"version": "0.1.0", "schema": 5}))
        application_commit = "a" * 64
        calls = []

        def transaction(operation, *args):
            calls.append((operation, *args))
            if operation == "location":
                return str(location)
            if "--show-permissions" in args:
                return "[Context]\nsockets=wayland;\ndevices=dri;\n"
            if "--show-runtime" in args:
                return self.ref
            if "--show-commit" in args:
                return runtime_commit
            return ""

        with (
            patch.object(client, "validate_descriptor"),
            patch.object(self.client, "verify_summary"),
            patch.object(self.client, "installed_source"),
            patch.object(self.client, "verify_remote"),
            patch.object(self.client, "commit", return_value=application_commit),
            patch.object(self.client, "run", side_effect=transaction),
        ):
            try:
                result = self.client.install_real(
                    "http://127.0.0.1/", public, "A" * 40, application_commit, "a" * 40
                )
            finally:
                install = next(c for c in calls if c[0] == "install")
                self.assertIn("--noninteractive", install)
                self.assertNotIn("--no-deps", install)
        return result

    def test_normal_dependency_install_cannot_report_PASS_after_runtime_drift(self):
        with self.assertRaises(native_distribution.RuntimeIdentityFailure):
            self.install(self.drifted)

    def test_normal_install_reports_exact_post_transaction_runtime_identity(self):
        result = self.install(self.expected)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["runtime_identity"]["commit"], self.expected)
        self.assertEqual(result["runtime"], self.ref)

    def test_prelaunch_recheck_blocks_changed_runtime_and_preserves_prepared_pair(self):
        pair = self.root / "pair"
        pair.mkdir()
        (pair / ".p6-real-update").write_bytes(
            core.encode({"purpose": "disposable P6 real update"})
        )
        (pair / "prepared.json").write_bytes(
            core.encode(
                {
                    "status": "PASS",
                    "complete": True,
                    "fingerprint": "A" * 40,
                    "A": {"source_commit": "a" * 40, "ostree_commit": "a" * 64},
                    "B": {"source_commit": "b" * 40, "ostree_commit": "b" * 64},
                }
            )
        )
        before = (pair / "prepared.json").read_bytes()
        diagnostic = {
            "category": "runtime-commit-drift",
            "expected_commit": self.expected,
            "actual_commit": self.drifted,
            "runtime_ref": self.ref,
        }

        class SyntheticClient:
            def __init__(self, root, progress):
                self.root, self.env = root, {}

            def runtimes(self):
                return {"status": "PASS"}

            def install_real(self, *args):
                return {"status": "PASS"}

            def verify_runtime(self):
                raise native_distribution.RuntimeIdentityFailure(diagnostic)

        attempt = self.root / "attempt"
        with (
            patch.object(native_distribution, "RuntimeClient", SyntheticClient),
            patch.object(real_update, "desktop_environment", return_value={}),
            patch.object(real_update.distribution, "plan", return_value={}),
            patch.object(real_update.distribution, "publish"),
            patch.object(
                real_update.distribution,
                "loopback",
                return_value=contextlib.nullcontext("http://127.0.0.1/"),
            ),
            patch.object(progress.Progress, "command") as launch,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = real_update.exercise(pair, attempt)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["complete"])
        self.assertFalse(result["generation_A_launch_attempted"])
        self.assertEqual(result["runtime_identity_failure"], diagnostic)
        launch.assert_not_called()
        self.assertEqual((pair / "prepared.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
