"""P3 host-only synthetic native acceptance; run through host supervisor."""

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path[:0] = ["/app/share/cyrnava", "/app/share/cyrnava/backend"]
from app.backup import BackupError
from app.migration import (
    content_fingerprint,
    durable_json,
    inspect,
    migrate,
    pack,
)
from app.migration_benchmark import dataset

from desktop.native.application import configuration
from desktop.native.storage import Profile


def wait_for_file_portal(app, *, connection=None, timeout_ms=10000):
    """Drain Qt's asynchronous theme probe before constructing the first chooser.

    Qt 6.11 creates a fallback dialog while its portal-version query is pending.
    A second query on the same bus plus event delivery provides a bounded barrier.
    Never fall back to sandbox HOME and call that a host export.
    """
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtDBus import (
        QDBusConnection,
        QDBusMessage,
        QDBusPendingCallWatcher,
    )

    bus = connection or QDBusConnection.sessionBus()
    message = QDBusMessage.createMethodCall(
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.DBus.Properties",
        "Get",
    )
    message.setArguments(["org.freedesktop.portal.FileChooser", "version"])
    watcher = QDBusPendingCallWatcher(bus.asyncCall(message, timeout_ms))
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    watcher.finished.connect(loop.quit)
    if not watcher.isFinished():
        timer.start(timeout_ms)
        loop.exec()
    timer.stop()
    # Deliver the platform theme's earlier pending query callback as well.
    app.processEvents()
    if not watcher.isFinished() or watcher.isError():
        raise ValueError("File portal unavailable; no sandbox fallback allowed")
    values = watcher.reply().arguments()
    version = values[0] if values else None
    if hasattr(version, "variant"):
        version = version.variant()
    if type(version) is not int or version < 1:
        raise ValueError("File portal version unavailable")
    return version


def require_document_grant(selected):
    """P3 host-export gate: reject ephemeral sandbox HOME lookalikes."""
    path = Path(selected)
    prefix = Path("/run/user") / str(os.getuid()) / "doc"
    if ".." in path.parts or not path.is_absolute() or not path.is_relative_to(prefix):
        raise ValueError("Host export requires a document portal grant")
    if len(path.relative_to(prefix).parts) < 2:
        raise ValueError("Host export requires a granted file")


def owner_edit_checks(directory):
    """Inspect saved synthetic edits without exposing titles or note contents."""
    import sqlite3
    from contextlib import closing

    summary = inspect(directory)
    uri = (directory / "engage.sqlite3").as_uri() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        title = connection.execute(
            "SELECT 1 FROM notes WHERE title=? LIMIT 1", ("P3 owner edit",)
        ).fetchone()
    return {
        "owner_title_saved": "PASS" if title else "FAIL",
        "additional_image_saved": "PASS"
        if summary["counts"]["assets"] >= 3
        else "FAIL",
    }


def files(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def main():
    phase, run_id = sys.argv[1:]
    import re

    if not re.fullmatch(r"run-[0-9a-f]{12}", run_id):
        raise ValueError("Invalid synthetic run ID")
    configuration()  # Real P2 sandbox/identity/security checks, never bypassed.
    root = (
        Path.home() / ".var/app/org.cyrnava.CyrNava.Devel/data/p3-verification" / run_id
    )
    if phase == "prepare":
        root.mkdir(mode=0o700, parents=True, exist_ok=False)
    elif not root.is_dir():
        raise ValueError("Synthetic run missing")
    result = {"phase": phase, "status": "FAIL", "complete": False, "checks": {}}
    evidence = root / (phase + ".json")
    durable_json(evidence, result)
    try:
        if phase == "prepare":
            legacy = root / "legacy"
            db = dataset(legacy, 2)
            # Exercise the supported legacy schema 4 -> 5 migration.
            with db.connect() as con:
                for name in (
                    "note_search_insert",
                    "note_search_update",
                    "note_search_delete",
                ):
                    con.execute(f"DROP TRIGGER {name}")
                con.execute("DROP TABLE note_search")
                con.execute("DROP TABLE note_search_documents")
                con.execute("PRAGMA user_version=4")
            durable_json(root / "source-fingerprint.json", files(legacy))
            durable_json(root / "content.json", {"hash": content_fingerprint(legacy)})
            pack(legacy, root / "legacy.cyrnava")
            from PySide6.QtWidgets import QApplication, QFileDialog

            app = QApplication(["P3 synthetic backup"])
            result["stage"] = "waiting_for_file_portal"
            durable_json(evidence, result)
            result["file_portal_version"] = wait_for_file_portal(app)
            result["stage"] = "native_save_dialog"
            durable_json(evidence, result)
            print(
                "The first window is the native SAVE FILE dialog. Keep the suggested "
                "filename, choose Downloads (Other Locations or Ctrl+L if needed), "
                "and click Save at the top right. Save becomes available when a "
                "filename is present. Migration prompts appear in the NEXT phase.",
                flush=True,
            )
            chosen, _ = QFileDialog.getSaveFileName(
                None,
                "Save synthetic P3 backup",
                "cyrnava-p3-synthetic-" + run_id + ".cyrnava",
                "CyrNava backup (*.cyrnava)",
            )
            if not chosen:
                result["reason"] = "native_save_cancelled"
                raise ValueError("Save cancelled")
            require_document_grant(chosen)
            result["checks"]["document_portal_destination"] = "PASS"
            result["stage"] = "export_and_readback"
            durable_json(evidence, result)
            # Explicit selected portal file, no permission to its siblings.
            from desktop.native.maintenance_io import export_selected

            export_selected(root / "legacy.cyrnava", Path(chosen), root)
            result["checks"]["real_backup_export_and_readback"] = "PASS"
            app.quit()
        elif phase == "import":
            from PySide6.QtWidgets import QApplication

            from desktop.native.maintenance import manage

            app = QApplication(["P3 synthetic migration"])
            manage(app, root / "desktop")
            profile = Profile(root / "desktop")
            try:
                assert profile.selection.startswith("workspaces/")
                assert inspect(profile.data)["schema"] == 5
                assert (
                    content_fingerprint(profile.data)
                    == json.loads((root / "content.json").read_text())["hash"]
                )
            finally:
                profile.close()
            assert files(root / "legacy") == json.loads(
                (root / "source-fingerprint.json").read_text()
            )
            result["checks"].update(
                real_native_import="PASS",
                schema_upgrade="PASS",
                source_unchanged="PASS",
                database_and_images_preserved="PASS",
            )
        elif phase in ("edit", "restart"):
            from desktop.native import application

            application.configuration = lambda: root / "desktop"
            assert application.run() == 0
            result["checks"]["native_application_closed"] = "PASS"
            result["stage"] = "checking_saved_owner_edits"
            result["checks"].update(
                owner_edit_checks(
                    root
                    / "desktop"
                    / json.loads((root / "desktop/active-workspace.json").read_text())[
                        "workspace"
                    ]
                )
            )
            if any(value != "PASS" for value in result["checks"].values()):
                result["reason"] = "required_title_or_screenshot_not_saved"
                raise ValueError("Required synthetic edits missing")
        elif phase == "verify":
            profile = Profile(root / "desktop")
            try:
                result["stage"] = "checking_saved_owner_edits"
                result["checks"].update(owner_edit_checks(profile.data))
                if any(value != "PASS" for value in result["checks"].values()):
                    result["reason"] = "required_title_or_screenshot_not_saved"
                    raise ValueError("Required synthetic edits missing")
                assert files(root / "legacy") == json.loads(
                    (root / "source-fingerprint.json").read_text()
                )
                # Restart the actual authenticated backend and confirm owned cleanup.
                from desktop.native.backend import Backend

                backend = Backend(profile)
                try:
                    backend.start()
                finally:
                    backend.stop()
                assert backend.child.poll() is not None
                before = files(profile.data)
                selected = profile.selection
                backup = root / "post-edit.cyrnava"
                pack(profile.data, backup)
                damaged = root / "invalid.cyrnava"
                damaged.write_bytes(b"not a backup")
                failed = profile.root / "workspaces" / ("f" * 32)
                try:
                    migrate(damaged, failed)
                except BackupError:
                    result["checks"]["invalid_backup_rejected"] = "PASS"
                else:
                    raise AssertionError("Invalid restore accepted")
                assert not failed.exists() and files(profile.data) == before
                recovery = "workspaces/" + ("e" * 32)
                migrate(backup, profile.root / recovery)
                profile.activate_workspace(recovery)
                assert content_fingerprint(profile.data) == content_fingerprint(
                    profile.root / selected
                )
                profile.activate_workspace(selected)
                result["checks"].update(
                    saved_edit_and_screenshot_after_restart="PASS",
                    source_unchanged="PASS",
                    backend_restart_and_reaping="PASS",
                    invalid_restore_preserves_active="PASS",
                    verified_restore_and_rollback="PASS",
                )
            finally:
                profile.close()
        else:
            raise ValueError("Unknown phase")
        result.update(status="PASS", complete=True)
    except Exception:  # noqa: BLE001 - retain redacted final evidence
        result.update(
            status="FAIL",
            complete=True,
            error="Verification failed or was cancelled; preserve this synthetic run for diagnosis.",
        )
    finally:
        durable_json(evidence, result)
        print(json.dumps(result), flush=True)
        print("Evidence: " + str(evidence), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
