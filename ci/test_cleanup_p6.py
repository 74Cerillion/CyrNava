"""Exercise deletion only on newly created fixtures, never repository targets."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "cleanup_p6", Path(__file__).with_name("cleanup_p6.py")
)
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix="cyrnava-cleanup-fixture-",
            dir=Path(__file__).resolve().parents[1] / "ci-output",
        )
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        self.target = self.root / "disposable"
        self.target.mkdir()
        (self.target / "file").write_text("fixture")

    def audit(self):
        snap = cleanup.snapshot(self.root, "disposable")
        return {
            "root_identity": [self.root.stat().st_dev, self.root.stat().st_ino],
            "head": "fixture",
            "guards": {},
            "targets": [{"path": "disposable", "fingerprint": snap["fingerprint"]}],
        }

    def test_identical_target_has_stable_snapshot(self):
        self.assertEqual(
            cleanup.snapshot(self.root, "disposable"),
            cleanup.snapshot(self.root, "disposable"),
        )

    def test_same_size_content_change_is_detected(self):
        old = cleanup.snapshot(self.root, "disposable")
        (self.target / "file").write_text("changed")
        self.assertNotEqual(
            old["fingerprint"], cleanup.snapshot(self.root, "disposable")["fingerprint"]
        )

    def test_symlink_escape_is_rejected(self):
        (self.target / "escape").symlink_to("/etc/passwd")
        with self.assertRaises(cleanup.Refused):
            cleanup.snapshot(self.root, "disposable")

    def test_symlink_ancestor_is_rejected(self):
        (self.root / "alias").symlink_to(self.target, target_is_directory=True)
        with self.assertRaises(cleanup.Refused):
            cleanup.snapshot(self.root, "alias/file")

    def test_nested_mount_even_on_same_device_is_rejected(self):
        text = f"1 0 1:1 / {self.target}/sub rw - ext4 fixture rw"
        with self.assertRaises(cleanup.Refused):
            cleanup.mount_check(self.root, "disposable", text)

    def test_ancestor_mount_is_rejected(self):
        text = f"1 0 1:1 / {self.target} rw - ext4 fixture rw"
        with self.assertRaises(cleanup.Refused):
            cleanup.mount_check(self.root, "disposable/file", text)

    def test_special_object_is_rejected(self):
        os.mkfifo(self.target / "pipe")
        with self.assertRaises(cleanup.Refused):
            cleanup.snapshot(self.root, "disposable")

    def test_changed_target_is_preserved(self):
        audit = self.audit()
        (self.target / "new").write_text("unique")
        with (
            patch.object(cleanup.subprocess, "check_output", return_value="fixture"),
            self.assertRaises(cleanup.Refused),
        ):
            cleanup.validate(self.root, audit)
        self.assertTrue((self.target / "new").exists())

    def test_changed_guard_is_preserved(self):
        guard = self.root / "source.py"
        guard.write_text("old")
        audit = self.audit()
        audit["guards"] = {"source.py": "0" * 64}
        with (
            patch.object(cleanup.subprocess, "check_output", return_value="fixture"),
            self.assertRaises(cleanup.Refused),
        ):
            cleanup.validate(self.root, audit)
        self.assertTrue(self.target.exists())

    def test_wrong_root_identity_is_rejected(self):
        audit = self.audit()
        audit["root_identity"][1] += 1
        with self.assertRaises(cleanup.Refused):
            cleanup.validate(self.root, audit)

    def test_fixture_removal_keeps_unlisted_file_and_link_destination(self):
        kept = self.root / "keep"
        kept.write_text("retained")
        (self.target / "link").symlink_to("../keep")
        snap = cleanup.snapshot(self.root, "disposable")
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            cleanup.erase_verified(fd, self.root, {"path": "disposable"}, snap)
        finally:
            os.close(fd)
        self.assertFalse(self.target.exists())
        self.assertEqual(kept.read_text(), "retained")

    def test_target_replaced_with_escape_after_snapshot_is_preserved(self):
        snap = cleanup.snapshot(self.root, "disposable")
        self.target.rename(self.root / "original")
        self.target.symlink_to("/tmp")
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            with self.assertRaises(cleanup.Refused):
                cleanup.erase_verified(fd, self.root, {"path": "disposable"}, snap)
        finally:
            os.close(fd)
        self.assertTrue((self.root / "original/file").exists())
        self.target.unlink()  # Fixture only; never a repository target.

    def test_known_editor_services_only_exempt_cwd_heuristic(self):
        for comm, argv in (
            ("node", ["node", "/editor/typescript/lib/tsserver.js", "--stdio"]),
            ("node", ["node", "/editor/eslintServer.js", "--stdio"]),
            ("python3", ["python3", "-m", "pylsp"]),
        ):
            with self.subTest(comm=comm, argv=argv):
                self.assertTrue(cleanup.editor_service(comm, argv))

    def test_build_test_app_and_unknown_workers_are_not_exempt(self):
        for comm, argv in (
            ("node", ["node", "vite", "build"]),
            ("npm", ["npm", "run", "test"]),
            ("python3", ["python3", "-m", "pytest"]),
            ("python3", ["python3", "-m", "uvicorn"]),
            ("node", ["node", "unknown.js"]),
            ("python3", ["python3", "worker.py"]),
            ("node", ["node", "not-tsserver.js"]),
        ):
            with self.subTest(comm=comm, argv=argv):
                self.assertFalse(cleanup.editor_service(comm, argv))

    def test_idle_editor_worker_in_repository_is_allowed(self):
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", "import time; time.sleep(20)"],
            cwd=self.root,
        )
        try:
            with patch.object(cleanup, "editor_service", return_value=True):
                cleanup.assert_idle(self.root, [{"path": "disposable"}])
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_unknown_worker_in_repository_fails_closed_with_safe_diagnostic(self):
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", "import time; time.sleep(20)"],
            cwd=self.root,
        )
        try:
            with self.assertRaisesRegex(
                cleanup.Refused, "unclassified worker"
            ) as error:
                cleanup.assert_idle(self.root, [{"path": "disposable"}])
            self.assertNotIn("import time", str(error.exception))
            self.assertNotIn(str(self.root), str(error.exception))
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_editor_service_with_open_target_is_still_rejected(self):
        child = subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-c",
                "import time; f=open('disposable/file'); time.sleep(20)",
            ],
            cwd=self.root,
        )
        try:
            # The child is exempted only from the broad cwd heuristic. Its open
            # target handle must independently block cleanup. Synchronize on fd.
            import time

            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                links = []
                for fd in Path(f"/proc/{child.pid}/fd").iterdir():
                    try:
                        links.append(os.readlink(fd))
                    except FileNotFoundError:
                        pass
                if str(self.target / "file") in links:
                    break
            else:
                self.fail("Fixture child did not open target")
            with (
                patch.object(cleanup, "editor_service", return_value=True),
                self.assertRaisesRegex(cleanup.Refused, "Open target"),
            ):
                cleanup.assert_idle(self.root, [{"path": "disposable"}])
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_busy_target_is_rejected(self):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(20)"], cwd=self.target
        )
        try:
            with self.assertRaises(cleanup.Refused):
                cleanup.assert_idle(self.root, [{"path": "disposable"}])
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_preview_never_prompts_or_deletes(self):
        audit = {
            "root": str(self.root),
            "targets": [
                {
                    "path": "disposable",
                    "allocated_bytes": 4096,
                    "estimated_reclaim_bytes": 4096,
                    "reason": "fixture",
                }
            ],
        }
        with (
            patch.object(cleanup, "AUDIT", audit),
            patch.object(sys, "argv", ["cleanup", "--preview"]),
            patch.object(
                cleanup,
                "validate",
                return_value={"disposable": cleanup.snapshot(self.root, "disposable")},
            ),
            patch("builtins.input") as prompt,
            patch.object(cleanup, "erase_verified") as erase,
        ):
            cleanup.main()
            prompt.assert_not_called()
            erase.assert_not_called()

    def test_apply_requires_exactly_one_confirmation(self):
        audit = {
            "root": str(self.root),
            "targets": [
                {
                    "path": "disposable",
                    "allocated_bytes": 4096,
                    "estimated_reclaim_bytes": 4096,
                    "reason": "fixture",
                }
            ],
        }
        with (
            patch.object(cleanup, "AUDIT", audit),
            patch.object(sys, "argv", ["cleanup"]),
            patch.object(
                cleanup,
                "validate",
                return_value={"disposable": cleanup.snapshot(self.root, "disposable")},
            ),
            patch.object(cleanup, "assert_idle"),
            patch.object(cleanup, "mount_check"),
            patch.object(sys.stdin, "isatty", return_value=True),
            patch("builtins.input", return_value="DELETE AUDITED TARGETS") as prompt,
            patch.object(cleanup, "erase_verified") as erase,
        ):
            cleanup.main()
            self.assertEqual(prompt.call_count, 1)
            self.assertEqual(erase.call_count, 1)
        self.assertTrue((self.target / "file").exists())

    def test_wrong_confirmation_never_deletes(self):
        audit = {
            "root": str(self.root),
            "targets": [
                {
                    "path": "disposable",
                    "allocated_bytes": 4096,
                    "estimated_reclaim_bytes": 4096,
                    "reason": "fixture",
                }
            ],
        }
        with (
            patch.object(cleanup, "AUDIT", audit),
            patch.object(sys, "argv", ["cleanup"]),
            patch.object(
                cleanup,
                "validate",
                return_value={"disposable": cleanup.snapshot(self.root, "disposable")},
            ),
            patch.object(cleanup, "assert_idle"),
            patch.object(sys.stdin, "isatty", return_value=True),
            patch("builtins.input", return_value="yes") as prompt,
            patch.object(cleanup, "erase_verified") as erase,
            self.assertRaises(cleanup.Refused),
        ):
            try:
                cleanup.main()
            finally:
                self.assertEqual(prompt.call_count, 1)
                erase.assert_not_called()

    def test_measure_uses_allocation_and_reports_actual_free_space(self):
        measured = cleanup.measure(self.root)
        self.assertGreater(measured["repository_allocated_bytes"], 0)
        self.assertGreater(measured["filesystem_available_bytes"], 0)

    def test_wrapper_only_delegates_to_the_audited_engine(self):
        wrapper = Path(__file__).resolve().parents[1] / "cleanup_cyrnava.sh"
        text = wrapper.read_text()
        subprocess.run(["bash", "-n", str(wrapper)], check=True)
        self.assertIn('exec python3 -B "$repo/ci/cleanup_p6.py" "$@"', text)
        self.assertNotIn("DELETE AUDITED TARGETS", text)
        self.assertNotIn("rm ", text)
        self.assertNotIn("sudo", text)

    def test_wrapper_rejects_execution_from_a_different_repository(self):
        source = Path(__file__).resolve().parents[1] / "cleanup_cyrnava.sh"
        copied = self.root / source.name
        copied.write_bytes(source.read_bytes())
        result = subprocess.run(
            ["bash", str(copied)], check=False, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("exact CyrNava repository", result.stderr)
        self.assertTrue((self.target / "file").exists())

    def test_guarded_material_cannot_be_a_deletion_target(self):
        audit = self.audit()
        audit["guards"] = {"disposable/file": "0" * 64}
        with (
            patch.object(cleanup.subprocess, "check_output", return_value="fixture"),
            self.assertRaisesRegex(cleanup.Refused, "intersects preserved"),
        ):
            cleanup.validate(self.root, audit)
        self.assertTrue((self.target / "file").exists())

    def test_overlapping_batch_is_rejected_before_deletion(self):
        audit = self.audit()
        audit["targets"].append({"path": "disposable/file", "fingerprint": "unused"})
        with (
            patch.object(cleanup.subprocess, "check_output", return_value="fixture"),
            self.assertRaisesRegex(cleanup.Refused, "Overlapping"),
        ):
            cleanup.validate(self.root, audit)
        self.assertTrue((self.target / "file").exists())

    def test_exact_extracted_child_keeps_parent_inputs_and_escaping_sibling(self):
        files = self.target / "files"
        files.mkdir()
        (files / "payload").write_text("regenerable fixture")
        (self.target / "bundle").write_text("accepted fixture artifact")
        (self.target / "outside").symlink_to("/run")
        snap = cleanup.snapshot(self.root, "disposable/files")
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            cleanup.erase_verified(fd, self.root, {"path": "disposable/files"}, snap)
        finally:
            os.close(fd)
        self.assertFalse(files.exists())
        self.assertEqual(
            (self.target / "bundle").read_text(), "accepted fixture artifact"
        )
        self.assertEqual(os.readlink(self.target / "outside"), "/run")

    def test_absent_target_is_reported_without_reclaim(self):
        audit = self.audit()
        (self.target / "file").unlink()
        self.target.rmdir()
        with patch.object(cleanup.subprocess, "check_output", return_value="fixture"):
            self.assertEqual(cleanup.validate(self.root, audit), {"disposable": None})

    def test_changed_git_staging_state_is_rejected(self):
        audit = self.audit()
        audit["index_stage_sha256"] = hashlib.sha256(b"approved").hexdigest()
        with (
            patch.object(
                cleanup.subprocess, "check_output", side_effect=["fixture", b"changed"]
            ),
            self.assertRaisesRegex(cleanup.Refused, "staging state changed"),
        ):
            cleanup.validate(self.root, audit)

    def test_tracked_target_is_rejected_even_with_matching_staging_snapshot(self):
        audit = self.audit()
        index = b"100644 " + b"a" * 40 + b" 0\tdisposable/file\0"
        audit["index_stage_sha256"] = hashlib.sha256(index).hexdigest()
        with (
            patch.object(
                cleanup.subprocess, "check_output", side_effect=["fixture", index]
            ),
            self.assertRaisesRegex(cleanup.Refused, "tracked or staged material"),
        ):
            cleanup.validate(self.root, audit)

    def test_reviewed_staged_file_outside_batch_is_allowed(self):
        audit = self.audit()
        index = b"100644 " + b"a" * 40 + b" 0\tapproved-source.py\0"
        audit["index_stage_sha256"] = hashlib.sha256(index).hexdigest()
        with patch.object(
            cleanup.subprocess, "check_output", side_effect=["fixture", index]
        ):
            self.assertIsNotNone(cleanup.validate(self.root, audit)["disposable"])

    @contextlib.contextmanager
    def invocation(self, snapshots=None):
        audit = self.audit()
        audit["root"] = str(self.root)
        audit["targets"][0]["reason"] = "fixture only"
        snaps = (
            snapshots
            if snapshots is not None
            else {"disposable": cleanup.snapshot(self.root, "disposable")}
        )
        with (
            patch.object(cleanup, "AUDIT", audit),
            patch.object(sys, "argv", ["cleanup"]),
            patch.object(cleanup, "validate", return_value=snaps),
            patch.object(cleanup, "assert_idle"),
            patch.object(cleanup, "mount_check"),
            patch.object(sys.stdin, "isatty", return_value=True),
        ):
            yield

    def test_eof_cancels_without_deletion(self):
        with (
            self.invocation(),
            patch("builtins.input", side_effect=EOFError),
            patch.object(cleanup, "erase_verified") as erase,
            self.assertRaisesRegex(cleanup.Refused, "end of input"),
        ):
            cleanup.main()
        erase.assert_not_called()

    def test_noninteractive_invocation_never_prompts_or_deletes(self):
        with (
            self.invocation(),
            patch.object(sys.stdin, "isatty", return_value=False),
            patch("builtins.input") as prompt,
            patch.object(cleanup, "erase_verified") as erase,
            self.assertRaisesRegex(cleanup.Refused, "interactively"),
        ):
            cleanup.main()
        prompt.assert_not_called()
        erase.assert_not_called()

    def test_preview_prints_measured_space_and_zero_for_absent_target(self):
        output = io.StringIO()
        with (
            self.invocation({"disposable": None}),
            patch.object(sys, "argv", ["cleanup", "--preview"]),
            patch("builtins.input") as prompt,
            contextlib.redirect_stdout(output),
        ):
            cleanup.main()
        self.assertIn("already absent; no reclaim", output.getvalue())
        self.assertIn("Estimated reclaim: 0 bytes", output.getvalue())
        self.assertIn("filesystem_available_bytes", output.getvalue())
        prompt.assert_not_called()

    def test_partial_target_failure_reports_completed_and_unfinished_paths(self):
        def partial(*_args):
            (self.target / "file").unlink()  # Disposable fixture only.
            raise OSError("fixture interruption")

        output = io.StringIO()
        with (
            self.invocation(),
            patch("builtins.input", return_value="DELETE AUDITED TARGETS"),
            patch.object(cleanup, "erase_verified", side_effect=partial),
            contextlib.redirect_stdout(output),
            self.assertRaises(OSError),
        ):
            cleanup.main()
        line = next(
            s
            for s in output.getvalue().splitlines()
            if s.startswith("Cleanup measurement: ")
        )
        report = json.loads(line.split(": ", 1)[1])
        self.assertFalse(report["complete"])
        self.assertEqual(report["deleted_paths"], [])
        self.assertEqual(report["not_completed_paths"], ["disposable"])
        self.assertEqual(report["interrupted_target_may_be_partial"], "disposable")
        self.assertIn("filesystem_available_bytes", report["before"])
        self.assertIn("filesystem_available_bytes", report["after"])


if __name__ == "__main__":
    unittest.main()
