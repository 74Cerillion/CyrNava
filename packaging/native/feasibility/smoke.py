"""One bounded offscreen renderer probe. Supplementary, never a Wayland/N1 PASS."""

import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1]).absolute()
output = root / "headless-render.json"
if output.exists():
    raise SystemExit("Preserve existing headless result")
if any(
    os.environ.get(k)
    for k in [
        "QTWEBENGINE_DISABLE_SANDBOX",
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "QTWEBENGINE_REMOTE_DEBUGGING",
    ]
):
    raise SystemExit("Unsafe sandbox/debug override refused")
# No owner-desktop connection/window. This is a confined supplementary experiment.
os.environ["QT_QPA_PLATFORM"] = "offscreen"
for key, value in [
    ("XDG_DATA_HOME", "data"),
    ("XDG_CONFIG_HOME", "config"),
    ("XDG_CACHE_HOME", "cache"),
]:
    os.environ[key] = str(root / "client" / value)
from PySide6.QtCore import QTimer, QUrl  # noqa: E402
from PySide6.QtWebEngineCore import QWebEnginePage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

record = {
    "status": "FAIL",
    "complete": False,
    "scope": "offscreen-supplementary",
    "Wayland": "NOT EXECUTED",
    "normal_launcher": "NOT EXECUTED",
}
app = QApplication(["CyrNava N1 bounded headless probe"])
page = QWebEnginePage()


def finish():
    record["complete"] = True
    output.write_text(json.dumps(record, indent=2) + "\n")
    app.quit()


def loaded(ok):
    if not ok:
        finish()
        return

    def seen(value):
        record["rendered"] = value == "N1 local rendering"
        record["renderer_pid"] = page.renderProcessPid()
        record["status"] = "CONTENT_RENDERED" if record["rendered"] else "FAIL"
        finish()

    page.runJavaScript("document.body.innerText", seen)


page.loadFinished.connect(loaded)
QTimer.singleShot(15000, finish)
page.setHtml("<html><body>N1 local rendering</body></html>", QUrl("about:blank"))
app.exec()
page.deleteLater()
raise SystemExit(0 if record["status"] == "CONTENT_RENDERED" else 1)
