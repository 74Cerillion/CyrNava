"""Build only an isolated, unpublished P2 review candidate on a regular host.

No installer, real-profile migration, publication or signing-key operations.
"""

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
APP_ID = "org.cyrnava.CyrNava.Devel"
REFS = (
    "org.kde.Platform//6.11",
    "org.kde.Sdk//6.11",
    "io.qt.PySide.BaseApp//6.11",
)
MIN_BUILD_FREE_BYTES = 4 * 1024**3


def manifest():
    return {
        "app-id": APP_ID,
        "branch": "p2",
        "runtime": "org.kde.Platform",
        "runtime-version": "6.11",
        "sdk": "org.kde.Sdk",
        "base": "io.qt.PySide.BaseApp",
        "base-version": "6.11",
        "command": "cyrnava",
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
                "name": "cyrnava",
                "buildsystem": "simple",
                "build-commands": [
                    "python3 -c 'import sys; assert sys.version_info[:2] == (3, 13)'",
                    "sha256sum --check wheels.sha256",
                    "python3 -m pip install --no-index --no-deps --no-compile --find-links=wheels --prefix=/app -r source/backend/requirements.txt",
                    "python3 -c 'import PySide6; from PySide6.QtCore import qVersion; from PySide6.QtWebEngineCore import qWebEngineVersion; assert all(v.startswith(\"6.11.\") for v in (PySide6.__version__, qVersion(), qWebEngineVersion()))'",
                    "mkdir -p /app/share/cyrnava /app/bin /app/share/applications /app/share/icons/hicolor/scalable/apps",
                    "cp -a source/. /app/share/cyrnava/",
                    "install -m755 cyrnava /app/bin/cyrnava",
                    f"install -m644 {APP_ID}.desktop /app/share/applications/{APP_ID}.desktop",
                    f"install -m644 source/desktop/icons/cyrnava.svg /app/share/icons/hicolor/scalable/apps/{APP_ID}.svg",
                ],
                "sources": [
                    {"type": "dir", "path": "application", "dest": "source"},
                    {"type": "dir", "path": "wheels", "dest": "wheels"},
                    {"type": "file", "path": "wheels.sha256"},
                    {"type": "file", "path": f"{APP_ID}.desktop"},
                    {
                        "type": "script",
                        "dest-filename": "cyrnava",
                        "commands": [
                            "cd /app/share/cyrnava",
                            'exec python3 -B -m desktop.native "$@"',
                        ],
                    },
                ],
            }
        ],
    }


def snapshot(source, destination):
    if source.is_symlink() or not source.is_dir():
        raise ValueError("Snapshot roots must be real source directories")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError("Source symlinks cannot enter the review snapshot")
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_file():
            if path.suffix.lower() in (
                ".sqlite",
                ".sqlite3",
                ".db",
                ".log",
                ".key",
                ".pem",
            ):
                raise ValueError("User data or secrets cannot enter the snapshot")
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def staging_root():
    configured = Path(os.environ.get("XDG_CACHE_HOME", ""))
    cache = configured if configured.is_absolute() else Path.home() / ".cache"
    root = cache / "cyrnava-builds/p2"
    for component in (root, *root.parents):
        if component.is_symlink():
            raise ValueError("Unsafe staging directory: symbolic link refused")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.stat().st_uid != os.getuid():
        raise ValueError("Staging directory must be owned")
    root.chmod(0o700)
    return root


def build_environment(directory):
    # The measured candidate uses about 2.3 GiB of build/cache/repository space.
    # Leave headroom and fail before downloading/copying on a nearly full volume.
    if shutil.disk_usage(directory).free < MIN_BUILD_FREE_BYTES:
        raise ValueError("At least 4 GiB free is required on the build filesystem")
    temporary = directory / "tmp"
    temporary.mkdir(mode=0o700, exist_ok=True)
    return {**os.environ, "TMPDIR": str(temporary)}


def stage(source=SOURCE):
    if not (source / "frontend/dist/index.html").is_file():
        raise ValueError("Build the frontend before staging")
    root = staging_root()
    directory = Path(tempfile.mkdtemp(prefix="review-", dir=root))
    app = directory / "application"
    for relative in ("backend/app", "frontend/dist", "desktop/native", "desktop/icons"):
        snapshot(source / relative, app / relative)
    (app / "backend/requirements.txt").write_bytes(
        (source / "backend/requirements.txt").read_bytes()
    )
    verification = app / "verification"
    verification.mkdir()
    shutil.copyfile(
        source / "packaging/flatpak/verify_native.py", verification / "verify_native.py"
    )
    shutil.copyfile(
        source / "packaging/flatpak/verify_outage.py", verification / "verify_outage.py"
    )
    (directory / "wheels").mkdir()
    (directory / f"{APP_ID}.json").write_text(json.dumps(manifest(), indent=2) + "\n")
    (directory / f"{APP_ID}.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=CyrNava Desktop Review\n"
        f"Exec=cyrnava\nIcon={APP_ID}\nTerminal=false\nCategories=Office;\n"
    )
    return directory


def checked(*args):
    return subprocess.check_output(args, text=True).strip()


def build(directory):
    environment = build_environment(directory)
    # A failed namespace check is a blocker, never grounds to disable a sandbox.
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
        env=environment,
    )
    refs = {
        ref: checked("flatpak", "info", "--user", "--show-commit", ref) for ref in REFS
    }
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
            "--platform=manylinux2014_x86_64",
            "--dest",
            str(directory / "wheels"),
            "-r",
            str(directory / "application/backend/requirements.txt"),
        ],
        check=True,
        env=environment,
    )
    hashes = {
        str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((directory / "application").rglob("*"))
        if p.is_file()
    }
    wheels = {
        str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((directory / "wheels").glob("*.whl"))
    }
    (directory / "wheels.sha256").write_text(
        "".join(f"{digest}  {path}\n" for path, digest in wheels.items())
    )
    (directory / "review-lock.json").write_text(
        json.dumps(
            {"runtime_commits": refs, "source_sha256": hashes, "wheel_sha256": wheels},
            indent=2,
        )
        + "\n"
    )
    # Existing locally installed runtime/BaseApp refs only; no silent runtime update.
    assert refs == {
        ref: checked("flatpak", "info", "--user", "--show-commit", ref) for ref in REFS
    }
    subprocess.run(
        [
            "flatpak-builder",
            "--user",
            "--install",
            "--disable-download",
            "--force-clean",
            "--repo=" + str(directory / "repo"),
            str(directory / "build"),
            str(directory / f"{APP_ID}.json"),
        ],
        cwd=directory,
        check=True,
        env=environment,
    )
    print("Installed only the private P2 review candidate. Run:")
    print(f"flatpak run --branch=p2 {APP_ID}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    directory = stage()
    print(f"Review snapshot: {directory}", flush=True)
    if args.build:
        try:
            build(directory)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            raise SystemExit(f"Review build stopped: {error}") from None
    else:
        print("Staged source only; no download, package build or install.")


if __name__ == "__main__":
    main()
