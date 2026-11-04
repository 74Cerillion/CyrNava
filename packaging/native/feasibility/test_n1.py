"""Offline policy fixtures; no GUI, downloads, real user profiles or installs."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prepare = module("n1_prepare_tests", HERE / "prepare.py")
config = module("desktop.native.n1_configuration_tests", HERE / "n1_configuration.py")
providers = module("n1_provider_tests", HERE / "providers.py")
sandbox = module("n1_sandbox_tests", HERE / "sandbox_probe.py")
owner_probe = module("n1_owner_probe_tests", HERE / "run_probe.py")


class NativePolicy(unittest.TestCase):
    def test_default_production_entry_remains_flatpak_only(self):
        from desktop.native import application

        with patch.dict("os.environ", {"CYRNAVA_ALLOW_HOST": "1"}, clear=True):
            with self.assertRaisesRegex(ValueError, "requires.*Flatpak"):
                application.configuration()

    def test_no_environment_switch_can_select_native_mode(self):
        from desktop.native import application, build_identity

        self.assertFalse(hasattr(build_identity, "DEPLOYMENT"))
        for variable in ["NATIVE_MODE", "CYRNAVA_NATIVE", "DEPLOYMENT"]:
            with patch.dict("os.environ", {variable: "native-n1"}, clear=True):
                with self.assertRaises(ValueError):
                    application.configuration()

    def test_existing_and_outside_output_rejected(self):
        for path in [ROOT / "ci/P6_REPORT.md", ROOT / "ci-output", Path("/tmp/n1")]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare.fresh(path)

    def test_config_rejects_wrong_identity_before_data_access(self):
        from desktop.native import build_identity

        with (
            patch.object(config.sys, "version_info", (3, 14)),
            patch.object(build_identity, "APP_ID", "wrong"),
        ):
            with self.assertRaisesRegex(ValueError, "development identity"):
                config.configuration(Path("/does-not-exist"))

    def test_private_directory_rejects_symlink_and_public_mode(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as tmp:
            p = Path(tmp)
            (p / "real").mkdir(mode=0o700)
            (p / "link").symlink_to(p / "real")
            with self.assertRaisesRegex(ValueError, "symlink"):
                config.private_path(p / "link")
            (p / "real").chmod(0o755)
            with self.assertRaisesRegex(ValueError, "private"):
                config.private_path(p / "real")

    def test_root_and_wrong_interpreter_are_rejected(self):
        with patch.object(config.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(ValueError, "root"):
                config.configuration(Path("/not-read"))
        with patch.object(config.sys, "version_info", (3, 12)):
            with self.assertRaisesRegex(ValueError, "3.14"):
                config.configuration(Path("/not-read"))

    def test_locks_match_original_versions_and_expected_qt_hashes(self):
        data = json.loads((HERE / "dependencies.json").read_text())["files"]
        originals = json.loads(
            (
                ROOT / "ci/evidence/p6/production-qt-compatibility/packages.json"
            ).read_text()
        )
        expected = {p["filename"]: p["sha256"] for p in originals}
        for p in data:
            self.assertTrue(p["url"].startswith("https://files.pythonhosted.org/"))
            self.assertTrue(p["filename"].endswith(".whl"))
            if p["filename"] in expected:
                self.assertEqual(expected[p["filename"]], p["sha256"])
        self.assertEqual(len(expected), 4)
        self.assertEqual(len(data), 19)

    def test_native_security_override_list_preserves_protections(self):
        for key in [
            "LD_PRELOAD",
            "LD_LIBRARY_PATH",
            "QT_PLUGIN_PATH",
            "QTWEBENGINEPROCESS_PATH",
            "QTWEBENGINE_DISABLE_SANDBOX",
            "QTWEBENGINE_REMOTE_DEBUGGING",
            "QTWEBENGINE_CHROMIUM_FLAGS",
        ]:
            self.assertIn(key, config.FORBIDDEN)

    def test_foreign_duplicate_or_incomplete_provider_is_rejected(self):
        prefix = Path("/candidate/.venv")
        good = {
            "python": [3, 14],
            "pyside": "6.11.3",
            "shiboken": "6.11.3",
            "qt": "6.11.3",
            "webengine": "6.11.3",
            "installed_record_hashes_valid": True,
            "helper_resources_locales_plugins": True,
            "missing_libraries": [],
            "qt_maps": {
                "libQt6Core.so.6": ["/candidate/.venv/PySide6/Qt/lib/libQt6Core.so.6"]
            },
            "binding_paths": ["/candidate/.venv/PySide6/QtCore.abi3.so"],
            "plugins_path": "/candidate/.venv/PySide6/Qt/plugins",
            "renderer": "NOT EXECUTED",
        }
        import copy

        self.assertEqual(providers.validate(good, prefix)["renderer"], "NOT EXECUTED")
        defects = {
            "pyside": "6.11.2",
            "installed_record_hashes_valid": False,
            "helper_resources_locales_plugins": False,
            "missing_libraries": ["missing"],
            "qt_maps": {"libQt6Core.so.6": ["/usr/lib/libQt6Core.so.6"]},
            "plugins_path": "/usr/lib/qt6/plugins",
            "binding_paths": ["/usr/PySide6/QtCore.so"],
        }
        for key, value in defects.items():
            bad = copy.deepcopy(good)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                providers.validate(bad, prefix)
        bad = copy.deepcopy(good)
        bad["qt_maps"]["libQt6Core.so.6"].append(
            "/candidate/.venv/other/libQt6Core.so.6"
        )
        with self.assertRaises(ValueError):
            providers.validate(bad, prefix)

    @contextlib.contextmanager
    def configured_fixture(self):
        from desktop.native import build_identity

        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as tmp:
            root = Path(tmp)
            source = root / "application"
            source.mkdir()
            (source / "synthetic.py").write_text("synthetic fixture")
            (root / "client/profile").mkdir(parents=True, mode=0o700)
            helper = root / ".venv/helper"
            helper.parent.mkdir()
            helper.write_bytes(b"not executable test bytes")
            helper.chmod(0o700)
            record = {
                "kind": "cyrnava-disposable-native-N1",
                "root": str(root),
                "synthetic_only": True,
                "application_files": {
                    "synthetic.py": prepare.sha(source / "synthetic.py")
                },
                "helper": ".venv/helper",
                "helper_sha256": prepare.sha(helper),
            }
            receipt = root / "n1.json"
            receipt.write_text(json.dumps(record))
            with (
                patch.dict("os.environ", {}, clear=True),
                patch.object(config.sys, "version_info", (3, 14)),
                patch.object(config.sys, "prefix", str(root / ".venv")),
                patch.object(build_identity, "EXPERIMENT_ROOT", str(root), create=True),
            ):
                yield root, source, record, receipt

    def test_valid_explicit_config_opens_only_synthetic_profile(self):
        with self.configured_fixture() as (root, source, record, receipt):
            self.assertEqual(config.configuration(source), root / "client/profile")

    def test_each_unsafe_override_fails_before_profile_use(self):
        with self.configured_fixture() as (root, source, record, receipt):
            for key in config.FORBIDDEN:
                with (
                    self.subTest(key=key),
                    patch.dict("os.environ", {key: "unsafe"}),
                    self.assertRaises(ValueError),
                ):
                    config.configuration(source)

    def test_changed_source_or_helper_rejected(self):
        for target in ["application/synthetic.py", ".venv/helper"]:
            with (
                self.subTest(target=target),
                self.configured_fixture() as (root, source, record, receipt),
            ):
                (root / target).write_bytes(b"changed")
                with self.assertRaises(ValueError):
                    config.configuration(source)

    def test_receipt_wrong_scope_or_path_rejected(self):
        for field, value in [
            ("synthetic_only", False),
            ("root", "/elsewhere"),
            ("helper", ".venv/../../outside"),
        ]:
            with (
                self.subTest(field=field),
                self.configured_fixture() as (root, source, record, receipt),
            ):
                record[field] = value
                receipt.write_text(json.dumps(record))
                with self.assertRaises(ValueError):
                    config.configuration(source)

    def test_owner_probe_wrong_receipt_cannot_launch(self):
        with self.configured_fixture() as (root, source, record, receipt):
            argv = [
                "probe",
                "--candidate",
                str(root),
                "--owner-host",
                "--receipt-sha256",
                "0" * 64,
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(owner_probe.subprocess, "Popen") as child,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                owner_probe.main()
            child.assert_not_called()

    def test_owner_probe_existing_result_is_preserved(self):
        with self.configured_fixture() as (root, source, record, receipt):
            result = root / "owner-sandbox-result.json"
            result.write_text("preserved fixture")
            argv = [
                "probe",
                "--candidate",
                str(root),
                "--owner-host",
                "--receipt-sha256",
                prepare.sha(receipt),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(owner_probe.subprocess, "Popen") as child,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                owner_probe.main()
            child.assert_not_called()
            self.assertEqual(result.read_text(), "preserved fixture")

    def test_resource_limits_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as tmp:
            with (
                patch.object(prepare, "allocated", return_value=prepare.CAP + 1),
                self.assertRaises(ValueError),
            ):
                prepare.budget(Path(tmp))

    def test_seccomp_alone_or_missing_process_evidence_cannot_pass(self):
        import copy

        good = {
            "qt_providers_coherent": True,
            "renderer_helper_matches": True,
            "renderer_role_verified": True,
            "process_status": {"NoNewPrivs": "1", "Seccomp": "2"},
            "namespace_separation": {"user": True, "pid": True, "net": True},
            "sandbox_diagnostic": [
                "Layer 1 Sandbox\tNamespace",
                "PID namespaces\tYes",
                "Network namespaces\tYes",
                "Seccomp-BPF sandbox\tYes",
                "You are adequately sandboxed.",
            ],
        }
        self.assertTrue(sandbox.security_pass(good))
        for defect in [
            "foreign_qt",
            "no_namespace",
            "no_role",
            "seccomp_disabled",
            "diagnostic_none",
            "explicit_inadequacy",
        ]:
            bad = copy.deepcopy(good)
            if defect == "foreign_qt":
                bad["qt_providers_coherent"] = False
            if defect == "no_namespace":
                bad["namespace_separation"]["pid"] = False
            if defect == "no_role":
                bad["renderer_role_verified"] = False
            if defect == "seccomp_disabled":
                bad["process_status"]["Seccomp"] = "0"
            if defect == "diagnostic_none":
                bad["sandbox_diagnostic"] = ["Layer 1 Sandbox\tNone"]
            if defect == "explicit_inadequacy":
                bad["sandbox_diagnostic"].append("You are NOT adequately sandboxed.")
            with self.subTest(defect=defect):
                self.assertFalse(sandbox.security_pass(bad))


if __name__ == "__main__":
    unittest.main()
