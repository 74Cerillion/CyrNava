"""Offline maintenance of derived search data: python -m app.search_index --help."""

import argparse
import sqlite3
import sys
from pathlib import Path

from app.backup import BackupError, safe_path, validate_profile
from app.database import Database, InvalidRelationship, default_database_path
from app.profile import ProfileBusy, profile_lock
from app.search import SearchIndexError, rebuild_index


def rebuild(profile: Path):
    profile = safe_path(profile)
    database = profile / "engage.sqlite3"
    # Do not create an empty profile when the operator mistypes the path.
    if not profile.is_dir() or not database.is_file() or database.is_symlink():
        raise BackupError("Choose an existing CyrNava profile directory.")
    with profile_lock(profile, offline=True):
        # Read-only canonical validation; never attempt to repair damaged notes.
        validate_profile(profile)
        with Database(database).connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("PRAGMA user_version").fetchone()[0] != 5:
                raise BackupError(
                    "Start the updated application once to upgrade first."
                )
            rebuild_index(connection)
            # Context commits before the exclusive profile lock is released.


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild derived local search data. Stop all backends first."
    )
    parser.add_argument("command", choices=["rebuild"])
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="Full profile directory (containing engage.sqlite3)",
    )
    args = parser.parse_args()
    try:
        rebuild(args.data_dir or default_database_path().parent)
    except (
        BackupError,
        ProfileBusy,
        SearchIndexError,
        OSError,
        sqlite3.Error,
        ValueError,
        KeyError,
        TypeError,
        InvalidRelationship,
    ) as error:
        detail = (
            str(error)
            if isinstance(error, (BackupError, ProfileBusy, SearchIndexError))
            else "Invalid or inaccessible local data; canonical data was not replaced."
        )
        print(f"Search rebuild failed. {detail}", file=sys.stderr)
        return 1
    print("Search index rebuilt and verified. Canonical notes were not changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
