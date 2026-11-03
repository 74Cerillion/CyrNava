"""Synthetic policy/driver tests. Never acquire dependencies or run Flatpak."""

import contextlib
import copy
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


build = module("candidate_build_test", HERE / "build_candidate.py")
probe = module("candidate_probe_test", HERE / "provider_probe.py")
LOCK = json.loads((HERE / "candidate.lock.json").read_text())


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix="p6-candidate-fixture-", dir=build.ROOT / "ci-output"
        )
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def good_provider(self):
        return {
            "python": [3, 13],
            "pyside": "6.11.3",
            "shiboken": "6.11.3",
            "qt": "6.11.3",
            "webengine": "6.11.3",
            "bindings_in_app": True,
            "shiboken_in_app": True,
            "wheel_qt": False,
            "runtime_qt_core": True,
            "application_webengine": True,
            "unique_qt_providers": True,
            "all_qt_providers_approved": True,
            "resources": True,
            "plugins": True,
            "flatpak_integration_marker": True,
            "missing_libraries": [],
            "sandbox_disabled": False,
            "renderer": "NOT EXECUTED",
            "normal_launcher": "NOT EXECUTED",
        }

    def test_import_evidence_never_promoted_to_renderer_or_release(self):
        value = probe.verify(self.good_provider())
        self.assertEqual(value["renderer"], "NOT EXECUTED")
        self.assertEqual(value["normal_launcher"], "NOT EXECUTED")
        self.assertNotIn("release", value)

    def test_wrong_abi_version_provider_and_security_inputs_rejected(self):
        bad = {
            "python": [3, 14],
            "pyside": "6.11.2",
            "shiboken": "6.11.2",
            "qt": "6.12.0",
            "webengine": "6.11.1",
            "bindings_in_app": False,
            "shiboken_in_app": False,
            "wheel_qt": True,
            "runtime_qt_core": False,
            "application_webengine": False,
            "unique_qt_providers": False,
            "all_qt_providers_approved": False,
            "resources": False,
            "plugins": False,
            "flatpak_integration_marker": False,
            "missing_libraries": ["missing"],
            "sandbox_disabled": True,
        }
        for key, value in bad.items():
            with self.subTest(key=key):
                record = self.good_provider()
                record[key] = value
                with self.assertRaises(ValueError):
                    probe.verify(record)

    def test_capacity_boundaries(self):
        build.capacity(2 * build.GIB, 7 * build.GIB, LOCK["budget"])
        for free, added in ((build.GIB, 0), (2 * build.GIB, 8 * build.GIB)):
            with self.subTest(free=free, added=added), self.assertRaises(build.Stopped):
                build.capacity(free, added, LOCK["budget"])

    def test_existing_or_outside_output_is_preserved(self):
        for path in (self.root, Path("/tmp/p6-binary-candidate-test"), build.ROOT):
            with self.subTest(path=path), self.assertRaises(build.Stopped):
                build.safe_new_output(path)
        self.assertTrue(self.root.exists())

    def test_symlink_attempt_refused(self):
        path = build.ROOT / "ci-output/p6-binary-candidate-fixture-link"
        path.symlink_to(self.root)
        try:
            with self.assertRaises(build.Stopped):
                build.safe_new_output(path)
        finally:
            path.unlink()  # Newly created fixture link only.

    def test_remote_key_url_and_signature_policy(self):
        key = self.root / "public.gpg"
        key.write_bytes(b"synthetic public key placeholder")
        text = '[remote "flathub"]\nurl=https://dl.flathub.org/repo/\ngpg-verify=true\ngpg-verify-summary=true\n'
        build.check_remote(text, LOCK["remote"], key, build.sha(key))
        for variant in (text.replace("true", "false"), text.replace("https:", "http:")):
            with self.assertRaises(build.Stopped):
                build.check_remote(variant, LOCK["remote"], key, build.sha(key))
        with self.assertRaises(build.Stopped):
            build.check_remote(text, LOCK["remote"], key, "0" * 64)

    def test_clean_environment_no_host_qt_python_or_signing_overrides(self):
        with patch.dict(
            os.environ,
            {
                "LD_LIBRARY_PATH": "/bad",
                "PYTHONPATH": "/bad",
                "GNUPGHOME": "/personal",
                "QTWEBENGINE_DISABLE_SANDBOX": "1",
            },
        ):
            attempt = build.Attempt(self.root, LOCK)
        for name in ("LD_LIBRARY_PATH", "PYTHONPATH", "QTWEBENGINE_DISABLE_SANDBOX"):
            self.assertNotIn(name, attempt.env)
        for name in ("HOME", "GNUPGHOME", "FLATPAK_USER_DIR", "TMPDIR"):
            self.assertTrue(Path(attempt.env[name]).is_relative_to(self.root))

    def acquisition(self, *, changed=False, fail=None):
        lock = copy.deepcopy(LOCK)
        key = self.root / "fixture-public.gpg"
        key.write_bytes(b"synthetic-public-key")
        lock["trusted_keys_sha256"] = build.sha(key)
        attempt = build.Attempt(self.root, lock)
        calls = []

        def run(operation, *args, **kwargs):
            calls.append((operation, args))
            if fail == operation:
                raise build.Stopped("fixture failure")
            if operation == "remote-add":
                repo = self.root / "flatpak/repo"
                repo.mkdir()
                (repo / "flathub.trustedkeys.gpg").write_bytes(key.read_bytes())
                (repo / "config").write_text(
                    '[remote "flathub"]\nurl=https://dl.flathub.org/repo/\ngpg-verify=true\ngpg-verify-summary=true\n'
                )
            if operation.startswith("remote-identity-"):
                commits = list(lock["refs"].values()) + [
                    lock["layered_webengine"]["commit"]
                ]
                return ("0" * 64 if changed else commits[int(operation[-1])]) + "\n"
            if operation.startswith("binding-"):
                return repr([list(lock["refs"])[int(operation[-1])]])
            return ""

        attempt.run = run
        attempt.verify_refs = lambda: None
        return attempt, calls

    def test_exact_signed_binary_acquisition_not_duplicate_webengine(self):
        attempt, calls = self.acquisition()
        attempt.acquire()
        pulls = [args for op, args in calls if op.startswith("pull-")]
        self.assertEqual(len(pulls), 3)
        for args in pulls:
            self.assertIn("--network-retries=0", args)
            self.assertIn("--depth=0", args)
            self.assertIn(args[-1], LOCK["refs"].values())
        self.assertNotIn(LOCK["layered_webengine"]["commit"], [x[-1] for x in pulls])
        self.assertEqual(next(op for op, _ in calls), "namespace")
        for i in range(3):
            ops = [op for op, _ in calls]
            self.assertLess(ops.index(f"signature-{i}"), ops.index(f"deploy-{i}"))
            self.assertLess(ops.index(f"binding-{i}"), ops.index(f"deploy-{i}"))

    def test_ref_movement_stops_before_large_download(self):
        attempt, calls = self.acquisition(changed=True)
        with self.assertRaisesRegex(build.Stopped, "ref moved"):
            attempt.acquire()
        self.assertFalse(any(op.startswith("pull-") for op, _ in calls))

    def test_namespace_or_signature_failure_stops_before_deploy(self):
        for failure in ("namespace", "signature-0"):
            with self.subTest(failure=failure):
                # Each synthetic acquisition has an independent fixture root.
                original = self.root
                self.root = original / failure
                self.root.mkdir()
                try:
                    attempt, calls = self.acquisition(fail=failure)
                    with self.assertRaises(build.Stopped):
                        attempt.acquire()
                    self.assertFalse(any(op.startswith("deploy-") for op, _ in calls))
                finally:
                    self.root = original

    def test_wrong_installed_commit_refused(self):
        attempt = build.Attempt(self.root, LOCK)
        with (
            patch.object(build.subprocess, "check_output", return_value="0" * 64),
            self.assertRaisesRegex(build.Stopped, "drift"),
        ):
            attempt.verify_refs()

    def test_failed_child_keeps_private_log_and_safe_operation_record(self):
        attempt = build.Attempt(self.root, LOCK)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaises(build.Stopped),
        ):
            attempt.run(
                "fixture-failure",
                build.sys.executable,
                "-B",
                "-c",
                "import sys; print('synthetic-token-fixture'); sys.exit(7)",
                timeout=5,
            )
        events = (self.root / "operations.jsonl").read_text()
        self.assertNotIn("synthetic-token-fixture", events)
        self.assertEqual(json.loads(events)["exit"], 7)
        self.assertEqual(attempt.record["failure_category"], "subprocess")
        log = self.root / "fixture-failure.private.log"
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)
        self.assertIn("synthetic-token-fixture", log.read_text())

    def test_parent_side_resource_failure_cannot_report_candidate_built(self):
        attempt = build.Attempt(self.root, LOCK)
        good = {"allocated_bytes": 4096, "available_bytes": 10 * build.GIB}
        attempt.usage = unittest.mock.Mock(
            side_effect=[good, build.Stopped("cap"), good]
        )
        attempt.acquire = unittest.mock.Mock()
        attempt.build = unittest.mock.Mock()
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch.object(
                build, "safe_new_output", return_value=self.root / "new-attempt"
            ),
            patch.object(build, "Attempt", return_value=attempt),
            patch.object(build.sys, "argv", ["candidate"]),
        ):
            self.assertEqual(build.main(), 1)
        self.assertEqual(attempt.record["status"], "BLOCKED")
        self.assertIsNone(attempt.record["candidate"])

    def test_wrapper_is_bash_and_no_acquisition_for_help(self):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch.object(build.sys, "argv", ["build_candidate", "--help"]),
            self.assertRaises(SystemExit) as result,
        ):
            build.main()
        self.assertEqual(result.exception.code, 0)
        self.assertIn(
            "exec python3 -B -u", (build.ROOT / "p6_binary_candidate.sh").read_text()
        )


if __name__ == "__main__":
    unittest.main()
