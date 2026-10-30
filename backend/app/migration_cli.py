"""Explicit legacy backup preparation; no implicit profile discovery."""

import argparse
import json
from pathlib import Path

from app.migration import inspect, migrate, pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["inspect", "backup", "restore"])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "inspect":
            result = inspect(
                args.source, backup=(args.source / "manifest.json").exists()
            )
            result.pop("files")
        else:
            if args.destination is None:
                parser.error("--destination is required")
            operation = pack if args.operation == "backup" else migrate
            result = operation(
                args.source,
                args.destination,
                progress=lambda stage: print(json.dumps({"stage": stage}), flush=True),
            )
            result.pop("files", None)
        print(json.dumps({"status": "PASS", "result": result}))
        return 0
    except Exception:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": "Invalid, busy or inaccessible source; "
                    "check integrity, schema "
                    "support and free space. Existing data was not replaced.",
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
