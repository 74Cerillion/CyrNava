"""Read-only R11 inventory and bounded synthetic-only copy for targeted P6."""

import contextlib
import fcntl
import hashlib
import os
import re
import shutil
import stat
import sys
from pathlib import Path

import core

POLICY_FILE = core.HERE / "targeted-b-policy.json"


def policy():
    return core.read_json(POLICY_FILE)


def migration():
    sys.path.insert(0, str(core.ROOT / "backend"))
    from app import migration as module

    return module


def private_object(path, directory=False):
    info = path.lstat()
    core.require(
        info.st_uid == os.getuid()
        and stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o600)
        and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
        and (directory or info.st_nlink == 1),
        "Unsafe synthetic source object or permissions",
    )
    return info


def snapshot(root):
    """Strict bounded snapshot, without chmod/open-for-write or following links."""
    root = core.safe_path(root)
    private_object(root, True)
    files = {}
    count = 0
    for base, dirs, names in os.walk(root, followlinks=False):
        count += len(dirs) + len(names)
        core.require(
            count < 4096 and len(Path(base).relative_to(root).parts) < 32,
            "Too many test files or directory levels",
        )
        for name in dirs:
            private_object(Path(base) / name, True)
        for name in names:
            path = Path(base) / name
            info = private_object(path)
            core.require(info.st_size <= 128 * 1024**2, "Test file exceeds bound")
            files[path.relative_to(root).as_posix()] = {
                "sha256": core.sha(path),
                "bytes": info.st_size,
            }
    core.require(
        len(files) < 4096 and sum(v["bytes"] for v in files.values()) <= 256 * 1024**2,
        "Synthetic profile exceeds bound",
    )
    h = hashlib.sha256()
    # Match the retained R11 inventory's component-wise pathlib ordering.
    for name in sorted(files, key=Path):
        value = files[name]
        h.update(name.encode())
        h.update(value["sha256"].encode())
    return {
        "files": len(files),
        "bytes": sum(v["bytes"] for v in files.values()),
        "tree_sha256": h.hexdigest(),
    }


def retained_profile(r11, expected):
    r11 = core.outside_source(r11)
    private_object(r11, True)
    for name in (".p6-gui-attempt", "owner-result.json"):
        private_object(r11 / name)
    core.require(
        core.sha(core.safe_path(r11 / ".p6-gui-attempt"))
        == expected["R11_marker_sha256"]
        and core.sha(core.safe_path(r11 / "owner-result.json"))
        == expected["R11_result_sha256"],
        "Unapproved R11 source evidence",
    )
    parent = r11 / "client/home/.var/app" / core.APP_ID / "data/p4-verification"
    core.safe_path(parent)
    entries = list(parent.iterdir())
    core.require(
        len(entries) == 1 and re.fullmatch(r"run-[0-9a-f]{12}", entries[0].name),
        "Unexpected R11 profile selection",
    )
    profile = core.safe_path(entries[0] / "desktop")
    core.require(snapshot(profile) == expected["R11_profile"], "R11 profile changed")
    pointer = core.read_json(profile / "active-workspace.json")
    selection = pointer.get("workspace")
    core.require(
        set(pointer) == {"version", "workspace"}
        and pointer["version"] == 1
        and isinstance(selection, str)
        and re.fullmatch(r"workspaces/[0-9a-f]{32}", selection),
        "R11 must select a separate imported workspace",
    )
    return profile, selection


def data_state(root):
    """Include empty directories as well as every file in preservation checks."""
    files = snapshot(root)
    directories = ["."] + sorted(
        p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_dir()
    )
    return {
        **files,
        "directories": len(directories),
        "directory_tree_sha256": hashlib.sha256(core.encode(directories)).hexdigest(),
    }


def validate_workspace(source, expected, *, exact_database):
    """P3's existing immutable read-only database/reference validator, no Profile."""
    source = core.safe_path(source)
    snapshot(source)
    module = migration()
    value = module.inspect(source)
    core.require(
        value["schema"] == expected["schema"] == 5
        and value["counts"] == expected["counts"]
        and module.content_fingerprint(source) == expected["content_fingerprint"]
        and snapshot(source / "assets") == expected["asset_tree"],
        "Synthetic database, folders, notes, images or references changed",
    )
    if exact_database:
        core.require(
            core.sha(source / "engage.sqlite3") == expected["database_sha256"],
            "Synthetic source database bytes changed",
        )
    return {
        "status": "PASS",
        "schema": value["schema"],
        "counts": value["counts"],
        "content_fingerprint": expected["content_fingerprint"],
        "asset_tree": expected["asset_tree"],
        "database_sha256": core.sha(source / "engage.sqlite3"),
        "database_integrity_and_references": "PASS",
    }


@contextlib.contextmanager
def source_lock(profile):
    # An existing lock opened read-only; never instantiate Profile on retained data.
    path = profile / ".instance.lock"
    private_object(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def copy_workspace(r11, destination, expected):
    profile, selection = retained_profile(r11, expected)
    destination = core.safe_path(destination)
    core.require(
        not destination.exists()
        and not destination.is_relative_to(profile)
        and not profile.is_relative_to(destination),
        "A new separate test profile is required",
    )
    with source_lock(profile):
        before = snapshot(profile)
        full_before = data_state(profile)
        core.require(before == expected["R11_profile"], "R11 changed before copy")
        source = profile / selection
        validate_workspace(source, expected["workspace"], exact_database=True)
        destination.mkdir(mode=0o700, parents=True)
        target = destination / selection
        target.parent.mkdir(mode=0o700)
        try:
            shutil.copytree(source, target, symlinks=True)
            # Reject replacements or symlinks, rather than traversing them.
            validate_workspace(target, expected["workspace"], exact_database=True)
            core.require(snapshot(source) == snapshot(target), "Synthetic copy differs")
            (destination / "active-workspace.json").write_bytes(
                core.encode({"version": 1, "workspace": selection})
            )
            (destination / "active-workspace.json").chmod(0o600)
            suffix = selection.split("/")[1]
            for prefix in ("web-profile-", "web-cache-"):
                (destination / (prefix + suffix)).mkdir(mode=0o700)
            after = snapshot(profile)
            core.require(before == after, "Retained R11 changed during copy")
        finally:
            # Even an interrupted or failed copy must independently check the source.
            core.require(data_state(profile) == full_before, "Retained source changed")
    identity = {
        "workspace": hashlib.sha256(selection.encode()).hexdigest(),
        "qt_profile": hashlib.sha256(("web-profile-" + suffix).encode()).hexdigest(),
    }
    return {
        "status": "PASS",
        "source_before": before,
        "source_after": after,
        "complete_source_tree_before_after": full_before,
        "workspace_identity": identity,
        "fresh_Qt_storage": True,
        "copied_workspace": validate_workspace(
            target, expected["workspace"], exact_database=True
        ),
    }


def validate_active(profile, expected, identity):
    pointer = core.read_json(profile / "active-workspace.json")
    selection = pointer.get("workspace")
    core.require(
        set(pointer) == {"version", "workspace"}
        and pointer["version"] == 1
        and isinstance(selection, str)
        and re.fullmatch(r"workspaces/[0-9a-f]{32}", selection),
        "Imported workspace pointer invalid",
    )
    suffix = selection.split("/")[1]
    actual = {
        "workspace": hashlib.sha256(selection.encode()).hexdigest(),
        "qt_profile": hashlib.sha256(("web-profile-" + suffix).encode()).hexdigest(),
    }
    core.require(actual == identity, "Active workspace or Qt profile changed")
    return validate_workspace(
        profile / selection, expected["workspace"], exact_database=False
    )
