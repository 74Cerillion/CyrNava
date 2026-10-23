"""Offline directory backups. Run with: python -m app.backup --help."""

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path
from uuid import UUID, uuid4

from app.assets import ASSET_NAME, FORMATS, MAX_BYTES, InvalidImage, validate_image
from app.database import Database, InvalidRelationship, default_database_path
from app.models import Note, validate_document
from app.profile import ProfileBusy, profile_lock

REPOSITORY = Path(__file__).resolve().parents[2]


class BackupError(Exception):
    pass


def safe_path(value: Path) -> Path:
    path = value.expanduser().absolute()
    if any(part.is_symlink() for part in [path, *path.parents]):
        raise BackupError("Choose a real directory, not a symbolic link.")
    path = path.resolve()
    if path.is_relative_to(REPOSITORY):
        raise BackupError("Application data and backups must remain outside Git.")
    return path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_profile(directory: Path) -> dict[str, str]:
    """Read-only validation; never initialize or repair a backup as a side effect."""
    database = directory / "engage.sqlite3"
    if not database.is_file() or database.is_symlink():
        raise BackupError("Backup requires an ENGAGE database.")
    if any(directory.glob("engage.sqlite3-*")):
        raise BackupError("Database sidecar files exist. Cleanly stop ENGAGE first.")
    assets = directory / "assets"
    if not assets.is_dir() or assets.is_symlink():
        raise BackupError("Backup requires an assets directory.")
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if connection.execute("PRAGMA integrity_check").fetchall()[0][0] != "ok":
            raise BackupError("Database integrity check failed.")
        if connection.execute("PRAGMA user_version").fetchone()[0] != 3:
            raise BackupError("Unsupported schema. Upgrade ENGAGE before backing up.")
        if connection.execute("PRAGMA foreign_key_check").fetchone():
            raise BackupError("Database contains broken relationships.")
        parents = {
            row["id"]: row["parent_id"]
            for row in connection.execute("SELECT * FROM folders")
        }
        done = set()
        for identifier in parents:
            UUID(identifier)
            current, chain = identifier, set()
            while current is not None and current not in done:
                if current in chain or current not in parents:
                    raise BackupError("Invalid folder hierarchy.")
                chain.add(current)
                current = parents[current]
            done.update(chain)
        rows = connection.execute("SELECT * FROM assets").fetchall()
        files = {"engage.sqlite3": digest(database)}
        for row in rows:
            if (
                not ASSET_NAME.fullmatch(row["id"])
                or row["disk_path"] != row["id"]
                or row["mime_type"] not in FORMATS.values()
                or not 0 < row["byte_size"] <= MAX_BYTES
            ):
                raise BackupError("Invalid image metadata.")
            path = assets / row["id"]
            if (
                path.is_symlink()
                or not path.is_file()
                or path.stat().st_size != row["byte_size"]
            ):
                raise BackupError("An image is missing or has the wrong size.")
            try:
                # Verify existing stored bytes too; hashing a damaged image
                # would produce a consistent but unusable backup.
                validate_image(path.read_bytes(), row["mime_type"])
            except InvalidImage:
                raise BackupError("An image failed validation.") from None
            files[f"assets/{row['id']}"] = digest(path)
        for row in connection.execute("SELECT * FROM notes"):
            note = Note.model_validate(Database._note(row))
            UUID(note.id)
            if note.format_version != 1 or note.revision < 1 or not note.title.strip():
                raise BackupError("Invalid saved note metadata.")
            validate_document(note.document_json)
            Database._check_images(connection, note.id, note.document_json)
        return files
    finally:
        connection.close()


def validate_backup(directory):
    manifest_path = directory / "manifest.json"
    if (
        manifest_path.is_symlink()
        or not manifest_path.is_file()
        or manifest_path.stat().st_size > 16 * 1024 * 1024
    ):
        raise BackupError("Missing or invalid backup manifest.")
    manifest = json.loads(manifest_path.read_text())
    actual = validate_profile(directory)
    if (
        not isinstance(manifest, dict)
        or manifest.get("backup_format") != 1
        or manifest.get("files") != actual
    ):
        raise BackupError("Backup contents do not match their checksum manifest.")
    # No archives or manifest paths are ever used to choose copy destinations.
    return actual


def _publish(source, destination, files, *, manifest=False):
    if destination.exists():
        raise BackupError(
            "Destination already exists; choose a new empty profile or backup path."
        )
    if not destination.parent.is_dir():
        raise BackupError("Destination parent directory must already exist.")
    stage = destination.parent / f".engage-stage-{uuid4()}"
    stage.mkdir(mode=0o700)
    reserved = False
    try:
        (stage / "assets").mkdir(mode=0o700)
        for name in files:
            target = stage / name  # names generated by validation, never manifest input
            shutil.copyfile(source / name, target)
            target.chmod(0o600)
        if validate_profile(stage) != files:
            raise BackupError("Copied data failed verification.")
        if manifest:
            content = {"backup_format": 1, "files": files}
            (stage / "manifest.json").write_text(json.dumps(content, indent=2) + "\n")
            (stage / "manifest.json").chmod(0o600)
            validate_backup(stage)
        # Reserve by exclusive mkdir. Never replace a preexisting destination,
        # including one created by another process while validation was running.
        destination.mkdir(mode=0o700)
        # A cooperating backend cannot open a half-published profile. If one
        # won the tiny mkdir/lock race, leave its directory untouched and fail.
        with profile_lock(destination, offline=True):
            reserved = True
            for child in stage.iterdir():
                child.rename(destination / child.name)
    except BaseException:
        if reserved:
            shutil.rmtree(destination)
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def create_backup(profile: Path, destination: Path):
    profile, destination = safe_path(profile), safe_path(destination)
    if not profile.is_dir():
        raise BackupError("Source profile does not exist.")
    if destination.is_relative_to(profile) or profile.is_relative_to(destination):
        raise BackupError("Backup and profile directories must be separate.")
    with profile_lock(profile, offline=True):
        files = validate_profile(profile)
        _publish(profile, destination, files, manifest=True)


def restore_backup(source: Path, destination: Path):
    source, destination = safe_path(source), safe_path(destination)
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise BackupError("Backup and restore directories must be separate.")
    files = validate_backup(source)
    _publish(source, destination, files)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Offline ENGAGE backup/restore. Stop the backend first. "
            "Backups are unencrypted."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("--data-dir", type=Path, default=None)
    backup.add_argument("--destination", type=Path, required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("--source", type=Path, required=True)
    restore.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "backup":
            create_backup(
                args.data_dir or default_database_path().parent, args.destination
            )
        else:
            restore_backup(args.source, args.data_dir)
    except (
        BackupError,
        ProfileBusy,
        OSError,
        sqlite3.Error,
        ValueError,
        KeyError,
        TypeError,
        InvalidRelationship,
    ) as error:
        print(
            f"{args.command.title()} failed. {error}"
            if isinstance(error, (BackupError, ProfileBusy))
            else (
                f"{args.command.title()} failed. Invalid or inaccessible local data; "
                "original data was not replaced."
            ),
            file=sys.stderr,
        )
        return 1
    print(
        f"{args.command.title()} completed and validated. "
        "Keep the data private; it is not encrypted."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
