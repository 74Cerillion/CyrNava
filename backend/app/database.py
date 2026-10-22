"""SQLite lifecycle and note operations. No HTTP or editor dependencies."""

import hashlib
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


class FolderNotFound(Exception):
    pass


class InvalidRelationship(Exception):
    pass


class DeletionConflict(Exception):
    pass


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
            if version > 2:
                raise RuntimeError("Database schema is newer than this ENGAGE version")
            if version < 2:
                connection.execute("""
                    CREATE TABLE folders (
                        id TEXT PRIMARY KEY,
                        parent_id TEXT REFERENCES folders(id) ON DELETE RESTRICT,
                        name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 200),
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                # M1's CHECK(folder_id IS NULL) cannot be removed with ALTER.
                # This is the only table rebuilt; all existing fields copy verbatim.
                connection.execute("""
                    CREATE TABLE notes_m2 (
                        id TEXT PRIMARY KEY,
                        folder_id TEXT REFERENCES folders(id) ON DELETE RESTRICT,
                        title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
                        document_json TEXT NOT NULL CHECK (json_valid(document_json)),
                        format_version INTEGER NOT NULL CHECK (format_version = 1),
                        revision INTEGER NOT NULL CHECK (revision >= 1),
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                if version == 1:
                    connection.execute("""INSERT INTO notes_m2
                        (id, folder_id, title, document_json, format_version,
                         revision, created_at, updated_at)
                        SELECT id, folder_id, title, document_json, format_version,
                               revision, created_at, updated_at FROM notes""")
                    connection.execute("DROP TABLE notes")
                connection.execute("ALTER TABLE notes_m2 RENAME TO notes")
                connection.execute("CREATE INDEX folders_parent ON folders(parent_id)")
                connection.execute("CREATE INDEX notes_folder ON notes(folder_id)")
                if connection.execute("PRAGMA foreign_key_check").fetchone():
                    raise RuntimeError("Database migration found invalid relationships")
                connection.execute("PRAGMA user_version = 2")

    @staticmethod
    def _note(row: sqlite3.Row) -> dict:
        note = dict(row)
        note["document_json"] = json.loads(note["document_json"])
        return note

    def create(
        self,
        title: str,
        document: list[dict],
        format_version: int,
        folder_id: str | None = None,
    ) -> dict:
        note_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._check_parent(connection, folder_id)
            connection.execute(
                """INSERT INTO notes
                   (id, folder_id, title, document_json, format_version, revision,
                    created_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (
                    note_id,
                    folder_id,
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
            connection.execute("BEGIN IMMEDIATE")
            if "folder_id" in changes:
                self._check_parent(connection, changes["folder_id"])
            # The revision test and write happen in ONE SQL statement/transaction.
            result = connection.execute(
                """UPDATE notes SET
                   title = COALESCE(?, title),
                   folder_id = CASE WHEN ? THEN ? ELSE folder_id END,
                   document_json = COALESCE(?, document_json),
                   revision = revision + 1, updated_at = ?
                   WHERE id = ? AND revision = ?""",
                (
                    changes.get("title"),
                    "folder_id" in changes,
                    changes.get("folder_id"),
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

    @staticmethod
    def _check_parent(connection, parent_id):
        if (
            parent_id is not None
            and not connection.execute(
                "SELECT 1 FROM folders WHERE id = ?", (parent_id,)
            ).fetchone()
        ):
            raise InvalidRelationship("Destination folder does not exist")

    @staticmethod
    def _folders(connection):
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM folders ORDER BY sort_order, name COLLATE NOCASE, id"
            )
        ]

    @staticmethod
    def _summaries(connection):
        return [
            dict(row)
            for row in connection.execute(
                """SELECT id, folder_id, title, revision, created_at, updated_at
                   FROM notes
               ORDER BY title COLLATE NOCASE, id"""
            )
        ]

    def tree(self):
        with self.connect() as connection:
            connection.execute("BEGIN")
            # A flat adjacency list avoids JSON/stack depth limits for folders.
            return {
                "folders": self._folders(connection),
                "notes": self._summaries(connection),
            }

    def create_folder(self, name: str, parent_id: str | None):
        identifier = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._check_parent(connection, parent_id)
            connection.execute(
                """INSERT INTO folders
                   (id, parent_id, name, sort_order, created_at, updated_at)
                   VALUES (?, ?, ?, 0, ?, ?)""",
                (identifier, parent_id, name, now, now),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM folders WHERE id = ?", (identifier,)
                ).fetchone()
            )

    def update_folder(self, identifier: str, changes: dict):
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            parents = {row["id"]: row["parent_id"] for row in self._folders(connection)}
            if identifier not in parents:
                raise FolderNotFound
            if "parent_id" in changes:
                parent = changes["parent_id"]
                self._check_parent(connection, parent)
                seen = set()
                while parent is not None:
                    if parent == identifier or parent in seen:
                        raise InvalidRelationship(
                            "A folder cannot move into itself or a descendant"
                        )
                    seen.add(parent)
                    parent = parents[parent]
            connection.execute(
                """UPDATE folders SET name = COALESCE(?, name),
                   parent_id = CASE WHEN ? THEN ? ELSE parent_id END, updated_at = ?
                   WHERE id = ?""",
                (
                    changes.get("name"),
                    "parent_id" in changes,
                    changes.get("parent_id"),
                    datetime.now(timezone.utc).isoformat(),
                    identifier,
                ),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM folders WHERE id = ?", (identifier,)
                ).fetchone()
            )

    def delete_note(self, identifier: str, revision: int):
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT revision FROM notes WHERE id = ?", (identifier,)
            ).fetchone()
            if row is None:
                raise NoteNotFound
            if row[0] != revision:
                raise RevisionConflict
            connection.execute(
                "DELETE FROM notes WHERE id = ? AND revision = ?",
                (identifier, revision),
            )

    def _impact(self, connection, identifier):
        folders = self._folders(connection)
        by_id = {folder["id"]: folder for folder in folders}
        if identifier not in by_id:
            raise FolderNotFound
        children = {}
        for folder in folders:
            children.setdefault(folder["parent_id"], []).append(folder["id"])
        # Iterative traversal and child-first deletion avoid recursion/trigger limits.
        ordered = []
        pending = [identifier]
        seen = set()
        while pending:
            current = pending.pop()
            if current in seen:
                raise DeletionConflict("Invalid cycle in stored hierarchy")
            seen.add(current)
            ordered.append(current)
            pending.extend(children.get(current, []))
        notes = [
            note for note in self._summaries(connection) if note["folder_id"] in seen
        ]
        signature = {
            "folders": sorted([by_id[key] for key in ordered], key=lambda f: f["id"]),
            "notes": sorted(notes, key=lambda note: note["id"]),
        }
        token = hashlib.sha256(
            json.dumps(signature, sort_keys=True).encode()
        ).hexdigest()
        return (
            {
                "folder_id": identifier,
                "name": by_id[identifier]["name"],
                "descendant_folders": len(ordered) - 1,
                "notes": len(notes),
                "token": token,
            },
            ordered,
            notes,
        )

    def deletion_impact(self, identifier):
        with self.connect() as connection:
            connection.execute("BEGIN")
            return self._impact(connection, identifier)[0]

    def delete_folder(self, identifier, intent):
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            impact, ordered, notes = self._impact(connection, identifier)
            if (
                impact["descendant_folders"] != intent["expected_descendant_folders"]
                or impact["notes"] != intent["expected_notes"]
                or impact["token"] != intent["impact_token"]
            ):
                raise DeletionConflict(
                    "Folder contents changed. Review the deletion counts again."
                )
            if (impact["descendant_folders"] or impact["notes"]) and not intent[
                "recursive"
            ]:
                raise DeletionConflict(
                    "Nonempty folders require explicit recursive deletion intent"
                )
            connection.executemany(
                "DELETE FROM notes WHERE id = ?", [(note["id"],) for note in notes]
            )
            connection.executemany(
                "DELETE FROM folders WHERE id = ?",
                [(key,) for key in reversed(ordered)],
            )
