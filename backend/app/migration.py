"""P3 offline portable backups and staged migration. Never opens a default profile."""

import fcntl
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import struct
import tempfile
import time
import zipfile
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.backup import BackupError, digest, safe_path, validate_backup, validate_profile
from app.database import Database
from app.search import verify_index

FORMAT = 2
SCHEMA = 5
MAX_DATABASE = 512 * 1024**2
MAX_TOTAL = 2 * 1024**3
MAX_FILES = 20000
MAX_MANIFEST = 8 * 1024**2
MAX_ASSET = 10 * 1024**2


def regular(path, limit):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        raise BackupError("Unsafe or inaccessible input file.") from None
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
        os.close(fd)
        raise BackupError("Unsafe or oversized input file.")
    return os.fdopen(fd, "rb")


def json_read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise BackupError("Duplicate metadata key.")
            result[key] = value
        return result

    with regular(path, MAX_MANIFEST) as stream:
        return json.load(stream, object_pairs_hook=unique)


def durable_json(path, value):
    temporary = path.with_name("." + path.name + "." + uuid4().hex + ".new")
    with temporary.open("x", encoding="utf-8") as stream:
        os.chmod(temporary, 0o600)
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    sync_directory(path.parent)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def source_guard(source):
    """Existing cooperative lock only: no lock creation or source writes."""
    source = safe_path(source)
    lock = source / ".engage.lock"
    with regular(lock, 1024) as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise BackupError("Stop CyrNava before migrating or backing up.") from None
        yield source


def schema_definition(connection):
    return {
        name: " ".join(sql.split())
        for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL"
        )
    }


@lru_cache(maxsize=3)
def expected_schema(version):
    with tempfile.TemporaryDirectory(prefix="cyrnava-schema-") as tmp:
        db = Database(Path(tmp) / "engage.sqlite3")
        db.initialize()
        with db.connect() as connection:
            result = schema_definition(connection)
        if version < 5:
            result = {
                k: v for k, v in result.items() if not k.startswith("note_search")
            }
        if version < 4:
            result = {
                k: v
                for k, v in result.items()
                if k not in ("templates", "template_images")
            }
        return result


def inspect(directory, *, backup=False):
    directory = safe_path(directory)
    if not directory.is_dir():
        raise BackupError("Choose a supported workspace or verified backup.")
    total = 0
    count = 0
    for base, dirs, files in os.walk(directory, followlinks=False):
        relative = Path(base).relative_to(directory)
        if (relative == Path(".") and set(dirs) != {"assets"}) or (
            relative != Path(".") and dirs
        ):
            raise BackupError("Unexpected workspace directory; source not changed.")
        if relative == Path(".") and set(files) - {
            "engage.sqlite3",
            ".engage.lock",
            "manifest.json",
        }:
            raise BackupError(
                "Unexpected workspace files or SQLite sidecars. Stop CyrNava first."
            )
        for name in dirs:
            if (Path(base) / name).is_symlink():
                raise BackupError("Symbolic links are not supported.")
        for name in files:
            path = Path(base) / name
            with regular(
                path, MAX_DATABASE if name == "engage.sqlite3" else MAX_ASSET
            ) as stream:
                total += os.fstat(stream.fileno()).st_size
            count += 1
            if count > MAX_FILES or total > MAX_TOTAL:
                raise BackupError("Workspace exceeds migration resource limits.")
    if any(directory.glob("engage.sqlite3-*")):
        raise BackupError("Database sidecars exist. Cleanly stop CyrNava first.")
    db = directory / "engage.sqlite3"
    with regular(db, MAX_DATABASE):
        pass
    connection = sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (3, 4, 5):
            raise BackupError("Supported source schemas: 3, 4, 5. No downgrades.")
        actual_schema = schema_definition(connection)
        if actual_schema != expected_schema(version):
            raise BackupError("Unexpected database schema; no SQL was transformed.")
        if connection.execute(
            "SELECT 1 FROM notes WHERE length(document_json) > 2097152 LIMIT 1"
        ).fetchone():
            raise BackupError("Saved document exceeds the migration size limit.")
        if version >= 4:
            for table in ("templates", "template_images"):
                if (
                    connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    > MAX_FILES
                ):
                    raise BackupError("Too many saved template records.")
            if connection.execute(
                "SELECT 1 FROM templates WHERE length(document_json)>2097152 LIMIT 1"
            ).fetchone():
                raise BackupError("Saved template exceeds migration limits.")
        counts = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("notes", "folders", "assets")
        }
        if any(value > MAX_FILES for value in counts.values()):
            raise BackupError("Workspace exceeds migration record limits.")
    finally:
        connection.close()
    files = (
        validate_backup(directory, bounded=True)
        if backup
        else validate_profile(directory, bounded=True)
    )
    actual_assets = {
        str(p.relative_to(directory)) for p in (directory / "assets").iterdir()
    }
    if actual_assets != {name for name in files if name.startswith("assets/")}:
        raise BackupError(
            "Untracked or unsafe assets found; reconcile them before migration."
        )
    hashes = [value for name, value in files.items() if name.startswith("assets/")]
    return {
        "schema": version,
        "counts": counts,
        "bytes": total,
        "duplicate_asset_contents": len(hashes) - len(set(hashes)),
        "files": files,
    }


def content_fingerprint(directory):
    """Compare application records and assets across additive schema migrations."""
    con = sqlite3.connect(
        (directory / "engage.sqlite3").as_uri() + "?mode=ro&immutable=1", uri=True
    )
    h = hashlib.sha256()
    try:
        tables = {
            row[0]
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        for table in ("folders", "notes", "assets", "templates", "template_images"):
            if table not in tables:
                continue
            # Empty new template tables do not alter the fingerprint.
            for row in con.execute(f"SELECT * FROM {table} ORDER BY 1, 2"):
                h.update(table.encode())
                for value in row:
                    data = (
                        value
                        if isinstance(value, bytes)
                        else json.dumps(value).encode()
                    )
                    h.update(str(len(data)).encode() + b":" + data)
        return h.hexdigest()
    finally:
        con.close()


def space(directory, amount):
    if shutil.disk_usage(directory).free < amount + 16 * 1024**2:
        raise BackupError(
            "Insufficient free storage; original and active data remain unchanged."
        )


def copy_checked(source, target, expected):
    limit = MAX_DATABASE if target.name == "engage.sqlite3" else MAX_ASSET
    with regular(source, limit) as src, target.open("xb") as dst:
        os.chmod(target, 0o600)
        h = hashlib.sha256()
        size = 0
        while chunk := src.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                raise BackupError("Input grew beyond the permitted limit.")
            h.update(chunk)
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())
    if h.hexdigest() != expected:
        raise BackupError(
            "Source changed during copying; stop writers and retry explicitly."
        )


def pack(source, destination, *, progress=lambda _: None):
    """Extend directory backups with a bounded portable format-2 file."""
    source, destination = safe_path(source), safe_path(destination)
    if destination.is_relative_to(source) or destination.exists():
        raise BackupError("Choose a new backup file outside the source.")
    is_backup = (source / "manifest.json").exists()
    guard = source_guard(source) if not is_backup else null_guard(source)
    with guard:
        progress("inspecting")
        summary = inspect(source, backup=is_backup)
        space(destination.parent, summary["bytes"] * 2)
        with tempfile.TemporaryDirectory(
            prefix=".cyrnava-backup-", dir=destination.parent
        ) as tmp:
            stage = Path(tmp)
            (stage / "assets").mkdir(mode=0o700)
            for name, checksum in summary["files"].items():
                copy_checked(source / name, stage / name, checksum)
            if inspect(stage)["files"] != summary["files"]:
                raise BackupError("Snapshot verification failed.")
            manifest = {
                "backup_format": FORMAT,
                "application_version": "0.1.0",
                "schema_version": summary["schema"],
                "files": summary["files"],
                "excluded": [
                    "browser preferences",
                    "browser recovery drafts",
                    "pending uploads",
                ],
                "sizes": {
                    name: (stage / name).stat().st_size for name in summary["files"]
                },
            }
            durable_json(stage / "manifest.json", manifest)
            archive = stage / "backup.cyrnava"
            progress("writing-backup")
            # Stored entries avoid decompression bombs and make size accounting exact.
            with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as out:
                for name in [*summary["files"], "manifest.json"]:
                    out.write(stage / name, name)
            os.chmod(archive, 0o600)
            with archive.open("rb") as stream:
                os.fsync(stream.fileno())
            with tempfile.TemporaryDirectory(dir=destination.parent) as check:
                unpack(archive, Path(check))
            # Exclusive hard-link publish never overwrites an existing backup.
            os.link(archive, destination)
            sync_directory(destination.parent)
            progress("backup-verified")
            return summary


@contextmanager
def null_guard(source):
    yield source


def unpack(archive, stage):
    """No extractall, no archive paths used until strict allowlist validation."""
    with regular(archive, MAX_TOTAL + MAX_MANIFEST + MAX_FILES * 512) as stream:
        # Bound central-directory allocation before ZipFile parses entries.
        stream.seek(0, 2)
        length = stream.tell()
        stream.seek(max(0, length - 65557))
        tail = stream.read(65557)
        offset = tail.rfind(b"PK\x05\x06")
        if offset < 0 or len(tail) - offset < 22:
            raise BackupError("Missing archive end record.")
        _, disk, central_disk, disk_count, count, size, start, comment = struct.unpack(
            "<4s4H2LH", tail[offset : offset + 22]
        )
        if (
            disk
            or central_disk
            or count != disk_count
            or count > MAX_FILES
            or size > MAX_MANIFEST
            or start + size != length - len(tail) + offset
            or len(tail) - offset != 22 + comment
        ):
            raise BackupError("Unsafe archive directory or unsupported ZIP64.")
        stream.seek(0)
        with zipfile.ZipFile(stream) as zipped:
            entries = zipped.infolist()
            if len(entries) != count:
                raise BackupError("Archive entry count mismatch.")
            names = [entry.filename for entry in entries]
            if (
                len(entries) > MAX_FILES
                or len(set(names)) != len(names)
                or "manifest.json" not in names
            ):
                raise BackupError("Invalid archive entry list.")
            total = 0
            for entry in entries:
                name = entry.filename
                from app.assets import ASSET_NAME

                allowed = name in ("manifest.json", "engage.sqlite3") or (
                    name.startswith("assets/") and ASSET_NAME.fullmatch(name[7:])
                )
                mode = entry.external_attr >> 16
                if (
                    not allowed
                    or entry.is_dir()
                    or (stat.S_IFMT(mode) not in (0, stat.S_IFREG))
                    or entry.compress_type != zipfile.ZIP_STORED
                    or entry.flag_bits & 1
                ):
                    raise BackupError(
                        "Unsafe archive entry or unsupported compression."
                    )
                limit = (
                    MAX_DATABASE
                    if name == "engage.sqlite3"
                    else MAX_MANIFEST
                    if name == "manifest.json"
                    else MAX_ASSET
                )
                total += entry.file_size
                if entry.file_size > limit or total > MAX_TOTAL:
                    raise BackupError("Archive exceeds resource limits.")
            space(stage, total * 2)
            (stage / "assets").mkdir(mode=0o700)
            for entry in entries:
                target = stage / entry.filename
                with zipped.open(entry) as src, target.open("xb") as dst:
                    os.chmod(target, 0o600)
                    left = entry.file_size
                    while left:
                        chunk = src.read(min(left, 1024 * 1024))
                        if not chunk:
                            raise BackupError("Truncated archive.")
                        dst.write(chunk)
                        left -= len(chunk)
                    if src.read(1):
                        raise BackupError("Archive size mismatch.")
                    dst.flush()
                    os.fsync(dst.fileno())
            manifest = json_read(stage / "manifest.json")
            if (
                not isinstance(manifest, dict)
                or manifest.get("backup_format") != FORMAT
            ):
                raise BackupError("Unsupported portable backup version.")
            if (
                set(manifest)
                != {
                    "backup_format",
                    "application_version",
                    "schema_version",
                    "files",
                    "excluded",
                    "sizes",
                }
                or not isinstance(manifest.get("application_version"), str)
                or not re.fullmatch(
                    r"[0-9]{1,6}\.[0-9]{1,6}\.[0-9]{1,6}",
                    manifest["application_version"],
                )
                or manifest.get("excluded")
                != ["browser preferences", "browser recovery drafts", "pending uploads"]
            ):
                raise BackupError("Malformed backup metadata.")
            summary = inspect(stage)
            if (
                manifest.get("files") != summary["files"]
                or manifest.get("schema_version") != summary["schema"]
                or manifest.get("sizes")
                != {name: (stage / name).stat().st_size for name in summary["files"]}
            ):
                raise BackupError("Backup hash, size or schema mismatch.")
            if set(names) != set(summary["files"]) | {"manifest.json"}:
                raise BackupError("Unexpected archive contents.")
            return summary


def migrate(
    archive, destination, *, progress=lambda _: None, checkpoint=lambda _: None
):
    """Restore into a NEW profile only. Durable journal, same-filesystem activation.

    The caller owns the desktop instance lock and must not start its backend until
    this returns. Existing destinations, even empty ones, are never replaced.
    """
    archive, destination = safe_path(archive), safe_path(destination)
    if destination.exists():
        raise BackupError(
            "Destination exists; use a new profile. No data was replaced."
        )
    parent = destination.parent
    space(parent, 16 * 1024**2)
    identifier = uuid4().hex
    stage = parent / (".migration-" + identifier)
    journal = parent / ("migration-" + identifier + ".json")
    stage.mkdir(mode=0o700)
    record = {
        "migration_format": 1,
        "id": identifier,
        "status": "staging",
        "schema_target": SCHEMA,
    }
    durable_json(journal, record)
    started = time.monotonic()
    try:
        progress("validating-backup")
        summary = unpack(archive, stage)
        initial_contents = content_fingerprint(stage)
        checkpoint("extracted")
        progress("upgrading-schema")
        Database(stage / "engage.sqlite3").initialize()
        with Database(stage / "engage.sqlite3").connect() as connection:
            verify_index(connection)
        checkpoint("upgraded")
        result = inspect(stage)
        if (
            result["schema"] != SCHEMA
            or result["counts"] != summary["counts"]
            or content_fingerprint(stage) != initial_contents
        ):
            raise BackupError("Post-migration validation failed.")
        # Preserve original validated backup outside the active profile for rollback.
        backup_path = parent / ("pre-migration-" + identifier + ".cyrnava")
        with (
            regular(archive, MAX_TOTAL + MAX_MANIFEST + MAX_FILES * 512) as src,
            backup_path.open("xb") as dst,
        ):
            os.chmod(backup_path, 0o600)
            shutil.copyfileobj(src, dst, 1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        if digest(backup_path) != digest(archive):
            raise BackupError("Recovery backup copy failed validation.")
        # Source-format manifest is provenance, not a checksum for upgraded bytes.
        (stage / "manifest.json").unlink()
        for path in stage.rglob("*"):
            if path.is_file():
                with path.open("rb") as stream:
                    os.fsync(stream.fileno())
        sync_directory(stage / "assets")
        sync_directory(stage)
        record.update(status="verified", backup=backup_path.name)
        durable_json(journal, record)
        checkpoint("before-activation")
        # Linux renameat2 NOREPLACE gives atomic visibility and exclusive destination.
        import ctypes

        libc = ctypes.CDLL(None, use_errno=True)
        if libc.renameat2(-100, os.fsencode(stage), -100, os.fsencode(destination), 1):
            raise OSError(ctypes.get_errno(), "Atomic profile activation refused")
        sync_directory(parent)
        record.update(
            status="activated",
            duration_ms=round((time.monotonic() - started) * 1000, 3),
            counts=result["counts"],
        )
        durable_json(journal, record)
        progress("complete")
        return record
    except BaseException:
        record["status"] = (
            "activation-uncertain" if destination.exists() else "failed-quarantined"
        )
        try:
            durable_json(journal, record)
        except OSError:
            pass
        # Keep stage/backup for explicit recovery; preserve source and active data.
        raise


def recover_draft(
    source, draft_file, destination, backup_file, *, progress=lambda _: None
):
    """Import explicit browser JSON into a new generation, never the live source.

    Only matching note/revision drafts are supported. Conflicts and missing image
    bytes require review in the old application; neither is silently discarded.
    """
    from uuid import UUID

    from app.models import validate_document

    with regular(draft_file, 2 * 1024**2) as stream:
        draft = json.load(stream)
    if (
        not isinstance(draft, dict)
        or draft.get("recovery_format") != 1
        or draft.get("format_version") != 1
        or type(draft.get("base_revision")) is not int
        or not isinstance(draft.get("title"), str)
        or not 1 <= len(draft["title"].strip()) <= 200
    ):
        raise BackupError("Unsupported recovery draft metadata.")
    UUID(draft["note_id"])
    validate_document(draft["document_json"])
    summary = inspect(source)
    if summary["schema"] != SCHEMA:
        raise BackupError("Migrate the workspace before importing a recovery draft.")
    connection = sqlite3.connect(
        (source / "engage.sqlite3").as_uri() + "?mode=ro&immutable=1", uri=True
    )
    try:
        row = connection.execute(
            "SELECT revision FROM notes WHERE id=?", (draft["note_id"],)
        ).fetchone()
        if row is None:
            raise BackupError("Draft note is absent from the migrated workspace.")
        note = {"revision": row[0]}
    finally:
        connection.close()
    if note["revision"] != draft["base_revision"]:
        raise BackupError(
            "Draft revision differs. Review the conflict in the old application."
        )
    pack(source, backup_file, progress=progress)
    migrate(backup_file, destination, progress=progress)
    restored = Database(destination / "engage.sqlite3")
    restored.update(
        draft["note_id"],
        draft["base_revision"],
        {
            "title": draft["title"],
            "document_json": draft["document_json"],
        },
    )
    inspect(destination)
    return {"status": "verified", "recovery_format": 1}
