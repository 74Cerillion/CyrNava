"""Native installed layout; no environment switch can enable this deployment."""

import importlib.util
import sys
from pathlib import Path


def configuration(source):
    from . import build_identity

    release = Path(source).parent
    spec = importlib.util.spec_from_file_location(
        "cyrnava_native_installation", release / "install_engine.py"
    )
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    engine.host_supported()
    engine.require(
        Path(sys.prefix) == release / ".venv", "Installed private interpreter required"
    )
    receipt, manifest = engine.installed(release, check_providers=False)
    engine.require(
        build_identity.APP_ID == manifest["app_id"],
        "Native application identity mismatch",
    )
    profile = engine.checked_path(receipt["profile"])
    if manifest["kind"] == "candidate":
        engine.require(
            profile == release.parent.parent / "client/profile",
            "Candidate profile escaped isolation",
        )
    else:
        engine.require(
            profile == release.parent.parent.parent / "cyrnava/native",
            "Native profile mismatch",
        )
    return profile
