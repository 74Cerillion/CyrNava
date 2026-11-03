"""Install reviewed CyrNava source with locked upstream dependencies.

The source inventory detects changed inputs; initial authenticity is the user's
trust in the versioned GitHub source download. It is not a release signature.
No GUI, privilege elevation, Qt compilation or publication is performed here.
"""

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import urllib.parse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METADATA = "packaging/native/source-release.json"
TARGET = "ubuntu-26.04-x86_64-wayland-cpython314"
HEADROOM = 1536 * 1024**2
ADDITIONAL_CAP = 2 * 1024**3
INITIAL_FREE = HEADROOM + ADDITIONAL_CAP
TIME_LIMIT = 900
LOCKED_INPUTS = {
    "packaging/native/feasibility/dependencies.json": (
        "621c640f428886a7944b654fe6726f2b3ab82644e4911a051f8281ab392eb8a3"
    ),
    "packaging/native/feasibility/requirements.lock": (
        "24876b72281d5427fc9c5c41cdb19a918815e9547e74c5eb4d2c93ac22e4a576"
    ),
    "frontend/package-lock.json": (
        "e042666c21379d991e8034f01cc7bfa8ee7fcd566ed41eaf820aba82d0ca7165"
    ),
}
EXCLUDED = {
    "node_modules",
    "dist",
    ".venv",
    "__pycache__",
    "evidence",
    ".pytest_cache",
    ".ruff_cache",
    ".git",
    "wheels",
}
SOURCE_ROOTS = (
    "backend/app",
    "desktop/native",
    "packaging/native",
    "frontend/src",
    "frontend/public",
    "frontend/scripts",
)
EXTENSIONS = {
    ".py",
    ".json",
    ".toml",
    ".txt",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".css",
    ".svg",
    ".png",
    ".woff",
    ".woff2",
    ".lock",
    ".sh",
    ".c",
}
ROOT_FILES = (
    "LICENSE",
    ".nvmrc",
    "README.md",
    "BACKUP_RESTORE.md",
    "install.sh",
    "update.sh",
    "desktop/install_engine.py",
    "desktop/native_operations.py",
    "desktop/native_profile_check.py",
)


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def regular(path):
    path = Path(path).absolute()
    require(
        not any(p.is_symlink() for p in (path, *path.parents)), "Source symlink refused"
    )
    info = path.stat()
    require(
        stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
        "Regular source file required",
    )
    require(info.st_size <= 16 * 1024**2, "Source file exceeds 16MiB bound")
    return path


def source_files(root):
    """Exact consumed source allowlist, independent of Git and ignored files."""
    root = Path(root).absolute()
    result = {}
    for base in SOURCE_ROOTS:
        for path in (root / base).rglob("*"):
            relative = path.relative_to(root)
            if set(relative.parts) & EXCLUDED:
                continue
            if path.is_symlink():
                raise ValueError("Source symlink refused")
            if path.is_file() and path.suffix in EXTENSIONS:
                result[relative.as_posix()] = regular(path)
    for name in ROOT_FILES:
        result[name] = regular(root / name)
    for path in (root / "frontend").iterdir():
        if path.is_file() and path.suffix in {".json", ".ts", ".js", ".mjs", ".html"}:
            result[path.relative_to(root).as_posix()] = regular(path)
    for name in (
        "native-installation.md",
        "native-release-notes-v0.1.0.md",
        "native-dependencies.md",
        "native-source-obligations.md",
        "native-third-party-notices.txt",
        "native-redistribution.json",
    ):
        path = root / "docs" / name
        if path.exists():
            result[path.relative_to(root).as_posix()] = regular(path)
    return dict(sorted(result.items()))


def refresh_inventory(root):
    """Maintainer preparation only; never called by installation/update."""
    root = Path(root)
    metadata = json.loads((root / METADATA).read_text())
    metadata["source_files"] = {
        name: sha(path) for name, path in source_files(root).items() if name != METADATA
    }
    (root / METADATA).write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    return metadata


def verified_source(root):
    metadata = json.loads(regular(root / METADATA).read_text())
    require(
        metadata.get("format") == 1 and metadata.get("mode") == "source-online",
        "Unsupported source release metadata",
    )
    require(
        re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?",
            metadata.get("release_version", ""),
        ),
        "Explicit source release version required",
    )
    require(
        metadata.get("target") == TARGET
        and metadata.get("repository") == "https://github.com/74Cerillion/CyrNava",
        "Source target/repository mismatch",
    )
    files = source_files(root)
    observed = {name: sha(path) for name, path in files.items() if name != METADATA}
    require(
        bool(observed) and observed == metadata.get("source_files"),
        "Source snapshot changed or inventory incomplete; "
        "use a reviewed versioned source",
    )
    require(
        metadata.get("locked_inputs") == LOCKED_INPUTS,
        "Reviewed lock identities changed",
    )
    for name, expected in LOCKED_INPUTS.items():
        require(
            name in observed and observed[name] == expected,
            "Reviewed dependency/build lock changed",
        )
    return metadata, files


def npm_lock(root):
    package = json.loads(regular(root / "frontend/package.json").read_text())
    lock = json.loads(regular(root / "frontend/package-lock.json").read_text())
    require(lock.get("lockfileVersion") == 3, "Reviewed npm lock format required")
    require(
        package.get("scripts", {}).get("build") == "tsc --noEmit && vite build",
        "Unexpected frontend build command",
    )
    require(
        package.get("engines") == {"node": "24.x", "npm": "11.x"},
        "Reviewed Node/npm versions required",
    )
    packages = lock.get("packages")
    require(
        isinstance(packages, dict) and 1 < len(packages) < 2000,
        "Bounded npm lock required",
    )
    for name, entry in packages.items():
        if name == "":
            continue
        require(
            name.startswith("node_modules/")
            and ".." not in Path(name).parts
            and not entry.get("link"),
            "Local npm dependency refused",
        )
        url = urllib.parse.urlsplit(entry.get("resolved", ""))
        require(
            url.scheme == "https"
            and url.hostname == "registry.npmjs.org"
            and not url.username
            and not url.password
            and not url.query
            and not url.fragment
            and url.port is None,
            "Only official pinned npm registry packages permitted",
        )
        integrity = entry.get("integrity", "")
        require(
            re.fullmatch(r"sha512-[A-Za-z0-9+/]+={0,2}", integrity),
            "Every npm package requires SHA-512 integrity",
        )
        require(
            len(base64.b64decode(integrity[7:], validate=True)) == 64,
            "Full npm SHA-512 digest required",
        )
    require(
        not (root / ".npmrc").exists() and not (root / "frontend/.npmrc").exists(),
        "Repository npm configuration refused",
    )
    return {
        "entries": len(packages) - 1,
        "lifecycle_scripts": "DISABLED",
        "registry": "https://registry.npmjs.org",
    }


def prerequisites(root):
    engine = module("source_prerequisite_engine", root / "desktop/install_engine.py")
    engine.host_supported()
    import importlib.util

    require(
        importlib.util.find_spec("venv") is not None
        and importlib.util.find_spec("ensurepip") is not None,
        "Install Ubuntu python3.14-venv prerequisite explicitly",
    )
    paths = {}
    for name in (
        "node",
        "npm",
        "cc",
        "ldd",
        "readelf",
        "gsettings",
        "apparmor_parser",
        "gio",
        "desktop-file-validate",
    ):
        path = shutil.which(name)
        if (
            not path
            and name == "apparmor_parser"
            and Path("/usr/sbin/apparmor_parser").is_file()
        ):
            path = "/usr/sbin/apparmor_parser"
        require(
            path,
            "Missing prerequisite: "
            + name
            + "; review Ubuntu prerequisite instructions; no sudo executed",
        )
        paths[name] = path
    with tempfile.TemporaryDirectory(prefix="cyrnava-prerequisites-") as temporary:
        work = Path(temporary)
        (work / "tmp").mkdir()
        config_files(work)
        for name, major in (("node", 24), ("npm", 11)):
            value = subprocess.check_output(
                [paths[name], "--version"],
                text=True,
                timeout=10,
                env=safe_environment(work),
            ).strip()
            require(
                re.fullmatch(r"v?" + str(major) + r"\.[0-9]+\.[0-9]+", value),
                "Required " + name + " major version " + str(major),
            )
    return {
        "status": "PASS",
        "target": TARGET,
        "executables": paths,
        "administrator_actions": "NONE",
        "GUI": "NOT EXECUTED",
    }


def config_files(work):
    for name in ("npm-user.conf", "npm-global.conf"):
        with (work / name).open("x"):
            pass


def safe_environment(work):
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.lower().startswith("npm_config_")
        and key
        not in {
            "NODE_OPTIONS",
            "NODE_PATH",
            "PYTHONPATH",
            "PYTHONHOME",
            "PIP_INDEX_URL",
            "PIP_EXTRA_INDEX_URL",
            "PIP_TRUSTED_HOST",
        }
    }
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_CONFIG_FILE": os.devnull,
            "NPM_CONFIG_USERCONFIG": str(work / "npm-user.conf"),
            "NPM_CONFIG_GLOBALCONFIG": str(work / "npm-global.conf"),
            "NPM_CONFIG_REGISTRY": "https://registry.npmjs.org",
            "NPM_CONFIG_CACHE": str(work / "npm-cache"),
            "NODE_OPTIONS": "--max-old-space-size=1536",
            "TMPDIR": str(work / "tmp"),
        }
    )
    return environment


def run(work, name, command, *, cwd=None, timeout=300):
    print("CyrNava source: " + name, flush=True)
    start = time.monotonic()
    with (work / (name + ".private.log")).open("xb") as log:
        child = subprocess.Popen(
            list(map(str, command)),
            cwd=cwd,
            env=safe_environment(work),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            while child.poll() is None:
                require(
                    time.monotonic() - start <= timeout, "Operation timeout: " + name
                )
                allocated = sum(
                    path.lstat().st_blocks * 512
                    for path in work.rglob("*")
                    if not path.is_symlink()
                )
                require(
                    allocated <= ADDITIONAL_CAP,
                    "Source work exceeds 2GiB additional storage cap",
                )
                require(
                    shutil.disk_usage(work).free >= HEADROOM,
                    "Source build must retain 1.5GiB disk headroom",
                )
                time.sleep(1)
            code = child.returncode
        except BaseException:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(5)
            raise
    require(code == 0, "Operation failed: " + name + "; preserve private log")
    return {"status": "PASS", "seconds": round(time.monotonic() - start, 3)}


def free_space(work, root):
    for path in (work.parent, root.parent):
        parent = path
        while not parent.exists():
            parent = parent.parent
        require(
            shutil.disk_usage(parent).free >= INITIAL_FREE,
            "Source install requires 3.5GiB free on work and installation "
            "filesystems (2GiB additional cap + 1.5GiB headroom)",
        )


def assemble(root, work, metadata, sources, frontend, *, disposable):
    release = module("source_release_primitives", root / "packaging/native/release.py")
    apparmor = module("source_apparmor", root / "packaging/native/apparmor_support.py")
    operations = module("source_operations", root / "desktop/native_operations.py")
    files = {}
    for name, path in sources.items():
        if (
            name.startswith(("backend/app/", "desktop/native/"))
            and path.suffix in {".py", ".json"}
            and not any(
                piece in name
                for piece in (
                    "test_",
                    "sqlite_fault",
                    "n1_configuration",
                    "build_identity.py",
                )
            )
        ):
            files["application/" + name] = path
    for path in frontend.rglob("*"):
        require(not path.is_symlink(), "Frontend output symlink refused")
        if path.is_file():
            require(
                path.suffix
                in {
                    ".html",
                    ".js",
                    ".css",
                    ".png",
                    ".svg",
                    ".woff",
                    ".woff2",
                    ".txt",
                    ".json",
                    ".ico",
                },
                "Unexpected frontend output",
            )
            files[
                "application/frontend/dist/" + path.relative_to(frontend).as_posix()
            ] = regular(path)
    for name in (
        "install_engine.py",
        "native_operations.py",
        "native_profile_check.py",
    ):
        files[name] = regular(root / "desktop" / name)
    for name in (
        "launch.py",
        "provider_check.py",
        "apparmor_support.py",
        "bootstrap.c",
    ):
        files[name] = regular(root / "packaging/native" / name)
    for name, original in (
        ("system_schemas.py", "run_probe.py"),
        ("backend_check.py", "backend_check.py"),
        ("requirements.lock", "requirements.lock"),
        ("dependencies.json", "dependencies.json"),
    ):
        files[name] = regular(root / "packaging/native/feasibility" / original)
    files["notices/LICENSE"] = regular(root / "LICENSE")
    files["notices/frontend-third-party-notices.txt"] = regular(
        frontend / "third-party-notices.txt"
    )
    bootstrap = apparmor.compile_bootstrap(
        root / "packaging/native/bootstrap.c", work / "cyrnava-native"
    )
    files["cyrnava-native"] = work / "cyrnava-native"
    generated = {
        "application/desktop/native/build_identity.py": release.build_identity(
            "candidate" if disposable else "release"
        )
    }
    archive = work / "local-application.zip"
    inventory = {}
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as output:
        for name in sorted(set(files) | set(generated)):
            content = generated[name] if name in generated else files[name].read_bytes()
            mode = 0o700 if name == "cyrnava-native" else 0o600
            release.zip_write(output, name, content, mode)
            inventory[name] = {
                "bytes": len(content),
                "mode": mode,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
    source_record = {
        "format": 1,
        "mode": "source-online",
        "initial_trust": (
            "User-selected versioned GitHub source; inventory is change detection, "
            "not independent authentication"
        ),
        "repository": metadata["repository"],
        "version": metadata["release_version"],
        "files": {
            name: {"sha256": sha(path), "bytes": path.stat().st_size}
            for name, path in sources.items()
        },
    }
    release.write_json(work / "source-inventory.json", source_record)
    engine = module("source_manifest_engine", root / "desktop/install_engine.py")
    manifest = {
        "format": 1,
        "kind": "candidate" if disposable else "release",
        "version": metadata["release_version"],
        "target": TARGET,
        "app_id": "org.cyrnava.CyrNava.Devel"
        if disposable
        else "io.github._74Cerillion.CyrNava",
        "apparmor": apparmor.CONTRACT,
        "maintenance": operations.CONTRACT,
        "archive_sha256": sha(archive),
        "expanded_bytes": sum(info["bytes"] for info in inventory.values()),
        "files": inventory,
        "bootstrap_build": {
            key: value for key, value in bootstrap.items() if key != "seconds"
        },
        "n1_receipt_sha256": release.N1_RECEIPT,
        "installation_mode": "source-online",
        "source_snapshot_sha256": sha(work / "source-inventory.json"),
        "source_contract": engine.source_contract(source_record["files"]),
    }
    release.write_json(work / "manifest.json", manifest)
    require(
        not any(name.startswith("wheels/") for name in inventory),
        "Source payload must not bundle wheels",
    )
    return archive, work / "manifest.json"


def prepare(root, work, target, *, disposable=False):
    metadata, sources = verified_source(root)
    original_sources = {name: sha(path) for name, path in sources.items()}
    npm_record = npm_lock(root)
    preflight = prerequisites(root)
    engine = module("source_paths", root / "desktop/install_engine.py")
    work = engine.checked_path(work)
    target = engine.checked_path(target)
    require(
        not work.exists() and work.parent.is_dir(),
        "Fresh work directory with existing parent required; prior attempts preserved",
    )
    require(
        not work.is_relative_to(target) and not target.is_relative_to(work),
        "Work and installation roots must be separate",
    )
    free_space(work, target)
    work.mkdir(mode=0o700)
    (work / "tmp").mkdir(mode=0o700)
    config_files(work)
    stage = work / "frontend"
    stage.mkdir(mode=0o700)
    for name, path in sources.items():
        if name.startswith("frontend/"):
            destination = stage / Path(name).relative_to("frontend")
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(path, destination)
            require(
                sha(destination) == original_sources[name],
                "Frontend source changed while staging",
            )
    record = {
        "status": "FAIL",
        "complete": False,
        "mode": "source-online",
        "prerequisites": preflight,
        "npm": npm_record,
        "operations": {},
        "GUI": "NOT EXECUTED",
        "signature": "NOT CREATED",
        "scope": "source-online preparation and headless installation only",
        "ready_for_native_launch": False,
        "pending_host_boundary": (
            "Exact application-specific AppArmor policy review/load approval "
            "and focused owner desktop verification; no automatic sudo or GUI"
        ),
    }
    try:
        npm = preflight["executables"]["npm"]
        record["operations"]["npm-ci"] = run(
            work,
            "npm-ci",
            [
                npm,
                "ci",
                "--ignore-scripts",
                "--audit=false",
                "--fund=false",
                "--fetch-retries=1",
                "--fetch-timeout=60000",
            ],
            cwd=stage,
        )
        record["operations"]["frontend-build"] = run(
            work, "frontend-build", [npm, "--ignore-scripts", "run", "build"], cwd=stage
        )
        verified_source(root)
        archive, manifest = assemble(
            root, work, metadata, sources, stage / "dist", disposable=disposable
        )
        _final_metadata, final_sources = verified_source(root)
        require(
            {name: sha(path) for name, path in final_sources.items()}
            == original_sources,
            "Source changed during preparation; preserve this attempt",
        )
        record.update(
            status="PREPARED",
            archive_sha256=sha(archive),
            manifest_sha256=sha(manifest),
            source_inventory_sha256=sha(work / "source-inventory.json"),
        )
        return archive, manifest, record
    except BaseException as error:
        record.update(error_type=type(error).__name__, complete=True)
        raise
    finally:
        record["complete"] = True
        (work / "preparation-result.json").write_text(
            json.dumps(record, indent=2) + "\n"
        )


def default_work(root):
    engine = module("source_default_paths", root / "desktop/install_engine.py")
    cache = engine.private_directory(Path.home() / ".cache/cyrnava-source")
    return cache / ("attempt-" + str(time.time_ns()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=("install", "update"), default="install")
    parser.add_argument("--disposable", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--check-prerequisites", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--reinstall", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    owned_work = None
    try:
        verified_source(ROOT)
        npm_lock(ROOT)
        if args.check_prerequisites:
            print(json.dumps(prerequisites(ROOT), indent=2))
            return 0
        require(
            not args.disposable or args.root is not None,
            "Explicit disposable installation root required",
        )
        target = (
            args.root
            or Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
            / "cyrnava-application"
        )
        work = args.work_dir or default_work(ROOT)
        if not work.exists():
            owned_work = work
        archive, manifest, result = prepare(
            ROOT, work.absolute(), target.absolute(), disposable=args.disposable
        )
        if not args.prepare_only:
            engine = module("source_install_engine", ROOT / "desktop/install_engine.py")
            context = engine.source_context(
                ROOT, work / "source-inventory.json", archive, manifest
            )
            operation = (
                engine.install_from_source
                if args.operation == "install"
                else engine.update_from_source
            )
            options = {"disposable": args.disposable, "context": context}
            if args.operation == "update":
                options["reinstall"] = args.reinstall
            result["installation"] = operation(
                archive, manifest, target.absolute(), **options
            )
            result["status"] = "PASS"
        result["complete"] = True
        (work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        result = {
            "status": "FAIL",
            "complete": True,
            "mode": "source-online",
            "error_type": type(error).__name__,
            "error": str(error)
            if isinstance(error, ValueError)
            else "Preserve attempt and private operation logs; no automatic retry",
            "GUI": "NOT EXECUTED",
        }
        if (
            owned_work
            and owned_work.is_dir()
            and not (owned_work / "result.json").exists()
        ):
            (owned_work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
