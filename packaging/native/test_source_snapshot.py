"""CI source-copy isolation; these fixtures do not establish online install PASS."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "source_snapshot_ci", ROOT / "ci/native_source.py"
)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class SourceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "checkout"
        self.root.mkdir()
        self.snapshot = self.base / "snapshot"
        (self.root / "install.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.root / "packaging/native").mkdir(parents=True)
        (self.root / driver.SOURCE_METADATA).write_text(
            json.dumps({"release_version": "0.1.0-n4.2"})
        )
        self.sources = {
            name: self.root / name for name in ("install.sh", driver.SOURCE_METADATA)
        }

    def test_clean_snapshot_omits_existing_git_environments_and_wheelhouse(self):
        for name in (
            ".git",
            ".venv",
            "frontend/node_modules",
            "frontend/dist",
            "wheels",
        ):
            path = self.root / name
            path.mkdir(parents=True)
            (path / "retained-data").write_text("must not be copied")
        record = driver.copy_source(self.root, self.snapshot, self.sources)
        driver.verify_source(self.snapshot, record)
        copied = {
            str(p.relative_to(self.snapshot))
            for p in self.snapshot.rglob("*")
            if p.is_file()
        }
        self.assertEqual(copied, set(self.sources))
        self.assertEqual(record["source_files"], 2)
        self.assertTrue((self.root / ".git/retained-data").is_file())
        self.assertTrue((self.root / "wheels/retained-data").is_file())

    def test_archive_and_clone_use_identical_explicit_source_bytes(self):
        first = driver.copy_source(self.root, self.snapshot, self.sources)
        (self.root / ".git").mkdir()
        (self.root / ".git/config").write_text("synthetic Git metadata")
        second = driver.copy_source(self.root, self.base / "clone-copy", self.sources)
        self.assertEqual(first, second)

    def test_actual_consumed_source_closure_survives_without_git_or_build_outputs(self):
        source = driver.module(
            "snapshot_source_recipe", ROOT / "packaging/native/source_install.py"
        )
        inputs = source.source_files(ROOT)
        for name in (
            "install.sh",
            "update.sh",
            ".nvmrc",
            driver.SOURCE_METADATA,
            "frontend/index.html",
            "frontend/package.json",
            "frontend/package-lock.json",
            "desktop/install_engine.py",
            "desktop/native_operations.py",
            "packaging/native/source_install.py",
        ):
            self.assertIn(name, inputs)
        record = driver.copy_source(ROOT, self.snapshot, inputs)
        driver.verify_source(self.snapshot, record)
        self.assertEqual(set(source.source_files(self.snapshot)), set(inputs))
        self.assertFalse((self.snapshot / ".git").exists())

    def test_generated_binary_and_escaping_inventory_paths_are_rejected(self):
        for name in (
            "../escape",
            "/absolute",
            ".git/config",
            "wheels/dependency.whl",
            "frontend/node_modules/dependency.js",
            "frontend/dist/index.html",
            "application.zip",
            "library.so",
            "library.so.6",
            "compiler.pyc",
            "bad\nname",
        ):
            with self.subTest(path=name), self.assertRaises(ValueError):
                driver.copy_source(
                    self.root,
                    self.snapshot,
                    {name: self.root / "install.sh"},
                )
            self.assertFalse(self.snapshot.exists())

    def test_symlink_and_hardlink_inputs_are_refused_before_copy(self):
        link = self.root / "linked.sh"
        link.symlink_to(self.root / "install.sh")
        with self.assertRaises(ValueError):
            driver.copy_source(self.root, self.snapshot, {"linked.sh": link})
        link.unlink()
        os.link(self.root / "install.sh", link)
        with self.assertRaises(ValueError):
            driver.copy_source(self.root, self.snapshot, {"linked.sh": link})
        self.assertFalse(self.snapshot.exists())

    def test_changed_source_and_existing_snapshot_are_refused(self):
        record = driver.copy_source(self.root, self.snapshot, self.sources)
        with self.assertRaises(ValueError):
            driver.copy_source(self.root, self.snapshot, self.sources)
        (self.snapshot / "install.sh").write_text("changed")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            driver.verify_source(self.snapshot, record)

    def test_snapshot_capacity_is_measured_before_creation(self):
        with patch.object(driver, "SOURCE_LIMIT", 1), self.assertRaises(ValueError):
            driver.copy_source(self.root, self.snapshot, self.sources)
        self.assertFalse(self.snapshot.exists())

    def test_online_commands_use_user_entrypoints_and_fresh_workdirs(self):
        for update in (False, True):
            command = driver.install_command(
                self.snapshot,
                self.snapshot / "ci-output/client",
                self.snapshot / "ci-output/fresh-work",
                update=update,
            )
            self.assertEqual(command[0], "bash")
            self.assertEqual(command[1].name, "update.sh" if update else "install.sh")
            self.assertIn("--disposable", command)
            self.assertNotIn("--wheelhouse", command)
            self.assertNotIn("--prepare-only", command)
            self.assertNotIn("--reinstall", command)

    def test_failure_and_interruption_are_not_silently_retried(self):
        child = Mock(pid=1234)
        child.wait.return_value = 1
        child.poll.return_value = 1
        with (
            patch.object(driver.subprocess, "Popen", return_value=child) as launch,
            self.assertRaises(subprocess.CalledProcessError),
        ):
            driver.run_operation(["synthetic"], self.base / "failure.log", timeout=3)
        launch.assert_called_once()
        self.assertEqual(launch.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(launch.call_args.kwargs["start_new_session"])
        child.wait.assert_called_once_with(3)
        child.wait.side_effect = [KeyboardInterrupt(), 0]
        child.poll.return_value = None
        with (
            patch.object(driver.subprocess, "Popen", return_value=child) as launch,
            patch.object(driver.os, "killpg") as terminate,
            self.assertRaises(KeyboardInterrupt),
        ):
            driver.run_operation(["synthetic"], self.base / "interrupted.log")
        launch.assert_called_once()
        terminate.assert_called_once_with(1234, driver.signal.SIGINT)

    def test_update_fixture_increments_only_packaging_version(self):
        self.assertEqual(driver.next_fixture_version("0.1.0-n4.2"), "0.1.0-n4.3")
        self.assertEqual(driver.next_fixture_version("0.1.0"), "0.1.1")
        for value in ("latest", "0.1", "0.1.0-preview"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                driver.next_fixture_version(value)


if __name__ == "__main__":
    unittest.main()
