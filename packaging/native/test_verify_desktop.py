"""Couple the real N1 monitor to the N2 adapter; synthetic processes, never Qt."""

import contextlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


driver = module("n2_driver_regressions", ROOT / "packaging/native/verify_desktop.py")
engine = module("n2_driver_engine", ROOT / "desktop/install_engine.py")


class MonitorAdapterTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "ci-output/native-n2-review-1/owner-1-correction-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.check = module(
            "n2_coupled_monitor",
            ROOT / "packaging/native/feasibility/check_application.py",
        )
        self.check.OUTPUT = self.root
        self.check.CANDIDATE = self.root / "synthetic-release"
        self.process = SimpleNamespace(
            pid=os.getpid(), returncode=0, poll=Mock(side_effect=[None, 0, 0])
        )
        self.factory = Mock(return_value=self.process)
        self.desktop = self.root / "synthetic.desktop"
        driver.configure_monitor(
            self.check, self.desktop, SimpleNamespace(DesktopProcess=self.factory)
        )
        self.sample = {
            "backend": True,
            "renderer": True,
            "qt_providers": True,
            "foreign_qt": False,
        }

    def launch(self, *, authenticated=True):
        with (
            patch.object(self.check, "child_no_core", contextlib.nullcontext),
            patch.object(
                self.check, "sample_tree", side_effect=lambda *_: dict(self.sample)
            ),
            patch.object(
                self.check, "unauthenticated_rejected", return_value=authenticated
            ) as authenticate,
            patch.object(self.check.time, "sleep"),
        ):
            result = self.check.launch("fixture", {"N2_TEST": "synthetic"})
        return result, authenticate

    def test_real_monitor_reaches_adapter_with_complete_subprocess_interface(self):
        # Previously failed while evaluating subprocess.STDOUT, before Spawn.
        result, authenticate = self.launch()
        self.factory.assert_called_once()
        self.assertEqual(
            self.factory.call_args.args[:2], (self.desktop, {"N2_TEST": "synthetic"})
        )
        self.assertEqual(self.check.subprocess.STDOUT, subprocess.STDOUT)
        self.assertEqual(result["normal_exit"], "PASS")
        self.assertEqual(result["renderer"], "PASS")
        authenticate.assert_called_once()

    def test_adapter_preserves_foreign_provider_rejection(self):
        self.sample["foreign_qt"] = True
        with self.assertRaisesRegex(RuntimeError, "Foreign Qt"):
            self.launch()

    def test_adapter_preserves_backend_authentication_failure(self):
        with self.assertRaisesRegex(RuntimeError, "Unauthenticated"):
            self.launch(authenticated=False)

    def test_adapter_preserves_nonzero_application_exit_failure(self):
        self.process.returncode = 1
        with self.assertRaisesRegex(RuntimeError, "exited unsuccessfully"):
            self.launch()

    def test_adapter_preserves_missing_renderer_failure(self):
        self.sample["renderer"] = False
        with self.assertRaisesRegex(RuntimeError, "evidence incomplete"):
            self.launch()

    def test_output_selection_is_explicit_and_repository_bounded(self):
        expected = ROOT / "ci-output/native-n2-owner-2"
        self.assertEqual(driver.attempt_path(engine, expected), expected)
        for invalid in (
            ROOT / "ci-output/nested/native-n2-owner-2",
            ROOT / "ci-output/native-n2-owner-0",
            ROOT / "ci-output/native-n2-owner-2/../../escape",
            Path("/tmp/native-n2-owner-2"),
        ):
            with self.subTest(path=invalid), self.assertRaises(ValueError):
                driver.attempt_path(engine, invalid)

    def test_error_summary_exposes_only_allowlisted_attribute(self):
        error = AttributeError(
            "private credential and path must not be copied", name="STDOUT"
        )
        result = driver.failure_details(error)
        self.assertEqual(result["missing_adapter_attribute"], "STDOUT")
        self.assertNotIn("credential", json.dumps(result))
        hidden = AttributeError("private", name="secret-value")
        self.assertNotIn("secret-value", json.dumps(driver.failure_details(hidden)))

    def test_cli_advertises_supported_fresh_output_option_without_launching(self):
        result = subprocess.run(
            [
                "/usr/bin/python3.14",
                "-B",
                str(ROOT / "packaging/native/verify_desktop.py"),
                "--help",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        self.assertIn("--output", result.stdout)
        self.assertIn("never overwrites", result.stdout)


if __name__ == "__main__":
    unittest.main()
