"""Stage P1B; --build downloads dependencies and installs only the disposable test ID."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
ROOT = Path("/tmp/cyrnava-p1b")
APP_ID = "org.cyrnava.P1B"
REFS = ("org.kde.Platform//6.11", "org.kde.Sdk//6.11", "io.qt.PySide.BaseApp//6.11")


def copy_source(source, destination):
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Source symlink refused: {path}")
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_file():
            if path.suffix.lower() in (".db", ".sqlite", ".sqlite3"):
                raise ValueError("Database files must not enter the prototype snapshot")
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def manifest():
    return {
        "app-id": APP_ID,
        "branch": "p1b",
        "runtime": "org.kde.Platform",
        "runtime-version": "6.11",
        "sdk": "org.kde.Sdk",
        "base": "io.qt.PySide.BaseApp",
        "base-version": "6.11",
        "command": "cyrnava-p1b",
        "finish-args": [
            "--socket=wayland",
            "--device=dri",
            "--unshare=network",
            "--nofilesystem=host",
            "--nofilesystem=home",
            "--env=QT_QPA_PLATFORM=wayland",
            "--env=QT_QPA_PLATFORMTHEME=xdgdesktopportal",
            "--env=QTWEBENGINEPROCESS_PATH=/app/bin/QtWebEngineProcess",
            "--env=QTWEBENGINE_DICTIONARIES_PATH=/app/qtwebengine_dictionaries",
        ],
        "build-options": {"env": {"PYTHONPATH": "/app/lib/python3.13/site-packages"}},
        "modules": [
            {
                "name": "cyrnava-p1b",
                "buildsystem": "simple",
                "build-commands": [
                    "python3 -c 'import sys; assert sys.version_info[:2] == (3, 13), sys.version'",
                    "python3 -m pip install --no-index --no-deps --no-compile --find-links=wheels --prefix=/app -r source/backend/requirements.txt",
                    "python3 -c 'import PySide6; from PySide6.QtCore import qVersion; from PySide6.QtWebEngineCore import qWebEngineVersion; versions = (PySide6.__version__, qVersion(), qWebEngineVersion()); print(versions); assert all(v.startswith(\"6.11.\") for v in versions)'",
                    "mkdir -p /app/share/cyrnava /app/bin",
                    "cp -a source/. /app/share/cyrnava/",
                    "install -m755 cyrnava-p1b /app/bin/cyrnava-p1b",
                ],
                "sources": [
                    {"type": "dir", "path": "application", "dest": "source"},
                    {"type": "dir", "path": "wheels", "dest": "wheels"},
                    {
                        "type": "script",
                        "dest-filename": "cyrnava-p1b",
                        "commands": [
                            'exec python3 /app/share/cyrnava/prototypes/p1_desktop/desktop.py --p1b-flatpak "$@"'
                        ],
                    },
                ],
            }
        ],
    }


def stage():
    if not (SOURCE / "frontend/dist/index.html").is_file():
        raise ValueError(
            "Build the existing frontend first; no development server is used"
        )
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    if ROOT.is_symlink() or ROOT.stat().st_uid != os.getuid():
        raise ValueError("P1B staging root must be owned and not a symlink")
    ROOT.chmod(0o700)
    directory = Path(tempfile.mkdtemp(prefix="stage-", dir=ROOT))
    app = directory / "application"
    copy_source(SOURCE / "backend/app", app / "backend/app")
    copy_source(SOURCE / "frontend/dist", app / "frontend/dist")
    target = app / "prototypes/p1_desktop/desktop.py"
    target.parent.mkdir(parents=True)
    shutil.copyfile(SOURCE / "prototypes/p1_desktop/desktop.py", target)
    shutil.copyfile(
        SOURCE / "backend/requirements.txt", app / "backend/requirements.txt"
    )
    (directory / "wheels").mkdir()
    (directory / f"{APP_ID}.json").write_text(json.dumps(manifest(), indent=2) + "\n")
    return directory


def checked(*args):
    return subprocess.run(
        args, check=True, text=True, capture_output=True
    ).stdout.strip()


def build(directory):
    # Ordinary host terminal only. Never attempt to escape agent confinement.
    for name in ("flatpak", "flatpak-builder", "bwrap"):
        if not shutil.which(name):
            raise ValueError(f"Missing {name}; use the host preflight")
    subprocess.run(
        [
            "bwrap",
            "--unshare-user",
            "--unshare-pid",
            "--unshare-net",
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "/usr/bin/true",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--only-binary=:all:",
            "--python-version=3.13",
            "--implementation=cp",
            "--abi=cp313",
            "--platform=manylinux_2_28_x86_64",
            "--platform=manylinux_2_27_x86_64",
            "--platform=manylinux_2_17_x86_64",
            "--platform=manylinux2014_x86_64",
            "--dest",
            str(directory / "wheels"),
            "-r",
            str(directory / "application/backend/requirements.txt"),
        ],
        check=True,
    )
    subprocess.run(
        [
            "flatpak-builder",
            "--user",
            "--install",
            "--install-deps-from=flathub",
            "--repo=repository",
            "build",
            f"{APP_ID}.json",
        ],
        cwd=directory,
        check=True,
    )
    evidence = {
        "note": "Build/install only; runtime acceptance remains untested",
        "flatpak": checked("flatpak", "--version"),
        "builder": checked("flatpak-builder", "--version"),
        "refs": {
            ref: checked("flatpak", "info", "--user", "--show-commit", ref)
            for ref in REFS
        },
        "application_commit": checked(
            "flatpak", "info", "--user", "--show-commit", f"{APP_ID}//p1b"
        ),
        "permissions": checked(
            "flatpak", "info", "--user", "--show-permissions", f"{APP_ID}//p1b"
        ),
        "installed_size": checked(
            "flatpak", "info", "--user", "--show-size", f"{APP_ID}//p1b"
        ),
        "inputs_sha256": {
            str(path.relative_to(directory)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for top in (directory / "application", directory / "wheels")
            for path in sorted(top.rglob("*"))
            if path.is_file()
        },
    }
    (directory / "build-evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    print(f"Build evidence: {directory / 'build-evidence.json'}")
    print(f"Launch synthetic prototype: flatpak run --user {APP_ID}//p1b")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build",
        action="store_true",
        help="Host terminal: download, build and install only the private test ID",
    )
    args = parser.parse_args()
    os.umask(0o077)
    directory = stage()
    print(f"Disposable source snapshot: {directory}", flush=True)
    if args.build:
        build(directory)
    else:
        print(
            "Source-only staging. No dependency download, package build or installation."
        )


if __name__ == "__main__":
    main()
