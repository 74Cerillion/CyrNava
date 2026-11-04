"""N2 human marker and reviewed restart continuation; synthetic fixtures only."""

import contextlib
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


driver = module("n2_state_continuation", ROOT / "packaging/native/verify_desktop.py")
engine = module("n2_state_engine", ROOT / "desktop/install_engine.py")


class StateTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "ci-output/native-n2-review-1/owner-2-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.check = module(
            "n2_snapshot_fixture",
            ROOT / "packaging/native/feasibility/check_application.py",
        )
        self.check.TITLE, self.check.FOLDER, self.check.TEXT = (
            "N2 installed note",
            "N2 installed folder",
            "N2 desktop verified",
        )
        with sqlite3.connect(self.root / "engage.sqlite3") as c:
            c.executescript(
                "CREATE TABLE folders(id TEXT,name TEXT); CREATE TABLE notes(id TEXT,title TEXT,folder_id TEXT,document_json TEXT); CREATE TABLE assets(id TEXT,note_id TEXT);"
            )
            c.execute("INSERT INTO folders VALUES('f',?)", (self.check.FOLDER,))
            c.execute("INSERT INTO notes VALUES('n',?,'f','[]')", (self.check.TITLE,))
            c.execute("INSERT INTO assets VALUES('asset','n')")
        self.write_note()

    def write_note(self, text="N2 Desktop Verified", *, bold=True, image=True):
        document = [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text, "styles": {"bold": bold}}],
            }
        ]
        if image:
            document.append({"type": "image", "props": {"url": "/api/assets/asset"}})
        with sqlite3.connect(self.root / "engage.sqlite3") as c:
            c.execute("UPDATE notes SET document_json=?", (json.dumps(document),))

    def snapshot(self):
        inspector = lambda _: {
            "schema": 5,
            "counts": {"notes": 1, "folders": 1, "assets": 1},
            "files": {"assets/asset": "synthetic-hash"},
        }
        return driver.state_snapshot(
            self.check,
            self.root,
            inspector,
            lambda _: engine.digest(self.root / "engage.sqlite3"),
        )

    def test_capitalization_variants_pass_with_bold_and_image(self):
        for text in (
            "N2 desktop verified",
            "N2 Desktop Verified",
            "N2 DESKTOP VERIFIED",
        ):
            self.write_note(text)
            with self.subTest(text=text):
                result = self.snapshot()
                self.assertEqual(result["required_note_folder_bold_image"], "PASS")
                self.assertEqual(
                    result["matched_bold_span_sha256"],
                    hashlib.sha256(text.encode()).hexdigest(),
                )
                self.assertEqual(self.check.TEXT, "N2 desktop verified")

    def test_unformatted_marker_is_still_rejected(self):
        self.write_note(bold=False)
        with self.assertRaisesRegex(
            driver.StateValidationError, "required_bold_marker"
        ):
            self.snapshot()

    def test_wrong_marker_is_still_rejected(self):
        self.write_note("unrelated synthetic text")
        with self.assertRaisesRegex(
            driver.StateValidationError, "required_bold_marker"
        ):
            self.snapshot()

    def test_missing_image_is_still_rejected(self):
        self.write_note(image=False)
        with self.assertRaisesRegex(driver.StateValidationError, "attached_image"):
            self.snapshot()
        self.assertEqual(self.check.TEXT, "N2 desktop verified")

    def test_case_changes_during_restart_are_not_hidden(self):
        before = self.snapshot()
        self.write_note("N2 desktop verified")
        after = self.snapshot()
        self.assertNotEqual(before["content_sha256"], after["content_sha256"])
        self.assertNotEqual(before, after)

    def test_snapshot_does_not_modify_database(self):
        before = engine.digest(self.root / "engage.sqlite3")
        self.snapshot()
        self.assertEqual(engine.digest(self.root / "engage.sqlite3"), before)

    def test_safe_error_names_specific_assertion(self):
        error = driver.StateValidationError("required_bold_marker")
        self.assertEqual(
            driver.failure_details(error)["failed_check"], "required_bold_marker"
        )


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "ci-output/native-n2-review-1/owner-2-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "ci-output/native-n2-owner-2"
        self.source.mkdir(parents=True)
        self.profile = self.root / "profile"
        self.data = self.profile / "workspace"
        self.data.mkdir(parents=True)
        (self.data / "engage.sqlite3").write_bytes(b"synthetic database bytes")
        self.desktop = self.root / "entry.desktop"
        self.desktop.write_text("synthetic desktop identity")
        self.manifest = {"archive_sha256": "a" * 64}
        self.manifest_hash = "b" * 64
        self.result = {
            "status": "FAIL",
            "complete": True,
            "stage": "edit-state-validation",
            "error_type": "CalledProcessError",
            "driver_sha256": driver.REVIEWED_EDIT_DRIVER,
            "manifest_sha256": self.manifest_hash,
            "archive_sha256": self.manifest["archive_sha256"],
            "desktop_sha256": engine.digest(self.desktop),
            "gio_adapter_sha256": engine.digest(
                ROOT / "packaging/native/desktop_process.py"
            ),
            "phases": {"edit": dict.fromkeys(driver.PHASE_CHECKS, "PASS")},
        }
        self.save_result()
        (self.source / "edit-state.private.log").write_text(
            "synthetic old validator log"
        )
        self.baseline = (
            self.root / "ci/evidence/n2/owner-2-state-validation/review.json"
        )
        self.baseline.parent.mkdir(parents=True)
        self.baseline.write_text(
            json.dumps(
                {
                    "workspace_files_sha256": {
                        "engage.sqlite3": engine.digest(self.data / "engage.sqlite3")
                    }
                }
            )
        )

    def save_result(self):
        (self.source / "result.json").write_text(json.dumps(self.result))

    def reviewed(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(driver, "ROOT", self.root))
            stack.enter_context(
                patch.object(
                    driver,
                    "REVIEWED_EDIT_RESULT",
                    engine.digest(self.source / "result.json"),
                )
            )
            stack.enter_context(
                patch.object(
                    driver,
                    "REVIEWED_EDIT_LOG",
                    engine.digest(self.source / "edit-state.private.log"),
                )
            )
            stack.enter_context(
                patch.object(
                    driver, "REVIEWED_EDIT_BASELINE", engine.digest(self.baseline)
                )
            )
            return driver.reviewed_edit(
                engine,
                self.source,
                self.profile,
                self.manifest,
                self.manifest_hash,
                self.desktop,
            )

    def test_reviewed_pass_is_explicitly_inherited_without_evidence_edits(self):
        before = engine.digest(self.source / "result.json")
        value = self.reviewed()
        self.assertEqual(
            value["edit_checks"], dict.fromkeys(driver.PHASE_CHECKS, "PASS")
        )
        self.assertIn("INHERITED", value["scope"])
        self.assertEqual(engine.digest(self.source / "result.json"), before)

    def test_failed_first_phase_cannot_be_promoted(self):
        self.result["phases"]["edit"]["renderer"] = "FAIL"
        self.save_result()
        with self.assertRaisesRegex(ValueError, "first phase"):
            self.reviewed()

    def test_changed_saved_data_blocks_continuation(self):
        (self.data / "engage.sqlite3").write_bytes(b"changed since review")
        with self.assertRaisesRegex(ValueError, "workspace changed"):
            self.reviewed()

    def test_changed_artifact_blocks_continuation(self):
        self.manifest["archive_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.reviewed()

    def test_changed_workspace_pointer_blocks_continuation(self):
        (self.profile / "active-workspace.json").write_text("unexpected pointer")
        with self.assertRaisesRegex(ValueError, "workspace selection"):
            self.reviewed()


if __name__ == "__main__":
    unittest.main()
