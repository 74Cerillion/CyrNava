"""Disposable simulated transactions only; never launch Flatpak or import PySide."""

import contextlib
import importlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, mock_open, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import historical_runtime as history
import native_distribution
import progress
import real_update


class HistoricalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.native = native_distribution.RuntimeClient(self.root / "client")
        self.replay = history.Replay(self.native, self.root, history.COMMIT)
        self.drift = "f" * 64

    def test_explicit_exact_opt_in_required(self):
        self.assertFalse(history.authorize(None))
        self.assertTrue(history.authorize(history.COMMIT))
        for value in (True, "latest", self.drift):
            with self.subTest(value=value), self.assertRaises(core.Rejected):
                history.authorize(value)

    def test_changed_lock_refused(self):
        with (
            patch.object(
                core,
                "read_json",
                return_value={"refs": {"org.kde.Platform//6.11": self.drift}},
            ),
            self.assertRaises(core.Rejected),
        ):
            history.authorize(history.COMMIT)

    def test_each_transaction_records_drift_separately_from_restoration(self):
        for name in sorted(history.TRANSACTIONS):
            with (
                self.subTest(name=name),
                patch.object(
                    self.replay,
                    "snapshot",
                    side_effect=[history.COMMIT, self.drift, history.COMMIT],
                ),
                patch.object(
                    self.replay, "trusted", return_value={"commit_signature": "PASS"}
                ),
                patch.object(self.native, "command") as restore,
            ):
                with self.replay.transaction(name):
                    pass
                event = self.replay.events[-1]
                self.assertEqual(event["before"], history.COMMIT)
                self.assertEqual(event["after"], self.drift)
                self.assertFalse(event["ordinary_runtime_compatible"])
                self.assertEqual(event["restoration"], "PASS")
                self.assertIn("--commit=" + history.COMMIT, restore.call_args.args)
                self.assertEqual(restore.call_args.kwargs["timeout"], 300)
        self.assertEqual(
            len(
                core.read_json(self.root / "runtime-transactions.json")["transactions"]
            ),
            6,
        )

    def test_default_drift_fails_without_restoring(self):
        strict = history.Replay(self.native, self.root)
        with (
            patch.object(strict, "snapshot", side_effect=[history.COMMIT, self.drift]),
            patch.object(self.native, "command") as command,
            self.assertRaises(native_distribution.RuntimeIdentityFailure),
        ):
            with strict.transaction("install-a"):
                pass
        command.assert_not_called()

    def test_wrong_origin_cannot_restore(self):
        with (
            patch.object(self.native, "run", return_value="untrusted"),
            self.assertRaisesRegex(core.Rejected, "origin"),
        ):
            self.replay.trusted()

    def test_disabled_signatures_rejected(self):
        repo = self.native.root / "flatpak/repo"
        repo.mkdir()
        (repo / "config").write_text(
            '[remote "flathub"]\nurl=https://dl.flathub.org/repo/\ngpg-verify=false\ngpg-verify-summary=true\n'
        )
        with (
            patch.object(self.native, "run", return_value="flathub"),
            self.assertRaisesRegex(core.Rejected, "signature"),
        ):
            self.replay.trusted()

    def test_signature_failure_is_sanitized(self):
        repo = self.native.root / "flatpak/repo"
        repo.mkdir()
        (repo / "config").write_text(
            '[remote "flathub"]\nurl=https://dl.flathub.org/repo/\ngpg-verify=true\ngpg-verify-summary=true\n'
        )
        with (
            patch.object(self.native, "run", return_value="flathub"),
            patch.object(
                subprocess,
                "run",
                side_effect=subprocess.CalledProcessError(1, ["SECRET"]),
            ),
            self.assertRaisesRegex(core.Rejected, "signature") as caught,
        ):
            self.replay.trusted()
        self.assertNotIn("SECRET", str(caught.exception))

    def test_missing_historical_object_fails_and_preserves_journal(self):
        with (
            patch.object(
                self.replay, "snapshot", side_effect=[history.COMMIT, self.drift]
            ),
            patch.object(
                self.replay,
                "trusted",
                side_effect=core.Rejected("Missing verified commit"),
            ),
            patch.object(self.native, "command") as command,
            self.assertRaises(core.Rejected),
        ):
            with self.replay.transaction("install-a"):
                pass
        command.assert_not_called()
        self.assertEqual(self.replay.events[-1]["validation"], "FAIL")

    def test_failed_restore_does_not_fall_back_to_latest(self):
        with (
            patch.object(
                self.replay,
                "snapshot",
                side_effect=[history.COMMIT, self.drift, self.drift],
            ),
            patch.object(self.replay, "trusted"),
            patch.object(
                self.native, "command", side_effect=core.Rejected("restore failed")
            ) as command,
            self.assertRaises(core.Rejected),
        ):
            with self.replay.transaction("update-b"):
                pass
        self.assertEqual(command.call_count, 1)
        self.assertEqual(self.replay.events[-1]["restored_commit"], self.drift)
        self.assertEqual(self.replay.events[-1]["restoration"], "FAIL")
        self.assertEqual(self.replay.events[-1]["validation"], "FAIL")

    def test_wrong_restored_commit_rejected(self):
        with (
            patch.object(
                self.replay,
                "snapshot",
                side_effect=[history.COMMIT, self.drift, "e" * 64],
            ),
            patch.object(self.replay, "trusted"),
            patch.object(self.native, "command"),
            self.assertRaisesRegex(core.Rejected, "mismatch"),
        ):
            with self.replay.transaction("rollback-a"):
                pass

    def test_interrupted_transaction_records_readback_without_mutation(self):
        with (
            patch.object(
                self.replay, "snapshot", side_effect=[history.COMMIT, self.drift]
            ),
            patch.object(self.native, "command") as command,
            self.assertRaises(KeyboardInterrupt),
        ):
            with self.replay.transaction("reinstall-b"):
                raise KeyboardInterrupt
        command.assert_not_called()
        event = self.replay.events[-1]
        self.assertEqual(event["after"], self.drift)
        self.assertEqual(event["restoration"], "NOT_ATTEMPTED")

    def test_import_script_is_import_only_covers_used_modules(self):
        compile(history.IMPORT_SCRIPT, "<import-check>", "exec")
        self.assertNotIn(b"QApplication(", history.IMPORT_SCRIPT)
        self.assertNotIn(b"desktop.native", history.IMPORT_SCRIPT)
        for name in history.MODULES:
            self.assertIn(name.encode(), history.IMPORT_SCRIPT)

    def test_failed_import_is_bounded_private_and_stops(self):
        monitor = Mock()
        monitor.command.side_effect = subprocess.CalledProcessError(
            1, [], b"", b"SECRET private error"
        )
        with (
            patch.object(self.native, "verify_runtime"),
            self.assertRaisesRegex(core.Rejected, "import check failed") as caught,
        ):
            history.probe(self.native, monitor, self.root, "A")
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertEqual(monitor.command.call_args.kwargs["timeout"], 60)
        diagnostic = core.read_json(self.root / "imports-a-failure.json")
        private = (
            self.root
            / "private-subprocess"
            / diagnostic["private_files"]["stderr"]["file"]
        )
        self.assertEqual(private.read_bytes(), b"SECRET private error")
        self.assertEqual(private.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("SECRET", json.dumps(diagnostic))

    def test_matching_versions_alone_do_not_pass(self):
        monitor = Mock()
        monitor.command.return_value = subprocess.CompletedProcess(
            [], 0, b'P6_IMPORT {"status":"PASS", "versions":{"qt":"6.11.2"}}\n', b""
        )
        with (
            patch.object(self.native, "verify_runtime"),
            self.assertRaises(core.Rejected),
        ):
            history.probe(self.native, monitor, self.root, "B")

    def test_import_success_requires_real_hashes_and_providers(self):
        value = {
            "status": "PASS",
            "modules": dict.fromkeys(history.MODULES, "a" * 64),
            "providers": dict.fromkeys(
                (
                    "runtime/libQt6Core.so.6.11.2",
                    "runtime/libQt6Gui.so.6.11.2",
                    "runtime/libQt6Widgets.so.6.11.2",
                    "app/libQt6WebEngineCore.so.6.11.1",
                ),
                "b" * 64,
            ),
            "versions": dict(pyside="6.11.2", shiboken="6.11.2", qt="6.11.2"),
        }
        monitor = Mock()
        monitor.command.return_value = subprocess.CompletedProcess(
            [], 0, b"P6_IMPORT " + json.dumps(value).encode() + b"\n", b""
        )
        with patch.object(
            self.native, "verify_runtime", return_value={"commit": history.COMMIT}
        ):
            result = history.probe(self.native, monitor, self.root, "A")
        self.assertEqual(result["status"], "PASS")
        self.assertIn("no GUI", result["scope"])

    def test_existing_attempt_and_prepared_inputs_preserved(self):
        pair = self.root / "pair"
        pair.mkdir()
        (pair / ".p6-real-update").write_bytes(
            core.encode({"purpose": "disposable P6 real update"})
        )
        (pair / "prepared.json").write_bytes(
            core.encode({"status": "PASS", "complete": True})
        )
        before = core.tree_manifest(pair)
        attempt = self.root / "old-attempt"
        attempt.mkdir()
        (attempt / "owner-result.json").write_text("retained failure")
        with self.assertRaises(FileExistsError):
            real_update.exercise(pair, attempt, history.COMMIT, True)
        self.assertEqual(before, core.tree_manifest(pair))
        self.assertEqual(
            (attempt / "owner-result.json").read_text(), "retained failure"
        )

    def test_application_transactions_keep_dependency_resolution(self):
        n = Mock()
        n.commit.return_value = "a" * 64
        history.application_update(n, "a" * 64, "b" * 40)
        args = n.run.call_args.args
        self.assertNotIn("--no-deps", args)
        self.assertIn("--commit=" + "a" * 64, args)
        n.verify_remote.assert_called_once_with(core.APP_ID)
        n.installed_source.assert_called_once_with("b" * 40)

    def test_wrong_application_commit_blocks_progress(self):
        n = Mock()
        n.commit.return_value = "c" * 64
        with self.assertRaises(core.Rejected):
            history.application_update(n, "a" * 64, "b" * 40)
        n.installed_source.assert_not_called()

    def exercise_gate(self, *, fail_b=False, imports_only=True):
        pair = self.root / "pair"
        pair.mkdir()
        (pair / ".p6-real-update").write_bytes(
            core.encode({"purpose": "disposable P6 real update"})
        )
        (pair / "prepared.json").write_bytes(
            core.encode(
                {
                    "status": "PASS",
                    "complete": True,
                    "fingerprint": "A" * 40,
                    "A": {"source_commit": "a" * 40, "ostree_commit": "a" * 64},
                    "B": {"source_commit": "b" * 40, "ostree_commit": "b" * 64},
                }
            )
        )
        preserved = core.tree_manifest(pair)
        calls = []
        n = Mock(root=self.native.root, env={})
        n.verify_runtime.return_value = {"status": "PASS"}
        n.runtimes.return_value = {"status": "PASS"}
        n.install_real.return_value = {"status": "DEFERRED_TO_REPLAY_TRANSACTION"}

        def probe(native, monitor, attempt, label):
            calls.append(label)
            if fail_b and label == "B":
                raise core.Rejected("synthetic B import failure")
            return {"status": "PASS"}

        def launch(*args, **kwargs):
            self.assertEqual(calls, ["A", "B"])
            raise core.Rejected("synthetic GUI stop")

        attempt = self.root / "new-attempt"
        with (
            patch.object(native_distribution, "RuntimeClient", return_value=n),
            patch.object(real_update, "desktop_environment", return_value={}),
            patch.object(history.Replay, "snapshot", return_value=history.COMMIT),
            patch.object(
                history.Replay, "trusted", return_value={"commit_signature": "PASS"}
            ),
            patch.object(history, "application_update"),
            patch.object(history, "probe", side_effect=probe),
            patch.object(real_update.distribution, "plan", return_value={}),
            patch.object(real_update.distribution, "publish"),
            patch.object(
                real_update.distribution,
                "loopback",
                return_value=contextlib.nullcontext("http://127.0.0.1/"),
            ),
            patch.object(
                real_update.native_diagnostics, "run", side_effect=launch
            ) as gui,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = real_update.exercise(pair, attempt, history.COMMIT, imports_only)
        self.assertEqual(preserved, core.tree_manifest(pair))
        self.assertTrue(core.read_json(attempt / "owner-result.json")["complete"])
        return result, gui, calls

    def test_import_only_completion_never_launches_GUI(self):
        result, gui, calls = self.exercise_gate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(calls, ["A", "B"])
        self.assertFalse(result["generation_A_launch_attempted"])
        gui.assert_not_called()

    def test_failed_B_import_stops_before_any_GUI(self):
        result, gui, calls = self.exercise_gate(fail_b=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertNotIn("both_generation_import_gate", result["checks"])
        gui.assert_not_called()

    def test_GUI_is_gated_on_both_imports_in_same_fresh_client(self):
        result, gui, calls = self.exercise_gate(imports_only=False)
        self.assertEqual(result["checks"]["both_generation_import_gate"], "PASS")
        self.assertTrue(result["generation_A_launch_attempted"])
        gui.assert_called_once()

    def test_actual_import_script_parses_maps_with_synthetic_modules_only(self):
        # Exercise the real script without loading any Qt/native library.
        package = SimpleNamespace(__version__="6.11.2")
        module = SimpleNamespace(__file__="/app/synthetic/module.so")
        qtcore = SimpleNamespace(qVersion=lambda: "6.11.2")
        maps = "\n".join(
            "0-1 r-xp 0 0:0 0 " + p
            for p in (
                "/usr/lib/x86_64-linux-gnu/libQt6Core.so.6.11.2",
                "/usr/lib/x86_64-linux-gnu/libQt6Gui.so.6.11.2",
                "/usr/lib/x86_64-linux-gnu/libQt6Widgets.so.6.11.2",
                "/app/lib/libQt6WebEngineCore.so.6.11.1",
            )
        )
        output = io.StringIO()
        with (
            patch.dict(
                sys.modules,
                {"PySide6": package, "shiboken6": package, "PySide6.QtCore": qtcore},
            ),
            patch.object(importlib, "import_module", return_value=module),
            patch.object(Path, "read_text", return_value=maps),
            patch.object(Path, "open", mock_open(read_data=b"synthetic-ELF")),
            contextlib.redirect_stdout(output),
        ):
            exec(compile(history.IMPORT_SCRIPT, "<synthetic-import-check>", "exec"), {})
        value = json.loads(output.getvalue().removeprefix("P6_IMPORT "))
        self.assertEqual(len(value["providers"]), 4)
        monitor = progress.Progress(self.root)
        result = subprocess.CompletedProcess([], 0, output.getvalue().encode(), b"")
        with (
            patch.object(
                progress.Progress, "command", autospec=True, return_value=result
            ) as command,
            patch.object(
                self.native, "verify_runtime", return_value={"commit": history.COMMIT}
            ),
        ):
            self.assertEqual(
                history.probe(self.native, monitor, self.root, "B")["status"], "PASS"
            )
        self.assertEqual(command.call_args.kwargs["input"], history.IMPORT_SCRIPT)

    def test_initial_runtime_install_and_restore_are_also_journaled(self):
        with (
            patch.object(self.native, "command"),
            patch.object(self.native, "run", side_effect=[self.drift, history.COMMIT]),
        ):
            retrieved = self.native.setup_transaction(
                "runtime-install",
                "ABSENT_EMPTY_CLIENT",
                "install",
                "--noninteractive",
                history.REF,
            )
            self.native.setup_transaction(
                "runtime-pin",
                retrieved,
                "update",
                "--commit=" + history.COMMIT,
                history.REF,
            )
        values = core.read_json(self.native.root / "runtime-setup.json")
        self.assertEqual(values[0]["before"], "ABSENT_EMPTY_CLIENT")
        self.assertEqual(values[0]["after"], self.drift)
        self.assertEqual(values[1]["before"], self.drift)
        self.assertEqual(values[1]["after"], history.COMMIT)

    def test_interrupted_initial_install_preserves_actual_readback(self):
        with (
            patch.object(self.native, "command", side_effect=KeyboardInterrupt),
            patch.object(self.native, "run", return_value=self.drift),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.native.setup_transaction(
                "runtime-install", "ABSENT_EMPTY_CLIENT", "install", history.REF
            )
        event = core.read_json(self.native.root / "runtime-setup.json")[0]
        self.assertEqual(event["status"], "FAIL")
        self.assertEqual(event["after"], self.drift)


if __name__ == "__main__":
    unittest.main()
