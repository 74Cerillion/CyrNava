"""R6 integration regressions using the real host driver and synthetic I/O.

No Flatpak, OSTree, PySide imports or owner workspace is accessed by these tests.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import client
import core
import historical_runtime as history
import native_distribution
import progress


class HistoricalInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p6-r6-sequence-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.native = native_distribution.RuntimeClient(self.root / "client")
        self.replay = history.Replay(self.native, self.root, history.COMMIT)
        self.drift = "fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415"
        self.active = history.COMMIT
        self.app_commit = "a" * 64
        self.source = "a" * 40
        self.trace = []
        self.fail_restore = self.fail_signature = self.drift_after_signature = False
        self.restore_to = history.COMMIT
        self.fail_origin = self.disable_signature = False
        repo = self.native.root / "flatpak/repo"
        repo.mkdir()
        (repo / "config").write_text(
            '[remote "flathub"]\nurl=https://dl.flathub.org/repo/\n'
            "gpg-verify=true\ngpg-verify-summary=true\n"
            '[remote "p5c"]\ngpg-verify=true\ngpg-verify-summary=true\n'
        )
        self.historical_object = repo / "synthetic-historical-object"
        self.historical_object.write_bytes(b"retrieved historical commit")
        self.public = self.root / "public"
        self.public.mkdir()
        (self.public / "staging-public.gpg").write_bytes(b"synthetic public key")
        self.location = self.native.root / "flatpak/synthetic-app"
        inputs = self.location / "files/share/cyrnava/build-inputs.json"
        inputs.parent.mkdir(parents=True)
        inputs.write_bytes(
            core.encode({"version": "0.1.0", "schema": 5, "git_commit": self.source})
        )
        self.original_inputs = core.tree_manifest(self.public)
        self.original_payload = inputs.read_bytes()
        for target, name, value in (
            (self.native, "run", self.flatpak),
            (self.native, "command", self.restore),
            (self.native, "verify_summary", lambda: None),
            (client, "validate_descriptor", lambda *args: None),
            (subprocess, "run", self.signature),
        ):
            replacement = patch.object(target, name, side_effect=value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def flatpak(self, operation, *args):
        if args[0] == "install":
            self.trace.append("installation-success")
            self.active = self.drift
            self.historical_object.unlink()
            if self.disable_signature:
                p = self.native.root / "flatpak/repo/config"
                p.write_text(
                    p.read_text().replace("gpg-verify=true", "gpg-verify=false")
                )
            return ""
        if "--show-commit" in args:
            return self.active if args[-1] == history.REF else self.app_commit
        if "--show-runtime" in args:
            return history.REF
        if "--show-origin" in args:
            if args[-1] == history.REF:
                return "untrusted" if self.fail_origin else "flathub"
            return "p5c"
        if "--show-location" in args:
            return str(self.location)
        if "--show-permissions" in args:
            return "[Context]\nsockets=wayland;\ndevices=dri;\n"
        return ""

    def restore(self, operation, *args, **kwargs):
        self.trace.append("restore-exact-commit")
        self.assertEqual(operation, "runtime-pin")
        self.assertIn("--commit=" + history.COMMIT, args)
        self.assertEqual(kwargs["timeout"], 300)
        self.assertNotIn("--no-gpg-verify", args)
        if self.fail_restore:
            raise core.Rejected("Synthetic historical commit unavailable")
        self.active = self.restore_to
        self.historical_object.write_bytes(b"re-fetched historical commit")
        return ""

    def signature(self, command, **kwargs):
        self.trace.append("verify-restored-signature")
        self.assertEqual(command[0], "ostree")
        self.assertIn("--gpg-verify-remote=flathub", command)
        self.assertEqual(command[-1], history.COMMIT)
        self.assertEqual(kwargs["timeout"], 60)
        if self.fail_signature or not self.historical_object.exists():
            raise subprocess.CalledProcessError(1, [], b"", b"SECRET signature failure")
        if self.drift_after_signature:
            self.active = self.drift
        return subprocess.CompletedProcess([], 0, b"synthetic signature verified", b"")

    def install_and_probe(self, *, authorized=True):
        replay = self.replay if authorized else history.Replay(self.native, self.root)
        with replay.transaction("install-a"):
            result = self.native.install_real(
                "http://127.0.0.1/",
                self.public,
                "A" * 40,
                self.app_commit,
                self.source,
                defer_runtime_check=replay.enabled,
            )
        # Execute the actual probe's eligibility gate; only its child is simulated.
        monitor = Mock(spec=progress.Progress)
        value = {
            "status": "PASS",
            "modules": dict.fromkeys(history.MODULES, "a" * 64),
            "providers": dict.fromkeys(
                (
                    "runtime/libQt6Core.so.6.11.2",
                    "runtime/libQt6Gui.so.6.11.2",
                    "runtime/libQt6Widgets.so.6.11.2",
                    "app/libQt6WebEngineCore.so.6.11.1",
                ),
                "b" * 64,
            ),
            "versions": dict(pyside="6.11.2", shiboken="6.11.2", qt="6.11.2"),
        }

        def imported(*args, **kwargs):
            self.trace.append("imports-eligible")
            self.assertEqual(self.active, history.COMMIT)
            self.assertLess(
                self.trace.index("restore-exact-commit"),
                self.trace.index("verify-restored-signature"),
            )
            return subprocess.CompletedProcess(
                [], 0, b"P6_IMPORT " + json.dumps(value).encode(), b""
            )

        monitor.command.side_effect = imported
        probe = history.probe(self.native, monitor, self.root, "A")
        return result, replay.events[-1], probe

    def assert_no_imports(self):
        self.assertNotIn("imports-eligible", self.trace)
        self.assertEqual(core.tree_manifest(self.public), self.original_inputs)
        self.assertEqual(
            (self.location / "files/share/cyrnava/build-inputs.json").read_bytes(),
            self.original_payload,
        )

    def test_pruned_historical_object_restores_before_signature_and_imports(self):
        result, event, probe = self.install_and_probe()
        self.assertEqual(
            self.trace,
            [
                "installation-success",
                "restore-exact-commit",
                "verify-restored-signature",
                "imports-eligible",
            ],
        )
        self.assertEqual(result["status"], "APP_IDENTITY_PASS_RUNTIME_DEFERRED")
        self.assertEqual(event["transaction"], "PASS")
        self.assertEqual(event["after"], self.drift)
        self.assertFalse(event["ordinary_runtime_compatible"])
        self.assertTrue(event["drift"])
        self.assertEqual(event["restoration_policy"]["approved_commit"], history.COMMIT)
        self.assertEqual(event["restoration"], "PASS")
        self.assertEqual(event["trust"]["runtime_identity"]["commit"], history.COMMIT)
        self.assertEqual(probe["status"], "PASS")
        self.assertEqual(core.tree_manifest(self.public), self.original_inputs)

    def test_no_authorization_keeps_strict_install_guard(self):
        with self.assertRaises(native_distribution.RuntimeIdentityFailure):
            self.install_and_probe(authorized=False)
        self.assertEqual(self.trace, ["installation-success"])
        self.assert_no_imports()

    def test_wrong_restored_commit_cannot_reach_signature_or_imports(self):
        self.restore_to = "e" * 64
        with self.assertRaisesRegex(core.Rejected, "mismatch"):
            self.install_and_probe()
        self.assertNotIn("verify-restored-signature", self.trace)
        self.assertEqual(self.replay.events[-1]["restoration"], "FAIL")
        self.assert_no_imports()

    def test_signature_failure_remains_fail_closed_with_private_diagnostics(self):
        self.fail_signature = True
        with self.assertRaisesRegex(
            core.Rejected, "signature verification failed"
        ) as caught:
            self.install_and_probe()
        self.assertNotIn("SECRET", str(caught.exception))
        diagnostic = core.read_json(self.root / "runtime-signature-failure.json")
        private = (
            self.root
            / "private-subprocess"
            / diagnostic["private_files"]["stderr"]["file"]
        )
        self.assertEqual(private.read_bytes(), b"SECRET signature failure")
        self.assertEqual(private.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("SECRET", json.dumps(diagnostic))
        self.assert_no_imports()

    def test_unavailable_historical_commit_is_not_substituted(self):
        self.fail_restore = True
        with self.assertRaisesRegex(core.Rejected, "unavailable"):
            self.install_and_probe()
        self.assertEqual(self.trace.count("restore-exact-commit"), 1)
        self.assertEqual(self.replay.events[-1]["restoration"], "FAIL")
        self.assert_no_imports()

    def test_unexpected_drift_after_signature_is_rejected(self):
        self.drift_after_signature = True
        with self.assertRaises(native_distribution.RuntimeIdentityFailure):
            self.install_and_probe()
        self.assertEqual(self.replay.events[-1]["validation"], "FAIL")
        self.assert_no_imports()

    def test_wrong_origin_prevents_restoration(self):
        self.fail_origin = True
        with self.assertRaisesRegex(core.Rejected, "origin"):
            self.install_and_probe()
        self.assertNotIn("restore-exact-commit", self.trace)
        self.assert_no_imports()

    def test_disabled_signature_policy_prevents_restoration(self):
        self.disable_signature = True
        with self.assertRaises(core.Rejected):
            self.install_and_probe()
        self.assertNotIn("restore-exact-commit", self.trace)
        self.assert_no_imports()

    def test_policy_precheck_does_not_need_a_local_historical_object(self):
        self.historical_object.unlink()
        policy = self.replay.origin_policy()
        self.assertEqual(policy["approved_commit"], history.COMMIT)
        self.assertEqual(self.trace, [])
        # Full signature verification still refuses the same missing object.
        with self.assertRaisesRegex(core.Rejected, "signature verification failed"):
            self.replay.trusted()

    def test_progress_command_signature_failure_is_private_and_fail_closed(self):
        self.fail_signature = True
        self.native.progress = Mock(spec=progress.Progress)
        self.native.progress.command.side_effect = lambda operation, command, **kw: (
            self.signature(command, **kw)
        )
        with self.assertRaisesRegex(core.Rejected, "signature verification failed"):
            self.install_and_probe()
        self.native.progress.command.assert_called_once()
        self.assertEqual(
            self.native.progress.command.call_args.args[0], "runtime-signature"
        )
        self.assertTrue((self.root / "runtime-signature-failure.json").exists())
        self.assert_no_imports()

    def test_runtime_drift_after_verification_before_import_is_rejected(self):
        with self.replay.transaction("install-a"):
            self.native.install_real(
                "http://127.0.0.1/",
                self.public,
                "A" * 40,
                self.app_commit,
                self.source,
                defer_runtime_check=True,
            )
        # A later external change must not reuse the earlier verification PASS.
        self.active = self.drift
        monitor = Mock(spec=progress.Progress)
        with self.assertRaises(native_distribution.RuntimeIdentityFailure):
            history.probe(self.native, monitor, self.root, "A")
        monitor.command.assert_not_called()
        self.assert_no_imports()


if __name__ == "__main__":
    unittest.main()
