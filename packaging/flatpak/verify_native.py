"""Test-only driver for the unpublished P2 Flatpak, never its launch path.

Run phase 1 then phase 2 in a regular Wayland terminal. Uses a separate synthetic
profile, real Qt window and owned backend. No CDP port or privileged JS bridge.
"""

import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, "/app/share/cyrnava")
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtTest import QTest
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.native import application
from desktop.native.backend import Backend

PHASE = int(sys.argv[1]) if len(sys.argv) == 2 else 0
if PHASE not in (1, 2):
    raise SystemExit("Choose verification phase 1 or 2")
original_configuration = application.configuration
backend = None
results = {"phase": PHASE, "checks": {}, "status": "FAIL"}
close_marker = "P2 close " + uuid4().hex[:12] if PHASE == 1 else None


def profile_root():
    # Keep all production permission/environment checks, change only the test root.
    return original_configuration().parent / "p2-verification"


def api(path, body=None, method=None):
    request = urllib.request.Request(
        backend.origin + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "X-CyrNava-Session": backend.token,
            "Origin": backend.origin,
            "Content-Type": "application/json",
        },
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=4) as response:
        return json.load(response)


class TestBackend(Backend):
    def start(self):
        global backend
        super().start()
        backend = self
        tree = api("/api/tree")
        if not tree["notes"]:
            if PHASE == 2:
                raise RuntimeError("Phase 1 data is missing")
            note = api(
                "/api/notes",
                {
                    "title": "Synthetic native verification",
                    "format_version": 1,
                    "document_json": [
                        {
                            "type": "heading",
                            "props": {"level": 1},
                            "content": [
                                {
                                    "type": "text",
                                    "text": "P2 native verification",
                                    "styles": {},
                                }
                            ],
                        },
                        {"type": "paragraph", "content": []},
                    ],
                },
            )
            # Exercise authenticated raw image upload and renderer image retrieval.
            from PIL import Image

            image = io.BytesIO()
            Image.new("RGB", (2, 2), "blue").save(image, format="PNG")
            request = urllib.request.Request(
                self.origin + "/api/assets?note_id=" + note["id"],
                data=image.getvalue(),
                headers={
                    "X-CyrNava-Session": self.token,
                    "Origin": self.origin,
                    "Content-Type": "image/png",
                },
            )
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                request
            ) as response:
                asset = json.load(response)
            document = note["document_json"]
            document.append(
                {
                    "type": "image",
                    "props": {"url": asset["url"], "name": "synthetic.png"},
                }
            )
            document.append({"type": "paragraph", "content": []})
            api(
                "/api/notes/" + note["id"],
                {"revision": note["revision"], "document_json": document},
                "PATCH",
            )


def process_observations():
    observations = []
    for path in Path("/proc").glob("[0-9]*/status"):
        try:
            values = dict(
                line.split(":", 1)
                for line in path.read_text().splitlines()
                if ":" in line
            )
            if "QtWebEngineProc" not in values.get(
                "Name", ""
            ) and path.parent.name != str(os.getpid()):
                continue
            observations.append(
                {
                    "pid": int(path.parent.name),
                    "renderer": b"--type=renderer"
                    in (path.parent / "cmdline").read_bytes(),
                    "status": {
                        key: values.get(key, "").strip()
                        for key in (
                            "Name",
                            "PPid",
                            "NSpid",
                            "NoNewPrivs",
                            "Seccomp",
                            "Seccomp_filters",
                        )
                    },
                    "namespaces": {
                        key: os.readlink(path.parent / "ns" / key)
                        for key in ("user", "pid", "net", "mnt")
                    },
                }
            )
        except (OSError, ValueError):
            continue
    return observations


class VerificationApp(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.stage = "load"
        self.waiting = False
        self.window = None
        self.deadline = time.monotonic() + 60
        self.tick = QTimer(self)
        self.tick.setInterval(100)
        self.tick.timeout.connect(self.advance)
        self.tick.start()
        self.diagnostic_profile = None

    def failure(self, reason):
        results["error"] = reason
        self.tick.stop()
        if self.window:
            self.window.allow_close = True
            self.window.close()
        else:
            self.quit()

    def advance(self):
        if time.monotonic() > self.deadline:
            self.failure("Native verification timed out at " + self.stage)
            return
        # Fail safely rather than leaving an unexpected modal and backend open.
        for widget in self.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.reject()
                self.failure("Unexpected native dialog")
                return
        if self.waiting:
            return
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
        window = self.window
        self.waiting = True

        def checked(value):
            self.waiting = False
            if self.stage == "load":
                if not value:
                    return
                results["checks"]["authenticated_frontend_and_image"] = "PASS"
                if PHASE == 2:
                    self.stage = "restart"
                    return
                self.stage = "typed"
                window.activateWindow()
                window.view.setFocus()
                QTest.keyClicks(
                    window.view.focusProxy() or window.view, "Native pending edit"
                )
                # Request normal closure immediately, without waiting for debounce.
                # SQLite evidence is checked after the real native close path.
                self.stage = "prepare-close"
            elif self.stage == "restart":
                if not value:
                    self.failure(
                        "Native edit or Qt localStorage did not survive restart"
                    )
                    return
                results["checks"]["restart_content_and_preferences"] = "PASS"
                self.stage = "prepare-close"
            elif self.stage == "prepare-close":
                if not value:
                    return  # Native input/renderer IPC can still be settling.
                self.stage = "diagnostic"
                self.sandbox_diagnostic()

        if self.stage == "load":
            script = """(() => {
              const editor=document.querySelector('[contenteditable="true"]');
              const image=document.querySelector('.editor img');
              if (!editor || !image?.complete || !image.naturalWidth) return false;
              const p=editor.querySelector('p:last-of-type') || editor.querySelector('p');
              if (!p) return false;
              editor.focus(); const r=document.createRange(); r.selectNodeContents(p); r.collapse(false);
              const s=window.getSelection(); s.removeAllRanges(); s.addRange(r);
              return true;
            })()"""
        elif self.stage == "restart":
            script = "document.querySelector('.editor')?.textContent.includes('Native pending edit') && localStorage.getItem('engage.navigation-collapsed.v1') === 'true'"
        elif self.stage == "prepare-close":
            script = "(() => { localStorage.setItem('engage.navigation-collapsed.v1','true'); return document.querySelector('.editor')?.textContent.includes('Native pending edit'); })()"
        else:
            self.waiting = False
            return
        window.page.runJavaScript(script, checked)

    def sandbox_diagnostic(self):
        # A separate test-only diagnostic page; production navigation stays closed.
        self.diagnostic_profile = QWebEngineProfile(self)
        self.diagnostic = QWebEnginePage(self.diagnostic_profile, self)

        def loaded(success):
            if not success:
                self.failure("Chromium sandbox diagnostic did not load")
                return

            def text(value):
                results["sandbox_diagnostic"] = value
                results["processes"] = process_observations()
                if "adequately sandboxed" not in value or "Flatpak" not in value:
                    self.failure("Renderer sandbox report requires review")
                    return
                results["checks"]["reported_flatpak_renderer_sandbox"] = "PASS"
                gui = next(
                    (p for p in results["processes"] if p["pid"] == os.getpid()), None
                )
                renderers = [p for p in results["processes"] if p.get("renderer")]
                if (
                    not gui
                    or not renderers
                    or not all(
                        p["status"]["NoNewPrivs"] == "1"
                        and p["status"]["Seccomp"] == "2"
                        and int(p["status"]["Seccomp_filters"]) >= 2
                        and p["namespaces"]["pid"] != gui["namespaces"]["pid"]
                        and p["namespaces"]["net"] != gui["namespaces"]["net"]
                        for p in renderers
                    )
                ):
                    self.failure(
                        "Effective renderer namespace/seccomp evidence requires review"
                    )
                    return
                results["checks"]["renderer_namespaces_seccomp"] = "PASS"

                self.tick.stop()

                def finish_diagnostic():
                    from shiboken6 import delete

                    # Leave the WebEngine callback before deleting its page.
                    # Qt requires pages to die before their profile.
                    delete(self.diagnostic)
                    delete(self.diagnostic_profile)
                    self.stage = "closing"
                    if PHASE == 1:
                        results["close_marker"] = close_marker
                        self.window.activateWindow()
                        self.window.view.setFocus()
                        QTest.keyClicks(
                            self.window.view.focusProxy() or self.window.view,
                            close_marker,
                        )
                    self.window.close()

                QTimer.singleShot(0, finish_diagnostic)

            self.diagnostic.toPlainText(text)

        self.diagnostic.loadFinished.connect(loaded)
        self.diagnostic.setUrl(QUrl("chrome://sandbox"))


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

    tree = Database(backend.profile.database).tree()
    note = Database(backend.profile.database).get(tree["notes"][0]["id"])
    document = json.dumps(note["document_json"])
    expected_marker = (
        close_marker
        if PHASE == 1
        else json.loads((profile_root() / "verification-phase-1.json").read_text()).get(
            "close_marker", "missing phase 1 marker"
        )
    )
    if "Native pending edit" in document and expected_marker in document:
        results["checks"]["native_close_committed_content"] = "PASS"
    else:
        results["error"] = "Normal close did not commit the typed text"
if (
    code == 0
    and "error" not in results
    and results["checks"].get("native_close_committed_content") == "PASS"
):
    results["status"] = "PASS"
path = profile_root() / f"verification-phase-{PHASE}.json"
path.write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
raise SystemExit(0 if results["status"] == "PASS" else 1)
