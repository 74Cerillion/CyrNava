"""Internal child entry point; not an HTTP/debug endpoint or user launcher."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from desktop.native.backend import worker

if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("This worker requires desktop-owned inherited descriptors")
    worker(*(int(value) for value in sys.argv[1:]))
