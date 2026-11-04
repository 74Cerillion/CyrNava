"""Installed-provider check before activation; no QApplication, GUI or renderer."""

import base64
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path


def require(value, message):
    if not value:
        raise ValueError(message)


def check(root):
    require(Path(sys.prefix) == root / ".venv", "Wrong private interpreter")
    require(sys.version_info[:2] == (3, 14), "Wrong Python ABI")
    dependencies = json.loads((root / "dependencies.json").read_text())
    files = {}
    # Validate the complete locked runtime closure, not just version strings.
    for entry in dependencies["files"]:
        distribution = importlib.metadata.distribution(entry["name"])
        require(distribution.version == entry["version"], "Wrong dependency version")
        for member in distribution.files:
            if member.hash is None:
                continue
            path = distribution.locate_file(member).absolute()
            require(
                not path.is_symlink() and path.resolve().is_relative_to(root / ".venv"),
                "Installed provider escaped private environment",
            )
            require(member.hash.mode == "sha256", "Wrong dependency digest algorithm")
            with path.open("rb") as stream:
                raw = hashlib.file_digest(stream, "sha256").digest()
            require(
                base64.urlsafe_b64encode(raw).decode().rstrip("=") == member.hash.value,
                "Installed dependency hash mismatch",
            )
            files[str(path.resolve().relative_to(root))] = raw.hex()
    import PySide6
    import shiboken6
    from PySide6 import (
        QtCore,
        QtGui,
        QtNetwork,
        QtWebChannel,
        QtWebEngineCore,
        QtWebEngineWidgets,
        QtWidgets,
    )

    versions = [
        PySide6.__version__,
        shiboken6.__version__,
        QtCore.qVersion(),
        QtWebEngineCore.qWebEngineVersion(),
    ]
    require(versions == ["6.11.3"] * 4, "Qt stack version mismatch")
    modules = [
        QtCore,
        QtGui,
        QtNetwork,
        QtWebChannel,
        QtWebEngineCore,
        QtWebEngineWidgets,
        QtWidgets,
    ]
    site = Path(PySide6.__file__).parent
    required = [
        site / "Qt/libexec/QtWebEngineProcess",
        site / "Qt/resources/icudtl.dat",
        site / "Qt/resources/qtwebengine_resources.pak",
        site / "Qt/translations/qtwebengine_locales/en-US.pak",
        site / "Qt/plugins/platforms/libqwayland.so",
    ]
    require(
        all(p.is_file() for p in required)
        and list((site / "Qt/plugins/tls").glob("*.so")),
        "Required renderer/helper/resources/plugins missing",
    )
    paths = [
        Path(line.split(maxsplit=5)[5])
        for line in Path("/proc/self/maps").read_text().splitlines()
        if "libQt6" in line and len(line.split(maxsplit=5)) == 6
    ]
    require(
        paths and all(p.is_relative_to(root / ".venv") for p in paths),
        "Foreign Qt provider loaded",
    )
    require(
        all(Path(m.__file__).is_relative_to(root / ".venv") for m in modules),
        "Foreign binding",
    )
    require(
        Path(
            QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PluginsPath)
        ).is_relative_to(root / ".venv"),
        "Foreign plugin search path",
    )
    selected = [Path(m.__file__) for m in modules] + [required[0]]
    selected += list((site / "Qt/plugins/platforms").glob("*wayland*.so"))
    selected += list((site / "Qt/plugins/imageformats").glob("*.so"))
    selected += list((site / "Qt/plugins/tls").glob("*.so"))
    for path in selected:
        linked = subprocess.run(
            ["/usr/bin/ldd", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout
        require("not found" not in linked, "Missing OS library")
        for library, provider in re.findall(r"(libQt6[^ ]+) => ([^ ]+)", linked):
            require(
                Path(provider).is_relative_to(root / ".venv"),
                "Foreign Qt ELF dependency: " + library,
            )
    return {
        "status": "PASS",
        "scope": "installed-imports-providers-and-ELF",
        "versions": versions,
        "provider_files": files,
        "renderer": "NOT EXECUTED",
        "GUI": "NOT EXECUTED",
        "loaded_qt": sorted({str(p.relative_to(root)) for p in paths}),
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    try:
        value = check(root)
        (root / "providers.json").write_text(json.dumps(value, indent=2) + "\n")
        print(json.dumps({k: v for k, v in value.items() if k != "provider_files"}))
    except (OSError, ValueError, ImportError, subprocess.SubprocessError):
        # Native loader details stay in the installer's private operation log.
        import traceback

        traceback.print_exc()
        raise SystemExit(1) from None
