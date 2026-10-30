"""Private desktop profile and explicit, verified workspace-generation selection."""

import fcntl
import json
import os
import re
import stat
from pathlib import Path

from .identity import DEVELOPMENT_ID

APP_ID = DEVELOPMENT_ID


def private_directory(path: Path):
    path = path.absolute()
    # Inspect each existing component before mkdir/resolve can follow a symlink.
    for component in reversed((path, *path.parents)):
        if component.is_symlink():
            raise ValueError("Symbolic links are not allowed in desktop storage")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.is_dir() or path.stat().st_uid != os.getuid():
        raise ValueError("Desktop storage must be an owned directory")
    path.chmod(0o700)
    return path


def open_private(path: Path):
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    info = os.fstat(fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_nlink != 1
    ):
        os.close(fd)
        raise ValueError("Unsafe desktop storage file")
    os.fchmod(fd, 0o600)
    return fd


class Profile:
    def __init__(self, root: Path, *, recovery=False):
        self.root = private_directory(root)
        self.lock = open_private(self.root / ".instance.lock")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Refuse unsafe pre-existing content, including SQLite sidecars and
            # Qt profile files. Same-user replacement races remain a host limit.
            for directory, dirs, files in os.walk(self.root, followlinks=False):
                for name in dirs + files:
                    path = Path(directory) / name
                    if path.is_symlink() or path.stat().st_uid != os.getuid():
                        raise ValueError("Unsafe existing desktop profile")
                    if path.is_dir():
                        path.chmod(0o700)
                    elif path.is_file():
                        fd = open_private(path)
                        os.close(fd)
                    else:
                        raise ValueError("Unexpected special file in desktop profile")
            self.selection = "workspace"
            pointer = self.root / "active-workspace.json"
            self.pointer_error = False
            if pointer.exists():
                try:
                    fd = open_private(pointer)
                    with os.fdopen(fd, "r") as stream:
                        value = json.loads(stream.read(1025))
                    if not isinstance(value, dict) or value.get("version") != 1:
                        raise ValueError("Unsupported workspace pointer")
                    self.selection = value.get("workspace")
                    self.validate_selection(self.selection)
                    if not (self.root / self.selection / "engage.sqlite3").is_file():
                        raise ValueError("Selected workspace is missing")
                except (ValueError, TypeError, AttributeError):
                    if not recovery:
                        raise ValueError(
                            "Workspace pointer invalid; use backup and recovery"
                        ) from None
                    self.selection = "workspace"
                    self.pointer_error = True
            self.select_paths(self.selection)
            self.config = self.root / "desktop.json"
            fd = open_private(self.config)
            with os.fdopen(fd, "r") as stream:
                text = stream.read(1025)
            self.port = json.loads(text).get("port") if text else 0
            if type(self.port) is not int or not 0 <= self.port <= 65535:
                raise ValueError("Invalid desktop port configuration")
        except BaseException:
            os.close(self.lock)
            raise

    @staticmethod
    def validate_selection(selection):
        if not isinstance(selection, str) or not re.fullmatch(
            r"workspace|workspaces/[0-9a-f]{32}", selection
        ):
            raise ValueError("Invalid workspace selection")

    def select_paths(self, selection):
        self.validate_selection(selection)
        self.selection = selection
        self.data = private_directory(self.root / selection)
        suffix = "" if selection == "workspace" else "-" + selection.split("/")[1]
        self.qt = private_directory(self.root / ("web-profile" + suffix))
        self.cache = private_directory(self.root / ("web-cache" + suffix))
        self.database = self.data / "engage.sqlite3"

    def activate_workspace(self, selection):
        """Caller retains instance lock. Validate before one atomic pointer change."""
        self.validate_selection(selection)
        from app.migration import durable_json, inspect

        summary = inspect(self.root / selection)
        if summary["schema"] != 5:
            raise ValueError("Recovery workspace requires schema 5")
        suffix = "" if selection == "workspace" else "-" + selection.split("/")[1]
        private_directory(self.root / ("web-profile" + suffix))
        private_directory(self.root / ("web-cache" + suffix))
        durable_json(
            self.root / "active-workspace.json",
            {
                "version": 1,
                "workspace": selection,
            },
        )
        self.select_paths(selection)

    def remember_port(self, port):
        temporary = self.root / ".desktop.json.new"
        fd = open_private(temporary)
        with os.fdopen(fd, "w") as stream:
            json.dump({"version": 1, "port": port}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.config)
        directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        self.port = port

    def close(self):
        if self.lock is not None:
            os.close(self.lock)
            self.lock = None
