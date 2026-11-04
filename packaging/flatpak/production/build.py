"""Pinned local production assembly. No installation, publication, signing or data access.

Copies a pinned BaseApp with flatpak build-init, installs hash-locked wheels as
cross-platform data using host pip (no target binary is executed), then uses
standard Flatpak finish/export/bundle commands with all validator sandboxes on.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2]
APP_ID = "io.github._74Cerillion.CyrNava"
BRANCH = "stable"
# flatpak build-export accepts an ISO 8601 date, not Unix epoch seconds.
EXPORT_TIMESTAMP = "2026-10-29T23:00:00Z"


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def output(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_refs():
    lock = json.loads((HERE / "toolchain.lock.json").read_text())
    if platform.machine() != lock["architecture"]:
        raise ValueError("This bounded package supports x86_64 only")
    for ref, expected in lock["refs"].items():
        actual = output("flatpak", "info", "--user", "--show-commit", ref)
        if actual != expected:
            raise ValueError(
                f"Pinned runtime mismatch for {ref}; expected {expected}. No automatic updates performed."
            )
    return lock


def copy_file(source, target):
    if source.is_symlink() or not source.is_file():
        raise ValueError("Only regular source files may enter production inputs")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def stage(directory, *, source=SOURCE, build_id="local-A"):
    if (
        not build_id
        or len(build_id) > 60
        or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
            for c in build_id
        )
    ):
        raise ValueError("Use a short alphanumeric local build ID")
    app = directory / "application"
    # Explicit code allowlists. New runtime modules require a reviewed list change.
    backend = [
        "__init__",
        "assets",
        "backup",
        "database",
        "desktop_security",
        "documents",
        "lifecycle",
        "main",
        "migration",
        "models",
        "profile",
        "release",
        "search",
        "search_index",
        "templates",
    ]
    native = [
        "__init__",
        "__main__",
        "application",
        "backend",
        "build_identity",
        "dialogs",
        "identity",
        "maintenance",
        "maintenance_io",
        "policy",
        "storage",
        "worker",
    ]
    for relative, names in (("backend/app", backend), ("desktop/native", native)):
        for name in names:
            copy_file(
                source / relative / (name + ".py"), app / relative / (name + ".py")
            )
    copy_file(
        source / "backend/app/document_format_v1.json",
        app / "backend/app/document_format_v1.json",
    )
    dist = source / "frontend/dist"
    for path in dist.rglob("*"):
        if path.is_symlink():
            raise ValueError("Frontend symlink refused")
        if path.is_file():
            relative = path.relative_to(dist)
            if path.suffix not in {
                ".html",
                ".js",
                ".css",
                ".txt",
                ".png",
                ".woff2",
                ".woff",
                ".ico",
            }:
                raise ValueError("Unexpected frontend output: " + str(relative))
            copy_file(path, app / "frontend/dist" / relative)
    if not (app / "frontend/dist/index.html").is_file():
        raise ValueError("Production frontend build missing")
    for name in (
        "requirements.lock",
        "build_identity.py",
        "cyrnava",
        "install_payload.py",
        APP_ID + ".desktop",
        APP_ID + ".metainfo.xml",
    ):
        copy_file(HERE / name, directory / name)
    for size in (16, 32, 48, 64, 128, 256, 512):
        copy_file(
            source / f"frontend/public/assets/branding/cyrnava-{size}.png",
            directory / f"icons/cyrnava-{size}.png",
        )
    notices = app / "third-party"
    for name in ("python-third-party-notices.txt", "dependencies-and-licenses.md"):
        copy_file(source / "docs" / name, notices / name)
    record = {
        "app_id": APP_ID,
        "channel": "production",
        "version": "0.1.0",
        "schema": 5,
        "build_id": build_id,
        "git_commit": output("git", "-C", source, "rev-parse", "HEAD"),
        "runtime_lock": json.loads((HERE / "toolchain.lock.json").read_text()),
        "source_sha256": {
            str(p.relative_to(directory)): sha(p)
            for p in sorted(directory.rglob("*"))
            if p.is_file()
        },
        "node": output("node", "--version"),
        "npm": output("npm", "--version"),
        "flatpak": output("flatpak", "--version"),
        "host_python": platform.python_version(),
        "reproducibility": "Pinned, hash-verified inputs; byte-for-byte reproducibility NOT VERIFIED",
        "frontend_lock_sha256": sha(source / "frontend/package-lock.json"),
        "frontend_package_sha256": sha(source / "frontend/package.json"),
        "packaging_tool_sha256": {
            name: sha(HERE / name)
            for name in (
                "build.py",
                "install_payload.py",
                APP_ID + ".json",
                "toolchain.lock.json",
            )
        },
        "metadata_license_approval": "Owner approved metadata-only CC0-1.0, 2026-10-30; code/logo unchanged",
    }
    (directory / "build-inputs.json").write_text(json.dumps(record, indent=2) + "\n")
    # Fixed manifest is copied, not derived by production-ID string replacement.
    copy_file(HERE / (APP_ID + ".json"), directory / (APP_ID + ".json"))
    return record


def assemble(directory):
    verify_refs()
    wheels = directory / "wheels"
    wheels.mkdir()
    common = [
        "--only-binary=:all:",
        "--python-version=3.13",
        "--implementation=cp",
        "--abi=cp313",
        "--platform=manylinux_2_28_x86_64",
        "--platform=manylinux2014_x86_64",
        "--require-hashes",
        "-r",
        str(directory / "requirements.lock"),
    ]
    run(
        sys.executable,
        "-m",
        "pip",
        "download",
        "--disable-pip-version-check",
        "--no-cache-dir",
        "--dest",
        wheels,
        *common,
    )
    target = directory / "build"
    run(
        "flatpak",
        "build-init",
        "--arch=x86_64",
        "--base=io.qt.PySide.BaseApp",
        "--base-version=6.11",
        target,
        APP_ID,
        "org.kde.Sdk",
        "org.kde.Platform",
        "6.11",
    )
    # Cross-install wheels as data; --no-compile avoids bytecode/toolchain drift.
    run(
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-index",
        "--find-links",
        wheels,
        "--no-deps",
        "--no-compile",
        "--target",
        target / "files/lib/python3.13/site-packages",
        *common,
    )
    record = json.loads((directory / "build-inputs.json").read_text())
    record["wheel_sha256"] = {p.name: sha(p) for p in sorted(wheels.glob("*.whl"))}
    (directory / "build-inputs.json").write_text(json.dumps(record, indent=2) + "\n")
    run(sys.executable, HERE / "install_payload.py", target / "files", directory)
    return finish(directory)


def finish(directory):
    directory = Path(directory).resolve()
    target = directory / "build"
    inputs = json.loads((directory / "build-inputs.json").read_text())
    if inputs.get("app_id") != APP_ID:
        raise ValueError("Not a CyrNava production build")
    manifest = json.loads((directory / (APP_ID + ".json")).read_text())
    verify_refs()  # Detect refs changing while copying, before producing an artifact.
    if not (target / "export").exists():
        run(
            "flatpak",
            "build-finish",
            "--command=cyrnava",
            *manifest["finish-args"],
            target,
        )
    from install_payload import audit

    report = audit(target / "files")
    inventory = directory / "package-inventory.json"
    if inventory.exists() and json.loads(inventory.read_text()) != report:
        raise ValueError("Payload changed after the recorded audit; rebuild required")
    inventory.write_text(json.dumps(report, indent=2) + "\n")
    run("desktop-file-validate", target / f"files/share/applications/{APP_ID}.desktop")
    run(
        "appstreamcli",
        "validate",
        "--no-net",
        target / f"files/share/metainfo/{APP_ID}.metainfo.xml",
    )
    run(
        "flatpak",
        "build-export",
        "--timestamp=" + EXPORT_TIMESTAMP,
        directory / "repo",
        target,
        BRANCH,
    )
    bundle = directory / (APP_ID + ".flatpak")
    run(
        "flatpak",
        "build-bundle",
        "--arch=x86_64",
        directory / "repo",
        bundle,
        APP_ID,
        BRANCH,
    )
    return {
        "status": "PASS",
        "bundle": str(bundle),
        "sha256": sha(bundle),
        "bytes": bundle.stat().st_size,
        "logical_installed_bytes": report["logical_bytes"],
        "ostree_commit": output(
            "ostree",
            "--repo=" + str(directory / "repo"),
            "rev-parse",
            f"app/{APP_ID}/x86_64/{BRANCH}",
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-id", default="local-A")
    parser.add_argument("--stage-only", action="store_true")
    parser.add_argument(
        "--output-directory",
        type=Path,
        help="New empty build directory (optional; default remains a private cache directory)",
    )
    parser.add_argument(
        "--finish",
        type=Path,
        help="Validate/export an assembled build, without rebuilding inputs",
    )
    args = parser.parse_args()
    if args.output_directory and args.finish:
        parser.error("--output-directory and --finish are mutually exclusive")
    os.umask(0o077)
    if args.finish:
        directory = args.finish.resolve()
        prior = directory / "result.json"
        if prior.exists():
            import time

            shutil.copyfile(
                prior,
                directory / ("result-before-finish-" + str(time.time_ns()) + ".json"),
            )
        result = {"status": "FAIL", "directory": str(directory), "app_id": APP_ID}
        try:
            result.update(finish(directory))
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            result.update(error_type=type(error).__name__, error=str(error))
        (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
        return 0 if result["status"] == "PASS" else 1
    cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    if not cache.is_absolute():
        raise SystemExit("XDG_CACHE_HOME must be absolute")
    root = cache / "cyrnava-builds/p4"
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise SystemExit("Symlink build root refused")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if shutil.disk_usage(root).free < 5 * 1024**3:
        raise SystemExit("At least 5 GiB free required on build volume")
    if args.output_directory:
        directory = args.output_directory.absolute()
        if any(p.is_symlink() for p in (directory, *directory.parents)):
            raise SystemExit("Symlink build output refused")
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    else:
        directory = Path(tempfile.mkdtemp(prefix=args.build_id + "-", dir=root))
    print("Build directory: " + str(directory), flush=True)
    result = {"status": "FAIL", "directory": str(directory), "app_id": APP_ID}
    try:
        if not args.stage_only:
            verify_refs()
            run(
                "npm",
                "ci",
                "--ignore-scripts",
                "--no-audit",
                "--no-fund",
                cwd=SOURCE / "frontend",
            )
            run("npm", "run", "build", cwd=SOURCE / "frontend")
        stage(directory, build_id=args.build_id)
        result.update({"status": "STAGED"} if args.stage_only else assemble(directory))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        result.update(error_type=type(error).__name__, error=str(error))
    finally:
        (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result["status"] in ("PASS", "STAGED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
