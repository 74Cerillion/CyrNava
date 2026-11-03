"""N1 import/provider/ELF evidence only; never creates a GUI or a renderer."""

import argparse
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


def qt_maps(text):
    result = {}
    for line in text.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and "libQt6" in fields[5]:
            path = Path(fields[5])
            result.setdefault(path.name, set()).add(str(path))
    return {k: sorted(v) for k, v in result.items()}


def validate(record, prefix):
    require(record["python"] == [3, 14], "Wrong Python ABI")
    for name in ["pyside", "shiboken", "qt", "webengine"]:
        require(record[name] == "6.11.3", "Mismatched component: " + name)
    require(record["installed_record_hashes_valid"], "Installed wheel content changed")
    require(
        record["helper_resources_locales_plugins"],
        "Missing helper/resources/locales/plugins",
    )
    require(not record["missing_libraries"], "ELF dependency unresolved")
    require(record["qt_maps"], "Qt provider evidence missing")
    require(
        all(
            len(paths) == 1 and Path(paths[0]).is_relative_to(prefix)
            for paths in record["qt_maps"].values()
        ),
        "Foreign or duplicate Qt provider",
    )
    require(
        all(Path(p).is_relative_to(prefix) for p in record["binding_paths"]),
        "Foreign binding",
    )
    require(
        Path(record["plugins_path"]).is_relative_to(prefix),
        "Foreign Qt plugin search path",
    )
    return record


def run(root):
    sys.path.insert(0, str(root / "application"))
    from desktop.native.application import configuration

    configuration()
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

    modules = [
        QtCore,
        QtGui,
        QtWidgets,
        QtNetwork,
        QtWebChannel,
        QtWebEngineCore,
        QtWebEngineWidgets,
    ]
    site = Path(PySide6.__file__).parent
    helper = site / "Qt/libexec/QtWebEngineProcess"
    verified = 0
    for name in ["PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6"]:
        distribution = importlib.metadata.distribution(name)
        require(distribution.version == "6.11.3", "Wrong installed distribution")
        for entry in distribution.files:
            if entry.hash is None:
                continue
            path = distribution.locate_file(entry)
            require(
                path.is_file() and path.resolve().is_relative_to(root / ".venv"),
                "Installed file missing/escaped",
            )
            require(entry.hash.mode == "sha256", "Unexpected wheel digest")
            with path.open("rb") as stream:
                actual = (
                    base64.urlsafe_b64encode(
                        hashlib.file_digest(stream, "sha256").digest()
                    )
                    .decode()
                    .rstrip("=")
                )
            require(actual == entry.hash.value, "Installed wheel file hash mismatch")
            verified += 1
    selected = [Path(m.__file__) for m in modules] + [
        helper,
        site / "Qt/lib/libQt6Core.so.6",
        site / "Qt/lib/libQt6WebEngineCore.so.6",
    ]
    selected += list((site / "Qt/plugins/platforms").glob("*wayland*.so"))
    selected += list((site / "Qt/plugins/imageformats").glob("*.so"))
    selected += list((site / "Qt/plugins/tls").glob("*.so"))
    missing = []
    elf = {}
    for path in selected:
        dynamic = subprocess.run(
            ["readelf", "-d", str(path)],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        ).stdout
        linked = subprocess.run(
            ["ldd", str(path)], capture_output=True, text=True, timeout=20, check=True
        ).stdout
        missing += [line.strip() for line in linked.splitlines() if "not found" in line]
        elf[str(path.relative_to(root))] = {
            "dynamic": [
                line.strip()
                for line in dynamic.splitlines()
                if any(key in line for key in ["(RPATH)", "(RUNPATH)", "(NEEDED)"])
            ],
            "resolved": linked.replace(str(root), "<candidate>"),
        }
    private_abi = {}
    for path in [Path(QtCore.__file__), site / "Qt/lib/libQt6Core.so.6"]:
        symbols = subprocess.run(
            ["readelf", "--dyn-syms", "--wide", str(path)],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        ).stdout
        private_abi[str(path.relative_to(root))] = sorted(
            set(re.findall(r"QtPrivate_[0-9_]+", symbols))
        )
    record = {
        "python": list(sys.version_info[:2]),
        "pyside": PySide6.__version__,
        "shiboken": shiboken6.__version__,
        "qt": QtCore.qVersion(),
        "webengine": QtWebEngineCore.qWebEngineVersion(),
        "binding_paths": [str(Path(m.__file__)) for m in modules]
        + [shiboken6.__file__],
        "qt_maps": qt_maps(Path("/proc/self/maps").read_text()),
        "plugins_path": QtCore.QLibraryInfo.path(
            QtCore.QLibraryInfo.LibraryPath.PluginsPath
        ),
        "helper_resources_locales_plugins": all(
            p.exists()
            for p in [
                helper,
                site / "Qt/resources/qtwebengine_resources.pak",
                site / "Qt/resources/icudtl.dat",
                site / "Qt/translations/qtwebengine_locales/en-US.pak",
                site / "Qt/plugins/platforms/libqwayland.so",
            ]
        )
        and bool(list((site / "Qt/plugins/tls").glob("*.so"))),
        "installed_record_hashes_valid": True,
        "wheel_files_verified": verified,
        "missing_libraries": missing,
        "elf": elf,
        "private_abi": private_abi,
        "renderer": "NOT EXECUTED",
        "normal_launcher": "NOT EXECUTED",
    }
    return validate(record, root / ".venv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--record", default="providers.json")
    args = parser.parse_args()
    root = args.candidate.absolute()
    if "/" in args.record or not args.record.endswith(".json"):
        parser.error("Candidate-local JSON basename required")
    output = root / args.record
    if output.exists():
        raise SystemExit("Preserve existing providers.json")
    record = {
        "status": "FAIL",
        "complete": True,
        "renderer": "NOT EXECUTED",
        "normal_launcher": "NOT EXECUTED",
    }
    try:
        record.update(run(root))
        record["status"] = "PASS"
    except (ImportError, OSError, ValueError, subprocess.SubprocessError) as error:
        record["error_type"] = type(error).__name__
        if isinstance(error, ValueError):
            record["error"] = str(error)
        # Raw native loader messages remain in the private stderr file.
        import traceback

        traceback.print_exc()
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in record.items()
                if k
                in [
                    "status",
                    "complete",
                    "pyside",
                    "qt",
                    "webengine",
                    "error_type",
                    "error",
                    "renderer",
                ]
            },
            indent=2,
        )
    )
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
