"""N1 schema-selection regressions; no Qt, renderer or owner profile execution."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location(
    "n1_system_schema_probe", HERE / "run_probe.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class SystemSchemasTests(unittest.TestCase):
    def test_only_schema_search_override_changes(self):
        inherited = {
            "GSETTINGS_SCHEMA_DIR": "/synthetic/old/editor/schemas",
            "QTWEBENGINE_DISABLE_SANDBOX": "1",
            "QTWEBENGINE_CHROMIUM_FLAGS": "--no-sandbox",
            "LD_PRELOAD": "/synthetic/untrusted.so",
            "DISPLAY": ":synthetic",
        }
        original = inherited.copy()
        response = Mock(returncode=0, stdout="\n".join(probe.FONT_KEYS))
        with patch.object(probe.subprocess, "run", return_value=response) as query:
            selected, record = probe.ubuntu_system_schema_environment(inherited)
        self.assertEqual(inherited, original)
        self.assertEqual(
            selected, {**inherited, "GSETTINGS_SCHEMA_DIR": str(probe.SYSTEM_SCHEMAS)}
        )
        self.assertNotIn("/synthetic", json.dumps(record))
        self.assertEqual(
            query.call_args.args[0],
            ["/usr/bin/gsettings", "list-keys", "org.gnome.desktop.interface"],
        )
        self.assertEqual(query.call_args.kwargs["env"], selected)
        # Unsafe renderer/loader flags remain present for the existing child
        # configuration to reject, rather than being silently hidden here.
        self.assertEqual(selected["QTWEBENGINE_DISABLE_SANDBOX"], "1")

    def test_schema_lookup_errors_and_missing_keys_fail_closed(self):
        cases = [
            Mock(returncode=1, stdout="", stderr="private information"),
            Mock(returncode=0, stdout="font-antialiasing\n"),
            subprocess.TimeoutExpired("gsettings", 3),
            OSError("private path"),
        ]
        for response in cases:
            with self.subTest(response=type(response).__name__):
                kwargs = (
                    {"side_effect": response}
                    if isinstance(response, Exception)
                    else {"return_value": response}
                )
                with (
                    patch.object(probe.subprocess, "run", **kwargs),
                    self.assertRaises(ValueError) as error,
                ):
                    probe.ubuntu_system_schema_environment({})
                self.assertNotIn("private", str(error.exception))

    def test_untrusted_or_symlink_schema_directory_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as temporary:
            root = Path(temporary)
            (root / "gschemas.compiled").write_bytes(b"synthetic")
            link = root / "system-link"
            link.symlink_to(probe.SYSTEM_SCHEMAS, target_is_directory=True)
            for directory in (root, link):
                with (
                    self.subTest(directory=directory.name),
                    patch.object(probe, "SYSTEM_SCHEMAS", directory),
                    patch.object(probe.subprocess, "run") as query,
                    self.assertRaises(ValueError),
                ):
                    probe.ubuntu_system_schema_environment({})
                query.assert_not_called()

    def test_schema_change_during_preflight_refused(self):
        response = Mock(returncode=0, stdout="\n".join(probe.FONT_KEYS))
        with (
            patch.object(probe.subprocess, "run", return_value=response),
            patch.object(Path, "read_bytes", side_effect=[b"first", b"changed"]),
            self.assertRaisesRegex(ValueError, "changed during preflight"),
        ):
            probe.ubuntu_system_schema_environment({})

    def test_real_glib_overlay_reproduces_missing_keys_and_system_selection_restores_visibility(
        self,
    ):
        compiler = shutil.which("glib-compile-schemas")
        self.assertIsNotNone(
            compiler, "This N1 regression requires Ubuntu's existing schema compiler"
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as temporary:
            root = Path(temporary)
            (root / "synthetic.gschema.xml").write_text(
                '<schemalist><schema id="org.gnome.desktop.interface" path="/org/gnome/desktop/interface/">'
                '<key name="synthetic-test-key" type="b"><default>false</default></key>'
                "</schema></schemalist>"
            )
            subprocess.run(
                [compiler, str(root)], check=True, capture_output=True, timeout=3
            )
            inherited = {**os.environ, "GSETTINGS_SCHEMA_DIR": str(root)}
            before = inherited.copy()
            command = ["/usr/bin/gsettings", "list-keys", "org.gnome.desktop.interface"]
            old = subprocess.run(
                command,
                env=inherited,
                check=True,
                capture_output=True,
                text=True,
                timeout=3,
            )
            self.assertFalse(probe.FONT_KEYS.intersection(old.stdout.splitlines()))
            selected, record = probe.ubuntu_system_schema_environment(inherited)
            corrected = subprocess.run(
                command,
                env=selected,
                check=True,
                capture_output=True,
                text=True,
                timeout=3,
            )
            self.assertTrue(probe.FONT_KEYS.issubset(corrected.stdout.splitlines()))
            self.assertEqual(inherited, before)
            self.assertEqual(
                record["required_font_keys_present"], sorted(probe.FONT_KEYS)
            )

    @contextlib.contextmanager
    def supervisor_fixture(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as temporary:
            root = Path(temporary)
            receipt = root / "n1.json"
            receipt.write_text(
                json.dumps({"kind": "cyrnava-disposable-native-N1", "root": str(root)})
            )
            historical = {}
            for name in (
                "owner-sandbox-result.json",
                "owner-sandbox.private.log",
                "owner-sandbox.json",
            ):
                (root / name).write_text("synthetic historical evidence")
                historical[name] = (root / name).read_bytes()
            argv = [
                "probe",
                "--candidate",
                str(root),
                "--owner-host",
                "--receipt-sha256",
                hashlib.sha256(receipt.read_bytes()).hexdigest(),
                "--ubuntu-system-schemas",
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(probe.resource, "setrlimit"),
                patch.object(
                    probe.shutil,
                    "disk_usage",
                    return_value=types.SimpleNamespace(free=5 * 1024**3),
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                yield root, historical

    def test_schema_preflight_failure_cannot_launch_renderer(self):
        with self.supervisor_fixture() as (root, historical):
            with (
                patch.object(
                    probe,
                    "ubuntu_system_schema_environment",
                    side_effect=ValueError("font keys unavailable"),
                ),
                patch.object(probe.subprocess, "Popen") as child,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                probe.main()
            child.assert_not_called()
            self.assertFalse((root / "owner-system-schemas-result.json").exists())
            self.assertEqual(
                historical, {name: (root / name).read_bytes() for name in historical}
            )

    def test_new_mode_preserves_old_outputs_and_cannot_promote_incomplete_sandbox(self):
        with self.supervisor_fixture() as (root, historical):
            selected = {"GSETTINGS_SCHEMA_DIR": str(probe.SYSTEM_SCHEMAS)}
            process = Mock()
            process.wait.return_value = 0

            def start(*args, **kwargs):
                self.assertEqual(kwargs["env"], selected)
                self.assertEqual(args[0][-1], "owner-system-schemas.json")
                (root / "owner-system-schemas.json").write_text(
                    json.dumps(
                        {
                            "complete": True,
                            "status": "PASS",
                            "platform": "wayland",
                            "renderer_sandbox": "NOT VERIFIED",
                        }
                    )
                )
                return process

            with (
                patch.object(
                    probe,
                    "ubuntu_system_schema_environment",
                    return_value=(selected, {"mode": "fixture"}),
                ),
                patch.object(probe.subprocess, "Popen", side_effect=start),
            ):
                self.assertEqual(probe.main(), 2)
            record = json.loads((root / "owner-system-schemas-result.json").read_text())
            self.assertEqual(record["status"], "BLOCKED")
            self.assertEqual(record["normal_application_launch"], "NOT EXECUTED")
            self.assertEqual(
                historical, {name: (root / name).read_bytes() for name in historical}
            )

    def test_existing_new_mode_output_is_not_reused(self):
        with self.supervisor_fixture() as (root, _historical):
            path = root / "owner-system-schemas-result.json"
            path.write_text("preserved new evidence")
            with (
                patch.object(probe.subprocess, "Popen") as child,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                probe.main()
            child.assert_not_called()
            self.assertEqual(path.read_text(), "preserved new evidence")

    def test_role_prefix_creates_fresh_outputs_and_preserves_both_previous_modes(self):
        with self.supervisor_fixture() as (root, historical):
            previous = root / "owner-system-schemas-result.json"
            previous.write_text("preserved schema-corrected owner result")
            process = Mock()
            process.wait.return_value = 2

            def start(*args, **kwargs):
                self.assertEqual(args[0][-1], "owner-system-schemas-role.json")
                return process

            with (
                patch.object(
                    sys,
                    "argv",
                    [*sys.argv, "--record-prefix", "owner-system-schemas-role"],
                ),
                patch.object(
                    probe,
                    "ubuntu_system_schema_environment",
                    return_value=({}, {"mode": "fixture"}),
                ),
                patch.object(probe.subprocess, "Popen", side_effect=start),
            ):
                self.assertEqual(probe.main(), 2)
            self.assertTrue((root / "owner-system-schemas-role-result.json").is_file())
            self.assertEqual(
                previous.read_text(), "preserved schema-corrected owner result"
            )
            self.assertEqual(
                historical, {name: (root / name).read_bytes() for name in historical}
            )

    def test_existing_private_command_line_prevents_relaunch(self):
        with self.supervisor_fixture() as (root, _historical):
            private = root / "owner-system-schemas-role.renderer-cmdline.private"
            private.write_bytes(b"preserved synthetic private evidence")
            with (
                patch.object(
                    sys,
                    "argv",
                    [*sys.argv, "--record-prefix", "owner-system-schemas-role"],
                ),
                patch.object(probe.subprocess, "Popen") as child,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                probe.main()
            child.assert_not_called()
            self.assertEqual(
                private.read_bytes(), b"preserved synthetic private evidence"
            )


if __name__ == "__main__":
    unittest.main()
