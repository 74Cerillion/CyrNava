"""Download one hash-verified workflow linter; extract only its executable."""

import hashlib
import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path


def install(destination):
    lock = json.loads((Path(__file__).parent / "tools.json").read_text())["actionlint"]
    with urllib.request.urlopen(lock["url"], timeout=60) as response:
        data = response.read(20 * 1024 * 1024 + 1)
    if hashlib.sha256(data).hexdigest() != lock["sha256"]:
        raise ValueError("actionlint download hash mismatch")
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.getmember("actionlint")
        if not member.isfile() or member.size > 30 * 1024 * 1024:
            raise ValueError("Unexpected actionlint executable")
        source = archive.extractfile(member)
        if source is None:
            raise ValueError("Missing actionlint executable")
        # No archive-controlled path is extracted.
        target = destination / "actionlint"
        target.write_bytes(source.read())
        target.chmod(0o755)
    return target


if __name__ == "__main__":
    print(install(Path(sys.argv[1])))
