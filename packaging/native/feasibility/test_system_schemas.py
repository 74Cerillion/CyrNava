"""N1 schema-selection regressions; no Qt, renderer or owner profile execution."""

import contextlib
import errno
import hashlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import traceback
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
    @contextlib.contextmanager
    def schema_metadata(self, *, owner=0, user=1000, overrides=None, symlinks=()):
        """Synthetic OS trust metadata only; never chmod/chown host objects."""
        compiled = probe.SYSTEM_SCHEMAS / "gschemas.compiled"
        paths = {compiled, probe.SYSTEM_SCHEMAS, *probe.SYSTEM_SCHEMAS.parents}
        original_stat, original_symlink, original_file = (
            Path.stat,
            Path.is_symlink,
            Path.is_file,
        )
        overrides = overrides or {}

        def metadata(path, *args, **kwargs):
            if path not in paths:
                return original_stat(path, *args, **kwargs)
            mode = stat.S_IFREG | 0o644 if path == compiled else stat.S_IFDIR | 0o755
            selected = overrides.get(path, (owner, mode))
            if isinstance(selected, Exception):
                raise selected
            uid, mode = selected
            return os.stat_result((mode, 1, 1, 1, uid, 0, 0, 0, 0, 0))

        def is_symlink(path):
            return path in symlinks if path in paths else original_symlink(path)

        def is_file(path, *args, **kwargs):
            if path == compiled:
                return stat.S_ISREG(metadata(path).st_mode)
            return original_file(path, *args, **kwargs)

        with (
            patch.object(Path, "stat", new=metadata),
            patch.object(Path, "is_symlink", new=is_symlink),
            patch.object(Path, "is_file", new=is_file),
            patch.object(probe.os, "getuid", return_value=user),
        ):
            yield

    def assert_safe_diagnostic(self, diagnostic):
        self.assertEqual(
            set(diagnostic),
            {"path_category", "reason", "uid", "expected_os_uid", "mode", "errno"},
        )
        self.assertIn(
            diagnostic["path_category"],
            {*probe.SCHEMA_PATH_CATEGORIES.values(), "unreviewed-path"},
        )
        self.assertIn(diagnostic["reason"], probe.SCHEMA_REJECTIONS)
        for name in ("uid", "expected_os_uid", "errno"):
            self.assertTrue(diagnostic[name] is None or type(diagnostic[name]) is int)
        if diagnostic["mode"] is not None:
            self.assertRegex(diagnostic["mode"], r"^[0-7]{4}$")

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
        with (
            self.schema_metadata(),
            patch.object(
                Path, "read_bytes", return_value=b"synthetic compiled schemas"
            ),
            patch.object(probe.subprocess, "run", return_value=response) as query,
        ):
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
                    self.schema_metadata(),
                    patch.object(Path, "read_bytes", return_value=b"synthetic schemas"),
                    patch.object(probe.subprocess, "run", **kwargs) as query,
                    self.assertRaises(ValueError) as error,
                ):
                    probe.ubuntu_system_schema_environment({})
                self.assertNotIn("private", str(error.exception))
                query.assert_called_once()

    def test_each_system_object_rejects_wrong_owner_before_query(self):
        for path, category in probe.SCHEMA_PATH_CATEGORIES.items():
            if path == Path("/"):
                continue  # Root defines the OS owner; separate-owner refusal is below.
            mode = (
                stat.S_IFREG | 0o644
                if path.name == "gschemas.compiled"
                else stat.S_IFDIR | 0o755
            )
            with (
                self.subTest(category=category),
                self.schema_metadata(overrides={path: (1001, mode)}),
                patch.object(Path, "read_bytes") as contents,
                patch.object(probe.subprocess, "run") as query,
                self.assertRaises(probe.SchemaTrustError) as error,
            ):
                probe.ubuntu_system_schema_environment({})
            detail = error.exception.diagnostic
            self.assert_safe_diagnostic(detail)
            self.assertEqual(detail["path_category"], category)
            self.assertEqual(detail["reason"], "os-owner-mismatch")
            self.assertEqual(detail["uid"], 1001)
            self.assertEqual(detail["expected_os_uid"], 0)
            query.assert_not_called()
            contents.assert_not_called()

    def test_each_system_object_rejects_group_and_world_write_before_query(self):
        for path, category in probe.SCHEMA_PATH_CATEGORIES.items():
            for bit in (0o020, 0o002):
                mode = (
                    stat.S_IFREG | 0o644
                    if path.name == "gschemas.compiled"
                    else stat.S_IFDIR | 0o755
                )
                with (
                    self.subTest(category=category, bit=bit),
                    self.schema_metadata(overrides={path: (0, mode | bit)}),
                    patch.object(Path, "read_bytes") as contents,
                    patch.object(probe.subprocess, "run") as query,
                    self.assertRaises(probe.SchemaTrustError) as error,
                ):
                    probe.ubuntu_system_schema_environment({})
                detail = error.exception.diagnostic
                self.assert_safe_diagnostic(detail)
                self.assertEqual(detail["path_category"], category)
                self.assertEqual(detail["reason"], "group-or-world-writable")
                self.assertEqual(detail["mode"], f"{stat.S_IMODE(mode | bit):04o}")
                query.assert_not_called()
                contents.assert_not_called()

    def test_each_system_object_rejects_symlinks_before_query(self):
        for path, category in probe.SCHEMA_PATH_CATEGORIES.items():
            with (
                self.subTest(category=category),
                self.schema_metadata(symlinks={path}),
                patch.object(probe.subprocess, "run") as query,
                self.assertRaises(probe.SchemaTrustError) as error,
            ):
                probe.ubuntu_system_schema_environment({})
            self.assert_safe_diagnostic(error.exception.diagnostic)
            self.assertEqual(error.exception.diagnostic["path_category"], category)
            self.assertEqual(error.exception.diagnostic["reason"], "symlink-refused")
            query.assert_not_called()

    def test_invoking_user_cannot_own_the_OS_trust_root(self):
        with (
            self.schema_metadata(owner=1000, user=1000),
            patch.object(probe.subprocess, "run") as query,
            self.assertRaises(probe.SchemaTrustError) as error,
        ):
            probe.ubuntu_system_schema_environment({})
        self.assert_safe_diagnostic(error.exception.diagnostic)
        self.assertEqual(
            error.exception.diagnostic["reason"], "separate-os-owner-required"
        )
        self.assertEqual(error.exception.diagnostic["path_category"], "filesystem-root")
        query.assert_not_called()

    def test_confined_overflow_OS_owner_remains_valid_when_separate(self):
        with (
            self.schema_metadata(owner=65534),
            patch.object(
                Path, "read_bytes", return_value=b"synthetic compiled schemas"
            ),
            patch.object(
                probe.subprocess,
                "run",
                return_value=Mock(returncode=0, stdout="\n".join(probe.FONT_KEYS)),
            ),
        ):
            _environment, record = probe.ubuntu_system_schema_environment({})
        self.assertEqual(record["required_font_keys_present"], sorted(probe.FONT_KEYS))

    def test_metadata_and_read_errors_are_sanitized_and_stop_query(self):
        compiled = probe.SYSTEM_SCHEMAS / "gschemas.compiled"
        for operation in ("stat", "read"):
            private_error = PermissionError(
                errno.EACCES, "sensitive-owner-message", "/private-owner-path"
            )
            with (
                self.subTest(operation=operation),
                self.schema_metadata(
                    overrides={compiled: private_error} if operation == "stat" else {}
                ),
                patch.object(Path, "read_bytes", side_effect=private_error),
                patch.object(probe.subprocess, "run") as query,
                self.assertRaises(probe.SchemaTrustError) as error,
            ):
                probe.ubuntu_system_schema_environment({})
            detail = error.exception.diagnostic
            self.assert_safe_diagnostic(detail)
            self.assertEqual(detail["errno"], errno.EACCES)
            self.assertEqual(detail["path_category"], "compiled-schemas")
            self.assertEqual(
                detail["reason"],
                "metadata-unavailable"
                if operation == "stat"
                else "compiled-read-unavailable",
            )
            formatted = "".join(traceback.format_exception(error.exception))
            self.assertNotIn("private-owner-path", formatted)
            self.assertNotIn("sensitive-owner-message", formatted)
            query.assert_not_called()

    def test_missing_and_nonregular_compiled_schema_fail_closed(self):
        compiled = probe.SYSTEM_SCHEMAS / "gschemas.compiled"
        for metadata, expected in (
            (
                FileNotFoundError(errno.ENOENT, "private missing schema"),
                "metadata-unavailable",
            ),
            ((0, stat.S_IFDIR | 0o755), "compiled-file-unavailable"),
        ):
            with (
                self.subTest(reason=expected),
                self.schema_metadata(overrides={compiled: metadata}),
                patch.object(probe.subprocess, "run") as query,
                self.assertRaises(probe.SchemaTrustError) as error,
            ):
                probe.ubuntu_system_schema_environment({})
            self.assert_safe_diagnostic(error.exception.diagnostic)
            self.assertEqual(error.exception.diagnostic["reason"], expected)
            query.assert_not_called()

    def test_unreviewed_diagnostic_path_never_exposes_its_name(self):
        error = probe.SchemaTrustError(
            path=Path("/private-owner-path"), reason="metadata-unavailable"
        )
        self.assert_safe_diagnostic(error.diagnostic)
        self.assertEqual(error.diagnostic["path_category"], "unreviewed-path")
        self.assertNotIn("private-owner-path", str(error))

    def test_records_actual_host_preflight_without_claiming_application_readiness(self):
        """Observation only: BLOCKED host trust remains BLOCKED in the job log."""
        observation = {
            "scope": "actual-system-schema-preflight-only",
            "application_launch": "NOT EXECUTED",
            "renderer": "NOT EXECUTED",
        }
        try:
            _environment, record = probe.ubuntu_system_schema_environment({})
        except probe.SchemaTrustError as error:
            self.assert_safe_diagnostic(error.diagnostic)
            observation.update(status="BLOCKED", diagnostic=error.diagnostic)
        except ValueError as error:
            known = {
                "System font-schema query unavailable": "query-unavailable",
                "Required Ubuntu font-schema keys unavailable": "font-keys-unavailable",
                "System compiled schemas changed during preflight": "compiled-schema-changed",
            }
            if str(error) not in known:
                raise
            observation.update(status="BLOCKED", failure_category=known[str(error)])
        else:
            observation.update(status="PASS", platform_integration=record)
        print(
            "N4 actual system-schema observation: "
            + json.dumps(observation, sort_keys=True),
            flush=True,
        )

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
            self.schema_metadata(),
            patch.object(probe.subprocess, "run", return_value=response),
            patch.object(Path, "read_bytes", side_effect=[b"first", b"changed"]),
            self.assertRaisesRegex(ValueError, "changed during preflight"),
        ):
            probe.ubuntu_system_schema_environment({})

    def test_real_glib_selection_uses_synthetic_schemas_and_trust_metadata(
        self,
    ):
        compiler = shutil.which("glib-compile-schemas")
        self.assertIsNotNone(
            compiler, "This N1 regression requires Ubuntu's existing schema compiler"
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as temporary:
            root = Path(temporary)
            shadow, system = root / "shadow", root / "synthetic-system"
            shadow.mkdir()
            system.mkdir()
            (shadow / "synthetic.gschema.xml").write_text(
                '<schemalist><schema id="org.gnome.desktop.interface" path="/org/gnome/desktop/interface/">'
                '<key name="synthetic-test-key" type="b"><default>false</default></key>'
                "</schema></schemalist>"
            )
            subprocess.run(
                [compiler, str(shadow)], check=True, capture_output=True, timeout=3
            )
            keys = "".join(
                f'<key name="{name}" type="b"><default>false</default></key>'
                for name in sorted(probe.FONT_KEYS)
            )
            (system / "synthetic.gschema.xml").write_text(
                '<schemalist><schema id="org.gnome.desktop.interface" path="/org/gnome/desktop/interface/">'
                + keys
                + "</schema></schemalist>"
            )
            subprocess.run(
                [compiler, str(system)], check=True, capture_output=True, timeout=3
            )
            inherited = {**os.environ, "GSETTINGS_SCHEMA_DIR": str(shadow)}
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
            # Real compiler/query/compiled bytes; only trust metadata is synthetic.
            # This does not certify the actual Ubuntu host schema ownership.
            with patch.object(probe, "SYSTEM_SCHEMAS", system), self.schema_metadata():
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
