"""Offline guard/diagnostic fixtures: no Qt, renderer, GDB or desktop execution."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "n1_startup_diagnostic", HERE / "diagnose_startup.py"
)
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


class StartupDiagnosticTests(unittest.TestCase):
    @contextlib.contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory(
            dir=diagnostic.ROOT / "ci-output"
        ) as temporary:
            parent = Path(temporary)
            candidate, output = parent / "candidate", parent / "startup"
            candidate.mkdir()
            (candidate / "n1.json").write_text("synthetic fixture receipt")
            (candidate / "owner-sandbox.private.log").write_text(
                "synthetic fixture log"
            )
            receipt = diagnostic.sha(candidate / "n1.json")
            previous = {
                "receipt_sha256": receipt,
                "private_log_sha256": diagnostic.sha(
                    candidate / "owner-sandbox.private.log"
                ),
                "probe_sha256": diagnostic.sha(HERE / "sandbox_probe.py"),
            }
            (candidate / "owner-sandbox-result.json").write_text(json.dumps(previous))
            with (
                patch.object(diagnostic, "CANDIDATE", candidate),
                patch.object(diagnostic, "OUTPUT", output),
                patch.object(diagnostic, "RECEIPT", receipt),
            ):
                yield candidate, output

    def test_exact_candidate_receipt_and_old_evidence_required(self):
        for changed in ("n1.json", "owner-sandbox.private.log", "probe-identity"):
            with self.subTest(changed=changed), self.fixture() as (candidate, output):
                diagnostic.preflight(candidate, output)
                if changed == "probe-identity":
                    path = candidate / "owner-sandbox-result.json"
                    record = json.loads(path.read_text())
                    record["probe_sha256"] = "0" * 64
                    path.write_text(json.dumps(record))
                else:
                    (candidate / changed).write_text("changed")
                with self.assertRaises(ValueError):
                    diagnostic.preflight(candidate, output)

    def test_existing_output_or_symlink_is_preserved(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink), self.fixture() as (candidate, output):
                if symlink:
                    output.symlink_to(candidate, target_is_directory=True)
                else:
                    output.mkdir()
                    (output / "result.json").write_text("preserved")
                with self.assertRaises(ValueError):
                    diagnostic.preflight(candidate, output)
                if not symlink:
                    self.assertEqual((output / "result.json").read_text(), "preserved")

    def test_unreviewed_paths_cannot_launch(self):
        with self.fixture() as (candidate, output):
            for first, second in (
                (candidate.parent, output),
                (candidate, output.parent),
            ):
                with (
                    self.subTest(first=first, second=second),
                    self.assertRaises(ValueError),
                ):
                    diagnostic.preflight(first, second)
        with (
            patch.object(sys, "argv", ["diagnostic"]),
            patch.object(diagnostic.subprocess, "Popen") as popen,
        ):
            with (
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                diagnostic.main()
            popen.assert_not_called()

    def test_debugger_is_offline_and_original_probe_is_not_rerun(self):
        command = diagnostic.debugger_command("/usr/bin/gdb", diagnostic.CANDIDATE)
        self.assertIn("set debuginfod enabled off", command)
        self.assertIn("set auto-load off", command)
        self.assertIn("set disable-randomization off", command)
        self.assertIn("--child", command)
        self.assertIn("--owner-host", command)
        self.assertNotIn(str(HERE / "sandbox_probe.py"), command)
        self.assertEqual(
            command[command.index("--args") + 1],
            str(diagnostic.CANDIDATE / ".venv/bin/python"),
        )

    def test_schema_diagnostic_never_records_values_or_raw_errors(self):
        response = Mock(
            returncode=0,
            stdout="font-antialiasing\nprivate-extra-key\n",
            stderr="private error",
        )
        with patch.object(diagnostic.subprocess, "run", return_value=response) as run:
            result = diagnostic.schema_keys()
        text = json.dumps(result)
        self.assertNotIn("private", text)
        self.assertTrue(
            result["org.gnome.desktop.interface"]["keys"]["font-antialiasing"]
        )
        for call in run.call_args_list:
            self.assertEqual(call.args[0][1], "list-keys")
            self.assertEqual(call.kwargs["timeout"], 2)

    def test_child_limits_preserve_stricter_caps_and_restore_supervisor(self):
        core = diagnostic.resource.RLIMIT_CORE
        size = diagnostic.resource.RLIMIT_FSIZE
        originals = {core: (4096, 8192), size: (1024, 4096)}
        with (
            patch.object(
                diagnostic.resource, "getrlimit", side_effect=originals.__getitem__
            ),
            patch.object(diagnostic.resource, "setrlimit") as set_limit,
            diagnostic.child_limits(),
        ):
            pass
        self.assertEqual(
            [call.args for call in set_limit.call_args_list],
            [
                (core, (0, 8192)),
                (size, (1024, 4096)),
                (core, (4096, 8192)),
                (size, (1024, 4096)),
            ],
        )

    def test_child_stops_at_application_construction_without_renderer_or_backend(self):
        with self.fixture() as (candidate, output):
            output.mkdir()
            app = object()
            widgets = types.SimpleNamespace(QApplication=Mock(return_value=app))
            shiboken = types.SimpleNamespace(delete=Mock())
            configuration = Mock()
            application = types.ModuleType("desktop.native.application")
            application.configuration = configuration
            modules = {
                "PySide6.QtCore": object(),
                "PySide6.QtWebEngineCore": object(),
                "PySide6.QtWidgets": widgets,
                "shiboken6": shiboken,
            }
            with (
                patch.dict(sys.modules, {"desktop.native.application": application}),
                patch.object(sys, "path", sys.path.copy()),
                patch.dict(os.environ),
                patch.object(
                    diagnostic.importlib,
                    "import_module",
                    side_effect=modules.__getitem__,
                ),
            ):
                diagnostic.child(candidate, output)
            configuration.assert_called_once_with()
            shiboken.delete.assert_called_once_with(app)
            self.assertEqual(
                json.loads((output / "progress.json").read_text())["stage"],
                "startup-only-complete",
            )

    def test_deadline_kills_only_owned_group_and_never_reports_renderer_success(self):
        with self.fixture() as (candidate, output):
            previous = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in candidate.iterdir()
            }
            process = Mock(pid=123456)
            process.wait.side_effect = [subprocess.TimeoutExpired("gdb", 20), -9]
            with (
                patch.object(sys, "argv", ["diagnostic", "--owner-host"]),
                patch.object(diagnostic.shutil, "which", return_value="/usr/bin/gdb"),
                patch.object(diagnostic, "schema_keys", return_value={}),
                patch.object(diagnostic.subprocess, "Popen", return_value=process),
                patch.object(diagnostic.os, "killpg") as kill,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(diagnostic.main(), 2)
            kill.assert_called_once_with(123456, signal.SIGKILL)
            result = json.loads((output / "result.json").read_text())
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["renderer_sandbox"], "NOT TESTED")
            self.assertEqual(result["normal_application_launch"], "NOT EXECUTED")
            self.assertFalse((output / "active").exists())
            self.assertEqual(
                previous,
                {
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in candidate.iterdir()
                },
            )


if __name__ == "__main__":
    unittest.main()
