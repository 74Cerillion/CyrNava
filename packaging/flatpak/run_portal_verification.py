"""Host-side supervisor for the disposable P2 Flatpak portal verification.

No Flatpak overrides, production profiles, Qt imports or third-party dependencies.
The parent can record FAIL even when the native test child crashes before Python
finally/atexit handlers run. It never dismisses dialogs or kills an open window.
"""

import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from desktop.native.storage import APP_ID, open_private, private_directory

REVISION = "p2-portal-window-filter-3"
REQUIRED = (
    "test_owned_backend_stopped",
    "owned_backend_reaped",
    "keep_open_choice",
    "live_offline_title_verified",
    "native_download_save_request",
    "native_blob_export_while_backend_stopped",
    "explicit_recovery_close",
    "real_save_chooser_and_granted_json_readback",
)
stdout_broken = False


def safe_print(text):
    global stdout_broken
    if stdout_broken:
        return
    try:
        print(text, flush=True)
    except BrokenPipeError:
        stdout_broken = True
        # Preserve disk evidence when an accidental pipeline closes stdout.
        try:
            fd = os.open(os.devnull, os.O_WRONLY)
            try:
                os.dup2(fd, sys.stdout.fileno())
            finally:
                os.close(fd)
        except (OSError, ValueError, AttributeError):
            pass


def atomic_json(path, value):
    temporary = path.with_name("." + path.name + "." + uuid4().hex)
    fd = open_private(temporary)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_record(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError("Missing or unsafe verification record")
    with path.open() as stream:
        record = json.load(stream)
    if not isinstance(record, dict):
        raise TypeError("Invalid verification record")
    return record


class Interrupted(BaseException):
    pass


def supervise(command, source, directory, timeout=330):
    """Only command/source injection in unit tests; the CLI always runs Flatpak."""
    directory = private_directory(directory)
    evidence = directory / "supervisor-result.json"
    report = {
        "supervisor_revision": REVISION,
        "status": "FAIL",
        "complete": False,
        "reason": "supervisor did not complete",
        "checks": {},
        "driver_sha256": hashlib.sha256(source).hexdigest(),
    }
    atomic_json(evidence, report)  # Incomplete FAIL exists before launching Qt.
    safe_print("P2 portal verification: " + directory.name)
    safe_print("Evidence directory: " + str(directory))
    safe_print(
        "Wait for the native Save dialog. Choose Downloads/Documents and a new JSON filename; click Save within four minutes."
    )
    safe_print(
        "The test uses only a fresh synthetic profile. No Flatpak permission overrides are applied."
    )
    process = None
    logs = []
    started = time.monotonic()
    previous = {}
    feed_done = threading.Event()
    feed_result = {"complete": False}
    feeder = None

    def interrupted(number, _frame):
        report["interrupted_by"] = "SIGINT" if number == signal.SIGINT else "SIGTERM"
        raise Interrupted()

    try:
        for number in (signal.SIGINT, signal.SIGTERM):
            previous[number] = signal.signal(number, interrupted)
        for name in ("driver-stdout.log", "driver-stderr.log"):
            logs.append(os.fdopen(open_private(directory / name), "wb", buffering=0))
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=logs[0],
            stderr=logs[1],
            start_new_session=True,
            bufsize=0,
        )

        def feed_source():
            # Exactly one writer, no communicate() timeout/retry input semantics.
            # Unbuffered FileIO avoids buffered-stream locks during parent exit.
            try:
                remaining_source = memoryview(source)
                while remaining_source:
                    count = process.stdin.write(remaining_source)
                    if not count:
                        raise OSError("Child input delivery stopped")
                    remaining_source = remaining_source[count:]
                process.stdin.close()
                feed_result["complete"] = True
            except (OSError, ValueError, TypeError) as error:
                feed_result["exception_type"] = type(error).__name__
            finally:
                try:
                    process.stdin.close()
                except (OSError, ValueError):
                    feed_result["complete"] = False
                feed_done.set()

        feeder = threading.Thread(target=feed_source, daemon=True)
        feeder.start()
        terminal_failure = False
        last_stage = None
        while True:
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, timeout)
            try:
                process.wait(timeout=min(0.5, remaining))
                feed_done.wait(timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                try:
                    child = read_record(directory / "outage-phase-3.json")
                    if child.get("terminal_failure") is True:
                        terminal_failure = True
                        break
                    state = read_record(directory / "driver-checkpoint.json").get(
                        "stage"
                    )
                    if state != last_stage:
                        last_stage = state
                        safe_print(
                            "P2 stage: "
                            + (
                                state
                                if state
                                in {
                                    "startup",
                                    "load",
                                    "typing",
                                    "typed",
                                    "first-close-ready",
                                    "first-close",
                                    "keep-open-settling",
                                    "export",
                                    "download",
                                    "second-close",
                                    "finished",
                                    "failed",
                                }
                                else "[unknown]"
                            )
                        )
                except (OSError, ValueError, TypeError):
                    pass
        code = process.poll()
        if code is not None:
            report["child_exit_code"] = code
        if code is not None and code < 0:
            report["child_signal"] = -code
        elif code in (134, 139):
            report["possible_child_signal"] = code - 128
        try:
            child = read_record(directory / "outage-phase-3.json")
        except (OSError, ValueError, TypeError):
            child = None
        if child is not None:
            report["driver_revision"] = child.get("driver_revision")
            report["driver_status"] = child.get("status")
            report["checks"] = child.get("checks", {})
            report["driver_complete"] = child.get("complete")
            report["driver_record"] = "outage-phase-3.json"
            if child.get("error"):
                report["driver_error"] = child["error"]
        if terminal_failure:
            report["reason"] = (
                "verification driver stopped with FAIL; window left for owner inspection"
            )
        elif code != 0:
            report["reason"] = "verification child exited unsuccessfully"
        elif child is None:
            report["reason"] = "verification child exited without final evidence"
        elif child.get("complete") is not True:
            report["reason"] = (
                "verification child exited before final evidence completed"
            )
        elif not feed_result["complete"]:
            report["reason"] = "verification script input was not completely delivered"
        elif child.get("driver_revision") != REVISION:
            report["reason"] = "verification child revision mismatch"
        elif child.get("real_save_portal") is not True or child.get("phase") != 3:
            report["reason"] = "verification child used the wrong test mode"
        elif child.get("status") != "PASS" or child.get("error"):
            report["reason"] = "verification driver reported failure"
        elif not isinstance(report["checks"], dict) or any(
            report["checks"].get(key) != "PASS" for key in REQUIRED
        ):
            report["reason"] = "verification child omitted required acceptance checks"
        else:
            report["status"] = "PASS"
            report["reason"] = (
                "real Save portal, JSON readback and recovery close verified"
            )
    except subprocess.TimeoutExpired:
        report["reason"] = (
            "supervisor deadline exceeded; window left for owner inspection"
        )
    except Interrupted:
        report["reason"] = "supervisor interrupted; window left for owner inspection"
    except BaseException as error:  # noqa: BLE001 - persist final FAIL at this process boundary.
        report["reason"] = "supervisor launch or monitoring exception"
        report["exception_type"] = type(error).__name__  # Never exception args/locals.
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)
        if process is not None:
            report["child_still_running"] = process.poll() is None
        if feeder is not None and feed_done.is_set():
            feeder.join(timeout=0.1)
        report["stdin_complete"] = feed_result["complete"]
        if "exception_type" in feed_result:
            report["stdin_exception_type"] = feed_result["exception_type"]
        for stream in logs:
            stream.close()
        report["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
        report["complete"] = True
        try:
            checkpoint = read_record(directory / "driver-checkpoint.json")
            report["last_driver_stage"] = checkpoint.get("stage")
        except (OSError, ValueError, TypeError):
            pass
        atomic_json(evidence, report)
        safe_print(json.dumps(report, indent=2))
        safe_print("Evidence: " + str(evidence))
        safe_print("Diagnostics: " + str(directory / "driver-stderr.log"))
        if report.get("child_still_running"):
            safe_print(
                "Verification is FAIL. Inspect and close the synthetic window manually using its normal recovery choices."
            )
    return 0 if report["status"] == "PASS" else 1


def main():
    os.umask(0o077)
    directory = (
        Path.home()
        / ".var/app"
        / APP_ID
        / "data/p2-portal-verification"
        / ("run-" + uuid4().hex[:12])
    )
    command = [
        "flatpak",
        "run",
        "--branch=p2",
        "--command=python3",
        APP_ID,
        "-X",
        "faulthandler",
        "-u",
        "-",
        "3",
        "--portal",
        "--run-id",
        directory.name,
    ]
    try:
        private_directory(directory)
        atomic_json(
            directory / "supervisor-result.json",
            {
                "supervisor_revision": REVISION,
                "status": "FAIL",
                "complete": False,
                "reason": "Supervisor initialization did not complete",
                "checks": {},
            },
        )
        source = Path(__file__).with_name("verify_outage.py").read_bytes()
        return supervise(command, source, directory)
    except BaseException as error:  # noqa: BLE001 - persist final FAIL at this process boundary.
        report = {
            "supervisor_revision": REVISION,
            "status": "FAIL",
            "complete": True,
            "reason": "could not initialize or persist supervisor evidence",
            "exception_type": type(error).__name__,
            "checks": {},
        }
        safe_print(json.dumps(report, indent=2))
        try:
            atomic_json(directory / "supervisor-result.json", report)
            safe_print("Evidence: " + str(directory / "supervisor-result.json"))
        except (OSError, ValueError):
            # A read-only/full disk can prevent any on-disk guarantee.
            safe_print("No saved evidence is claimed: evidence storage is unavailable")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
