"""N3 handoff guards; fixtures do not count as native GUI evidence."""

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "n3_handoff_tests", ROOT / "packaging/native/verify_update.py"
)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class HandoffTests(unittest.TestCase):
    def test_unrelated_Qt_cache_changes_do_not_mask_saved_data_changes(self):
        before = {
            "files": {
                "workspaces/abc/engage.sqlite3": {"sha256": "1"},
                "desktop.json": {"sha256": "2"},
                "web-profile-abc/cache": {"sha256": "3"},
            }
        }
        after = {"files": {**before["files"], "web-profile-abc/cache": {"sha256": "4"}}}
        self.assertEqual(driver.saved_data(before), driver.saved_data(after))
        after["files"]["workspaces/abc/engage.sqlite3"] = {"sha256": "5"}
        self.assertNotEqual(driver.saved_data(before), driver.saved_data(after))

    def test_visual_confirmation_requires_explicit_phrase(self):
        with (
            patch("builtins.input", side_effect=["", "CONFIRM N3 UPDATE"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            driver.confirmation()
        for response in ("", "NO"):
            with (
                patch("builtins.input", return_value=response),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(ValueError),
            ):
                driver.confirmation()

    def test_no_owner_terminal_means_no_application_or_menu_operation(self):
        engine = driver.module(
            "n3_handoff_guard_engine", ROOT / "desktop/install_engine.py"
        )
        real = driver.module

        def load(name, path):
            return engine if name == "n3_owner_engine" else real(name, path)

        with (
            patch.object(driver, "module", side_effect=load),
            patch.object(engine, "host_supported"),
            patch.object(driver.sys.stdin, "isatty", return_value=False),
            patch.object(
                driver.sys,
                "argv",
                [
                    "verify_update.py",
                    "--owner-host",
                    "--manifest-sha256",
                    "0" * 64,
                    "--output",
                    str(ROOT / "ci-output/native-n3-owner-999"),
                ],
            ),
            self.assertRaisesRegex(ValueError, "Owner GNOME"),
        ):
            driver.main()
        self.assertFalse((ROOT / "ci-output/native-n3-owner-999").exists())


if __name__ == "__main__":
    unittest.main()
