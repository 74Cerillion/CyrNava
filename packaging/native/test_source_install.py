"""Focused source trust/acquisition configuration tests; no downloads or GUI."""

import base64
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "source_install_fixture", Path(__file__).with_name("source_install.py")
)
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)


class SourceInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name, content="fixture\n"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def npm_fixture(self):
        self.write(
            "frontend/package.json",
            json.dumps(
                {
                    "scripts": {"build": "tsc --noEmit && vite build"},
                    "engines": {"node": "24.x", "npm": "11.x"},
                }
            ),
        )
        self.lock = {
            "lockfileVersion": 3,
            "packages": {
                "": {},
                "node_modules/example": {
                    "version": "1.2.3",
                    "resolved": "https://registry.npmjs.org/example/-/example-1.2.3.tgz",
                    "integrity": "sha512-" + base64.b64encode(b"a" * 64).decode(),
                },
            },
        }
        self.save_lock()

    def save_lock(self):
        self.write("frontend/package-lock.json", json.dumps(self.lock))

    def source_fixture(self):
        for base in source.SOURCE_ROOTS:
            (self.root / base).mkdir(parents=True, exist_ok=True)
        for name in source.ROOT_FILES:
            self.write(name)
        self.npm_fixture()
        self.write(
            source.METADATA,
            json.dumps(
                {
                    "format": 1,
                    "mode": "source-online",
                    "release_version": "0.1.0-n4.2",
                    "repository": "https://github.com/74Cerillion/CyrNava",
                    "target": source.TARGET,
                    "locked_inputs": {},
                    "source_files": {},
                }
            ),
        )
        self.lock_patch = patch.object(source, "LOCKED_INPUTS", {})
        self.lock_patch.start()
        self.addCleanup(self.lock_patch.stop)
        source.refresh_inventory(self.root)

    def test_no_git_required_and_outputs_excluded(self):
        self.source_fixture()
        for name in (
            "frontend/node_modules/injected.js",
            "frontend/dist/injected.js",
            "packaging/native/.venv/injected.py",
            "desktop/native/evidence/private.json",
        ):
            self.write(name)
        metadata, files = source.verified_source(self.root)
        self.assertEqual(metadata["release_version"], "0.1.0-n4.2")
        self.assertFalse((self.root / ".git").exists())
        self.assertFalse(
            any("injected" in name or "private.json" in name for name in files)
        )

    def test_changed_source_rejected(self):
        self.source_fixture()
        self.write("desktop/install_engine.py", "changed")
        with self.assertRaisesRegex(ValueError, "Source snapshot changed"):
            source.verified_source(self.root)

    def test_new_consumed_source_rejected(self):
        self.source_fixture()
        self.write("backend/app/unreviewed.py")
        with self.assertRaisesRegex(ValueError, "Source snapshot changed"):
            source.verified_source(self.root)

    def test_frontend_html_and_config_are_copied_source_inputs(self):
        self.source_fixture()
        self.write("frontend/index.html", "<html><div id='root'></div></html>")
        self.write("frontend/vite.config.ts", "export default {}")
        source.refresh_inventory(self.root)
        _metadata, files = source.verified_source(self.root)
        self.assertIn("frontend/index.html", files)
        self.assertIn("frontend/vite.config.ts", files)
        self.assertIn(".nvmrc", files)

    def test_symlink_refused(self):
        self.source_fixture()
        (self.root / "frontend/public/escape.js").symlink_to(self.root / "LICENSE")
        with self.assertRaisesRegex(ValueError, "symlink"):
            source.source_files(self.root)

    def test_reviewed_npm_registry_and_integrity(self):
        self.npm_fixture()
        self.assertEqual(source.npm_lock(self.root)["entries"], 1)

    def test_npm_url_overrides_rejected(self):
        self.npm_fixture()
        for url in (
            "http://registry.npmjs.org/a.tgz",
            "https://mirror.invalid/a.tgz",
            "file:../a",
            "git+https://github.com/example/a",
            "https://user:secret@registry.npmjs.org/a.tgz",
        ):
            with self.subTest(url=url):
                self.lock["packages"]["node_modules/example"]["resolved"] = url
                self.save_lock()
                with self.assertRaisesRegex(ValueError, "official pinned"):
                    source.npm_lock(self.root)

    def test_npm_missing_integrity_and_local_links_rejected(self):
        self.npm_fixture()
        self.lock["packages"]["node_modules/example"].pop("integrity")
        self.save_lock()
        with self.assertRaisesRegex(ValueError, "SHA-512"):
            source.npm_lock(self.root)
        self.lock["packages"]["node_modules/example"]["link"] = True
        self.save_lock()
        with self.assertRaisesRegex(ValueError, "Local npm"):
            source.npm_lock(self.root)

    def test_project_npmrc_refused(self):
        self.npm_fixture()
        self.write("frontend/.npmrc", "registry=https://example.invalid\n")
        with self.assertRaisesRegex(ValueError, "configuration refused"):
            source.npm_lock(self.root)

    def test_environment_removes_overrides_and_distinct_configs(self):
        source.config_files(self.root)
        with patch.dict(
            os.environ,
            {
                "NODE_OPTIONS": "--require=evil",
                "npm_config_registry": "https://evil.invalid",
                "PYTHONPATH": "evil",
                "PIP_INDEX_URL": "https://evil.invalid",
            },
        ):
            environment = source.safe_environment(self.root)
        self.assertNotIn("npm_config_registry", environment)
        self.assertNotIn("PYTHONPATH", environment)
        self.assertNotIn("PIP_INDEX_URL", environment)
        self.assertEqual(environment["NODE_OPTIONS"], "--max-old-space-size=1536")
        self.assertNotEqual(
            environment["NPM_CONFIG_USERCONFIG"], environment["NPM_CONFIG_GLOBALCONFIG"]
        )
        self.assertEqual(Path(environment["NPM_CONFIG_USERCONFIG"]).read_bytes(), b"")

    @unittest.skipUnless(
        shutil.which("npm"),
        "npm unavailable; exact no-network config probe not executed",
    )
    def test_actual_npm_distinct_empty_configs_do_not_double_load(self):
        source.config_files(self.root)
        result = subprocess.run(
            [shutil.which("npm"), "--version"],
            env=source.safe_environment(self.root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            result.returncode,
            0,
            "npm must accept distinct owned empty user/global configs",
        )
        self.assertRegex(result.stdout.strip(), r"^[0-9]+\.[0-9]+\.[0-9]+$")

    def test_source_inventory_not_self_authentication(self):
        self.source_fixture()
        metadata = json.loads((self.root / source.METADATA).read_text())
        metadata["locked_inputs"] = {"frontend/package-lock.json": "0" * 64}
        self.write(source.METADATA, json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "lock identities changed"):
            source.verified_source(self.root)

    def test_unsupported_host_refused_before_tool_execution(self):
        def unsupported():
            raise ValueError("Supported target is Ubuntu 26.04 x86_64")

        with (
            patch.object(
                source,
                "module",
                return_value=SimpleNamespace(host_supported=unsupported),
            ),
            patch.object(source.subprocess, "check_output") as execute,
        ):
            with self.assertRaisesRegex(ValueError, "Supported target"):
                source.prerequisites(self.root)
        execute.assert_not_called()

    def test_existing_attempt_is_never_overwritten(self):
        work = self.root / "attempt"
        work.mkdir()
        retained = work / "original-evidence.json"
        retained.write_text("retained")
        with (
            patch.object(source, "verified_source", return_value=({}, {})),
            patch.object(source, "npm_lock", return_value={}),
            patch.object(source, "prerequisites", return_value={}),
            patch.object(
                source,
                "module",
                return_value=SimpleNamespace(checked_path=lambda path: Path(path)),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "Fresh work directory"):
                source.prepare(self.root, work, self.root / "installation")
        self.assertEqual(retained.read_text(), "retained")
        self.assertEqual(
            [path.name for path in work.iterdir()], ["original-evidence.json"]
        )

    def test_timeout_stops_owned_child_and_preserves_private_log(self):
        (self.root / "tmp").mkdir()
        source.config_files(self.root)
        with self.assertRaisesRegex(ValueError, "Operation timeout"):
            source.run(
                self.root,
                "timeout-fixture",
                [
                    sys.executable,
                    "-B",
                    "-c",
                    "import os,time; print(os.getpid(),flush=True); time.sleep(20)",
                ],
                timeout=0.05,
            )
        log = self.root / "timeout-fixture.private.log"
        self.assertTrue(log.is_file())
        pid = int(log.read_text().strip())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_fresh_home_missing_cache_gets_private_owned_work_parent(self):
        self.assertFalse((self.root / ".cache").exists())
        with patch.object(Path, "home", return_value=self.root):
            work = source.default_work(source.ROOT)
        self.assertEqual(work.parent, self.root / ".cache/cyrnava-source")
        self.assertFalse(work.exists())
        self.assertEqual(work.parent.stat().st_mode & 0o777, 0o700)

    def test_mid_assembly_source_change_refused_before_installation(self):
        self.source_fixture()
        work = self.root / "fresh-attempt"

        def changed_source(*args, **kwargs):
            self.write("README.md", "changed during assembly")
            return work / "local-application.zip", work / "manifest.json"

        with (
            patch.object(
                source,
                "prerequisites",
                return_value={"executables": {"npm": "/usr/bin/npm"}},
            ),
            patch.object(source, "free_space"),
            patch.object(source, "run", return_value={"status": "PASS"}),
            patch.object(source, "assemble", side_effect=changed_source),
            patch.object(
                source,
                "module",
                return_value=SimpleNamespace(checked_path=lambda path: Path(path)),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "Source snapshot changed"):
                source.prepare(self.root, work, self.root / "installation")
        evidence = json.loads((work / "preparation-result.json").read_text())
        self.assertEqual(evidence["status"], "FAIL")
        self.assertTrue(evidence["complete"])
        self.assertFalse((self.root / "installation").exists())


if __name__ == "__main__":
    unittest.main()
