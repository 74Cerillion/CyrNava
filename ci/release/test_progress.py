"""P6 interruption/progress tests; synthetic processes, never launch Flatpak/Qt."""

import contextlib
import io
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import native_distribution
import progress
import real_update


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p6-progress-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.monitor = progress.Progress(self.root)
        self.process = Mock(
            pid=12345, returncode=0, stdin=None, stdout=None, stderr=None
        )
        self.process.poll.return_value = None

    def run_command(self, timeout=30):
        return self.monitor.command(
            "runtime-install",
            ["SENSITIVE/path", "TOKEN_SECRET"],
            env={"SECRET": "TOKEN_SECRET"},
            timeout=timeout,
        )

    def test_interruption_records_operation_and_terminates_child_group(self):
        self.process.communicate.side_effect = KeyboardInterrupt
        output = io.StringIO()
        with (
            patch.object(subprocess, "Popen", return_value=self.process) as popen,
            patch.object(os, "killpg") as kill,
            contextlib.redirect_stdout(output),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.run_command()
        kill.assert_called_once_with(12345, signal.SIGTERM)
        self.process.wait.assert_called_once_with(timeout=5)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertEqual(popen.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(self.monitor.failure["operation"], "runtime-install")
        self.assertEqual(self.monitor.failure["category"], "interrupted")
        self.assertNotIn("TOKEN_SECRET", output.getvalue())
        self.assertNotIn("SENSITIVE", (self.root / "operations.jsonl").read_text())
        self.assertEqual(
            core.read_json(self.root / "progress.json")["state"], "interrupted"
        )

    def test_running_heartbeats_do_not_extend_existing_deadline(self):
        clock = [0.0]

        def blocked(*, input, timeout):
            clock[0] += timeout
            raise subprocess.TimeoutExpired(["TOKEN_SECRET"], timeout)

        self.process.communicate.side_effect = blocked
        with (
            patch.object(progress.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(subprocess, "Popen", return_value=self.process),
            patch.object(os, "killpg"),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaises(subprocess.TimeoutExpired),
        ):
            self.run_command(timeout=15)
        self.assertEqual(clock[0], 15)
        self.assertEqual(self.monitor.failure["category"], "timeout")
        self.assertEqual(
            [c.kwargs["timeout"] for c in self.process.communicate.call_args_list],
            [10, 5],
        )
        self.assertTrue(any(e["state"] == "running" for e in self.monitor.events))

    def test_child_ignoring_TERM_is_KILLed_with_bounded_wait(self):
        self.process.wait.side_effect = [subprocess.TimeoutExpired([], 5), 0]
        with patch.object(os, "killpg") as kill:
            progress.Progress.stop(self.process)
        self.assertEqual(
            [c.args for c in kill.call_args_list],
            [(12345, signal.SIGTERM), (12345, signal.SIGKILL)],
        )
        self.assertEqual(
            [c.kwargs["timeout"] for c in self.process.wait.call_args_list], [5, 5]
        )

    def test_successful_child_records_completion_without_raw_output(self):
        self.process.communicate.return_value = (b"TOKEN_SECRET", b"SENSITIVE")
        with (
            patch.object(subprocess, "Popen", return_value=self.process),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = self.run_command()
        self.assertEqual(result.stdout, b"TOKEN_SECRET")
        self.assertEqual(self.monitor.events[-1]["state"], "completed")
        self.assertNotIn("TOKEN_SECRET", (self.root / "operations.jsonl").read_text())

    def test_nonzero_child_exit_is_not_recorded_as_completed(self):
        self.process.returncode = 7
        self.process.communicate.return_value = (b"TOKEN_SECRET", b"SENSITIVE")
        with (
            patch.object(subprocess, "Popen", return_value=self.process),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            self.run_command()
        self.assertEqual(self.monitor.failure["category"], "exit-7")
        self.assertNotIn("SENSITIVE", str(self.monitor.events))

    def test_unknown_operation_is_rejected_before_output_or_spawn(self):
        with (
            patch.object(subprocess, "Popen") as popen,
            self.assertRaises(core.Rejected),
        ):
            self.monitor.command("SECRET/path", [], env={}, timeout=1)
        popen.assert_not_called()
        self.assertEqual(self.monitor.events, [])

    def test_heartbeat_does_not_resend_GUI_script_input(self):
        self.process.communicate.side_effect = [
            subprocess.TimeoutExpired([], 10),
            (b"", b""),
        ]
        with (
            patch.object(subprocess, "Popen", return_value=self.process),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.monitor.command(
                "gui-edit",
                ["synthetic"],
                env={},
                timeout=900,
                input=b"synthetic script",
            )
        self.assertEqual(
            [c.kwargs["input"] for c in self.process.communicate.call_args_list],
            [b"synthetic script", None],
        )


class PrelaunchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p6-prelaunch-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pair = self.root / "prepared-pair"
        self.pair.mkdir()
        (self.pair / ".p6-real-update").write_bytes(
            core.encode({"purpose": "disposable P6 real update"})
        )
        (self.pair / "prepared.json").write_bytes(
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
        (self.pair / "owner-result.json").write_text(
            '{"status":"FAIL","historical":true}'
        )
        self.before = {p.name: p.read_bytes() for p in self.pair.iterdir()}
        self.attempt = self.root / "fresh-attempt"

    def fake_client(self, failure):
        class SyntheticClient:
            def __init__(self, root, progress):
                self.root, self.env, self.progress = root, {}, progress

            def runtimes(self):
                with self.progress.operation("runtime-install", timeout=1800):
                    raise failure

        return SyntheticClient

    def test_SIGINT_prelaunch_has_final_record_and_preserves_preparation(self):
        with (
            patch.object(
                native_distribution,
                "RuntimeClient",
                self.fake_client(KeyboardInterrupt()),
            ),
            patch.object(real_update, "desktop_environment", return_value={}),
            patch.object(real_update.distribution, "loopback") as server,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = real_update.exercise(self.pair, self.attempt)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["complete"])
        self.assertTrue(result["interrupted"])
        self.assertEqual(result["failure_category"], "interrupted")
        self.assertEqual(result["checks"], {})
        self.assertFalse(result["generation_A_launch_attempted"])
        self.assertEqual(result["failed_operation"]["operation"], "runtime-install")
        self.assertEqual(core.read_json(self.attempt / "owner-result.json"), result)
        self.assertEqual(
            {p.name: p.read_bytes() for p in self.pair.iterdir()}, self.before
        )
        server.assert_not_called()

    def test_prelaunch_timeout_is_distinct_from_owner_interruption(self):
        with (
            patch.object(
                native_distribution,
                "RuntimeClient",
                self.fake_client(subprocess.TimeoutExpired([], 1800)),
            ),
            patch.object(real_update, "desktop_environment", return_value={}),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = real_update.exercise(self.pair, self.attempt)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failed_operation"]["category"], "timeout")
        self.assertNotIn("interrupted", result)
        self.assertFalse(result["generation_A_launch_attempted"])

    def test_attempt_root_cannot_reuse_old_failed_client_or_results(self):
        self.attempt.mkdir()
        sentinel = self.attempt / "preserve"
        sentinel.write_text("synthetic evidence")
        with (
            patch.object(native_distribution, "RuntimeClient") as client,
            self.assertRaises(FileExistsError),
        ):
            real_update.exercise(self.pair, self.attempt)
        client.assert_not_called()
        self.assertEqual(sentinel.read_text(), "synthetic evidence")

    def test_P6_runtime_metadata_deadline_is_bounded_without_reducing_download_budget(
        self,
    ):
        client = native_distribution.RuntimeClient(
            self.root / "client", progress=Mock()
        )
        client.progress.command.return_value = subprocess.CompletedProcess(
            [], 0, b"", b""
        )
        client.command(
            "runtime-remote", "remote-add", "--from", "synthetic", timeout=300
        )
        self.assertEqual(client.progress.command.call_args.kwargs["timeout"], 300)
        client.command("runtime-install", "install", "--noninteractive", "synthetic")
        self.assertEqual(client.progress.command.call_args.kwargs["timeout"], 1800)

    def test_native_signature_failure_keeps_accepted_security_classification(self):
        client = native_distribution.RuntimeClient(
            self.root / "client", progress=Mock()
        )
        client.progress.command.side_effect = subprocess.CalledProcessError(
            1, [], output=b"", stderr=b"GPG signature rejected"
        )
        with self.assertRaisesRegex(core.Rejected, "signature"):
            client.command(
                "runtime-install", "install", "--noninteractive", "synthetic"
            )


if __name__ == "__main__":
    unittest.main()
