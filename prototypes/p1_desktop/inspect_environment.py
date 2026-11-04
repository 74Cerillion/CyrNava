"""Reproduce P1 size/namespace probes; optional isolated blank Firefox comparison."""

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path("/tmp/cyrnava-p1")
SOURCE = Path(__file__).resolve().parents[2]


def inspect(firefox=False):
    ROOT.mkdir(parents=True, exist_ok=True)
    if ROOT.is_symlink() or ROOT.stat().st_uid != os.getuid():
        raise ValueError("Prototype root must be owned by you and not a symlink")
    ROOT.chmod(0o700)
    result = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "logical_cpus": os.cpu_count(),
        "flatpak": shutil.which("flatpak"),
        "flatpak_builder": shutil.which("flatpak-builder"),
        "dependencies": {},
    }
    for name in ("PySide6", "PySide6_Addons", "PySide6_Essentials", "shiboken6"):
        distribution = importlib.metadata.distribution(name)
        result["dependencies"][name] = {
            "version": distribution.version,
            "installed_bytes": sum(
                distribution.locate_file(path).stat().st_size
                for path in distribution.files or []
                if distribution.locate_file(path).is_file()
            ),
        }
    # Optional already-downloaded pip cache. Never downloads packages during measurement.
    for path in (ROOT / "pip-cache").rglob("*.body"):
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                metadata = next(
                    (
                        name
                        for name in archive.namelist()
                        if name.endswith(".dist-info/METADATA")
                    ),
                    None,
                )
                if metadata:
                    name = next(
                        (
                            line[6:]
                            for line in archive.read(metadata).decode().splitlines()
                            if line.startswith("Name: ")
                        ),
                        "",
                    )
                    if name in result["dependencies"]:
                        result["dependencies"][name]["download_bytes"] = (
                            path.stat().st_size
                        )
    result["environment_bytes"] = sum(
        path.stat().st_size
        for path in Path(sys.prefix).rglob("*")
        if path.is_file() and not path.is_symlink()
    )
    result["frontend_dist_bytes"] = sum(
        path.stat().st_size
        for path in (SOURCE / "frontend/dist").rglob("*")
        if path.is_file()
    )
    if shutil.which("bwrap"):
        code = "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(); c=socket.socket(); c.connect(s.getsockname()); a,_=s.accept(); a.sendall(b'p1'); assert c.recv(2)==b'p1'; print('private loopback bind/connect passed')"
        probe = subprocess.run(
            [
                "bwrap",
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
                "/usr/bin/python3.12",
                "-c",
                code,
            ],
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
        result["namespace_probe"] = {
            "exit_code": probe.returncode,
            "stdout": probe.stdout,
            "stderr": probe.stderr,
            "note": "Bubblewrap probe only; not an actual Flatpak package test",
        }
    if firefox:
        directory = Path(tempfile.mkdtemp(prefix="firefox-comparison-", dir=ROOT))
        profile = directory / "profile"
        profile.mkdir(mode=0o700)
        env = {
            **os.environ,
            "XDG_DATA_HOME": str(directory / "data"),
            "XDG_CONFIG_HOME": str(directory / "config"),
            "XDG_CACHE_HOME": str(directory / "cache"),
        }
        started = time.perf_counter()
        child = subprocess.Popen(
            [
                "/usr/bin/firefox",
                "--no-remote",
                "--profile",
                str(profile),
                "--new-window",
                "about:blank",
            ],
            env=env,
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = child.communicate(timeout=12)
            result["firefox_probe"] = {
                "exit_code": child.returncode,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "stderr": stderr.decode()[-5000:],
                "stdout": stdout.decode()[-1000:],
                "note": "Blank isolated Firefox launch only; not a full-app performance measurement",
            }
        except subprocess.TimeoutExpired:
            child.terminate()
            try:
                child.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.communicate(timeout=5)
            result["firefox_probe"] = {
                "ran_for_seconds": 12,
                "note": "Isolated Firefox remained running; full-app performance was not measured",
            }
    (ROOT / "environment.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--firefox",
        action="store_true",
        help="Attempt a blank dedicated Firefox profile; never use the normal profile",
    )
    inspect(parser.parse_args().firefox)
