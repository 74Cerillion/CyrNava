"""Explicit offline backup/import UI. Only native file dialogs grant host access."""

import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from .backend import SOURCE
from .dialogs import choose_backup_destination, choose_backup_source
from .storage import Profile


def manage(app, root):
    # Import backend domain code, never create a backend listener or JS bridge.
    sys.path.insert(0, str(SOURCE / "backend"))
    from app.migration import inspect, migrate, pack, regular, unpack
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import (
        QDialog,
        QFileDialog,
        QInputDialog,
        QLabel,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
    )

    class Job(QThread):
        progress = Signal(str)
        finished_work = Signal(bool, str, object)

        def __init__(self, operation, parent):
            super().__init__(parent)
            self.operation = operation

        def run(self):
            try:
                result = self.operation(self.progress.emit)
            except Exception:  # noqa: BLE001 - redact untrusted data in UI
                # Raw SQLite/OS exceptions can include paths or note contents.
                self.finished_work.emit(
                    False,
                    "Operation failed. Source data was preserved. Check storage, "
                    "close other instances, and use a valid supported backup. "
                    "Incomplete migration stages remain quarantined for recovery.",
                    None,
                )
            else:
                self.finished_work.emit(
                    True,
                    "Completed and verified. Close this manager and launch CyrNava.",
                    result,
                )

    class Manager(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("CyrNava — Backup and recovery")
            self.resize(620, 320)
            self.job = None
            self.profile = Profile(root, recovery=True)
            self.layout = QVBoxLayout(self)
            self.label = QLabel(
                "Offline maintenance. Backups contain unencrypted notes and images. Browser preferences, recovery drafts, and unfinished uploads are excluded; export drafts and finish saving in the old application first."
            )
            if self.profile.pointer_error:
                self.label.setText(
                    "Workspace pointer is invalid. Select a previous verified workspace or import a backup. No pointer has been changed."
                )
            self.label.setWordWrap(True)
            self.layout.addWidget(self.label)
            self.bar = QProgressBar()
            self.bar.setRange(0, 1)
            self.layout.addWidget(self.bar)
            self.buttons = []
            for title, callback in [
                ("Create verified backup", self.backup),
                ("Import backup into a new workspace", self.restore),
                ("Use a previous verified workspace", self.recover),
                ("Import an exported recovery draft", self.import_draft),
                ("Prepare backup from a legacy workspace", self.legacy_backup),
                ("Close", self.close),
            ]:
                button = QPushButton(title)
                button.clicked.connect(callback)
                self.layout.addWidget(button)
                self.buttons.append(button)

        def start(self, operation, completed=None):
            self.completed = completed
            for button in self.buttons:
                button.setEnabled(False)
            self.bar.setRange(0, 0)
            self.job = Job(operation, self)
            self.job.progress.connect(self.label.setText)
            self.job.finished_work.connect(self.done_work)
            self.job.start()

        def done_work(self, success, message, result):
            self.job.wait()
            self.job = None
            self.bar.setRange(0, 1)
            self.bar.setValue(int(success))
            self.label.setText(message)
            for button in self.buttons:
                button.setEnabled(True)
            if self.completed:
                callback, self.completed = self.completed, None
                callback(success, result)

        def backup(self):
            chosen = choose_backup_destination(QFileDialog, self)
            if not chosen:
                return

            self.backup_to(self.profile.data, chosen)

        def backup_to(self, source, chosen):
            def operation(progress):
                with tempfile.TemporaryDirectory(dir=self.profile.root) as tmp:
                    archive = Path(tmp) / "workspace.cyrnava"
                    pack(source, archive, progress=progress)
                    from .maintenance_io import export_selected

                    export_selected(archive, Path(chosen), self.profile.root)

            self.start(operation)

        def restore(self):
            chosen = choose_backup_source(QFileDialog, self)
            if not chosen:
                return
            # Validation and summary are explicit before activation. Background work
            # owns all staging; no processEvents reentrancy during filesystem changes.
            self.pending = tempfile.TemporaryDirectory(dir=self.profile.root)
            stage = Path(self.pending.name)

            def preview_operation(progress):
                progress("Copying and validating selected backup…")
                with (
                    regular(Path(chosen), 3 * 1024**3) as src,
                    (stage / "input.cyrnava").open("xb") as out,
                ):
                    copied = 0
                    while chunk := src.read(1024 * 1024):
                        copied += len(chunk)
                        if copied > 3 * 1024**3:
                            raise ValueError("Backup exceeded input limit")
                        out.write(chunk)
                preview = stage / "preview"
                preview.mkdir(mode=0o700)
                return unpack(stage / "input.cyrnava", preview)

            self.start(preview_operation, self.confirm_restore)

        def confirm_restore(self, success, summary):
            if not success:
                self.pending.cleanup()
                return
            stage = Path(self.pending.name)
            counts = summary["counts"]
            answer = QMessageBox.question(
                self,
                "Confirm migration",
                f"Validated schema {summary['schema']}: {counts['folders']} folders, {counts['notes']} notes and {counts['assets']} images. Import into a new workspace? Your current workspace and its drafts will remain preserved.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.pending.cleanup()
                return

            def operation(progress):
                try:
                    from .storage import private_directory

                    generation = uuid4().hex
                    parent = private_directory(self.profile.root / "workspaces")
                    migrate(
                        stage / "input.cyrnava", parent / generation, progress=progress
                    )
                    self.profile.activate_workspace("workspaces/" + generation)
                finally:
                    self.pending.cleanup()

            self.start(operation)

        def legacy_backup(self):
            source = QFileDialog.getExistingDirectory(
                self, "Select legacy workspace or directory backup", ""
            )
            if not source:
                return
            chosen = choose_backup_destination(
                QFileDialog, self, "Save portable backup"
            )
            if not chosen:
                return
            answer = QMessageBox.question(
                self,
                "Confirm legacy backup",
                "Close the old application first. Read and validate the selected source, then create a portable backup? The source will not be changed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            # Same portal-only file writer as native backup, explicit chosen source.
            self.backup_to(Path(source), chosen)

        def import_draft(self):
            chosen, _ = QFileDialog.getOpenFileName(
                self, "Choose exported recovery draft", "", "Recovery JSON (*.json)"
            )
            if not chosen:
                return
            if (
                QMessageBox.question(
                    self,
                    "Confirm draft recovery",
                    "Import a matching saved-revision draft into a new workspace copy? The current workspace is preserved. Conflicting revisions and missing images are rejected.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return

            def operation(progress):
                from app.migration import recover_draft

                from .storage import private_directory

                generation = uuid4().hex
                parent = private_directory(self.profile.root / "workspaces")
                recover_draft(
                    self.profile.data,
                    Path(chosen),
                    parent / generation,
                    parent / ("pre-draft-" + generation + ".cyrnava"),
                    progress=progress,
                )
                self.profile.activate_workspace("workspaces/" + generation)

            self.start(operation)

        def recover(self):
            candidates = ["workspace"]
            parent = self.profile.root / "workspaces"
            if parent.exists():
                candidates += [
                    "workspaces/" + p.name
                    for p in parent.iterdir()
                    if p.is_dir() and len(p.name) == 32
                ]
            candidates = [name for name in candidates if name != self.profile.selection]
            if not candidates:
                self.label.setText("No previous workspace is available.")
                return
            chosen, ok = QInputDialog.getItem(
                self,
                "Choose preserved workspace",
                "Validate and switch to:",
                candidates,
                0,
                False,
            )
            if not ok:
                return
            if (
                QMessageBox.question(
                    self,
                    "Confirm recovery",
                    "Switch only after integrity validation? The current workspace and its browser drafts remain preserved.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return

            def operation(progress):
                progress("Validating preserved workspace…")
                inspect(self.profile.root / chosen)
                self.profile.activate_workspace(chosen)

            self.start(operation)

        def reject(self):
            self.close()

        def closeEvent(self, event):
            if self.job is not None:
                event.ignore()
                return
            self.profile.close()
            event.accept()

    try:
        window = Manager()
    except (OSError, ValueError):
        QMessageBox.warning(
            None, "Profile unavailable", "Close CyrNava before offline maintenance."
        )
        return 1
    window.exec()
    return 0


def run():
    from PySide6.QtWidgets import QApplication

    from .application import configuration

    os.umask(0o077)
    app = QApplication(["CyrNava backup and recovery"])
    return manage(app, configuration())
