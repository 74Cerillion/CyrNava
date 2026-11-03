"""Bounded source-online CI checks; upload safe records, never installed binaries."""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import stat
import subprocess
import time
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE_LIMIT = 32 * 1024**2
SOURCE_FILES_LIMIT = 3000
SOURCE_METADATA = "packaging/native/source-release.json"
FLOOR = 5 * 1024**3
FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "ci-output",
    "dist",
    "build",
}
FORBIDDEN_SUFFIXES = {".whl", ".zip", ".tgz", ".xz", ".so", ".exe", ".dll", ".pyc"}


def require(value, message):
    if not value:
        raise ValueError(message)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def copy_source(root, destination, sources):
    """Copy explicit sources; no development environment or Git is inherited."""
    root, destination = root.absolute(), destination.absolute()
    require(not destination.exists(), "Fresh source snapshot required")
    require(
        not any(
            p.is_symlink()
            for p in (root, *root.parents, destination, *destination.parents)
        ),
        "Source snapshot symlink refused",
    )
    require(0 < len(sources) <= SOURCE_FILES_LIMIT, "Source inventory size refused")
    records, total = {}, 0
    for name, path in sorted(sources.items()):
        relative = PurePosixPath(name)
        require(
            name == str(relative)
            and name
            and not relative.is_absolute()
            and ".." not in relative.parts
            and "\\" not in name
            and not any(ord(c) < 32 or ord(c) == 127 for c in name)
            and not FORBIDDEN_PARTS.intersection(relative.parts)
            and relative.suffix.lower() not in FORBIDDEN_SUFFIXES
            and ".so." not in relative.name,
            "Non-source snapshot input refused",
        )
        path = Path(path).absolute()
        require(path == root / name, "Source inventory path mismatch")
        require(
            not any(p.is_symlink() for p in (path, *path.parents)),
            "Source input symlink refused",
        )
        info = path.stat()
        require(
            stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
            "Regular source input required",
        )
        total += info.st_size
        require(total <= SOURCE_LIMIT, "Source snapshot byte bound exceeded")
        records[name] = {"bytes": info.st_size, "sha256": digest(path)}
    destination.mkdir(mode=0o700)
    for name, record in records.items():
        target = destination / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (root / name).open("rb") as source, target.open("xb") as output:
            shutil.copyfileobj(source, output)
        target.chmod(0o700 if target.suffix == ".sh" else 0o600)
        require(digest(target) == record["sha256"], "Source changed during snapshot")
    return {"files": records, "source_files": len(records), "source_bytes": total}


def verify_source(snapshot, records):
    require(
        all(
            digest(snapshot / name) == info["sha256"]
            for name, info in records["files"].items()
        ),
        "Reviewed source snapshot changed",
    )
    require(
        all(
            not (snapshot / name).exists()
            for name in (
                ".git",
                ".venv",
                "frontend/node_modules",
                "frontend/dist",
                "wheels",
            )
        ),
        "Clean source snapshot contains generated inputs",
    )


def run_operation(command, log, timeout=900):
    with log.open("xb") as stream:
        child = subprocess.Popen(
            list(map(str, command)),
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            code = child.wait(timeout)
            if code:
                raise subprocess.CalledProcessError(code, command)
        except BaseException:
            if child.poll() is None:
                # Let the installer unwind its own retained operation groups first.
                os.killpg(child.pid, signal.SIGINT)
                try:
                    child.wait(15)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(5)
            raise


def child_diagnostic(log):
    """Translate terminal installer JSON into fixed public text, never raw output."""
    result = {
        "failure_category": "child-process-failed",
        "diagnostic_reason": (
            "Private child output retained; reason not safely classified"
        ),
    }
    try:
        with log.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 65536))
            tail = stream.read(65536).decode("utf-8", errors="replace")
        child = json.loads(tail[tail.rfind("\n{") + 1 :])
    except (OSError, ValueError):
        return result
    if not isinstance(child, dict) or (
        child.get("status") != "FAIL" or child.get("mode") != "source-online"
    ):
        return result
    if child.get("error_type") in (
        "ValueError",
        "FileNotFoundError",
        "PermissionError",
        "CalledProcessError",
        "TimeoutExpired",
        "KeyboardInterrupt",
    ):
        result["child_error_type"] = child["error_type"]
    reasons = {
        (
            "Fresh work directory with existing parent required; "
            "prior attempts preserved"
        ): (
            "fresh-work-path-refused",
            "Fresh work directory or existing parent required",
        ),
        "Install Ubuntu python3.14-venv prerequisite explicitly": (
            "missing-prerequisite",
            "Ubuntu python3.14-venv prerequisite missing",
        ),
        "Required node major version 24": ("prerequisite-version", "Node 24 required"),
        "Required npm major version 11": ("prerequisite-version", "npm 11 required"),
    }
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
        reasons[
            f"Missing prerequisite: {name}; "
            "review Ubuntu prerequisite instructions; no sudo executed"
        ] = ("missing-prerequisite", f"Required Ubuntu executable missing: {name}")
    for name in ("npm-ci", "frontend-build"):
        reasons[f"Operation failed: {name}; preserve private log"] = (
            "installer-operation-failed",
            f"Installer operation failed: {name}",
        )
    message = child.get("error")
    if child.get("error_type") == "ValueError" and isinstance(message, str):
        if message in reasons:
            result["failure_category"], result["diagnostic_reason"] = reasons[message]
    return result


SEED = r"""
import io, json, os, sys
from pathlib import Path
os.umask(0o077)
application, root = map(Path, sys.argv[1:])
sys.path.insert(0, str(application / "backend"))
sys.path.insert(0, str(application))
from PIL import Image
from app.assets import AssetStore
from app.database import Database
from desktop.native.storage import Profile
profile = Profile(root)
try:
    database = Database(profile.database)
    database.initialize()
    folder = database.create_folder("Source update synthetic folder", None)
    document = [{"type":"paragraph", "content":[{
        "type":"text", "text":"Source update retained text",
        "styles":{"bold":True}
    }]}]
    note = database.create("Source update synthetic note", document, 1, folder["id"])
    image = io.BytesIO()
    Image.new("RGB", (16,16), (20,80,140)).save(image, format="PNG")
    asset = AssetStore(database).upload(note["id"], image.getvalue(), "image/png")
    database.update(note["id"], note["revision"], {
        "document_json": document + [{"type":"image", "props":{
            "url":asset["url"], "caption":"Synthetic image"
        }}]
    })
    profile.remember_port(49152)
    (profile.qt / "source-ci-synthetic-state.json").write_text('{"synthetic":true}\n')
    print(json.dumps({"status":"PASS", "scope":"synthetic domain API seed",
        "GUI":"NOT EXECUTED", "browser":"NOT EXECUTED",
        "folders":1, "notes":1, "images":1}))
finally:
    profile.close()
"""


def installed(engine, client):
    current = engine.load(client / "current.json")
    release = client / "releases" / current["release"]
    receipt, manifest = engine.installed(release)
    return release, receipt, manifest


def install_command(snapshot, client, work, *, update=False):
    return [
        "bash",
        snapshot / ("update.sh" if update else "install.sh"),
        "--disposable",
        "--root",
        client,
        "--work-dir",
        work,
    ]


def next_fixture_version(value):
    """Change a synthetic release ID, preserving application/runtime versions."""
    core, separator, suffix = value.partition("-")
    numbers = core.split(".")
    require(
        len(numbers) == 3 and all(n.isdecimal() for n in numbers),
        "Invalid fixture version",
    )
    if separator:
        parts = suffix.split(".")
        require(parts[-1].isdecimal(), "Numeric fixture suffix required")
        parts[-1] = str(int(parts[-1]) + 1)
        return core + "-" + ".".join(parts)
    numbers[-1] = str(int(numbers[-1]) + 1)
    return ".".join(numbers)


def run(args):
    output = args.output.absolute()
    require(
        output.parent == ROOT / "ci-output"
        and not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "Fresh direct repository output required",
    )
    require(
        shutil.disk_usage(ROOT).free >= FLOOR + 6 * 1024**3,
        "Keep 11GiB free for two bounded source builds and private environments",
    )
    output.parent.mkdir(mode=0o700, exist_ok=True)
    output.mkdir(mode=0o700)
    public = output / "artifacts"
    public.mkdir(mode=0o700)
    record = {
        "status": "FAIL",
        "complete": False,
        "scope": "no-Git source-online install and synthetic release update; no GUI",
        "GUI": "NOT EXECUTED",
        "renderer": "NOT EXECUTED",
        "host_policy": "NOT LOADED",
        "production_signature": "NOT CREATED",
        "public_payload": (
            "safe JSON only; no wheels, frontend bundle or installed tree"
        ),
        "steps": [],
    }
    started, stage = time.monotonic(), "source-preflight"
    try:
        source = module(
            "native_source_install", ROOT / "packaging/native/source_install.py"
        )
        engine = module("native_source_engine", ROOT / "desktop/install_engine.py")
        engine.host_supported()
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=10
        ).strip()
        require(
            not subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, timeout=10
            ),
            "CI requires clean committed source",
        )
        snapshot = output / "source"
        source_record = copy_source(ROOT, snapshot, source.source_files(ROOT))
        verify_source(snapshot, source_record)
        record["source_commit"] = commit
        record["source_snapshot"] = {
            key: value for key, value in source_record.items() if key != "files"
        }
        write_json(
            public / "source-snapshot.json", {"source_commit": commit, **source_record}
        )
        record["steps"].append(
            {
                "operation": stage,
                "status": "PASS",
                "Git_metadata": "ABSENT",
                "wheelhouse": "ABSENT",
                "frontend_build": "ABSENT",
            }
        )
        client = snapshot / "ci-output/client"
        stage = "online-source-install"
        (snapshot / "ci-output").mkdir(mode=0o700)
        print("CI: " + stage, flush=True)
        run_operation(
            install_command(snapshot, client, snapshot / "ci-output/install-work"),
            output / "install.private.log",
        )
        release, receipt, manifest = installed(engine, client)
        record["steps"].append(
            {
                "operation": stage,
                "status": "PASS",
                "provider_files": len(receipt["provider_files"]),
                "archive_sha256": manifest["archive_sha256"],
            }
        )
        stage = "synthetic-profile-seed"
        run_operation(
            [
                release / ".venv/bin/python",
                "-B",
                "-I",
                "-c",
                SEED,
                release / "application",
                receipt["profile"],
            ],
            output / "profile-seed.private.log",
            timeout=60,
        )
        operations = engine.support(release, "native_operations")
        before = operations.inventory(engine, Path(receipt["profile"]))
        require(before["exists"] and before["files"], "Synthetic profile seed missing")
        old_release = release
        stage = "source-update-fixture"
        config_path = snapshot / SOURCE_METADATA
        config = json.loads(config_path.read_text())
        previous = config["release_version"]
        config["release_version"] = next_fixture_version(previous)
        config_path.write_text(json.dumps(config, sort_keys=True, indent=2) + "\n")
        record["update_fixture"] = {
            "scope": "synthetic packaging identifier only; not a public version",
            "before": previous,
            "after": config["release_version"],
            "source_release_sha256": digest(config_path),
        }
        require(
            all(
                digest(snapshot / name) == info["sha256"]
                for name, info in source_record["files"].items()
                if name != SOURCE_METADATA
            ),
            "Update fixture changed non-version source",
        )
        stage = "online-source-update"
        print("CI: " + stage, flush=True)
        run_operation(
            install_command(
                snapshot, client, snapshot / "ci-output/update-work", update=True
            ),
            output / "update.private.log",
        )
        release, receipt, manifest = installed(engine, client)
        require(
            release != old_release and old_release.is_dir(),
            "Versioned update did not retain old release",
        )
        require(
            operations.inventory(engine, Path(receipt["profile"])) == before,
            "Synthetic profile bytes changed during source update",
        )
        require(
            not (client / "transaction.json").exists(),
            "Source transaction did not finish",
        )
        record["steps"].append(
            {
                "operation": stage,
                "status": "PASS",
                "provider_files": len(receipt["provider_files"]),
                "profile_bytes_unchanged": True,
                "old_release_retained": True,
            }
        )
        require(
            shutil.disk_usage(ROOT).free >= FLOOR,
            "Free-space floor crossed; preserve output",
        )
        record["status"] = "PASS"
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        KeyboardInterrupt,
    ) as error:
        record.update(failed_operation=stage, error_type=type(error).__name__)
        if isinstance(error, subprocess.CalledProcessError):
            record["exit_code"] = error.returncode
            if stage in ("online-source-install", "online-source-update"):
                log = (
                    "install.private.log"
                    if stage.endswith("install")
                    else "update.private.log"
                )
                record.update(child_diagnostic(output / log))
    finally:
        record.update(complete=True, seconds=round(time.monotonic() - started, 3))
        write_json(public / "result.json", record)
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "complete": True,
                    "scope": "source-online CI preflight",
                    "error_type": type(error).__name__,
                    "GUI": "NOT EXECUTED",
                }
            ),
            flush=True,
        )
        return 1


if __name__ == "__main__":
    os.umask(0o077)
    raise SystemExit(main())
