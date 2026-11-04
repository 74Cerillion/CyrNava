"""N3 read-only stopped-profile audit in an already verified application venv."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def check(application, profile):
    sys.path.insert(0, str(application / "backend"))
    sys.path.insert(0, str(application))
    from app.migration import inspect

    if not profile.exists():
        return {"status": "PASS", "scope": "never-launched-empty-profile"}
    selection = "workspace"
    pointer = profile / "active-workspace.json"
    if pointer.exists():
        value = json.loads(pointer.read_bytes())
        if value.get("version") != 1:
            raise ValueError("Unsupported workspace pointer")
        selection = value.get("workspace")
    if not isinstance(selection, str) or not re.fullmatch(
        r"workspace|workspaces/[0-9a-f]{32}", selection
    ):
        raise ValueError("Invalid workspace selection")
    workspaces = [profile / "workspace"] if (profile / "workspace").exists() else []
    generations = profile / "workspaces"
    if generations.exists():
        for entry in sorted(generations.iterdir()):
            # The unchanged recovery tool intentionally retains these beside
            # activated UUID workspaces. They are not extra workspace folders.
            if (
                re.fullmatch(r"migration-[0-9a-f]{32}\.json", entry.name)
                and entry.is_file()
            ):
                if json.loads(entry.read_bytes()).get("status") != "activated":
                    raise ValueError(
                        "Unfinished workspace recovery requires explicit review"
                    )
                continue
            if (
                re.fullmatch(r"pre-migration-[0-9a-f]{32}\.cyrnava", entry.name)
                and entry.is_file()
            ):
                continue
            if not re.fullmatch(r"[0-9a-f]{32}", entry.name) or not entry.is_dir():
                raise ValueError("Unexpected workspace generation")
            workspaces.append(entry)
    results = []
    for workspace in workspaces:
        summary = inspect(workspace)
        if summary["schema"] != 5:
            raise ValueError("N3 supports schema 5 without migration; data unchanged")
        results.append({"schema": summary["schema"], "counts": summary["counts"]})
    if not (profile / selection / "engage.sqlite3").is_file():
        raise ValueError("Selected workspace is missing")
    config = json.loads((profile / "desktop.json").read_bytes())
    port = config.get("port")
    if type(port) is not int or not 0 < port <= 65535:
        raise ValueError("Invalid persisted origin")
    return {
        "status": "PASS",
        "scope": "all-stopped-workspaces-read-only-domain-validation",
        "workspaces": results,
        "workspace_selection_sha256": hashlib.sha256(selection.encode()).hexdigest(),
        "origin_sha256": hashlib.sha256(
            f"http://127.0.0.1:{port}".encode()
        ).hexdigest(),
        "data_migrated": False,
        "GUI": "NOT EXECUTED",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("application", "profile", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = check(args.application, args.profile)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
