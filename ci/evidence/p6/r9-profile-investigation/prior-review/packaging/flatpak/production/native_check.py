"""Host-streamed P4 checks. Never shipped or used by the production entry point."""

import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path[:0] = ["/app/share/cyrnava", "/app/share/cyrnava/backend"]
from app.database import Database
from app.migration import durable_json, inspect, migrate, pack
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.native import application
from desktop.native.backend import Backend
from desktop.native.storage import APP_ID, Profile


def processes():
    result = []
    for path in Path("/proc").glob("[0-9]*/status"):
        try:
            status = dict(
                line.split(":", 1)
                for line in path.read_text().splitlines()
                if ":" in line
            )
            if path.parent.name != str(
                os.getpid()
            ) and "QtWebEngineProc" not in status.get("Name", ""):
                continue
            result.append(
                {
                    "pid": int(path.parent.name),
                    "renderer": b"--type=renderer"
                    in (path.parent / "cmdline").read_bytes(),
                    "status": {
                        key: status.get(key, "").strip()
                        for key in ("NoNewPrivs", "Seccomp", "Seccomp_filters", "VmRSS")
                    },
                    "namespaces": {
                        key: os.readlink(path.parent / "ns" / key)
                        for key in ("user", "pid", "net", "mnt")
                    },
                }
            )
        except (OSError, ValueError):
            continue
    return result


def owner_edit_state(profile):
    # Only booleans/count-derived checks leave this synthetic profile.
    import sqlite3
    from contextlib import closing

    uri = profile.database.as_uri() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        title = connection.execute(
            "SELECT 1 FROM notes WHERE title=?", ("P4 owner edit",)
        ).fetchone()
    summary = inspect(profile.data)
    return {
        "required_title_saved": "PASS" if title else "FAIL",
        "screenshot_asset_saved": "PASS"
        if summary["counts"]["assets"] >= 1
        else "FAIL",
        "folder_saved": "PASS" if summary["counts"]["folders"] >= 1 else "FAIL",
    }


def saved_edit(profile):
    return all(value == "PASS" for value in owner_edit_state(profile).values())


def maintenance_state(selection_changed, content_preserved, edits_preserved):
    return {
        "import_activated_new_workspace": "PASS" if selection_changed else "FAIL",
        "import_preserved_records": "PASS" if content_preserved else "FAIL",
        "import_preserved_owner_edits": "PASS" if edits_preserved else "FAIL",
    }


def preference_state(value):
    # Qt WebEngine callbacks reliably deliver strings. Do not depend on automatic
    # QVariantMap conversion for JavaScript objects.
    try:
        preferences = json.loads(value) if isinstance(value, str) else None
    except ValueError:
        preferences = None
    if not isinstance(preferences, dict):
        return {"dark_preference_saved": "FAIL"}, None
    digest = hashlib.sha256(
        json.dumps(preferences, sort_keys=True).encode()
    ).hexdigest()
    return {
        "dark_preference_saved": "PASS"
        if preferences.get("appearance") == "dark"
        else "FAIL"
    }, digest


def main():
    phase, run_id, host_net, canary = sys.argv[1:]
    import re

    if phase not in (
        "edit",
        "restart",
        "updated",
        "rollback",
        "recovery",
        "maintenance",
    ) or not re.fullmatch(r"run-[0-9a-f]{12}", run_id):
        raise ValueError("Invalid P4 synthetic test arguments")
    base = application.configuration().parent / "p4-verification" / run_id
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    profile_root = base / "desktop"
    result = {
        "phase": phase,
        "status": "FAIL",
        "complete": False,
        "checks": {},
        "timings_ms": {},
    }
    record = base / (phase + ".json")
    durable_json(record, result)
    started = time.monotonic()
    owned = None
    try:
        assert APP_ID == "io.github._74Cerillion.CyrNava"
        assert os.readlink("/proc/self/ns/net") != host_net
        assert not Path(canary).exists()
        result["checks"]["production_identity_private_network_and_filesystem"] = "PASS"
        if phase == "maintenance":
            from app.migration import content_fingerprint

            from desktop.native.maintenance import manage

            profile = Profile(profile_root)
            old_selection, old_content = (
                profile.selection,
                content_fingerprint(profile.data),
            )
            profile.close()
            app = QApplication(["CyrNava native backup and import test"])
            result["stage"] = "awaiting_native_backup_and_import"
            durable_json(record, result)
            manage(app, profile_root)
            profile = Profile(profile_root)
            try:
                result["stage"] = "validating_imported_workspace"
                result["checks"].update(
                    maintenance_state(
                        profile.selection != old_selection,
                        content_fingerprint(profile.data) == old_content,
                        saved_edit(profile),
                    )
                )
                missing = [
                    name
                    for name, status in result["checks"].items()
                    if status != "PASS"
                ]
                if missing:
                    result["missing_checks"] = missing
                    raise AssertionError("Native backup/import incomplete")
                result["checks"]["real_native_backup_export_and_import"] = "PASS"
            finally:
                profile.close()
        elif phase == "recovery":
            profile = Profile(profile_root)
            try:
                assert saved_edit(profile)
                original = profile.selection
                before = hashlib.sha256(profile.database.read_bytes()).hexdigest()
                backup = base / "verified.cyrnava"
                pack(profile.data, backup)
                restored = "workspaces/" + "b" * 32
                migrate(backup, profile.root / restored)
                profile.activate_workspace(restored)
                assert saved_edit(profile)
                # Safely test incompatible schema refusal on a disposable restored copy.
                db = Database(profile.database)
                with db.connect() as connection:
                    connection.execute("PRAGMA user_version=6")
                newer = hashlib.sha256(profile.database.read_bytes()).hexdigest()
                try:
                    db.initialize()
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Future schema accepted")
                assert (
                    newer == hashlib.sha256(profile.database.read_bytes()).hexdigest()
                )
                profile.activate_workspace(original)
                assert (
                    before == hashlib.sha256(profile.database.read_bytes()).hexdigest()
                )
                result["checks"].update(
                    verified_backup_restore="PASS",
                    incompatible_schema_refused_unchanged="PASS",
                    previous_profile_recovered="PASS",
                )
            finally:
                profile.close()
        else:

            class MeasuredBackend(Backend):
                def start(self):
                    nonlocal owned
                    then = time.monotonic()
                    super().start()
                    owned = self
                    result["timings_ms"]["backend_ready"] = round(
                        (time.monotonic() - then) * 1000, 1
                    )
                    result["backend_pid"] = self.child.pid
                    result["backend_origin"] = self.origin
                    assert self.origin.startswith("http://127.0.0.1:")
                    try:
                        duplicate = Profile(profile_root)
                    except BlockingIOError:
                        result["checks"]["single_instance_lock"] = "PASS"
                    else:
                        duplicate.close()
                        raise AssertionError("Duplicate profile lock accepted")
                    # Unauthenticated and foreign-Origin requests must fail.
                    for headers, expected in (
                        ({}, 401),
                        (
                            {
                                "X-CyrNava-Session": self.token,
                                "Origin": "https://invalid.example",
                            },
                            403,
                        ),
                    ):
                        request = urllib.request.Request(
                            self.origin + "/api/tree", headers=headers
                        )
                        try:
                            urllib.request.build_opener(
                                urllib.request.ProxyHandler({})
                            ).open(request, timeout=4)
                        except urllib.error.HTTPError as error:
                            assert error.code == expected
                        else:
                            raise AssertionError("API security check accepted")
                    result["checks"]["backend_authentication_and_origin"] = "PASS"
                    # Seed only this new synthetic profile, never the real launcher root.
                    if phase == "edit":
                        tree_request = urllib.request.Request(
                            self.origin + "/api/tree",
                            headers={
                                "X-CyrNava-Session": self.token,
                                "Origin": self.origin,
                            },
                        )
                        with urllib.request.build_opener(
                            urllib.request.ProxyHandler({})
                        ).open(tree_request, timeout=4) as response:
                            tree = json.load(response)
                        if tree["notes"]:
                            return  # Resume preserves the existing synthetic work.
                        request = urllib.request.Request(
                            self.origin + "/api/notes",
                            data=json.dumps(
                                {
                                    "title": "P4 synthetic note",
                                    "format_version": 1,
                                    "document_json": [
                                        {"type": "paragraph", "content": []}
                                    ],
                                }
                            ).encode(),
                            headers={
                                "X-CyrNava-Session": self.token,
                                "Origin": self.origin,
                                "Content-Type": "application/json",
                            },
                        )
                        urllib.request.build_opener(
                            urllib.request.ProxyHandler({})
                        ).open(request, timeout=4).close()

                def stop(self):
                    running = self.child and self.child.poll() is None
                    then = time.monotonic()
                    super().stop()
                    if running:
                        result["timings_ms"]["backend_shutdown"] = round(
                            (time.monotonic() - then) * 1000, 1
                        )

            class ProbeApp(QApplication):
                def __init__(self, args):
                    super().__init__(args)
                    self.sampled = False
                    self.timer = QTimer(self)
                    self.timer.timeout.connect(self.observe)
                    self.timer.start(200)

                def observe(self):
                    window = next(
                        (
                            w
                            for w in self.topLevelWidgets()
                            if hasattr(w, "request_id")
                            and hasattr(w, "loaded")
                            and w.loaded
                        ),
                        None,
                    )
                    if window is None:
                        return

                    def preference(value):
                        checks, digest = preference_state(value)
                        if digest:
                            result["checks"].update(checks)
                            result["preferences_sha256"] = digest
                        # A callback cancelled during normal WebEngine teardown
                        # must not erase the last valid preference sample.

                    window.page.runJavaScript(
                        "JSON.stringify({appearance:localStorage.getItem('engage.appearance.v1'),theme:localStorage.getItem('cyrnava.theme.v1')})",
                        preference,
                    )
                    if self.sampled:
                        return
                    self.sampled = True
                    if phase == "edit":
                        QTimer.singleShot(
                            0,
                            lambda: QMessageBox.information(
                                window,
                                "P4 synthetic verification — complete before closing",
                                "Keep this window open while completing these steps:\n\n"
                                "1. Set the NOTE TITLE field to exactly: P4 owner edit\n"
                                "2. Create a folder if you have not already.\n"
                                "3. Add bold text and paste a screenshot into the note body.\n"
                                "4. Set Appearance to Dark.\n"
                                "5. Wait for Saved and completed uploads, then close.\n\n"
                                "Existing synthetic work is retained when resuming.",
                            ),
                        )
                    result["timings_ms"]["frontend_loaded"] = round(
                        (time.monotonic() - started) * 1000, 1
                    )
                    result["checks"]["production_window_title"] = (
                        "PASS" if window.windowTitle() == "CyrNava" else "FAIL"
                    )
                    self.diagnostic_profile = QWebEngineProfile(self)
                    self.diagnostic = QWebEnginePage(self.diagnostic_profile, self)

                    def loaded(ok):
                        if not ok:
                            result["checks"]["renderer_sandbox"] = "FAIL"
                            return

                        def observed(text):
                            samples = processes()
                            gui = next(
                                (p for p in samples if p["pid"] == os.getpid()), None
                            )
                            renderers = [p for p in samples if p["renderer"]]
                            valid = (
                                gui
                                and renderers
                                and all(
                                    p["status"]["NoNewPrivs"] == "1"
                                    and p["status"]["Seccomp"] == "2"
                                    and int(p["status"]["Seccomp_filters"]) >= 2
                                    and p["namespaces"]["pid"]
                                    != gui["namespaces"]["pid"]
                                    and p["namespaces"]["net"]
                                    != gui["namespaces"]["net"]
                                    for p in renderers
                                )
                            )
                            result["sandbox_diagnostic"] = text
                            result["processes"] = samples
                            result["checks"]["renderer_sandbox"] = (
                                "PASS"
                                if valid
                                and "adequately sandboxed" in text
                                and "Flatpak" in text
                                else "FAIL"
                            )

                            def cleanup():
                                from shiboken6 import delete

                                delete(self.diagnostic)
                                delete(self.diagnostic_profile)

                            QTimer.singleShot(0, cleanup)

                        self.diagnostic.toPlainText(observed)

                    self.diagnostic.loadFinished.connect(loaded)
                    self.diagnostic.setUrl(QUrl("chrome://sandbox"))

            with (
                patch.object(application, "configuration", lambda: profile_root),
                patch.object(application, "Backend", MeasuredBackend),
                patch("PySide6.QtWidgets.QApplication", ProbeApp),
            ):
                assert application.run() == 0
            result["checks"]["owned_backend_reaped"] = (
                "PASS" if owned and owned.child.poll() is not None else "FAIL"
            )
            profile = Profile(profile_root)
            try:
                result["stage"] = "saved_owner_edit_checks"
                result["checks"].update(owner_edit_state(profile))
                missing = [
                    name
                    for name in (
                        "required_title_saved",
                        "screenshot_asset_saved",
                        "folder_saved",
                        "dark_preference_saved",
                    )
                    if result["checks"].get(name) != "PASS"
                ]
                if missing:
                    result["missing_checks"] = missing
                    raise AssertionError("Required synthetic edits incomplete")
                result["checks"]["saved_title_and_screenshot"] = "PASS"
            finally:
                profile.close()
            assert result["checks"].get("renderer_sandbox") == "PASS"
        if not result["checks"] or any(v != "PASS" for v in result["checks"].values()):
            raise AssertionError("Incomplete P4 checks")
        result.update(status="PASS", complete=True)
    except Exception as error:  # noqa: BLE001 - retain redacted final host evidence
        result.update(
            status="FAIL",
            complete=True,
            error_type=type(error).__name__,
            error="P4 synthetic check failed; preserve the run and phase for diagnosis.",
        )
    finally:
        if owned:
            owned.stop()
        durable_json(record, result)
        print(json.dumps(result, indent=2), flush=True)
        print("Evidence: " + str(record), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
