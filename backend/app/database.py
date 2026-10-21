"""SQLite lifecycle and note operations. No HTTP or editor dependencies."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class NoteNotFound(Exception):
    pass


class RevisionConflict(Exception):
    pass


def default_database_path() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME", "")
    # XDG requires absolute paths; ignore a relative environment value.
    base = (
        Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / ".local/share"
    )
    path = (base / "engage/engage.sqlite3").resolve()
    repository = Path(__file__).resolve().parents[2]
    if path.is_relative_to(repository):
        raise ValueError("XDG_DATA_HOME must put ENGAGE data outside the repository")
    return path


class Database:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            # Commit on success, roll back on failure, and always close.
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Exclusive creation avoids truncating an existing database.
        descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(descriptor)
        with self.connect() as connection:
            # Serializes first startup/schema changes across local processes.
            connection.execute("BEGIN IMMEDIATE")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise RuntimeError("Database schema is newer than this ENGAGE version")
            if version == 0:
                connection.execute("""
                    CREATE TABLE notes (
                        id TEXT PRIMARY KEY,
                        folder_id TEXT DEFAULT NULL CHECK (folder_id IS NULL),
                        title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
                        document_json TEXT NOT NULL CHECK (json_valid(document_json)),
                        format_version INTEGER NOT NULL CHECK (format_version = 1),
                        revision INTEGER NOT NULL CHECK (revision >= 1),
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                # Future schema changes can add a version == 1 branch here.
                connection.execute("PRAGMA user_version = 1")

    @staticmethod
    def _note(row: sqlite3.Row) -> dict:
        note = dict(row)
        note["document_json"] = json.loads(note["document_json"])
        return note

    def create(self, title: str, document: list[dict], format_version: int) -> dict:
        note_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO notes
                   (id, title, document_json, format_version, revision, created_at,
                    updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)""",
                (
                    note_id,
                    title,
                    json.dumps(document, ensure_ascii=False),
                    format_version,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
        return self._note(row)

    def get(self, note_id: str) -> dict:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
        if row is None:
            raise NoteNotFound
        return self._note(row)

    def update(self, note_id: str, revision: int, changes: dict) -> dict:
        with self.connect() as connection:
            # The revision test and write happen in ONE SQL statement/transaction.
            result = connection.execute(
                """UPDATE notes SET
                   title = COALESCE(?, title),
                   document_json = COALESCE(?, document_json),
                   revision = revision + 1, updated_at = ?
                   WHERE id = ? AND revision = ?""",
                (
                    changes.get("title"),
                    json.dumps(changes["document_json"], ensure_ascii=False)
                    if "document_json" in changes
                    else None,
                    datetime.now(timezone.utc).isoformat(),
                    note_id,
                    revision,
                ),
            )
            if result.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM notes WHERE id = ?", (note_id,)
                ).fetchone()
                if exists is None:
                    raise NoteNotFound
                raise RevisionConflict
            row = connection.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
        return self._note(row)
