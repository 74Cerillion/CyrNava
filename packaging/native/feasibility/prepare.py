"""Bounded N1 assembly only. No installation, GUI, signing, Git writes or Flatpak."""

import argparse
import hashlib
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAP = 3 * 1024**3
HEADROOM = 1536 * 1024**2


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def allocated(root):
    return sum(p.lstat().st_blocks * 512 for p in root.rglob("*") if not p.is_symlink())


def budget(root):
    if shutil.disk_usage(root).free < HEADROOM or allocated(root) > CAP:
        raise ValueError("N1 disk budget exceeded")


def fresh(path):
    path = Path(path).absolute()
    if (
        path.parent != ROOT / "ci-output"
        or not path.name.startswith("p6-native-n1-")
        or path.exists()
        or any(p.is_symlink() for p in (path, *path.parents))
    ):
        raise ValueError("Fresh direct ci-output/p6-native-n1-* directory required")
    return path


def run(root, name, command, *, cwd=None, timeout=120):
    budget(root)
    print("N1: " + name, flush=True)
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_CONFIG_FILE=os.devnull,
        TMPDIR=str(root / "tmp"),
    )
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    log = root / (name + ".private.log")
    start = time.monotonic()
    with log.open("xb") as stream:
        child = subprocess.Popen(
            list(map(str, command)),
            cwd=cwd,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
        try:
            while child.poll() is None:
                if time.monotonic() - start > timeout:
                    raise TimeoutError("N1 operation timeout: " + name)
                budget(root)
                time.sleep(1)
        except BaseException:
            child.terminate()
            try:
                child.wait(10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(5)
            raise
    if child.returncode:
        raise RuntimeError("N1 operation failed: " + name)
    budget(root)


def copy(source, destination):
    if source.is_symlink() or not source.is_file():
        raise ValueError("Regular source file required")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "ci-output/p6-native-n1-1"
    )
    args = parser.parse_args()
    root = None
    record = {
        "status": "FAIL",
        "complete": False,
        "renderer": "NOT EXECUTED",
        "normal_launcher": "NOT EXECUTED",
        "candidate": None,
    }
    start = time.monotonic()
    os.umask(0o077)
    try:
        target = fresh(args.output)
        if platform.machine() != "x86_64" or sys.version_info[:2] != (3, 14):
            raise ValueError("Use host x86_64 ordinary Python3.14")
        if shutil.disk_usage(target.parent).free < CAP + HEADROOM:
            raise ValueError("N1 requires 4.5GiB free before assembly")
        target.mkdir(mode=0o700)
        root = target
        for name in ["tmp", "wheels", "client", "client/profile"]:
            (root / name).mkdir(mode=0o700)
        lock = json.loads((HERE / "dependencies.json").read_text())
        record["dependencies_sha256"] = sha(HERE / "dependencies.json")
        # These exact runtime pins were already approved; metadata cannot pick latest.
        for entry in lock["files"]:
            budget(root)
            path = root / "wheels" / entry["filename"]
            print("N1: acquire " + entry["filename"], flush=True)
            if not entry["url"].startswith("https://files.pythonhosted.org/"):
                raise ValueError("Unexpected wheel supplier")
            with (
                urllib.request.urlopen(entry["url"], timeout=30) as response,
                path.open("xb") as out,
            ):
                count = 0
                acquired_at = time.monotonic()
                while block := response.read(1024 * 1024):
                    count += len(block)
                    if time.monotonic() - acquired_at > 120:
                        raise TimeoutError("N1 bounded wheel download timeout")
                    if count > entry["bytes"]:
                        raise ValueError("Wheel size exceeds lock")
                    out.write(block)
            if path.stat().st_size != entry["bytes"] or sha(path) != entry["sha256"]:
                raise ValueError("Wheel hash/size mismatch")
        run(root, "venv", [sys.executable, "-B", "-m", "venv", root / ".venv"])
        python = root / ".venv/bin/python"
        run(
            root,
            "install-locked",
            [
                python,
                "-B",
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-index",
                "--no-cache-dir",
                "--no-compile",
                "--require-hashes",
                "--only-binary=:all:",
                "--find-links",
                root / "wheels",
                "-r",
                HERE / "requirements.lock",
            ],
        )
        run(root, "pip-check", [python, "-B", "-m", "pip", "--isolated", "check"])
        # Existing build tools, fresh frontend source/output: don't replace source dist.
        front = root / "frontend-build"
        front.mkdir()
        front_inputs = {}
        for path in (ROOT / "frontend").rglob("*"):
            rel = path.relative_to(ROOT / "frontend")
            if set(rel.parts) & {"node_modules", "dist", "test-results", ".cache"}:
                continue
            if path.is_file() and not path.is_symlink():
                copy(path, front / rel)
                front_inputs[str(rel)] = sha(path)
        (front / "node_modules").symlink_to(
            ROOT / "frontend/node_modules", target_is_directory=True
        )
        run(root, "frontend-build", ["npm", "run", "build"], cwd=front, timeout=180)
        application = root / "application"
        for relative in ["backend/app", "desktop/native"]:
            for path in (ROOT / relative).iterdir():
                if path.suffix in {".py", ".json"}:
                    copy(path, application / relative / path.name)
        shutil.copytree(front / "dist", application / "frontend/dist")
        copy(
            HERE / "n1_configuration.py",
            application / "desktop/native/n1_configuration.py",
        )
        identity = application / "desktop/native/build_identity.py"
        icon = application / "frontend/dist/assets/branding/cyrnava-256.png"
        identity.write_text(
            'APP_ID = "org.cyrnava.CyrNava.Devel"\nCHANNEL = "development"\n'
            'DEPLOYMENT = "native-n1"\n'
            'WINDOW_TITLE = "CyrNava — Native N1 feasibility"\n'
            f"EXPERIMENT_ROOT = {str(root)!r}\n"
            f"ICON_PATH = {str(icon)!r}\n"
        )
        helper = (
            root
            / ".venv/lib/python3.14/site-packages/PySide6/Qt/libexec/QtWebEngineProcess"
        )
        receipt = {
            "kind": "cyrnava-disposable-native-N1",
            "root": str(root),
            "synthetic_only": True,
            "helper": str(helper.relative_to(root)),
            "helper_sha256": sha(helper),
            "frontend_source": front_inputs,
            "application_files": {
                str(p.relative_to(application)): sha(p)
                for p in sorted(application.rglob("*"))
                if p.is_file()
            },
        }
        (root / "n1.json").write_text(json.dumps(receipt, indent=2) + "\n")
        receipt_digest = sha(root / "n1.json")
        (root / "launch.py").write_text(
            "import os,sys,hashlib\nfrom pathlib import Path\n"
            "root=Path(__file__).resolve().parent\n"
            f"EXPECTED_RECEIPT = {receipt_digest!r}\n"
            'receipt_hash = hashlib.sha256((root/"n1.json").read_bytes()).hexdigest()\n'
            "if receipt_hash != EXPECTED_RECEIPT:\n"
            ' raise SystemExit("N1 receipt changed")\n'
            'sys.path.insert(0,str(root/"application"))\n'
            "from desktop.native.application import configuration,run\n"
            "configuration()\n"
            'for key,value in [("XDG_DATA_HOME","data"),\n'
            ' ("XDG_CONFIG_HOME","config"),("XDG_CACHE_HOME","cache")]:\n'
            ' os.environ[key]=str(root/"client"/value)\n'
            "raise SystemExit(run())\n"
        )
        record.update(
            status="ASSEMBLED",
            candidate=str(root),
            receipt_sha256=sha(root / "n1.json"),
            launch_sha256=sha(root / "launch.py"),
            application_files=receipt["application_files"],
            source_head=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            source_patch_identity=sha(ROOT / "desktop/native/application.py"),
            wheel_bytes=sum(e["bytes"] for e in lock["files"]),
            installed_bytes=allocated(root / ".venv"),
        )
    except (
        OSError,
        ValueError,
        RuntimeError,
        TimeoutError,
        KeyboardInterrupt,
    ) as error:
        record.update(error_type=type(error).__name__)
        if isinstance(error, (ValueError, RuntimeError, TimeoutError)):
            record["error"] = str(error)
    finally:
        record.update(
            complete=True,
            seconds=round(time.monotonic() - start, 3),
            maximum_child_rss_KiB=resource.getrusage(
                resource.RUSAGE_CHILDREN
            ).ru_maxrss,
        )
        if root:
            record["allocated_bytes"] = allocated(root)
            record["filesystem_free_bytes"] = shutil.disk_usage(root).free
            (root / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        print(
            json.dumps(
                {k: v for k, v in record.items() if k != "application_files"}, indent=2
            ),
            flush=True,
        )
    return 0 if record["status"] == "ASSEMBLED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
