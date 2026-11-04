"""Test-only native outage/recovery drill. Run phase 3, then phase 4.

The default save destination is stubbed inside this synthetic profile. With
``3 --portal``, use a separate profile and the real production save chooser; the
owner selects a destination and the driver checks that exact granted JSON file.
"""

import argparse
import json
import os
import re
import signal
import sys
import time
import urllib.request
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, "/app/share/cyrnava")
from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from desktop.native import application
from desktop.native.backend import Backend
from desktop.native.storage import open_private, private_directory

PORTAL = False
PHASE = 0
PORTAL_RUN = ""
original_configuration = application.configuration
original_choose_destination = application.choose_draft_destination
backend = None
export_path = None
portal_dialog_open = False
results = {}
DRIVER_REVISION = "p2-portal-window-filter-3"
original_signal = signal.signal
checkpoint_enabled = False
evidence_directory = None
active_app = None
stdout_broken = False


def safe_print(value):
    global stdout_broken
    if stdout_broken:
        return
    try:
        print(value, flush=True)
    except BrokenPipeError:
        stdout_broken = True
        results["stdout_closed"] = True
        try:
            fd = os.open(os.devnull, os.O_WRONLY)
            try:
                os.dup2(fd, sys.stdout.fileno())
            finally:
                os.close(fd)
        except (OSError, ValueError, AttributeError):
            pass


def persist(path, value):
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


def checkpoint():
    if checkpoint_enabled:
        persist(
            evidence_directory / "driver-checkpoint.json",
            {
                **results,
                "stage": getattr(active_app, "stage", "startup"),
                "complete": False,
            },
        )


class CloseObserver(QObject):
    """Main-window-only filter; never register on QApplication/QCoreApplication."""

    def eventFilter(self, receiver, event):
        app = self.parent()
        kind = event.type()
        if kind == QEvent.Type.Close and receiver is app.window:
            app.record(
                "qt-close-event",
                spontaneous=event.spontaneous(),
                python_close_context=app.python_close_origin or "none",
                intent=app.close_intent or "none",
                request_pending=bool(getattr(receiver, "request_id", None)),
                allow_close=bool(getattr(receiver, "allow_close", False)),
                action_busy=app.busy,
                action_pending=app.action_pending,
            )
        return False


class TracedMainWindow(QMainWindow):
    """Test-only Python close entry tracing; native Close events are separate."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app = QApplication.instance()
        app.window = self  # Retain the actual main window from construction.
        # Installing on QApplication would expose every WebEngine/private QObject
        # to the Python binding, even if eventFilter later checks the receiver.
        self.installEventFilter(app.close_observer)
        app.record("main-window-created")

    def close(self):
        app = QApplication.instance()
        previous = getattr(app, "python_close_origin", None)
        # Record fixed function labels, never frame locals, paths or arguments.
        caller = sys._getframe(1).f_code.co_name
        origin = (
            caller
            if caller in {"request_close", "failure", "close_problem", "received"}
            else "other-python"
        )
        if caller == "perform" and app.close_intent is not None:
            origin = "driver-queued-close"
        app.python_close_origin = origin
        app.record("python-close-enter", origin=origin)
        try:
            return super().close()
        finally:
            app.record("python-close-return", origin=origin)
            app.python_close_origin = previous


def trace_signal_registration(number, handler):
    """Forward the application's handlers unchanged, with bounded metadata."""
    if number not in (signal.SIGINT, signal.SIGTERM) or not callable(handler):
        return original_signal(number, handler)

    def forwarded(signum, frame):
        app = QApplication.instance()
        if app is not None:
            app.record(
                "termination-signal",
                signal="SIGINT" if signum == signal.SIGINT else "SIGTERM",
            )
        return handler(signum, frame)

    return original_signal(number, forwarded)


def profile_root():
    if PORTAL:
        # Preserve failed-run drafts/evidence; a new portal run never inherits
        # an unresolved recovery prompt from the previous synthetic attempt.
        return original_configuration().parent / "p2-portal-verification" / PORTAL_RUN
    return original_configuration().parent / "p2-outage-verification"


def api(path, body=None):
    request = urllib.request.Request(
        backend.origin + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "X-CyrNava-Session": backend.token,
            "Origin": backend.origin,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
        request, timeout=4
    ) as response:
        return json.load(response)


class TestBackend(Backend):
    def start(self):
        global backend
        super().start()
        backend = self
        if not api("/api/tree")["notes"]:
            if PHASE == 4:
                raise RuntimeError("Phase 3 synthetic profile is missing")
            api(
                "/api/notes",
                {
                    "title": "Synthetic outage verification",
                    "document_json": [{"type": "paragraph", "content": []}],
                    "format_version": 1,
                },
            )


class VerificationApp(QApplication):
    def __init__(self, args):
        global active_app
        super().__init__(args)
        active_app = self
        self.initialize_driver()
        self.close_observer = CloseObserver(self)
        self.aboutToQuit.connect(lambda: self.record("qt-about-to-quit"))
        self.lastWindowClosed.connect(lambda: self.record("qt-last-window-closed"))
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.advance)
        self.timer.start()

    def initialize_driver(self):
        self.window = None
        self.waiting = False
        self.stage = "load"
        self.failed = False
        self.shutting_down = False
        self.busy = False
        self.action_pending = False
        self.close_active = False
        self.close_intent = None
        self.python_close_origin = None
        self.generation = 0
        self.query_serial = 0
        self.pending_query = None
        self.replies = []
        self.trace_started = time.monotonic()
        self.trace = []
        self.trace_dropped = 0
        self.deadline = self.trace_started + (240 if PORTAL else 60)
        self.marker = (
            "P2 unsaved " + uuid4().hex[:12]
            if PHASE == 3
            else json.loads((profile_root() / "outage-phase-3.json").read_text())[
                "marker"
            ]
        )
        results["marker"] = self.marker
        results["driver_revision"] = DRIVER_REVISION
        results["trace"] = self.trace
        self.record("driver-initialized")

    def record(self, event, **fields):
        # All callers supply fixed labels, integers and booleans. No note text,
        # URLs, credentials, request UUIDs, file names or frame locals enter trace.
        entry = {
            "sequence": self.trace_dropped + len(self.trace) + 1,
            "ms": round((time.monotonic() - self.trace_started) * 1000, 3),
            "event": event,
            "phase": PHASE,
            "stage": self.stage,
            "generation": self.generation,
            **fields,
        }
        if len(self.trace) == 384:
            del self.trace[0]  # retain the events closest to any late failure
            self.trace_dropped += 1
            results["trace_dropped"] = self.trace_dropped
        self.trace.append(entry)
        checkpoint()

    def exec(self):
        self.record("event-loop-enter")
        code = None
        try:
            code = super().exec()
            return code
        finally:
            self.shutting_down = True
            self.generation += 1
            self.pending_query = None
            self.replies.clear()
            self.action_pending = False
            self.timer.stop()
            results["event_loop_exit_code"] = code
            self.record("event-loop-return")
            if self.stage != "finished" and not self.failed:
                self.failure("Qt event loop exited before verification finished")

    def transition(self, stage):
        self.stage = stage
        self.generation += 1
        self.pending_query = None
        self.waiting = False
        self.record("transition")

    def failure(self, message):
        if self.failed:
            return
        observed_stage = self.stage
        self.failed = True
        results["error"] = message
        results["terminal_failure"] = True
        results["failure_stage"] = observed_stage
        self.transition("failed")
        self.record("failure-locked")
        self.timer.stop()
        # Preserve unexpected dialogs and close protections for owner inspection.
        # Persist now even if a modal loop awaits the owner's explicit choice.
        results["status"] = "FAIL"
        if backend and backend.child and backend.child.poll() is not None:
            results["checks"]["owned_backend_reaped"] = "PASS"
        write_evidence()
        safe_print(
            "Verification stopped: "
            + message
            + ". Inspect the window; close it manually when ready."
        )

    def request_close(self, reason, stage):
        permitted = {
            ("verify-keep-open", "first-close-ready", "first-close"),
            ("verify-recovery-close", "download", "second-close"),
            ("verify-recovered-save", "recovered-close-ready", "finished"),
        }
        if self.failed or (reason, self.stage, stage) not in permitted:
            self.failure("Driver close requested outside its permitted state")
            return
        self.transition(stage)

        def perform():
            self.close_active = True
            self.close_intent = reason
            self.record("driver-close-request", reason=reason)
            try:
                self.window.close()
            finally:
                self.record("driver-close-return", reason=reason)
                self.close_active = False
                self.close_intent = None
            # Wait until closeEvent/close_problem/exec has fully unwound.
            if not self.failed and self.stage == "keep-open-settling":
                self.transition("export")

        self.schedule_action(perform)

    def schedule_action(self, action):
        generation = self.generation
        self.action_pending = True
        self.record("native-action-queued")

        def perform():
            self.action_pending = False
            if self.failed or self.shutting_down or self.generation != generation:
                self.record("native-action-stale")
                return
            self.busy = True
            try:
                action()
            except Exception as error:  # noqa: BLE001 - record slot/cleanup failure before finalization.
                self.failure("Native action exception: " + type(error).__name__)
            finally:
                self.busy = False

        # A modal opened from the polling timer's own timeout slot starves
        # that same timer. A separate queued turn keeps its observer available.
        QTimer.singleShot(0, perform)

    def query(self, script):
        self.query_serial += 1
        ticket = (self.generation, self.query_serial, self.stage)
        self.pending_query = ticket
        self.waiting = True
        self.record("js-query", query=self.query_serial)

        def observed(value):
            # WebEngine completions can run inside QTest or a native modal.
            # Store a boolean observation only; NEVER stop/type/close here.
            if self.failed or self.shutting_down or self.pending_query != ticket:
                self.record("js-reply-ignored", query=ticket[1])
                return
            self.pending_query = None
            valid = value is True or value is False
            self.replies.append((ticket, value if valid else None))
            self.record(
                "js-reply-queued", query=ticket[1], ready=value is True, valid=valid
            )

        self.window.page.runJavaScript(script, observed)

    def consume_reply(self):
        while self.replies:
            ticket, ready = self.replies.pop(0)
            if ticket[0] != self.generation or ticket[2] != self.stage:
                self.record("js-observation-stale", query=ticket[1])
                continue
            self.waiting = False
            if ready is None:
                self.failure("Invalid JavaScript observation at " + self.stage)
                return
            if not ready:
                if self.stage == "download":
                    self.transition("export")
                return
            if self.stage == "load":
                if PHASE == 4:
                    results["checks"]["recovery_choice_present"] = "PASS"
                    self.transition("recovered")
                else:
                    self.transition("typing")
            elif self.stage == "typed":
                results["checks"]["live_offline_title_verified"] = "PASS"
                self.transition("first-close-ready")
            elif self.stage == "recovered":
                results["checks"]["recovered_draft_saved"] = "PASS"
                self.transition("recovered-close-ready")
            return

    def advance(self):
        # Modal handling is allowed during an intentional close. No other side
        # effect may reenter the actor while QTest or a close stack is running.
        if self.failed or self.shutting_down or portal_dialog_open:
            return
        if PORTAL and "error" in results:
            self.failure(results["error"])
            return
        if time.monotonic() > self.deadline:
            self.failure("Timed out at " + self.stage)
            return
        for dialog in self.topLevelWidgets():
            if not isinstance(dialog, QMessageBox) or not dialog.isVisible():
                continue
            observed_stage = self.stage
            choice = (
                "Keep open"
                if self.stage == "first-close" and self.close_active
                else "Close with recovery draft"
                if self.stage == "second-close" and self.close_active
                else None
            )
            button = next((b for b in dialog.buttons() if b.text() == choice), None)
            self.record("native-confirmation-observed", expected=button is not None)
            if button is None:
                # Dialog identity is restricted to this fixed application dialog;
                # unknown modal content is never copied into evidence.
                known = dialog.windowTitle() == "CyrNava has unconfirmed changes"
                results["unexpected_dialog"] = {
                    "kind": "unconfirmed-changes" if known else "other-message-box",
                    "title": "CyrNava has unconfirmed changes"
                    if known
                    else "[redacted]",
                    "buttons": [
                        b.text()
                        if b.text()
                        in {"Keep open", "Close with recovery draft", "OK", "Cancel"}
                        else "[redacted]"
                        for b in dialog.buttons()
                    ][:8],
                    "observed_stage": observed_stage,
                }
                self.failure("Unexpected native dialog at " + observed_stage)
                return
            if self.stage == "first-close":
                results["checks"]["keep_open_choice"] = "PASS"
                self.transition("keep-open-settling")
            else:
                results["checks"]["explicit_recovery_close"] = "PASS"
                self.transition("finished")
                self.timer.stop()
            button.click()
            return
        if self.busy or self.close_active or self.action_pending:
            return
        self.busy = True
        try:
            self.step()
        finally:
            self.busy = False

    def step(self):
        if self.window is None:
            self.window = next(
                (
                    w
                    for w in self.topLevelWidgets()
                    if hasattr(w, "page") and hasattr(w, "request_id")
                ),
                None,
            )
        if self.window is None or not self.window.loaded:
            return
        self.consume_reply()
        if self.failed or self.waiting:
            return
        if self.stage == "typing":
            self.schedule_action(self.type_offline)
            return
        if self.stage == "first-close-ready":
            self.request_close("verify-keep-open", "first-close")
            return
        if self.stage == "recovered-close-ready":
            self.timer.stop()
            self.request_close("verify-recovered-save", "finished")
            return
        if self.stage == "download":
            if PORTAL and export_path is None:
                return
            try:
                exported = json.loads(
                    (
                        export_path
                        if PORTAL
                        else profile_root() / "synthetic-export.json"
                    ).read_text()
                )
            except (OSError, ValueError):
                return
            if exported.get("title") != self.marker:
                self.failure("Export did not contain the live offline draft")
                return
            results["checks"]["native_blob_export_while_backend_stopped"] = "PASS"
            if PORTAL:
                results["checks"]["real_save_chooser_and_granted_json_readback"] = (
                    "PASS"
                )
            self.record("granted-json-verified")
            self.request_close("verify-recovery-close", "second-close")
            return
        if self.stage == "export":
            self.transition("download")
            script = "(() => {const button=Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='Download pending draft');if(!button || button.disabled)return false;button.click();return true;})()"
        elif self.stage == "load" and PHASE == 3:
            self.window.activateWindow()
            self.window.view.setFocus()
            script = "(() => {const input=document.querySelector('#note-title'); if(!input || input.disabled || document.querySelector('.save-state')?.dataset.state !== 'Saved')return false; input.focus();return document.activeElement===input;})()"
        elif self.stage == "load":
            script = "(() => {const button=Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='Recover draft');if(!button)return false;button.click();return true;})()"
        elif self.stage == "typed":
            script = 'document.querySelector("#note-title")?.value === ' + json.dumps(
                self.marker
            )
        elif self.stage == "recovered":
            script = (
                'document.querySelector("#note-title")?.value === '
                + json.dumps(self.marker)
                + ' && document.querySelector(".save-state")?.dataset.state === "Saved"'
            )
        else:
            return
        self.query(script)

    def type_offline(self):
        self.record("native-typing-begin")
        try:
            backend.stop()
            results["checks"]["test_owned_backend_stopped"] = "PASS"
            self.record("test-backend-stopped")
            if self.failed:
                return
            target = self.window.view.focusProxy() or self.window.view
            QTest.keyClick(target, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
            if self.failed:
                return
            QTest.keyClicks(target, self.marker)
            if not self.failed:
                self.record("native-typing-return")
                self.transition("typed")
        except (OSError, RuntimeError, TypeError):
            self.failure("Native typing failed")


def destination(*_args):
    results["checks"]["native_download_save_request"] = "PASS"
    return str(profile_root() / "synthetic-export.json"), "JSON (*.json)"


def real_destination(dialog, parent):
    global export_path, portal_dialog_open
    portal_dialog_open = True
    try:
        selected = original_choose_destination(dialog, parent)
    finally:
        portal_dialog_open = False
    if selected:
        export_path = Path(selected)
        results["checks"]["native_download_save_request"] = "PASS"
    else:
        results["error"] = "The real save chooser was cancelled; no PASS claimed"
    return selected


def write_evidence(final=False):
    results["complete"] = final
    evidence = (evidence_directory or profile_root()) / f"outage-phase-{PHASE}.json"
    try:
        persist(evidence, results)
    except OSError as error:
        results["status"] = "FAIL"
        results["evidence_write_error"] = type(error).__name__
        safe_print(json.dumps(results, indent=2))
        safe_print("Evidence write failed; no saved result is claimed")
        return
    safe_print(json.dumps(results, indent=2))
    safe_print("Evidence: " + str(evidence))


def callback_exception(kind, _value, _traceback):
    # PySide invokes sys.excepthook for Python slot/virtual exceptions. Exception
    # args/locals could contain content; record only the exception class.
    results["callback_exception_type"] = kind.__name__
    if active_app is not None and hasattr(active_app, "timer"):
        active_app.failure("Unhandled Qt callback exception: " + kind.__name__)
    else:
        results["error"] = "Unhandled Qt startup callback exception"
        checkpoint()


def main():
    global PORTAL, PHASE, PORTAL_RUN, results, backend, export_path, portal_dialog_open
    global checkpoint_enabled, evidence_directory, active_app
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", type=int, choices=(3, 4))
    parser.add_argument("--portal", action="store_true")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    PHASE, PORTAL = args.phase, args.portal
    if (PORTAL and PHASE != 3) or (
        args.run_id
        and (not PORTAL or not re.fullmatch(r"run-[0-9a-f]{12}", args.run_id))
    ):
        parser.error("A generated run-ID is allowed only for phase 3 --portal")
    PORTAL_RUN = args.run_id or ("run-" + uuid4().hex[:12] if PORTAL else "")
    active_app = None
    checkpoint_enabled = False
    evidence_directory = None
    backend = None
    export_path = None
    portal_dialog_open = False
    results = {
        "phase": PHASE,
        "real_save_portal": PORTAL,
        "status": "FAIL",
        "checks": {},
        "driver_revision": DRIVER_REVISION,
        "complete": False,
    }
    evidence_directory = private_directory(profile_root())
    checkpoint_enabled = True
    checkpoint()
    persist(
        evidence_directory / f"outage-phase-{PHASE}.json",
        {**results, "error": "Driver did not reach finalization"},
    )
    safe_print("Driver revision: " + DRIVER_REVISION)
    if PORTAL:
        safe_print(
            "A REAL save chooser will open. Choose Downloads (or Documents), name the "
            "file cyrnava-p2-portal-test.json, and click Save within four minutes. "
            "This test stops only its own backend and validates the selected export."
        )
    handlers = {
        number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)
    }
    code = None
    previous_hook = sys.excepthook
    sys.excepthook = callback_exception
    try:
        checkpoint()
        with (
            patch.object(application, "configuration", profile_root),
            patch.object(application, "Backend", TestBackend),
            patch("PySide6.QtWidgets.QApplication", VerificationApp),
            patch("PySide6.QtWidgets.QMainWindow", TracedMainWindow),
            patch.object(signal, "signal", trace_signal_registration),
            patch.object(application, "choose_draft_destination", real_destination)
            if PORTAL
            else nullcontext(),
            nullcontext()
            if PORTAL
            else patch.object(QFileDialog, "getSaveFileName", destination),
        ):
            code = application.run()
    except BaseException as error:  # noqa: BLE001 - terminal test boundary must persist every Python failure.
        results["error"] = "Application execution exception: " + type(error).__name__
        results["exception_type"] = type(error).__name__
    finally:
        try:
            if active_app is not None and hasattr(active_app, "timer"):
                active_app.shutting_down = True
                active_app.generation += 1
                active_app.pending_query = None
                try:
                    active_app.timer.stop()
                except Exception as error:  # noqa: BLE001 - retain cleanup failure and restore hooks below.
                    results["timer_cleanup_exception_type"] = type(error).__name__
                    results.setdefault("error", "Driver timer cleanup failed")
            # Construction can fail before production run() enters its own
            # exec/finally block. Reap only the retained synthetic backend child.
            if backend is not None:
                try:
                    backend.stop()
                except Exception as error:  # noqa: BLE001 - retain cleanup failure and restore hooks below.
                    results["backend_cleanup_exception_type"] = type(error).__name__
                    results.setdefault("error", "Owned backend cleanup failed")
        finally:
            sys.excepthook = previous_hook
            for number, handler in handlers.items():
                original_signal(number, handler)
    if backend and backend.child and backend.child.poll() is not None:
        results["checks"]["owned_backend_reaped"] = "PASS"
        if PHASE == 4:
            sys.path.insert(0, "/app/share/cyrnava/backend")
            from app.database import Database

            database = Database(backend.profile.database)
            note = database.get(database.tree()["notes"][0]["id"])
            if note["title"] == results["marker"]:
                results["checks"]["recovered_title_committed_in_sqlite"] = "PASS"
            else:
                results["error"] = "Recovered title did not commit"
    required = (
        (
            "test_owned_backend_stopped",
            "owned_backend_reaped",
            "keep_open_choice",
            "live_offline_title_verified",
            "native_download_save_request",
            "native_blob_export_while_backend_stopped",
            "explicit_recovery_close",
        )
        if PHASE == 3
        else (
            "recovered_draft_saved",
            "recovered_title_committed_in_sqlite",
            "owned_backend_reaped",
        )
    )
    if PORTAL:
        required += ("real_save_chooser_and_granted_json_readback",)
    if (
        code == 0
        and "error" not in results
        and all(results["checks"].get(key) == "PASS" for key in required)
    ):
        results["status"] = "PASS"
    if results["status"] != "PASS" and "error" not in results:
        results["error"] = (
            "Application returned before all required verification checks completed"
        )
    write_evidence(final=True)
    checkpoint_enabled = False
    return 0 if results["status"] == "PASS" else 1


def entrypoint():
    try:
        return main()
    except BaseException as error:  # noqa: BLE001 - terminal test boundary must persist every Python failure.
        # The external supervisor also covers import errors and native crashes.
        # This covers Python failures before/after the application execution try.
        results.update(
            status="FAIL",
            complete=True,
            error="Driver exception: " + type(error).__name__,
        )
        try:
            if evidence_directory is not None:
                write_evidence(final=True)
            else:
                safe_print(json.dumps(results, indent=2))
        except BaseException:  # noqa: BLE001 - last-resort reporting must not escape silently.
            safe_print('{"status":"FAIL","error":"Driver could not persist evidence"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(entrypoint())
