"""Private native diagnostics using synthetic Python children; no Flatpak or Qt."""

import contextlib
import hashlib
import io
import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import native_diagnostics as diagnostics
import native_distribution
import progress
import real_update


class NativeDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p6-native-diag-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def child(self, script, *args):
        return subprocess.run(
            [sys.executable, "-u", "-", *args],
            input=diagnostics.wrap_script(script),
            capture_output=True,
            check=False,
            timeout=10,
        )

    def test_import_failure_reports_exact_helper_line_without_importing_Qt(self):
        script = b"import nonexistent_p6_synthetic_module\n"
        result = self.child(script)
        self.assertEqual(result.returncode, 1)
        summary = diagnostics.summarize(result.stdout, result.stderr, script)
        self.assertEqual(summary["component"], "host-streamed-P4-verifier")
        self.assertEqual(summary["stage"], "helper-exception")
        self.assertEqual(summary["exception_type"], "ModuleNotFoundError")
        self.assertEqual(summary["helper_line"], 1)
        self.assertEqual(summary["stderr_category"], "python-traceback")

    def test_wrapper_preserves_script_argv_main_and_SystemExit_semantics(self):
        script = (
            b'import sys\nassert __name__ == "__main__"\n'
            b'assert sys.argv[1:] == ["edit", "synthetic"]\nraise SystemExit(7)\n'
        )
        result = self.child(script, "edit", "synthetic")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(
            diagnostics.summarize(result.stdout, result.stderr, script)["stage"],
            "helper-system-exit",
        )

    def test_non_main_exception_message_is_private_only(self):
        script = b'raise ValueError("TOKEN_SECRET /private/personal/path")\n'
        result = self.child(script)
        summary = diagnostics.summarize(result.stdout, result.stderr, script)
        self.assertIn(b"TOKEN_SECRET", result.stderr)
        self.assertNotIn("TOKEN_SECRET", json.dumps(summary))
        self.assertNotIn("/private", json.dumps(summary))

    def test_private_capture_is_0600_in_0700_directory_and_outside_source(self):
        script = b"synthetic"
        summary = diagnostics.capture(
            self.root, "gui-edit", b"TOKEN_SECRET", b"/private/path", script, 1
        )
        private = self.root / "private-subprocess"
        self.assertEqual(stat.S_IMODE(private.stat().st_mode), 0o700)
        for info in summary["private_files"].values():
            self.assertEqual(
                stat.S_IMODE((private / info["file"]).stat().st_mode), 0o600
            )
        self.assertNotIn("TOKEN_SECRET", json.dumps(summary))
        self.assertNotIn("/private/path", json.dumps(summary))
        self.assertEqual(
            (private / summary["private_files"]["stdout"]["file"]).read_bytes(),
            b"TOKEN_SECRET",
        )

    def test_large_private_output_is_bounded_and_truncation_explicit(self):
        raw = b"x" * (diagnostics.LIMIT + 50)
        summary = diagnostics.capture(self.root, "gui-edit", b"", raw, b"synthetic", 1)
        info = summary["private_files"]["stderr"]
        self.assertTrue(info["truncated"])
        self.assertEqual(info["original_bytes"], len(raw))
        self.assertEqual(
            (self.root / "private-subprocess" / info["file"]).stat().st_size,
            diagnostics.LIMIT,
        )

    def test_malformed_or_wrong_hash_markers_cannot_inject_diagnostics(self):
        script = b"synthetic"
        expected = hashlib.sha256(script).hexdigest()
        values = [
            [],
            {"stage": "helper-exception", "helper_sha256": "f" * 64},
            {"stage": ["SECRET"], "helper_sha256": expected},
            {"stage": "SECRET", "helper_sha256": expected},
        ]
        output = b"\n".join(
            (diagnostics.PREFIX + json.dumps(v)).encode() for v in values
        )
        summary = diagnostics.summarize(output, b"", script)
        self.assertEqual(summary["component"], "unresolved-native-child")
        self.assertNotIn("SECRET", str(summary))

    def test_stderr_categories_are_fixed_and_never_copy_raw_details(self):
        for stderr, expected in [
            (b"bwrap: SECRET", "flatpak-bwrap-diagnostic"),
            (b"qt.qpa: SECRET", "qt-platform-diagnostic"),
            (b"error: app SECRET is not installed", "flatpak-startup-diagnostic"),
        ]:
            with self.subTest(category=expected):
                value = diagnostics.summarize(b"", stderr, b"synthetic")
                self.assertEqual(value["stderr_category"], expected)
                self.assertNotIn("SECRET", str(value))

    def test_driver_error_retains_private_output_and_exposes_only_safe_summary(self):
        monitor = Mock()
        monitor.command.side_effect = subprocess.CalledProcessError(
            1, ["SECRET"], output=b"TOKEN_SECRET", stderr=b"/private/path"
        )
        with self.assertRaises(diagnostics.NativePhaseFailure) as caught:
            diagnostics.run(
                monitor,
                self.root,
                "gui-edit",
                ["SECRET"],
                env={"SECRET": "TOKEN_SECRET"},
                script=b"synthetic",
            )
        self.assertNotIn("TOKEN_SECRET", str(caught.exception))
        self.assertNotIn("/private", json.dumps(caught.exception.diagnostic))
        self.assertEqual(caught.exception.diagnostic["exit_code"], 1)
        self.assertEqual(monitor.command.call_args.kwargs["timeout"], 900)

    def test_existing_private_logs_are_not_overwritten(self):
        for _ in range(2):
            diagnostics.capture(
                self.root, "gui-edit", b"stdout", b"stderr", b"synthetic", 1
            )
        self.assertEqual(len(list((self.root / "private-subprocess").iterdir())), 4)

    def test_symlink_capture_destination_is_rejected(self):
        (self.root / "private-subprocess").symlink_to(
            self.root, target_is_directory=True
        )
        with self.assertRaises(core.Rejected):
            diagnostics.capture(self.root, "gui-edit", b"", b"", b"synthetic", 1)

    def test_owner_record_has_native_failure_details_and_preserves_prepared_input(self):
        pair = self.root / "pair"
        pair.mkdir()
        prepared = {
            "status": "PASS",
            "complete": True,
            "fingerprint": "A" * 40,
            "A": {"source_commit": "a" * 40, "ostree_commit": "a" * 64},
            "B": {"source_commit": "b" * 40, "ostree_commit": "b" * 64},
        }
        (pair / ".p6-real-update").write_bytes(
            core.encode({"purpose": "disposable P6 real update"})
        )
        (pair / "prepared.json").write_bytes(core.encode(prepared))
        original = (pair / "prepared.json").read_bytes()

        class SyntheticClient:
            def __init__(self, root, progress):
                self.root, self.env = root, {}

            def runtimes(self):
                return {"status": "PASS"}

            def install_real(self, *args):
                return {"status": "PASS"}

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
            patch.object(
                progress.Progress,
                "command",
                side_effect=subprocess.CalledProcessError(
                    1, [], output=b"", stderr=b"TOKEN_SECRET"
                ),
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = real_update.exercise(pair, attempt)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["complete"])
        self.assertTrue(result["generation_A_launch_attempted"])
        self.assertEqual(result["native_subprocess_failure"]["operation"], "gui-edit")
        self.assertNotIn("TOKEN_SECRET", json.dumps(result))
        self.assertEqual((pair / "prepared.json").read_bytes(), original)
        self.assertEqual(core.read_json(attempt / "owner-result.json"), result)


if __name__ == "__main__":
    unittest.main()
