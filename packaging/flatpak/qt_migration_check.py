"""Actual QtWidgets workflow probe; mocked chooser selection, never a portal PASS."""

import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from app.database import Database
from app.migration import pack, unpack
from app.migration_benchmark import dataset
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QWidget,
)

from desktop.native.maintenance import manage
from desktop.native.storage import Profile

app = QApplication(["P3 disposable QtWidgets probe"])
with tempfile.TemporaryDirectory(prefix="cyrnava-p3-qt-") as tmp:
    root = Path(tmp)
    source = root / "legacy"
    dataset(source, 2)
    archive = root / "source.cyrnava"
    pack(source, archive)
    native = Profile(root / "desktop")
    Database(native.database).initialize()
    (native.data / "assets").mkdir()
    old = Database(native.database).create(
        "Previous workspace", [{"type": "paragraph", "content": []}], 1
    )
    native.close()
    exported = root / "exported.cyrnava"
    QFileDialog.getOpenFileName = lambda *a, **k: (str(archive), "")
    QFileDialog.getSaveFileName = lambda *a, **k: (str(exported), "")
    QInputDialog.getItem = lambda *a, **k: ("workspace", True)
    QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes
    errors = []
    QMessageBox.warning = lambda *a, **k: errors.append("unexpected-warning")
    state = {"phase": "import", "wait": False, "guard": False, "ticks": 0}

    def tick():
        state["ticks"] += 1
        window = next(
            (
                w
                for w in app.topLevelWidgets()
                if w.windowTitle() == "CyrNava — Backup and recovery"
            ),
            None,
        )
        if window is None:
            return
        if state["ticks"] > 600:
            errors.append("timeout")
            app.exit(1)
            return
        if window.job is not None:
            window.reject()
            assert window.isVisible(), "Escape dismissed an active worker"
            state["guard"] = True
            return
        if state["wait"]:
            if "Completed and verified" not in window.label.text():
                return
            state["wait"] = False
            state["phase"] = {
                "import": "export",
                "export": "recover",
                "recover": "done",
            }[state["phase"]]
        if state["phase"] == "done":
            window.close()
            return
        prefix = {
            "import": "Import backup",
            "export": "Create verified backup",
            "recover": "Use a previous",
        }[state["phase"]]
        button = next(
            b for b in window.findChildren(QPushButton) if b.text().startswith(prefix)
        )
        state["wait"] = True
        button.click()

    # Exercise the real menu lifecycle: main loop ends, then maintenance opens.
    prior = QWidget()
    prior.show()
    QTimer.singleShot(30, prior.close)
    app.exec()
    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(20)
    assert manage(app, root / "desktop") == 0
    timer.stop()
    # First-launch import also returns to a fresh main event loop.
    next_window = QWidget()
    next_window.show()
    started = time.monotonic()
    QTimer.singleShot(100, next_window.close)
    app.exec()
    assert time.monotonic() - started >= 0.07, "Premature post-maintenance exit"
    assert not errors, errors
    assert state["phase"] == "done" and state["guard"], state
    with tempfile.TemporaryDirectory(dir=root) as check:
        assert unpack(exported, Path(check))["counts"]["notes"] == 2
    final = Profile(root / "desktop")
    assert final.selection == "workspace"
    assert Database(final.database).get(old["id"])["title"] == "Previous workspace"
    final.close()
    print(
        "PASS: actual Qt import, confirmed generation activation, export/readback, rollback, worker-close guard. Chooser paths mocked; native portal NOT TESTED."
    )
