"""N4 security regressions. No keys, downloads, GUI or real installation."""

import copy
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


release = load("n4_release", HERE / "release.py")
driver = load("n4_ci", HERE.parents[1] / "ci/native.py")
policy = load("n4_policy", HERE / "policy_setup.py")


class PayloadTests(unittest.TestCase):
    def test_private_or_unreviewed_files_rejected(self):
        for name in [
            ".env",
            "application/backend/tests/test_secret.py",
            "workspace/engage.sqlite3",
            "private-key.asc",
            ".venv/bin/python",
            "logs/install.log",
            "application/backend/app/sqlite_fault.py",
            "wheels/nested/key.whl",
            "application/frontend/dist/leak.map",
        ]:
            with self.subTest(name=name):
                self.assertFalse(release.allowed_payload(name))

    def test_traversal_and_ambiguous_members_rejected(self):
        for name in ["../key", "/etc/passwd", "a/../b", "a//b", "a\\b", "a\nkey"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                release.member(name)

    def test_required_runtime_material_allowed(self):
        for name in [
            "cyrnava-native",
            "native_operations.py",
            "application/frontend/dist/index.html",
            "application/desktop/native/application.py",
            "notices/LICENSE",
        ]:
            self.assertTrue(release.allowed_payload(name))

    def test_file_symlinks_and_symlink_ancestors_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "actual").mkdir()
            (root / "actual/file").write_text("synthetic")
            (root / "alias").symlink_to(root / "actual", target_is_directory=True)
            with self.assertRaises(ValueError):
                release.regular(root / "alias/file")

    def test_candidate_and_release_identities_are_distinct(self):
        candidate = release.build_identity("candidate")
        normal = release.build_identity("release")
        self.assertIn(b"org.cyrnava.CyrNava.Devel", candidate)
        self.assertIn(b"io.github._74Cerillion.CyrNava", normal)
        self.assertNotIn(b"N2 installation candidate", normal)
        for content in [candidate, normal]:
            self.assertNotIn(b"--no-sandbox", content)
            self.assertNotIn(b"QTWEBENGINE_DISABLE_SANDBOX", content)

    def test_dirty_source_requires_explicit_local_mode(self):
        with patch.object(
            release.subprocess, "check_output", side_effect=["a" * 40, b" M file"]
        ):
            with self.assertRaisesRegex(ValueError, "Clean source"):
                release.provenance(Path("/synthetic"))

    def test_source_snapshot_excludes_history_and_private_outputs(self):
        names = release.source_files(HERE.parents[1])
        self.assertIn("desktop/native/application.py", names)
        self.assertIn("LICENSE", names)
        self.assertNotIn("ci/p6-cleanup-inventory.json", names)
        self.assertFalse(
            any(n.startswith(("ci-output/", "ci/evidence/")) for n in names)
        )


class WheelTests(unittest.TestCase):
    def fixture(self, root):
        files = []
        for name in ["PySide6", "PySide6_Addons", "PySide6_Essentials", "shiboken6"]:
            p = root / (name + "-6.11.3-py3-none-any.whl")
            with zipfile.ZipFile(p, "x") as archive:
                archive.writestr(
                    name + "-6.11.3.dist-info/METADATA",
                    f"Name: {name}\nVersion: 6.11.3\n"
                    "License-Expression: LGPL-3.0-only\n",
                )
                archive.writestr(name + "/synthetic.so", b"\x7fELFsynthetic")
            files.append(
                {
                    "name": name,
                    "version": "6.11.3",
                    "filename": p.name,
                    "bytes": p.stat().st_size,
                    "sha256": release.sha(p),
                }
            )
        return {"files": files}

    def test_exact_stack_and_hashes_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dependencies = self.fixture(root)
            self.assertEqual(len(release.wheels(root, dependencies)), 4)
            changed = copy.deepcopy(dependencies)
            changed["files"][0]["sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                release.wheels(root, changed)

    def test_missing_or_mixed_qt_member_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dependencies = self.fixture(root)
            dependencies["files"].pop()
            with self.assertRaisesRegex(ValueError, "Coherent"):
                release.wheels(root, dependencies)

    def test_notice_absence_is_not_cleared_by_import_or_license_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dependencies = self.fixture(root)
            inventory = release.dependency_inventory(release.wheels(root, dependencies))
            self.assertFalse(inventory["complete_SBOM"])
            for entry in inventory["distributions"]:
                self.assertEqual(entry["notice_coverage"], "MISSING IN WHEEL")
                self.assertEqual(
                    entry["redistribution_clearance"], "NOT INFERRED FROM METADATA"
                )
                self.assertEqual(len(entry["ELF_files"]), 1)

    def test_official_redirect_required(self):
        handler = driver.OfficialOnly()
        for url in [
            "http://files.pythonhosted.org/file",
            "https://unreviewed.example/file",
            "https://credential@files.pythonhosted.org/file",
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                handler.redirect_request(None, None, 302, "", {}, url)


class HandoffTests(unittest.TestCase):
    def test_policy_preflight_error_is_safe_and_does_not_overwrite_evidence(self):
        output = io.StringIO()
        with patch.object(
            policy, "main", side_effect=ValueError("private-token/private-path")
        ):
            with redirect_stdout(output):
                self.assertEqual(policy.safe_main(), 2)
        record = json.loads(output.getvalue())
        self.assertTrue(record["complete"])
        self.assertIn("NOT CONFIRMED", record["host_policy"])
        self.assertNotIn("private-token", output.getvalue())

    def test_normal_policy_setup_refuses_noncanonical_root(self):
        engine = load("n4_real_engine", HERE.parents[1] / "desktop/install_engine.py")
        with self.assertRaisesRegex(ValueError, "canonical"):
            policy.prepare(
                engine,
                Path("/unreviewed-install"),
                "0" * 64,
                Path("/unreviewed-output"),
            )

    def test_policy_preparation_never_loads_a_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            api = SimpleNamespace(
                require_contract=lambda *a: None,
                render_policy=lambda *a, **kw: b"synthetic policy\n",
                profile_name=lambda *a: "synthetic-profile",
                read_loaded_profile=lambda *a: {"state": "ABSENT"},
            )
            engine = SimpleNamespace(
                checked_path=lambda p: p,
                deployment_paths=lambda *a: None,
                load=lambda p: {"release": "synthetic"},
                member_name=lambda n: n,
                installed=lambda p: (
                    {"manifest_sha256": "a" * 64},
                    {"kind": "candidate", "apparmor": {}},
                ),
                require=release.require,
                support=lambda *a: api,
            )
            with patch.object(policy.subprocess, "run") as run:
                _, _, record = policy.prepare(
                    engine, root, "a" * 64, root / "evidence", disposable=True
                )
            self.assertEqual(record["host_policy"], "NOT MODIFIED")
            command = run.call_args.args[0]
            self.assertIn("-Q", command)
            self.assertNotIn("sudo", command)

    def test_wrong_manifest_stops_before_policy_parser_or_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = SimpleNamespace(
                checked_path=lambda p: p,
                deployment_paths=lambda *a: None,
                load=lambda p: {"release": "synthetic"},
                member_name=lambda n: n,
                installed=lambda p: ({"manifest_sha256": "a" * 64}, {}),
                require=release.require,
            )
            with patch.object(policy.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "Exact reviewed"):
                    policy.prepare(engine, root, "b" * 64, root / "evidence")
            run.assert_not_called()
            self.assertFalse((root / "evidence").exists())

    def test_no_claim_that_headless_verification_is_renderer_pass(self):
        source = (HERE.parents[1] / "ci/native.py").read_text()
        self.assertIn('"renderer": "NOT EXECUTED"', source)
        self.assertNotIn("QTWEBENGINE_DISABLE_SANDBOX=", source)
        self.assertNotIn("--no-sandbox", source)


if __name__ == "__main__":
    unittest.main()
