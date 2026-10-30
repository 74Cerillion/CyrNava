"""Test-only native held-upload/layout drill against the installed P2 shell.

Stream this file to Flatpak's Python with `close`, then `restart`. No package
rebuild, production hooks, debug port or host permission changes are needed.
The test temporarily holds the renderer's asset fetch, pastes a synthetic Qt
clipboard image, requests real native closure, checks the panes, then releases
the real authenticated upload. It never reads the owner's clipboard or notes.
"""

import json
import sys
import time
import urllib.request
from unittest.mock import patch

sys.path.insert(0, "/app/share/cyrnava")
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.native import application
from desktop.native.backend import Backend

PHASE = sys.argv[1] if len(sys.argv) == 2 else ""
if PHASE not in ("close", "restart"):
    raise SystemExit("Choose close, then restart")
original_configuration = application.configuration
backend = None
results = {"phase": PHASE, "status": "FAIL", "checks": {}}
note_id = None
before_images = 0


def profile_root():
    return original_configuration().parent / "p2-upload-verification"


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


def images(document):
    return [block for block in document if block["type"] == "image"]


class TestBackend(Backend):
    def start(self):
        global backend, note_id, before_images
        super().start()
        backend = self
        notes = api("/api/tree")["notes"]
        if not notes:
            if PHASE == "restart":
                raise RuntimeError("Run the close phase first")
            note = api(
                "/api/notes",
                {
                    "title": "Synthetic native held upload",
                    "format_version": 1,
                    "document_json": [{"type": "paragraph", "content": []}],
                },
            )
        else:
            note = api("/api/notes/" + notes[0]["id"])
        note_id = note["id"]
        before_images = len(images(note["document_json"]))
        if PHASE == "restart":
            previous = json.loads((profile_root() / "upload-close.json").read_text())
            if previous["status"] != "PASS" or note != previous["saved_note"]:
                raise RuntimeError("Restarted SQLite note differs from the close result")
            results["checks"]["sqlite_document_unchanged_after_restart"] = "PASS"


# This test-only gate delays a real asset fetch; it neither synthesizes an API
# success nor changes credentials, the editor, the native close code or backend.
INSTALL_GATE = """(() => {
  const editor = document.querySelector('[contenteditable="true"]');
  if (!editor || document.querySelector('.save-state')?.dataset.state !== 'Saved') return false;
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar || sidebar.getBoundingClientRect().width === 0) {
    Array.from(document.querySelectorAll('button')).find(b => b.textContent === 'Show navigation')?.click();
    return false;
  }
  if (!window.__p2UploadGate) {
    const original = window.fetch;
    let release;
    const held = new Promise(resolve => { release = resolve; });
    window.__p2UploadGate = { started: false, release };
    window.fetch = async function(input, init) {
      const raw = typeof input === 'string' ? input : input.url || String(input);
      if (new URL(raw, location.href).pathname === '/api/assets' && init?.method === 'POST') {
        window.__p2UploadGate.started = true;
        await held;
      }
      return original.call(this, input, init);
    };
  }
  editor.focus();
  const range = document.createRange(); range.selectNodeContents(editor); range.collapse(false);
  const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
  return true;
})()"""

LAYOUT = """(() => {
  const a = document.querySelector('.sidebar')?.getBoundingClientRect();
  const b = document.querySelector('main')?.getBoundingClientRect();
  return JSON.stringify({
    started: window.__p2UploadGate?.started === true,
    state: window.__cyrnavaDesktop?.state(REQUEST_ID),
    saved: document.querySelector('.save-state')?.dataset.state === 'Saved',
    same_row: !!a && !!b && a.width > 0 && b.width > 0 && Math.abs(a.y - b.y) < 2,
    adjacent: !!a && !!b && Math.abs(a.right - b.x) < 2
  });
})()"""


class VerificationApp(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.window = None
        self.stage = "load"
        self.waiting = False
        self.deadline = time.monotonic() + 75
        self.held_since = None
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.advance)
        self.timer.start()

    def fail(self, message):
        results["error"] = message
        self.timer.stop()
        if self.window:
            self.window.allow_close = True
            self.window.close()
        else:
            self.quit()

    def advance(self):
        try:
            self.check()
        except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
            self.fail(type(error).__name__ + ": " + str(error))

    def check(self):
        if time.monotonic() > self.deadline:
            self.fail("Timed out at " + self.stage)
            return
        for dialog in self.topLevelWidgets():
            if isinstance(dialog, QMessageBox):
                dialog.reject()
                self.fail("Unexpected native dialog at " + self.stage)
                return
        if self.waiting:
            return
        if self.window is None:
            self.window = next(
                (w for w in self.topLevelWidgets() if hasattr(w, "request_id")), None
            )
        if self.window is None or not self.window.loaded or self.stage == "released":
            return
        self.waiting = True
        stage = self.stage

        def checked(value):
            self.waiting = False
            if stage != self.stage:
                return
            try:
                self.received(stage, value)
            except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                self.fail(type(error).__name__ + ": " + str(error))

        if self.stage == "load":
            if PHASE == "restart":
                script = """(() => {
                  const images = Array.from(document.querySelectorAll('.editor img'));
                  return document.querySelector('.save-state')?.dataset.state === 'Saved'
                    && images.length === IMAGE_COUNT
                    && images.every(img => img.complete && img.naturalWidth > 0);
                })()""".replace("IMAGE_COUNT", str(before_images))
            else:
                script = INSTALL_GATE
        elif self.stage == "paste":
            script = "window.__p2UploadGate?.started === true"
        else:
            script = LAYOUT.replace("REQUEST_ID", json.dumps(self.window.request_id))
        self.window.page.runJavaScript(script, checked)

    def received(self, stage, value):
        if not value:
            return
        if stage == "load" and PHASE == "restart":
            results["checks"]["persisted_images_render_after_restart"] = "PASS"
            self.stage = "released"
            self.timer.stop()
            self.window.close()
        elif stage == "load":
            self.window.activateWindow()
            self.window.view.setFocus()
            image = QImage(96, 64, QImage.Format.Format_RGB32)
            image.fill(Qt.GlobalColor.cyan)
            self.clipboard().setImage(image)
            # Refocus after the native activation, then send a real Qt Ctrl+V.
            self.stage = "paste"
            self.window.page.runJavaScript(
                "document.querySelector('[contenteditable=\"true\"]').focus()",
                lambda _value: QTest.keyClick(
                    self.window.view.focusProxy() or self.window.view,
                    Qt.Key.Key_V,
                    Qt.KeyboardModifier.ControlModifier,
                ),
            )
        elif stage == "paste":
            results["checks"]["qt_clipboard_paste_reaches_real_upload"] = "PASS"
            self.stage = "held-close"
            self.held_since = time.monotonic()
            self.window.close()
        elif stage == "held-close":
            state = json.loads(value)
            if not (
                state["started"] and state["state"] == "waiting"
                and not state["saved"] and state["same_row"] and state["adjacent"]
                and self.window.isVisible() and backend.child.poll() is None
            ):
                self.fail("Held native close/layout invariant failed: " + value)
                return
            if time.monotonic() - self.held_since < 2:
                return
            results["checks"]["native_close_waits_without_false_saved"] = "PASS"
            results["checks"]["two_panes_keep_their_positions_while_closing"] = "PASS"
            self.window.grab().save(str(profile_root() / "held-close.png"))
            self.stage = "released"
            self.window.page.runJavaScript("window.__p2UploadGate.release()")


with (
    patch.object(application, "configuration", profile_root),
    patch.object(application, "Backend", TestBackend),
    patch("PySide6.QtWidgets.QApplication", VerificationApp),
):
    code = application.run()

if backend and backend.child and backend.child.poll() is not None:
    results["checks"]["owned_backend_reaped"] = "PASS"
    sys.path.insert(0, "/app/share/cyrnava/backend")
    from app.database import Database

    database = Database(backend.profile.database)
    note = database.get(note_id)
    if PHASE == "close":
        saved_images = images(note["document_json"])
        if len(saved_images) == before_images + 1 and all(
            block.get("props", {}).get("url", "").startswith("/api/assets/")
            for block in saved_images
        ):
            results["checks"]["released_upload_committed_to_sqlite_before_exit"] = "PASS"
            results["saved_note"] = note

required = (
    (
        "qt_clipboard_paste_reaches_real_upload",
        "native_close_waits_without_false_saved",
        "two_panes_keep_their_positions_while_closing",
        "released_upload_committed_to_sqlite_before_exit",
    )
    if PHASE == "close"
    else ("sqlite_document_unchanged_after_restart", "persisted_images_render_after_restart")
)
if code == 0 and "error" not in results and all(
    results["checks"].get(key) == "PASS" for key in (*required, "owned_backend_reaped")
):
    results["status"] = "PASS"
(profile_root() / f"upload-{PHASE}.json").write_text(json.dumps(results, indent=2) + "\n")
# Keep the synthetic document in its private evidence file, not terminal logs.
print(json.dumps({key: value for key, value in results.items() if key != "saved_note"}, indent=2))
raise SystemExit(0 if results["status"] == "PASS" else 1)
