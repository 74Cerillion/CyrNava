"""Installed native entry; the existing Qt application owns the GUI/backend."""

import importlib.util
import json
import re
import sys
from pathlib import Path

entry = Path(__file__).absolute().parent
release = entry
if sys.argv[1:] not in ([], ["--check"]):
    raise SystemExit("Only --check or normal application launch is supported")
if (entry / "current.json").is_file():
    current = json.loads((entry / "current.json").read_text())
    name = current.get("release", "")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?-[0-9a-f]{16}", name):
        raise SystemExit("Invalid native release selection")
    release = entry / "releases" / name
spec = importlib.util.spec_from_file_location(
    "cyrnava_installer", release / "install_engine.py"
)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
try:
    result = engine.launch(release, check_only=sys.argv[1:] == ["--check"])
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
        raise SystemExit(0)
    raise SystemExit(result)
except (OSError, ValueError) as error:
    print("CyrNava native launch refused: " + str(error), file=sys.stderr)
    raise SystemExit(1) from None
