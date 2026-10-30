"""One stable, private desktop profile; no legacy-profile discovery/migration."""

import fcntl
import json
import os
import stat
from pathlib import Path

APP_ID = "org.cyrnava.CyrNava.Devel"


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
    def __init__(self, root: Path):
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
            self.data = private_directory(self.root / "workspace")
            self.qt = private_directory(self.root / "web-profile")
            self.cache = private_directory(self.root / "web-cache")
            self.database = self.data / "engage.sqlite3"
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
