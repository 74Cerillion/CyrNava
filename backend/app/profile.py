"""Cooperative Linux profile lock shared by backend processes and offline tools."""

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path


class ProfileBusy(Exception):
    pass


@contextmanager
def profile_lock(directory: Path, *, offline: bool = False):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(
        directory / ".engage.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600
    )
    try:
        mode = fcntl.LOCK_EX if offline else fcntl.LOCK_SH
        try:
            fcntl.flock(fd, mode | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ProfileBusy(
                "Stop all ENGAGE backend processes before backup or restore."
            ) from None
        yield
    finally:
        os.close(fd)
