"""Synthetic fixtures for the N1 owner application driver; no Qt/desktop launch."""

import contextlib
import importlib.util
import io
import json
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "n1_application_check", HERE / "check_application.py"
)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class ApplicationCheckTests(unittest.TestCase):
    @contextlib.contextmanager
    def workspace(self, *, bold=True, image=True, title=None):
        with tempfile.TemporaryDirectory(dir=check.ROOT / "ci-output") as temporary:
            data = Path(temporary)
            con = sqlite3.connect(data / "engage.sqlite3")
            con.executescript(
                "CREATE TABLE folders(id TEXT,name TEXT); CREATE TABLE notes(id TEXT,folder_id TEXT,title TEXT,document_json TEXT); CREATE TABLE assets(id TEXT,note_id TEXT);"
            )
            document = [
                {
                    "type": "paragraph",
                    "content": [{"text": check.TEXT, "styles": {"bold": bold}}],
                }
            ]
            if image:
                document.append(
                    {"type": "image", "props": {"url": "/api/assets/synthetic-asset"}}
                )
            con.execute("INSERT INTO folders VALUES(?,?)", ("folder", check.FOLDER))
            con.execute(
                "INSERT INTO notes VALUES(?,?,?,?)",
                ("note", "folder", title or check.TITLE, json.dumps(document)),
            )
            con.execute("INSERT INTO assets VALUES(?,?)", ("synthetic-asset", "note"))
            con.commit()
            con.close()
            inspector = Mock(
                return_value={
                    "schema": 5,
                    "counts": {"notes": 1, "folders": 1, "assets": 1},
                    "files": {"assets/synthetic-asset": "synthetic-hash"},
                }
            )
            yield data, inspector

    def test_snapshot_requires_saved_note_folder_rich_text_and_attached_image(self):
        with self.workspace() as (data, inspector):
            before = check.sha(data / "engage.sqlite3")
            snapshot = check.snapshot(data, inspector, lambda _: "content-hash")
            self.assertEqual(snapshot["required_note_folder_bold_image"], "PASS")
            self.assertEqual(
                snapshot["asset_hashes"], {"assets/synthetic-asset": "synthetic-hash"}
            )
            self.assertEqual(check.sha(data / "engage.sqlite3"), before)
            inspector.assert_called_once_with(data)

    def test_incomplete_owner_edits_fail_instead_of_becoming_a_gui_pass(self):
        for kwargs in ({"bold": False}, {"image": False}, {"title": "wrong title"}):
            with (
                self.subTest(kwargs=kwargs),
                self.workspace(**kwargs) as (data, inspector),
                self.assertRaises(ValueError),
            ):
                check.snapshot(data, inspector, lambda _: "not-used")

    def test_existing_validator_error_is_not_suppressed(self):
        with self.workspace() as (data, inspector):
            inspector.side_effect = ValueError("Invalid synthetic image/database")
            with self.assertRaises(ValueError):
                check.snapshot(data, inspector, lambda _: "not-used")

    @contextlib.contextmanager
    def candidate(self):
        with tempfile.TemporaryDirectory(dir=check.ROOT / "ci-output") as temporary:
            base = Path(temporary)
            candidate, output = base / "candidate", base / "output"
            candidate.mkdir()
            (candidate / "n1.json").write_text("synthetic receipt")
            (candidate / "launch.py").write_text("synthetic launcher; never executed")
            (candidate / "owner-system-schemas-role.private.log").write_bytes(b"")
            raw = candidate / "owner-system-schemas-role.renderer-cmdline.private"
            raw.write_bytes(b"synthetic evidence; not a real renderer")
            record = {
                "status": "PASS",
                "complete": True,
                "exit_code": 0,
                "receipt_sha256": check.sha(candidate / "n1.json"),
                "probe_sha256": check.sha(HERE / "sandbox_probe.py"),
                "supervisor_sha256": check.sha(HERE / "run_probe.py"),
                "private_log_sha256": check.sha(
                    candidate / "owner-system-schemas-role.private.log"
                ),
                "diagnostic": {
                    "platform": "wayland",
                    "renderer_pid_stable": True,
                    "renderer_cmdline_sha256": check.sha(raw),
                },
            }
            (candidate / "owner-system-schemas-role-result.json").write_text(
                json.dumps(record)
            )
            with (
                patch.object(check, "CANDIDATE", candidate),
                patch.object(check, "OUTPUT", output),
                patch.object(check, "RECEIPT", record["receipt_sha256"]),
                patch.object(check, "LAUNCHER", check.sha(candidate / "launch.py")),
            ):
                yield candidate, output, record

    def test_preflight_binds_candidate_and_actual_renderer_pass(self):
        with (
            self.candidate() as (candidate, _output, record),
            patch.object(
                check,
                "support",
                return_value=types.SimpleNamespace(security_pass=lambda _: True),
            ),
        ):
            self.assertEqual(check.preflight(), record)
            (candidate / "owner-system-schemas-role.private.log").write_bytes(
                b"changed"
            )
            with self.assertRaises(ValueError):
                check.preflight()

    def test_existing_attempt_or_workspace_preserved(self):
        for kind in ("attempt", "workspace"):
            with (
                self.subTest(kind=kind),
                self.candidate() as (candidate, output, _record),
            ):
                target = (
                    output / "result.json"
                    if kind == "attempt"
                    else candidate / "client/profile/workspace/engage.sqlite3"
                )
                target.parent.mkdir(parents=True)
                target.write_bytes(b"preserve")
                with (
                    patch.object(
                        check,
                        "support",
                        return_value=types.SimpleNamespace(
                            security_pass=lambda _: True
                        ),
                    ),
                    self.assertRaises(ValueError),
                ):
                    check.preflight()
                self.assertEqual(target.read_bytes(), b"preserve")

    def test_a_clean_application_exit_alone_cannot_pass(self):
        with tempfile.TemporaryDirectory(dir=check.ROOT / "ci-output") as temporary:
            process = Mock(returncode=0)
            process.poll.return_value = 0
            with (
                patch.object(check, "OUTPUT", Path(temporary)),
                patch.object(check.subprocess, "Popen", return_value=process),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(RuntimeError),
            ):
                check.launch("edit", {})

    def test_actual_launcher_command_has_no_monkeypatch_or_application_substitute(self):
        with tempfile.TemporaryDirectory(dir=check.ROOT / "ci-output") as temporary:
            process = Mock(returncode=0)
            process.poll.side_effect = [None, 0, 0]
            evidence = {
                "backend": True,
                "renderer": True,
                "qt_providers": True,
                "foreign_qt": False,
            }
            with (
                patch.object(check, "OUTPUT", Path(temporary)),
                patch.object(check.time, "sleep"),
                patch.object(check, "sample_tree", return_value=evidence),
                patch.object(check, "unauthenticated_rejected", return_value=True),
                patch.object(check.subprocess, "Popen", return_value=process) as popen,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = check.launch("edit", {"QT_QPA_PLATFORM": "wayland"})
            self.assertEqual(
                popen.call_args.args[0],
                [
                    str(check.CANDIDATE / ".venv/bin/python"),
                    "-B",
                    "-I",
                    str(check.CANDIDATE / "launch.py"),
                ],
            )
            self.assertEqual(result["owned_process_cleanup"], "PASS")

    def test_interruption_requests_normal_close_and_preserves_failure(self):
        with tempfile.TemporaryDirectory(dir=check.ROOT / "ci-output") as temporary:
            process = Mock()
            process.poll.return_value = None
            with (
                patch.object(check, "OUTPUT", Path(temporary)),
                patch.object(check, "sample_tree", side_effect=KeyboardInterrupt),
                patch.object(check.subprocess, "Popen", return_value=process),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(KeyboardInterrupt),
            ):
                check.launch("edit", {})
            process.terminate.assert_called_once_with()
            process.wait.assert_called_once_with(15)

    def test_noninteractive_execution_cannot_open_the_owner_desktop(self):
        with (
            patch.object(sys, "argv", ["check", "--owner-host"]),
            patch.object(sys.stdin, "isatty", return_value=False),
            patch.object(check.subprocess, "Popen") as process,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit),
        ):
            check.main()
        process.assert_not_called()

    def test_unauthenticated_check_requires_401_without_sending_credentials(self):
        import urllib.error
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory(dir=check.ROOT / "ci-output") as temporary:
            candidate = Path(temporary)
            profile = candidate / "client/profile"
            profile.mkdir(parents=True)
            (profile / "desktop.json").write_text(json.dumps({"port": 12345}))
            for code, expected in ((401, True), (403, False), (200, False)):
                opener = Mock()
                if code == 200:
                    opener.open.return_value = MagicMock()
                else:
                    opener.open.side_effect = urllib.error.HTTPError(
                        "synthetic", code, "synthetic", {}, None
                    )
                with (
                    self.subTest(code=code),
                    patch.object(check, "CANDIDATE", candidate),
                    patch("urllib.request.build_opener", return_value=opener),
                ):
                    self.assertEqual(check.unauthenticated_rejected(), expected)
                opener.open.assert_called_once_with(
                    "http://127.0.0.1:12345/api/tree", timeout=3
                )

    def test_full_driver_needs_both_preserved_state_and_owner_visual_confirmation(self):
        for case, answer, after, expected in (
            ("complete", "confirm n1 gui", {"content": "first"}, "PASS"),
            ("not-confirmed", "no", {"content": "first"}, "FAIL"),
            ("changed", "confirm n1 gui", {"content": "changed"}, "FAIL"),
        ):
            with (
                self.subTest(case=case),
                tempfile.TemporaryDirectory(dir=check.ROOT / "ci-output") as temporary,
            ):
                output = Path(temporary) / "new-attempt"
                helper = types.SimpleNamespace(
                    ubuntu_system_schema_environment=lambda _: ({}, {"mode": "fixture"})
                )
                with (
                    patch.object(check, "OUTPUT", output),
                    patch.object(sys, "argv", ["check", "--owner-host"]),
                    patch.object(sys.stdin, "isatty", return_value=True),
                    patch.dict("os.environ", {"WAYLAND_DISPLAY": "synthetic"}),
                    patch.object(check, "preflight"),
                    patch.object(check, "support", return_value=helper),
                    patch.object(
                        check, "launch", return_value={"normal_exit": "PASS"}
                    ) as launch,
                    patch.object(
                        check, "state", side_effect=[{"content": "first"}, after]
                    ),
                    patch("builtins.input", side_effect=["", "", answer]),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    result = check.main()
                record = json.loads((output / "result.json").read_text())
                self.assertEqual(record["status"], expected)
                self.assertEqual(result, 0 if expected == "PASS" else 2)
                self.assertEqual(launch.call_count, 2)
                self.assertFalse((output / "active").exists())


if __name__ == "__main__":
    unittest.main()
