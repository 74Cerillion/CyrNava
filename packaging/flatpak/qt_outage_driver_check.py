"""Real QtWidgets regression probe; no WebEngine, backend, files or portal.

Run with an existing compatible PySide6 interpreter and QT_QPA_PLATFORM=offscreen:
    python packaging/flatpak/qt_outage_driver_check.py normal
    python packaging/flatpak/qt_outage_driver_check.py unexpected-typed
    python packaging/flatpak/qt_outage_driver_check.py early-exit
    python packaging/flatpak/qt_outage_driver_check.py main-early-exit
    python packaging/flatpak/qt_outage_driver_check.py filter-scope

The injected unexpected Close must FAIL the driver, remain visible, and be
traceable to a non-driver Close. Only this harness then simulates owner cleanup.
A successful probe does not constitute native Save portal acceptance.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QTimer
from PySide6.QtWidgets import QLineEdit, QMessageBox

spec = importlib.util.spec_from_file_location(
    "driver", Path(__file__).with_name("verify_outage.py")
)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
mode = sys.argv[1]
if mode == "main-early-exit":
    # Exercise the actual main()/patch/finalization path with real QApplication,
    # not only a direct VerificationApp constructor or Qt import doubles.
    def application_run():
        from PySide6.QtWidgets import QApplication

        native = QApplication(["synthetic early-exit check"])
        QTimer.singleShot(0, lambda: native.exit(0))
        return native.exec()

    with tempfile.TemporaryDirectory(prefix="cyrnava-qt-finalization-") as temporary:
        driver.original_configuration = lambda: Path(temporary) / "unused-profile"
        driver.application.run = application_run
        sys.argv = ["verify_outage.py", "3", "--portal"]
        assert driver.entrypoint() == 1
        evidence = json.loads(
            (driver.evidence_directory / "outage-phase-3.json").read_text()
        )
        assert evidence["status"] == "FAIL" and evidence["complete"] is True
        assert evidence["error"] == "Qt event loop exited before verification finished"
        assert evidence["event_loop_exit_code"] == 0
    print(
        json.dumps(
            {
                "mode": mode,
                "status": "PASS",
                "boundary": "QtWidgets main() finalization only; no WebEngine or portal",
            }
        )
    )
    raise SystemExit(0)
driver.PHASE = 3
driver.PORTAL = False
driver.results = {"checks": {}}
driver.write_evidence = lambda: None  # no files, no portal PASS
foreign_target = None
foreign_observations = []
if mode == "filter-scope":

    class ObservedFilter(driver.CloseObserver):
        def eventFilter(self, receiver, event):
            if receiver is foreign_target:
                foreign_observations.append(event.type())
            return super().eventFilter(receiver, event)

    driver.CloseObserver = ObservedFilter
app = driver.VerificationApp(["synthetic QtWidgets check"])
driver.backend = SimpleNamespace(stop=lambda: None, child=None)
observed = []
done = {}


class Page:
    def runJavaScript(self, script, callback=None):
        if callback is None:
            return
        if app.stage == "load":
            if mode == "early-exit":
                QTimer.singleShot(0, lambda: app.exit(0))
                return
            line.setFocus()
            value = True
        elif app.stage == "typed":
            value = line.text() == app.marker
            if mode == "unexpected-typed":
                QTimer.singleShot(0, window.close)
                return
        elif app.stage == "download":
            done["export"] = True
            app.timer.stop()
            app.transition("finished")  # End this limited probe at handoff.
            window.allow_close = True
            QTimer.singleShot(0, window.close)
            return
        else:
            value = False
        QTimer.singleShot(0, lambda: callback(value))


class Window(driver.TracedMainWindow):
    loaded = True
    request_id = None
    allow_close = False

    def closeEvent(self, event):
        observed.append(("close", app.stage))
        if self.allow_close:
            event.accept()
            return
        event.ignore()
        box = QMessageBox(self)
        box.setWindowTitle("CyrNava has unconfirmed changes")
        keep = box.addButton("Keep open", QMessageBox.ButtonRole.RejectRole)
        leave = box.addButton(
            "Close with recovery draft", QMessageBox.ButtonRole.DestructiveRole
        )
        box.setDefaultButton(keep)
        if mode == "unexpected-typed":

            def inspect_and_owner_cleanup():
                assert app.failed
                assert box.isVisible()  # driver MUST NOT dismiss the dialog
                assert app.stage == "failed"
                assert not driver.results["checks"].get("keep_open_choice")
                done["preserved"] = True
                # Harness cleanup, separate from stopped verification driver.
                keep.click()
                self.allow_close = True
                QTimer.singleShot(0, self.close)

            QTimer.singleShot(350, inspect_and_owner_cleanup)
        box.exec()
        observed.append(("unwound", app.stage, box.isVisible()))
        if box.clickedButton() is leave:
            self.allow_close = True
            self.close()


window = Window()
line = QLineEdit("initial synthetic title", window)
window.setCentralWidget(line)
window.page = Page()
window.view = SimpleNamespace(setFocus=line.setFocus, focusProxy=lambda: line)
window.show()
app.window = window
if mode == "filter-scope":
    foreign_target = QObject(app)
    QCoreApplication.sendEvent(foreign_target, QEvent(QEvent.Type.User))
    assert not foreign_observations, "Unrelated QObject reached the close observer"
    app.timer.stop()
    app.transition("finished")
    window.allow_close = True
    QTimer.singleShot(0, window.close)
QTimer.singleShot(6000, app.quit)
app.exec()
if mode == "normal":
    assert done.get("export")
    assert driver.results["checks"]["live_offline_title_verified"] == "PASS"
    assert driver.results["checks"]["keep_open_choice"] == "PASS"
    assert observed[0] == ("close", "first-close")
    assert ("unwound", "keep-open-settling", False) in observed
    assert not app.failed
elif mode == "unexpected-typed":
    assert done.get("preserved")
    assert driver.results["failure_stage"] == "typed"
    assert driver.results["error"] == "Unexpected native dialog at typed"
    assert not any(e["event"] == "driver-close-request" for e in app.trace)
    assert any(
        e["event"] == "qt-close-event" and e["intent"] == "none" for e in app.trace
    )
elif mode == "early-exit":
    assert app.failed and app.shutting_down and app.pending_query is None
    assert driver.results["failure_stage"] == "load"
    assert (
        driver.results["error"] == "Qt event loop exited before verification finished"
    )
    window.allow_close = True
    window.close()  # Harness cleanup after checking the stopped driver.
elif mode == "filter-scope":
    assert not app.failed and not foreign_observations
    assert any(event["event"] == "qt-close-event" for event in app.trace)
else:
    raise ValueError("Unknown probe mode")
print(
    json.dumps(
        {
            "mode": mode,
            "status": "PASS",
            "boundary": "QtWidgets only; no WebEngine or portal",
            "events": app.trace,
        },
        indent=2,
    )
)
