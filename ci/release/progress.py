"""P6 safe operation progress and bounded, cancellable child execution."""

import contextlib
import json
import os
import signal
import subprocess
import time

import core

OPERATIONS = {
    "runtime-retrieval",
    "runtime-remote",
    "runtime-install",
    "runtime-pin",
    "launch",
    "runtime-signature",
    "imports-a",
    "imports-b",
    "activate-a",
    "activate-b",
    "http-start",
    "install-a",
    "install-b",
    "reinstall-b",
    "uninstall-b",
    "source-validation",
    "workspace-copy",
    "workspace-validation",
    "artifact-validation",
    "signed-B-validation",
    "update-b",
    "rollback-a",
    "uninstall-reinstall",
    "gui-edit",
    "gui-restart",
    "gui-updated",
    "gui-rollback",
    "gui-maintenance",
    "gui-recovery",
    *(
        "flatpak-" + x
        for x in ("install", "update", "commit", "location", "remote", "list")
    ),
}


class Progress:
    def __init__(self, root):
        self.root = root
        self.started = time.monotonic()
        self.events = []
        self.failure = None

    def emit(self, operation, state, started, **fields):
        core.require(operation in OPERATIONS, "Unreviewed progress operation")
        event = {
            "sequence": len(self.events) + 1,
            "operation": operation,
            "state": state,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            **fields,
        }
        self.events.append(event)
        (self.root / "progress.json.tmp").write_bytes(core.encode(event))
        os.replace(self.root / "progress.json.tmp", self.root / "progress.json")
        with (self.root / "operations.jsonl").open("a") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
        print("P6 " + json.dumps(event, sort_keys=True), flush=True)
        return event

    @contextlib.contextmanager
    def operation(self, operation, *, timeout=None):
        core.require(operation in OPERATIONS, "Unreviewed progress operation")
        start = time.monotonic()
        self.emit(operation, "started", start, timeout_seconds=timeout)
        try:
            yield start
        except (Exception, KeyboardInterrupt) as error:
            state = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
            category = (
                "interrupted"
                if isinstance(error, KeyboardInterrupt)
                else "timeout"
                if isinstance(error, subprocess.TimeoutExpired)
                else f"exit-{int(error.returncode)}"
                if isinstance(error, subprocess.CalledProcessError)
                else "operation-failed"
            )
            event = self.emit(operation, state, start, category=category)
            if self.failure is None:
                self.failure = event
            raise
        else:
            self.emit(operation, "completed", start)

    @staticmethod
    def stop(process):
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)

    def command(self, operation, command, *, env, timeout, input=None):
        with self.operation(operation, timeout=timeout) as start:
            process = subprocess.Popen(
                command,
                env=env,
                start_new_session=True,
                stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                first = True
                while True:
                    remaining = timeout - (time.monotonic() - start)
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired([], timeout)
                    try:
                        stdout, stderr = process.communicate(
                            input=input if first else None, timeout=min(10, remaining)
                        )
                        if process.returncode:
                            raise subprocess.CalledProcessError(
                                process.returncode, [], output=stdout, stderr=stderr
                            )
                        return subprocess.CompletedProcess(
                            [], process.returncode, stdout, stderr
                        )
                    except subprocess.TimeoutExpired:
                        first = False
                        self.emit(operation, "running", start, timeout_seconds=timeout)
            except (Exception, KeyboardInterrupt):
                self.stop(process)
                raise
            finally:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()
