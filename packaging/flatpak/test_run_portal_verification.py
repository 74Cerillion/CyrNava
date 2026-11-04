"""Real subprocess crash/exit evidence regressions; no Qt or Flatpak is launched."""

import importlib.util
import json
import signal
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

spec = importlib.util.spec_from_file_location(
    "portal_supervisor", Path(__file__).with_name("run_portal_verification.py")
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def command(code, directory):
    return [sys.executable, "-c", code, str(directory)]


def result(directory):
    return json.loads((directory / "supervisor-result.json").read_text())


def child_record(**changes):
    return {
        "driver_revision": runner.REVISION,
        "status": "PASS",
        "complete": True,
        "real_save_portal": True,
        "phase": 3,
        "checks": {key: "PASS" for key in runner.REQUIRED},
        **changes,
    }


def writer(record, exit_code=0):
    return (
        "import json,sys; from pathlib import Path; "
        'p=Path(sys.argv[1])/"outage-phase-3.json"; '
        f"p.write_text({json.dumps(json.dumps(record))}); "
        f"raise SystemExit({exit_code})"
    )


@pytest.mark.parametrize(
    "code", ["raise SystemExit(0)", "import os; os._exit(0)", "raise SystemExit(7)"]
)
def test_premature_child_exit_always_produces_final_failure(tmp_path, code):
    directory = tmp_path / "run"
    crash = [sys.executable, "-X", "faulthandler", "-c", code, str(directory)]
    assert runner.supervise(crash, b"", directory, timeout=5) == 1
    record = result(directory)
    assert record["status"] == "FAIL" and record["complete"] is True
    assert record["child_still_running"] is False
    assert (directory / "driver-stdout.log").exists()
    assert (directory / "driver-stderr.log").exists()


def test_real_native_signal_crash_is_captured_by_parent(tmp_path):
    directory = tmp_path / "run"
    code = "import os,resource,signal; resource.setrlimit(resource.RLIMIT_CORE,(0,0)); os.kill(os.getpid(),signal.SIGSEGV)"
    crash = [sys.executable, "-X", "faulthandler", "-c", code, str(directory)]
    assert runner.supervise(crash, b"", directory, timeout=5) == 1
    record = result(directory)
    assert record["child_exit_code"] == -signal.SIGSEGV
    assert record["child_signal"] == signal.SIGSEGV
    assert record["status"] == "FAIL" and record["complete"] is True
    assert "Fatal Python error" in (directory / "driver-stderr.log").read_text()


@pytest.mark.parametrize(
    "changes",
    [
        {"complete": False},
        {"driver_revision": "old"},
        {"status": "FAIL"},
        {"checks": {}},
        {"phase": 4},
        {"real_save_portal": False},
        {"error": "synthetic error"},
    ],
)
def test_no_success_from_incomplete_or_wrong_child_record(tmp_path, changes):
    directory = tmp_path / "run"
    assert (
        runner.supervise(
            command(writer(child_record(**changes)), directory),
            b"",
            directory,
            timeout=5,
        )
        == 1
    )
    assert result(directory)["status"] == "FAIL"


def test_success_requires_complete_record_every_boundary_and_zero_exit(tmp_path):
    directory = tmp_path / "run"
    assert (
        runner.supervise(
            command(writer(child_record()), directory), b"", directory, timeout=5
        )
        == 0
    )
    record = result(directory)
    assert record["status"] == "PASS" and record["complete"] is True
    assert record["checks"]["real_save_chooser_and_granted_json_readback"] == "PASS"
    assert record["child_exit_code"] == 0 and not record["child_still_running"]


def test_pass_record_cannot_hide_nonzero_or_signal_style_exit(tmp_path):
    directory = tmp_path / "run"
    assert (
        runner.supervise(
            command(writer(child_record(), 139), directory), b"", directory, timeout=5
        )
        == 1
    )
    record = result(directory)
    assert record["status"] == "FAIL" and record["possible_child_signal"] == 11


def test_malformed_child_json_cannot_remove_final_evidence(tmp_path):
    directory = tmp_path / "run"
    code = 'import sys; from pathlib import Path; (Path(sys.argv[1])/"outage-phase-3.json").write_text("{")'
    assert runner.supervise(command(code, directory), b"", directory, timeout=5) == 1
    assert result(directory)["complete"] is True


def test_launch_exception_is_safe_and_persisted(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        Mock(side_effect=OSError("sensitive exception arguments")),
    )
    directory = tmp_path / "run"
    assert runner.supervise(["missing-command"], b"", directory) == 1
    record = result(directory)
    assert record["exception_type"] == "OSError"
    assert "sensitive" not in json.dumps(record)
    assert record["complete"] is True


def test_watchdog_leaves_window_untouched_and_reports_failure(tmp_path, monkeypatch):
    process = Mock()
    process.wait.side_effect = subprocess.TimeoutExpired(["synthetic-child"], 0.1)
    process.poll.return_value = None
    monkeypatch.setattr(runner.subprocess, "Popen", Mock(return_value=process))
    directory = tmp_path / "run"
    assert runner.supervise(["synthetic-child"], b"x", directory, timeout=0.1) == 1
    record = result(directory)
    assert record["complete"] and record["child_still_running"]
    assert "deadline" in record["reason"]
    process.terminate.assert_not_called()
    process.kill.assert_not_called()


def test_signal_interruption_preserves_dialog_and_restores_handlers(
    tmp_path, monkeypatch
):
    registered = {}
    previous = object()

    def register(number, handler):
        old = registered.get(number, previous)
        registered[number] = handler
        return old

    monkeypatch.setattr(runner.signal, "signal", register)
    process = Mock()
    process.poll.return_value = None
    process.wait.side_effect = lambda **_: registered[signal.SIGTERM](
        signal.SIGTERM, None
    )
    monkeypatch.setattr(runner.subprocess, "Popen", Mock(return_value=process))
    directory = tmp_path / "run"
    assert runner.supervise(["synthetic-child"], b"", directory) == 1
    record = result(directory)
    assert record["interrupted_by"] == "SIGTERM" and record["status"] == "FAIL"
    assert all(handler is previous for handler in registered.values())
    process.terminate.assert_not_called()
    process.kill.assert_not_called()


def test_closed_stdout_does_not_prevent_supervisor_final_evidence(tmp_path):
    directory = tmp_path / "run"
    module_path = str(Path(runner.__file__).resolve())
    code = (
        "import importlib.util,sys; from pathlib import Path; "
        f's=importlib.util.spec_from_file_location("supervisor",{module_path!r}); '
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "p=Path(sys.argv[1]); "
        'raise SystemExit(m.supervise([sys.executable,"-c","raise SystemExit(0)"],b"",p,timeout=5))'
    )
    process = subprocess.Popen(
        command(code, directory), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    process.stdout.close()  # Reproduce the closed reader from `| echo $?`.
    assert process.wait(timeout=8) == 1
    assert (
        result(directory)["complete"] is True and result(directory)["status"] == "FAIL"
    )
    assert b"BrokenPipeError" not in process.stderr.read()


def test_stdin_delivery_is_inside_watchdog_not_unbounded_write(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    children = []

    def start(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        children.append(process)
        return process

    monkeypatch.setattr(runner.subprocess, "Popen", start)
    directory = tmp_path / "run"
    try:
        assert (
            runner.supervise(
                command("import time; time.sleep(10)", directory),
                b"x" * 1_000_000,
                directory,
                timeout=0.05,
            )
            == 1
        )
        assert result(directory)["child_still_running"] is True
        assert "deadline" in result(directory)["reason"]
    finally:
        # Only the retained non-GUI synthetic fixture child; never a real app.
        for process in children:
            process.terminate()
            process.wait(timeout=5)


def test_initial_fail_record_exists_before_starting_child(tmp_path, monkeypatch):
    directory = tmp_path / "run"

    def start(*_args, **_kwargs):
        initial = result(directory)
        assert initial["status"] == "FAIL" and initial["complete"] is False
        raise OSError("synthetic start failure")

    monkeypatch.setattr(runner.subprocess, "Popen", start)
    assert runner.supervise(["synthetic-child"], b"", directory) == 1
    assert result(directory)["complete"] is True
    assert (directory / "supervisor-result.json").stat().st_mode & 0o777 == 0o600


def test_terminal_driver_failure_is_reported_without_closing_its_dialog(
    tmp_path, monkeypatch
):
    real_popen = subprocess.Popen
    children = []

    def start(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        children.append(process)
        return process

    monkeypatch.setattr(runner.subprocess, "Popen", start)
    directory = tmp_path / "run"
    record = child_record(status="FAIL", complete=False, terminal_failure=True)
    code = writer(record).split("raise SystemExit")[0] + "import time; time.sleep(10)"
    try:
        assert (
            runner.supervise(command(code, directory), b"", directory, timeout=3) == 1
        )
        observed = result(directory)
        assert observed["child_still_running"] is True
        assert observed["driver_complete"] is False
        assert "driver stopped with FAIL" in observed["reason"]
        assert children[0].poll() is None  # Supervisor did not dismiss/terminate it.
    finally:
        for process in children:
            process.terminate()  # Only retained non-GUI fixture, not a real window.
            process.wait(timeout=5)


def test_missing_source_is_a_final_failure_not_a_bare_traceback(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        runner.Path,
        "read_bytes",
        Mock(side_effect=FileNotFoundError("synthetic source missing")),
    )
    assert runner.main() == 1
    records = list(
        tmp_path.glob(
            ".var/app/*/data/p2-portal-verification/run-*/supervisor-result.json"
        )
    )
    assert len(records) == 1
    record = json.loads(records[0].read_text())
    assert record["complete"] is True and record["status"] == "FAIL"
    assert record["exception_type"] == "FileNotFoundError"


def test_partial_stdin_resumes_after_monitor_poll_without_duplicate_source(
    tmp_path, monkeypatch
):
    real_popen = subprocess.Popen
    children = []

    def start(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        children.append(process)
        return process

    monkeypatch.setattr(runner.subprocess, "Popen", start)
    directory = tmp_path / "run"
    code = (
        "import sys,time; time.sleep(0.65); payload=sys.stdin.buffer.read(); "
        'assert payload == b"x" * 200_000; ' + writer(child_record())
    )
    try:
        assert (
            runner.supervise(
                command(code, directory), b"x" * 200_000, directory, timeout=4
            )
            == 0
        )
        assert result(directory)["status"] == "PASS"
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()  # Retained non-GUI fixture only.
            process.wait(timeout=5)
