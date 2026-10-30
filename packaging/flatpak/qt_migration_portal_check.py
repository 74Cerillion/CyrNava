"""Qt event-delivery regression; simulated DBus replies, no native portal PASS."""

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from PySide6.QtCore import QTimer
from PySide6.QtDBus import QDBusMessage, QDBusPendingCall, QDBusVariant
from PySide6.QtWidgets import QApplication

spec = importlib.util.spec_from_file_location(
    "p3_native_verify", Path(__file__).with_name("verify_migration.py")
)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
app = QApplication(["P3 portal readiness regression"])


class Bus:
    def __init__(self, reply):
        self.reply = reply

    def asyncCall(self, message, timeout):
        assert message.arguments() == ["org.freedesktop.portal.FileChooser", "version"]
        assert timeout == 10000
        return QDBusPendingCall.fromCompletedCall(self.reply)


request = QDBusMessage.createMethodCall("org.test", "/", "org.test", "Probe")


def reply_with(values):
    reply = request.createReply()
    reply.setArguments(values)
    return reply


delivered = []
QTimer.singleShot(0, lambda: delivered.append(True))
assert (
    helper.wait_for_file_portal(app, connection=Bus(reply_with([QDBusVariant(4)]))) == 4
)
assert delivered, "Theme callback must be delivered before first chooser construction"
for reply in (
    request.createErrorReply("org.test.Unavailable", "synthetic"),
    reply_with([QDBusVariant(0)]),
    reply_with([]),
):
    try:
        helper.wait_for_file_portal(app, connection=Bus(reply))
    except ValueError:
        pass
    else:
        raise AssertionError("Unavailable portal accepted")

for selected in (
    "/home/test/workspace.cyrnava",
    "relative.cyrnava",
    "/tmp/test.cyrnava",
    f"/run/user/{os.getuid()}/doc",
    f"/run/user/{os.getuid()}/doc/id/../bad",
):
    try:
        helper.require_document_grant(selected)
    except ValueError:
        pass
    else:
        raise AssertionError("Sandbox-only or invalid destination accepted")
helper.require_document_grant(f"/run/user/{os.getuid()}/doc/grant/test.cyrnava")
print(
    "PASS: Qt pending theme callback delivered; unavailable portal and ephemeral sandbox outputs rejected. DBus replies simulated; real portal NOT TESTED.",
    flush=True,
)

# A clean window close must not stand in for a saved title/screenshot edit.
import tempfile

with tempfile.TemporaryDirectory(prefix="p3-owner-edit-check-") as tmp:
    root = Path(tmp)
    helper.dataset(root / "unedited", 2)
    assert helper.owner_edit_checks(root / "unedited") == {
        "owner_title_saved": "FAIL",
        "additional_image_saved": "FAIL",
    }
    db = helper.dataset(root / "edited", 3)
    with db.connect() as connection:
        connection.execute(
            "UPDATE notes SET title=? WHERE id=(SELECT id FROM notes LIMIT 1)",
            ("P3 owner edit",),
        )
    assert set(helper.owner_edit_checks(root / "edited").values()) == {"PASS"}
print(
    "PASS: unedited fixture rejected; required saved title and additional image detected.",
    flush=True,
)
