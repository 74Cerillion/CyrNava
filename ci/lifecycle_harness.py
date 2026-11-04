"""Disposable legacy-launcher fixture; deliberately excluded from production staging.

No application import/config/environment switch activates this module. Tests copy
this executable beside an explicit harness-source.json and invoke that copy.
"""

import argparse
import contextvars
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

OPERATION = contextvars.ContextVar("p5a_operation", default=None)
TABLE = "_p5a_test_guard"
MARKER = "CyrNava disposable lifecycle fixture v1"


class Journal:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()

    def emit(self, event, **fields):
        record = {"event": event, "mono_ns": time.monotonic_ns(), "pid": os.getpid()}
        operation = OPERATION.get()
        if operation is not None:
            record["operation"] = operation
        record.update(fields)
        # One bounded append, without SQL, note bodies, headers or exceptions.
        payload = (json.dumps(record, separators=(",", ":")) + "\n").encode()
        with self.lock:
            fd = os.open(
                self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600
            )
            try:
                os.write(fd, payload)
            finally:
                os.close(fd)


def install_guard(path):
    with sqlite3.connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            f"CREATE TABLE IF NOT EXISTS {TABLE} "
            "(id INTEGER PRIMARY KEY CHECK(id=1), marker TEXT NOT NULL, "
            "armed INTEGER NOT NULL CHECK(armed IN (0,1)))"
        )
        connection.execute(f"INSERT OR IGNORE INTO {TABLE} VALUES (1, ?, 0)", (MARKER,))
        for action in ("INSERT", "UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER IF NOT EXISTS p5a_block_{action.lower()} "
                f"BEFORE {action} ON notes "
                f"WHEN (SELECT armed FROM {TABLE} WHERE id=1)=1 "
                "BEGIN SELECT RAISE(ABORT, 'P5A synthetic no-write boundary'); END"
            )


def fingerprints(connection):
    return [
        {
            "note_id": row[0],
            "revision": row[1],
            "digest": hashlib.sha256(
                json.dumps(row[2:], ensure_ascii=False).encode()
            ).hexdigest(),
        }
        for row in connection.execute(
            "SELECT id,revision,title,document_json,folder_id,format_version,"
            "created_at,updated_at FROM notes ORDER BY id"
        )
    ]


def boundary(path, action, journal):
    # No owner profile may be armed: the test-created marker and three triggers
    # must already exist. BEGIN IMMEDIATE serializes against an existing writer;
    # its commit is the linearization point, not receipt of a browser event.
    with sqlite3.connect(path, timeout=5) as connection:
        connection.execute("BEGIN IMMEDIATE")
        marker = connection.execute(f"SELECT marker FROM {TABLE} WHERE id=1").fetchone()
        if marker != (MARKER,):
            raise ValueError("Not a disposable lifecycle fixture")
        triggers = connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name IN "
            "('p5a_block_insert','p5a_block_update','p5a_block_delete')"
        ).fetchone()[0]
        if triggers != 3:
            raise ValueError("Incomplete no-write guard")
        if action != "inspect":
            connection.execute(
                f"UPDATE {TABLE} SET armed=? WHERE id=1", (int(action == "arm"),)
            )
        result = {
            "armed": bool(
                connection.execute(f"SELECT armed FROM {TABLE} WHERE id=1").fetchone()[
                    0
                ]
            ),
            "notes": fingerprints(connection),
        }
    journal.emit(
        "boundary_" + action + "_committed",
        armed=result["armed"],
        notes=result["notes"],
    )
    return result


def verify_boundary(path, expected, journal):
    observed = boundary(path, "inspect", journal)
    if not observed["armed"] or observed["notes"] != expected["notes"]:
        raise ValueError("Canonical note changed or guard was disarmed")
    journal.emit("boundary_verified", notes=observed["notes"])
    return observed


def instrument_database(base, journal):
    class ObservedDatabase(base):
        def initialize(self):
            # A mistaken fixture config must never convert an existing workspace.
            # Restart is allowed only for this harness's already marked database.
            if self.path.exists():
                with sqlite3.connect(
                    f"file:{self.path}?mode=ro", uri=True
                ) as connection:
                    try:
                        marker = connection.execute(
                            f"SELECT marker FROM {TABLE} WHERE id=1"
                        ).fetchone()
                    except sqlite3.Error as error:
                        raise ValueError(
                            "Existing non-fixture database refused"
                        ) from error
                    if marker != (MARKER,):
                        raise ValueError("Existing non-fixture database refused")
            super().initialize()
            install_guard(self.path)
            journal.emit("fixture_database_ready")

        @contextmanager
        def connect(self):
            operation = OPERATION.get()
            try:
                with super().connect() as connection:
                    if operation:

                        def statement(sql):
                            # Never record expanded SQL: it contains note text.
                            kind = sql.lstrip().split(" ", 1)[0].upper()
                            if kind in {
                                "BEGIN",
                                "UPDATE",
                                "INSERT",
                                "DELETE",
                                "COMMIT",
                                "ROLLBACK",
                            }:
                                journal.emit("sqlite_statement", kind=kind)

                        connection.set_trace_callback(statement)
                    yield connection
                if operation:
                    journal.emit("sqlite_commit_complete")
            except BaseException as error:
                if operation:
                    journal.emit(
                        "sqlite_transaction_failed", error_type=type(error).__name__
                    )
                raise

        def update(self, note_id, revision, changes):
            journal.emit("database_update_enter", expected_revision=revision)
            try:
                result = super().update(note_id, revision, changes)
            except BaseException as error:
                journal.emit("database_update_failed", error_type=type(error).__name__)
                raise
            journal.emit("database_update_return", revision=result["revision"])
            return result

    return ObservedDatabase


class Correlation:
    def __init__(self, app, journal):
        self.app, self.journal = app, journal

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/notes"):
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        supplied = headers.get(b"x-p5a-operation", b"").decode("ascii", errors="ignore")
        operation = (
            supplied if re.fullmatch(r"[0-9a-f-]{36}", supplied) else str(uuid.uuid4())
        )
        token = OPERATION.set(operation)
        frontend = {}
        try:
            raw = json.loads(headers.get(b"x-p5a-frontend", b"{}"))
            for key in ("perf_ms", "time_origin_ms", "sequence"):
                if isinstance(raw.get(key), (int, float)):
                    frontend[key] = raw[key]
            for key in ("close_intent", "keepalive", "service_worker"):
                if isinstance(raw.get(key), bool):
                    frontend[key] = raw[key]
            if raw.get("visibility") in ("hidden", "visible"):
                frontend["visibility"] = raw["visibility"]
        except (ValueError, TypeError):
            pass
        self.journal.emit(
            "fastapi_request_enter", method=scope["method"], frontend=frontend
        )

        async def response(message):
            if message["type"] == "http.response.start":
                self.journal.emit("fastapi_response", status=message["status"])
            await send(message)

        try:
            await self.app(scope, receive, response)
        finally:
            self.journal.emit("fastapi_request_exit")
            OPERATION.reset(token)


def launch():
    source = json.loads(Path(__file__).with_name("harness-source.json").read_text())
    spec = importlib.util.spec_from_file_location(
        "p5a_original_launcher", source["launcher"]
    )
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    # Every supervisor/worker subprocess returns through this explicit fixture.
    launcher.__file__ = __file__
    original_worker = launcher.worker

    def worker(config, nonce):
        sys.path.insert(0, str(Path(config["release"]) / "backend"))
        from app import main

        journal = Journal(Path(config["state_dir"]) / "p5a-events.jsonl")
        main.Database = instrument_database(main.Database, journal)
        factory = main.create_app

        def create_app(*args, **kwargs):
            app = factory(*args, **kwargs)
            app.add_middleware(Correlation, journal=journal)
            return app

        main.create_app = create_app
        return original_worker(config, nonce)

    launcher.worker = worker
    return launcher.main()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in {
        "arm",
        "disarm",
        "inspect",
        "marker",
        "verify",
    }:
        parser = argparse.ArgumentParser()
        parser.add_argument("action")
        parser.add_argument("database", type=Path)
        parser.add_argument("journal", type=Path)
        args = parser.parse_args()
        journal = Journal(args.journal)
        if args.action == "marker":
            journal.emit("driver_close_intent")
            print("{}")
        elif args.action == "verify":
            print(
                json.dumps(
                    verify_boundary(args.database, json.load(sys.stdin), journal)
                )
            )
        else:
            print(json.dumps(boundary(args.database, args.action, journal)))
        return 0
    return launch()


if __name__ == "__main__":
    raise SystemExit(main())
