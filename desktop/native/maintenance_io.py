"""Portal-granted file output. Private staging never assumes sibling grants."""

import os
import shutil
import stat
import tempfile
from pathlib import Path


def export_selected(archive, selected, private_root):
    from app.migration import unpack

    fd = os.open(
        selected, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600
    )
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size or info.st_nlink != 1:
            raise ValueError("Choose a new empty output file")
        with os.fdopen(fd, "wb", closefd=False) as out, archive.open("rb") as src:
            shutil.copyfileobj(src, out, 1024 * 1024)
            out.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    with tempfile.TemporaryDirectory(dir=private_root) as verify:
        unpack(Path(selected), Path(verify))
