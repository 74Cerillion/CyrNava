"""Driver sequencing regressions using Qt import doubles; no portal PASS claimed."""

import importlib.util
import json
import signal
import sys
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture
def driver(monkeypatch, tmp_path):
    def application_init(self, *_args):
        self.installEventFilter = Mock()
        self.aboutToQuit = Mock()
        self.lastWindowClosed = Mock()

    def window_init(self, *_args):
        self.installEventFilter = Mock()

    qt = SimpleNamespace(
        Key=SimpleNamespace(Key_A="A"),
        KeyboardModifier=SimpleNamespace(ControlModifier="Control"),
    )
    for name, members in {
        "PySide6": {},
        "PySide6.QtCore": {
            "Qt": qt,
            "QTimer": Mock(),
            "QObject": type(
                "QObject",
                (),
                {
                    "__init__": lambda self, parent=None: setattr(
                        self, "owner", parent
                    ),
                    "parent": lambda self: self.owner,
                },
            ),
            "QEvent": SimpleNamespace(Type=SimpleNamespace(Close=1, Quit=2)),
        },
        "PySide6.QtTest": {"QTest": Mock()},
        "PySide6.QtWidgets": {
            "QApplication": type(
                "QApplication", (), {"__init__": application_init, "exec": lambda *_: 0}
            ),
            "QMainWindow": type(
                "QMainWindow",
                (),
                {"__init__": window_init, "close": lambda *_: True},
            ),
            "QFileDialog": Mock(),
            "QMessageBox": type("QMessageBox", (), {}),
        },
    }.items():
        imported = ModuleType(name)
        imported.__dict__.update(members)
        monkeypatch.setitem(sys.modules, name, imported)
    spec = importlib.util.spec_from_file_location(
        "portal_driver_under_test", Path(__file__).with_name("verify_outage.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.PORTAL = True
    module.PHASE = 3
    module.results = {"checks": {}, "status": "FAIL"}
    module.real_write_evidence = module.write_evidence
    module.write_evidence = Mock()
    module.original_configuration = lambda: tmp_path / "unused-normal-profile"
    module.QTimer.singleShot.side_effect = lambda _ms, callback: callback()
    return module


def state(driver, stage="load"):
    app = driver.VerificationApp.__new__(driver.VerificationApp)
    app.initialize_driver()
    app.close_observer = Mock()
    app.stage = stage
    app.timer = Mock()
    app.topLevelWidgets = list
    app.window = SimpleNamespace(
        loaded=True,
        page=Mock(),
        close=Mock(),
        activateWindow=Mock(),
        view=Mock(),
        request_id=None,
        allow_close=False,
    )
    return app


def replies(app):
    callbacks = []
    app.window.page.runJavaScript.side_effect = lambda _script, callback: (
        callbacks.append(callback)
    )
    return callbacks


def test_javascript_reply_only_queues_without_stopping_typing_or_closing(driver):
    app = state(driver)
    callbacks = replies(app)
    driver.backend = SimpleNamespace(stop=Mock(), child=None)
    app.advance()
    callbacks[0](True)
    driver.backend.stop.assert_not_called()
    driver.QTest.keyClicks.assert_not_called()
    app.window.close.assert_not_called()
    assert app.stage == "load" and app.waiting
    app.advance()
    driver.backend.stop.assert_called_once()
    driver.QTest.keyClicks.assert_called_once()
    assert app.stage == "typed" and not app.waiting


def test_typing_reentrant_timer_and_duplicate_load_reply_cannot_close(driver):
    app = state(driver)
    callbacks = replies(app)
    app.advance()
    callbacks[0](True)

    def nested(*_args):
        assert app.stage == "typing" and app.busy
        callbacks[0](True)
        app.advance()
        app.window.close.assert_not_called()
        assert app.stage == "typing" and app.busy

    driver.backend = SimpleNamespace(stop=Mock(side_effect=nested))
    driver.QTest.keyClick.side_effect = nested
    driver.QTest.keyClicks.side_effect = nested
    app.advance()
    driver.backend.stop.assert_called_once()
    driver.QTest.keyClicks.assert_called_once()
    app.window.close.assert_not_called()
    assert app.stage == "typed"
    app.advance()
    callbacks[1](True)
    app.window.close.assert_not_called()  # even a positive JS reply cannot close
    app.advance()
    app.window.close.assert_called_once()
    assert driver.results["checks"]["live_offline_title_verified"] == "PASS"


def test_old_generation_reply_in_same_named_stage_is_ignored(driver):
    app = state(driver)
    callbacks = replies(app)
    app.advance()
    app.transition("load")
    app.advance()
    callbacks[0](True)
    assert not app.replies and app.waiting
    callbacks[1](False)
    app.advance()
    assert not any(e["event"] == "native-typing-begin" for e in app.trace)


def dialog_class(driver):
    class Dialog:
        def __init__(self):
            self.reject = Mock()
            self.visible = True
            self.keep = Mock()
            self.keep.text.return_value = "Keep open"
            self.leave = Mock()
            self.leave.text.return_value = "Close with recovery draft"

        def isVisible(self):
            return self.visible

        def windowTitle(self):
            return "CyrNava has unconfirmed changes"

        def buttons(self):
            return [self.keep, self.leave]

    driver.QMessageBox = Dialog
    return Dialog


@pytest.mark.parametrize("stage", ["typing", "typed"])
def test_exact_unexpected_close_dialog_preserved_and_failure_is_terminal(driver, stage):
    app = state(driver, stage)
    dialog = dialog_class(driver)()
    app.topLevelWidgets = lambda: [dialog]
    app.advance()
    assert driver.results["error"] == "Unexpected native dialog at " + stage
    assert driver.results["failure_stage"] == stage
    assert driver.results["unexpected_dialog"]["kind"] == "unconfirmed-changes"
    assert driver.results["status"] == "FAIL" and app.failed
    dialog.reject.assert_not_called()
    dialog.keep.click.assert_not_called()
    dialog.leave.click.assert_not_called()
    app.window.close.assert_not_called()
    driver.write_evidence.assert_called_once()
    app.advance()
    assert app.stage == "failed" and not driver.results["checks"]


def test_unexpected_dialog_during_qtest_does_not_resume_typing(driver):
    app = state(driver, "typing")
    dialog = dialog_class(driver)()
    driver.backend = SimpleNamespace(stop=Mock(), child=None)

    def native_event(*_):
        app.topLevelWidgets = lambda: [dialog]
        app.advance()

    driver.QTest.keyClick.side_effect = native_event
    app.advance()
    assert app.failed and app.stage == "failed"
    driver.QTest.keyClicks.assert_not_called()
    assert "live_offline_title_verified" not in driver.results["checks"]
    assert driver.results["checks"]["test_owned_backend_stopped"] == "PASS"


def test_expected_keep_open_waits_until_native_close_stack_unwinds(driver):
    app = state(driver, "first-close-ready")
    dialog = dialog_class(driver)()

    def close():
        assert app.stage == "first-close" and app.close_active
        app.topLevelWidgets = lambda: [dialog]
        dialog.keep.click.side_effect = lambda: setattr(dialog, "visible", False)
        app.advance()
        assert app.stage == "keep-open-settling"
        app.advance()
        app.window.page.runJavaScript.assert_not_called()
        assert app.close_active

    app.window.close.side_effect = close
    app.advance()
    assert app.stage == "export" and not app.close_active
    assert driver.results["checks"]["keep_open_choice"] == "PASS"
    dialog.keep.click.assert_called_once()
    dialog.reject.assert_not_called()


def test_export_reentrant_timer_and_js_completion_dispatch_once(driver):
    app = state(driver, "export")

    def dispatch(_script, callback):
        assert app.stage == "download"
        app.advance()
        app.advance()
        callback(True)
        app.advance()

    app.window.page.runJavaScript.side_effect = dispatch
    app.advance()
    app.advance()
    app.advance()
    app.window.page.runJavaScript.assert_called_once()
    assert app.stage == "download" and not app.failed


def test_export_retries_readiness_without_repeating_successful_click(driver):
    app = state(driver, "export")
    callbacks = replies(app)
    app.advance()
    callbacks[0](False)
    app.advance()
    assert len(callbacks) == 2
    callbacks[1](True)
    app.advance()
    app.advance()
    assert len(callbacks) == 2 and app.stage == "download"


def test_portal_wrapper_uses_real_chooser_and_blocks_nested_polling(driver, tmp_path):
    app = state(driver, "export")
    selected = tmp_path / "explicitly granted.json"

    def choose(dialog, parent):
        assert driver.portal_dialog_open
        assert (dialog, parent) == ("dialog", "parent")
        app.advance()
        return str(selected)

    driver.original_choose_destination = Mock(side_effect=choose)
    assert driver.real_destination("dialog", "parent") == str(selected)
    app.window.page.runJavaScript.assert_not_called()
    assert driver.export_path == selected and not driver.portal_dialog_open
    assert driver.results["checks"]["native_download_save_request"] == "PASS"


def test_portal_cancellation_is_not_success(driver):
    driver.original_choose_destination = lambda *_: ""
    assert driver.real_destination(None, None) == ""
    assert "cancelled" in driver.results["error"]
    assert not driver.results["checks"]


def test_granted_json_readback_then_explicit_recovery_close(driver, tmp_path):
    app = state(driver, "download")
    exported = tmp_path / "granted.json"
    exported.write_text(json.dumps({"title": app.marker}))
    driver.export_path = exported
    dialog = dialog_class(driver)()

    def close():
        assert app.stage == "second-close" and app.close_active
        app.topLevelWidgets = lambda: [dialog]
        app.advance()

    app.window.close.side_effect = close
    app.advance()
    assert app.stage == "finished"
    for check in (
        "native_blob_export_while_backend_stopped",
        "real_save_chooser_and_granted_json_readback",
        "explicit_recovery_close",
    ):
        assert driver.results["checks"][check] == "PASS"
    dialog.leave.click.assert_called_once()


def test_mismatched_granted_json_cannot_pass_or_close(driver, tmp_path):
    app = state(driver, "download")
    driver.export_path = tmp_path / "granted.json"
    driver.export_path.write_text('{"title":"wrong synthetic marker"}')
    app.advance()
    assert app.failed
    app.window.close.assert_not_called()
    assert not driver.results["checks"]


def test_timeout_is_bounded_and_preserves_failure(driver):
    app = state(driver, "typed")
    app.deadline = time.monotonic() - 1
    app.advance()
    assert driver.results["error"] == "Timed out at typed"
    app.timer.stop.assert_called_once()
    app.advance()
    driver.write_evidence.assert_called_once()
    app.window.close.assert_not_called()


def test_failure_invalidates_pending_javascript_reply(driver):
    app = state(driver)
    callbacks = replies(app)
    app.advance()
    app.failure("synthetic failure")
    callbacks[0](True)
    app.advance()
    assert not app.replies and app.stage == "failed"
    assert driver.results["error"] == "synthetic failure"


def test_nonboolean_javascript_observation_is_failure_not_readiness_retry(driver):
    app = state(driver)
    callbacks = replies(app)
    app.advance()
    callbacks[0](None)
    assert not app.failed  # callback records only; next actor turn handles failure
    app.advance()
    assert (
        app.failed
        and driver.results["error"] == "Invalid JavaScript observation at load"
    )
    driver.QTest.keyClicks.assert_not_called()


def test_window_close_observer_never_consumes_events_or_observes_app_quit(driver):
    app = state(driver, "typed")
    app.python_close_origin = "other-python"
    for kind in (driver.QEvent.Type.Close, driver.QEvent.Type.Quit):
        observer = driver.CloseObserver(app)
        assert (
            observer.eventFilter(
                app.window,
                SimpleNamespace(type=lambda kind=kind: kind, spontaneous=lambda: True),
            )
            is False
        )
    events = [e for e in app.trace if e["event"].startswith("qt-")]
    assert [e["event"] for e in events] == ["qt-close-event"]
    assert all(
        e["python_close_context"] == "other-python" and e["intent"] == "none"
        for e in events
    )


def test_python_close_trace_records_entry_and_return(driver, monkeypatch):
    app = state(driver)
    monkeypatch.setattr(driver.QApplication, "instance", lambda: app, raising=False)
    app.close_observer = Mock()
    assert driver.TracedMainWindow().close()
    assert [e["event"] for e in app.trace][-2:] == [
        "python-close-enter",
        "python-close-return",
    ]
    assert app.python_close_origin is None


def test_signal_trace_forwards_application_handler_once(driver, monkeypatch):
    app = state(driver)
    monkeypatch.setattr(driver.QApplication, "instance", lambda: app, raising=False)
    registered = {}
    driver.original_signal = lambda number, handler: registered.setdefault(
        number, handler
    )
    handler = Mock()
    driver.trace_signal_registration(signal.SIGTERM, handler)
    registered[signal.SIGTERM](signal.SIGTERM, None)
    handler.assert_called_once_with(signal.SIGTERM, None)
    assert app.trace[-1]["event"] == "termination-signal"


def test_trace_is_bounded_and_contains_no_marker_or_window_content(driver):
    app = state(driver)
    app.window.secret = "private note content"
    for _ in range(500):
        app.record("synthetic-tick")
    text = json.dumps(app.trace)
    assert len(app.trace) == 384 and driver.results["trace_dropped"] > 0
    assert app.marker not in text and app.window.secret not in text
    assert "token" not in text


def test_portal_runs_keep_separate_profiles_and_historical_evidence(driver, tmp_path):
    driver.original_configuration = lambda: tmp_path / "cyrnava"
    driver.PORTAL_RUN = "run-first"
    first = driver.profile_root()
    driver.PORTAL_RUN = "run-second"
    assert first != driver.profile_root()
    assert (
        first.parent
        == driver.profile_root().parent
        == tmp_path / "p2-portal-verification"
    )


def test_close_intent_during_typing_is_rejected_without_touching_window(driver):
    app = state(driver, "typing")
    app.request_close("verify-keep-open", "first-close")
    assert app.failed and driver.results["failure_stage"] == "typing"
    app.window.close.assert_not_called()


def test_native_actions_wait_for_separate_turn_and_cannot_overlap(driver):
    app = state(driver, "typing")
    queued = []
    driver.QTimer.singleShot.side_effect = lambda _ms, callback: queued.append(callback)
    driver.backend = SimpleNamespace(stop=Mock(), child=None)
    app.advance()
    app.advance()
    driver.backend.stop.assert_not_called()
    assert app.action_pending and len(queued) == 1
    queued[0]()
    driver.backend.stop.assert_called_once()
    assert app.stage == "typed" and not app.action_pending and not app.busy


def test_queued_action_cannot_run_after_terminal_failure(driver):
    app = state(driver, "typing")
    queued = []
    driver.QTimer.singleShot.side_effect = lambda _ms, callback: queued.append(callback)
    driver.backend = SimpleNamespace(stop=Mock(), child=None)
    app.advance()
    app.failure("Synthetic interruption")
    queued[0]()
    driver.backend.stop.assert_not_called()
    driver.QTest.keyClicks.assert_not_called()
    assert app.stage == "failed"


def test_unknown_dialog_text_is_redacted_from_evidence(driver):
    app = state(driver, "typed")
    dialog = dialog_class(driver)()
    dialog.windowTitle = lambda: "private note title"
    dialog.keep.text.return_value = "private note body"
    app.topLevelWidgets = lambda: [dialog]
    app.advance()
    text = json.dumps(driver.results)
    assert "private note" not in text
    assert driver.results["unexpected_dialog"]["title"] == "[redacted]"


@pytest.mark.parametrize(
    "missing",
    [
        "test_owned_backend_stopped",
        "owned_backend_reaped",
        "native_download_save_request",
        "real_save_chooser_and_granted_json_readback",
        "explicit_recovery_close",
        None,
    ],
)
def test_final_portal_acceptance_requires_every_native_boundary(
    driver, monkeypatch, missing
):
    checks = {
        name: "PASS"
        for name in (
            "test_owned_backend_stopped",
            "owned_backend_reaped",
            "keep_open_choice",
            "live_offline_title_verified",
            "native_download_save_request",
            "native_blob_export_while_backend_stopped",
            "explicit_recovery_close",
            "real_save_chooser_and_granted_json_readback",
        )
        if name != missing
    }
    monkeypatch.setattr(sys, "argv", ["verify_outage.py", "3", "--portal"])

    def run():
        driver.results["checks"].update(checks)
        return 0

    monkeypatch.setattr(driver.application, "run", run)
    assert driver.main() == (0 if missing is None else 1)
    assert driver.results["status"] == ("PASS" if missing is None else "FAIL")


def test_early_event_loop_return_is_failure_and_cancels_late_callbacks(driver):
    app = state(driver)
    callbacks = replies(app)
    app.advance()
    assert app.exec() == 0
    callbacks[0](True)
    assert app.shutting_down and app.failed and app.stage == "failed"
    assert app.pending_query is None and not app.replies
    assert (
        driver.results["error"] == "Qt event loop exited before verification finished"
    )
    driver.write_evidence.assert_called_once()
    app.window.close.assert_not_called()


def test_queued_action_cannot_touch_window_after_event_loop_return(driver):
    app = state(driver, "typing")
    queued = []
    driver.QTimer.singleShot.side_effect = lambda _ms, callback: queued.append(callback)
    driver.backend = SimpleNamespace(stop=Mock(), child=None)
    app.advance()
    app.exec()
    queued[0]()
    driver.backend.stop.assert_not_called()
    driver.QTest.keyClicks.assert_not_called()
    app.window.close.assert_not_called()


def test_finished_event_loop_return_is_not_reclassified_as_failure(driver):
    app = state(driver, "finished")
    assert app.exec() == 0
    assert app.shutting_down and not app.failed
    assert driver.results["event_loop_exit_code"] == 0
    assert "error" not in driver.results


def test_application_exception_finalizes_fail_reaps_child_and_restores_hooks(
    driver, monkeypatch
):
    monkeypatch.setattr(sys, "argv", ["verify_outage.py", "3", "--portal"])
    previous_hook = sys.excepthook
    previous_handlers = {
        number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)
    }
    owned = SimpleNamespace(stop=Mock(), child=SimpleNamespace(poll=lambda: 0))

    def run():
        driver.backend = owned
        raise RuntimeError("private exception argument")

    monkeypatch.setattr(driver.application, "run", run)
    assert driver.main() == 1
    owned.stop.assert_called_once()
    assert driver.results["checks"]["owned_backend_reaped"] == "PASS"
    assert driver.results["status"] == "FAIL"
    assert driver.results["exception_type"] == "RuntimeError"
    assert "private exception" not in json.dumps(driver.results)
    driver.write_evidence.assert_called_once_with(final=True)
    assert sys.excepthook is previous_hook
    assert all(
        signal.getsignal(number) is handler
        for number, handler in previous_handlers.items()
    )


def test_qt_callback_exception_locks_failure_without_exposing_arguments(driver):
    app = state(driver, "typing")
    driver.active_app = app
    driver.callback_exception(ValueError, ValueError("private document"), None)
    assert app.failed
    assert driver.results["callback_exception_type"] == "ValueError"
    assert "private document" not in json.dumps(driver.results)
    app.window.close.assert_not_called()


def test_entrypoint_catches_python_failure_after_or_before_application(
    driver, monkeypatch
):
    monkeypatch.setattr(driver, "main", Mock(side_effect=RuntimeError("private data")))
    assert driver.entrypoint() == 1
    assert driver.results["complete"] is True
    assert driver.results["error"] == "Driver exception: RuntimeError"
    assert "private data" not in json.dumps(driver.results)


def test_driver_writes_fail_checkpoint_before_application_is_constructed(
    driver, monkeypatch
):
    monkeypatch.setattr(sys, "argv", ["verify_outage.py", "3", "--portal"])

    def run():
        initial = json.loads(
            (driver.evidence_directory / "outage-phase-3.json").read_text()
        )
        checkpoint = json.loads(
            (driver.evidence_directory / "driver-checkpoint.json").read_text()
        )
        assert initial["status"] == "FAIL" and initial["complete"] is False
        assert checkpoint["stage"] == "startup"
        raise RuntimeError("synthetic startup failure")

    monkeypatch.setattr(driver.application, "run", run)
    assert driver.main() == 1
    driver.write_evidence.assert_called_once_with(final=True)


def test_scoped_observer_ignores_unrelated_widget_close(driver):
    app = state(driver)
    observer = driver.CloseObserver(app)
    assert (
        observer.eventFilter(
            object(), SimpleNamespace(type=lambda: driver.QEvent.Type.Close)
        )
        is False
    )
    assert not any(item["event"] == "qt-close-event" for item in app.trace)
    assert "notify" not in driver.VerificationApp.__dict__


def test_real_final_evidence_is_written_after_premature_application_return(
    driver, monkeypatch
):
    monkeypatch.setattr(sys, "argv", ["verify_outage.py", "3", "--portal"])
    monkeypatch.setattr(driver.application, "run", lambda: 0)
    driver.write_evidence = driver.real_write_evidence
    assert driver.main() == 1
    record = json.loads((driver.evidence_directory / "outage-phase-3.json").read_text())
    assert record["status"] == "FAIL" and record["complete"] is True
    assert "before all required" in record["error"]
    assert (
        driver.evidence_directory / "outage-phase-3.json"
    ).stat().st_mode & 0o777 == 0o600


def test_cleanup_exception_cannot_skip_final_evidence_or_hook_restoration(
    driver, monkeypatch
):
    monkeypatch.setattr(sys, "argv", ["verify_outage.py", "3", "--portal"])
    hook = sys.excepthook
    previous_handlers = {
        number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)
    }

    def run():
        driver.active_app = SimpleNamespace(timer=Mock(), generation=0)
        driver.active_app.timer.stop.side_effect = RuntimeError("deleted Qt timer")
        driver.backend = SimpleNamespace(
            stop=Mock(side_effect=RuntimeError("cleanup")), child=None
        )
        raise ValueError("original failure")

    monkeypatch.setattr(driver.application, "run", run)
    assert driver.main() == 1
    assert driver.results["exception_type"] == "ValueError"
    assert driver.results["timer_cleanup_exception_type"] == "RuntimeError"
    assert driver.results["backend_cleanup_exception_type"] == "RuntimeError"
    driver.write_evidence.assert_called_once_with(final=True)
    assert sys.excepthook is hook
    assert all(
        signal.getsignal(number) is handler
        for number, handler in previous_handlers.items()
    )


def test_main_window_is_retained_from_construction_not_delayed_poll(
    driver, monkeypatch
):
    app = state(driver)
    monkeypatch.setattr(driver.QApplication, "instance", lambda: app, raising=False)
    window = driver.TracedMainWindow()
    assert app.window is window
    assert app.trace[-1]["event"] == "main-window-created"


def test_filter_registration_is_window_local_never_application_global(
    driver, monkeypatch
):
    app = driver.VerificationApp(["synthetic registration check"])
    monkeypatch.setattr(driver.QApplication, "instance", lambda: app, raising=False)
    native = driver.TracedMainWindow()
    native.installEventFilter.assert_called_once_with(app.close_observer)
    app.installEventFilter.assert_not_called()
    assert "notify" not in driver.VerificationApp.__dict__
    # Quit diagnostics use a signal rather than a global event filter.
    app.aboutToQuit.connect.call_args.args[0]()
    assert app.trace[-1]["event"] == "qt-about-to-quit"
