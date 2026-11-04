"""Read host/renderer namespace evidence for the disposable P1B app only. No signaling."""

import argparse
import configparser
import json
import os
from pathlib import Path

APP_ID = "org.cyrnava.P1B"


def inspect():
    result = {
        "note": "Raw host observations; inspect with in-app evidence, not an automatic security PASS",
        "host_namespaces": {
            key: os.readlink(f"/proc/self/ns/{key}")
            for key in ("user", "pid", "net", "mnt")
        },
        "processes": [],
        "unreadable_process_count": 0,
    }
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            if path.stat().st_uid != os.getuid():
                continue
            command = (path / "cmdline").read_bytes().split(b"\0")
            if not command or not (
                b"QtWebEngineProcess" in command[0]
                or b"/app/share/cyrnava/prototypes/p1_desktop/desktop.py" in command
            ):
                continue
            info = configparser.ConfigParser()
            info.read(path / "root/.flatpak-info")
            if info.get("Application", "name", fallback="") != APP_ID:
                continue
            status = (path / "status").read_text()
            role = (
                "renderer"
                if b"--type=renderer" in command
                else "webengine-helper"
                if b"QtWebEngineProcess" in command[0]
                else "backend"
                if b"--worker" in command
                else "desktop"
            )
            sample = {
                "host_pid": int(path.name),
                "role": role,
                "status": {
                    key: value.strip()
                    for line in status.splitlines()
                    for key, _, value in [line.partition(":")]
                    if key
                    in (
                        "Name",
                        "PPid",
                        "NSpid",
                        "NoNewPrivs",
                        "Seccomp",
                        "Seccomp_filters",
                    )
                },
                "namespaces": {
                    key: os.readlink(path / "ns" / key)
                    for key in ("user", "pid", "net", "mnt")
                },
                "instance_id": info.get(
                    "Instance", "instance-id", fallback="unavailable"
                ),
            }
            result["processes"].append(sample)
        except (OSError, configparser.Error):
            result["unreadable_process_count"] += 1
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(inspect(), indent=2))


if __name__ == "__main__":
    main()
