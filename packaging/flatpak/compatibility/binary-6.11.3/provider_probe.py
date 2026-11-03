"""Read-only imports/provider checks INSIDE a candidate Flatpak build sandbox.

Does not instantiate QApplication or a renderer. Passing is NOT native success.
"""

import json
import mmap
import os
import subprocess
import sys
from pathlib import Path


def require(value, message):
    if not value:
        raise ValueError(message)


def verify(record):
    require(record["python"] == [3, 13], "Unexpected runtime Python ABI")
    for key in ("pyside", "shiboken", "qt", "webengine"):
        require(record[key] == "6.11.3", "Component version mismatch: " + key)
    require(record["bindings_in_app"], "Bindings outside application")
    require(record["shiboken_in_app"], "Shiboken outside application")
    require(not record["wheel_qt"], "Pip-bundled Qt provider refused")
    require(record["runtime_qt_core"], "Core Qt must use the approved KDE runtime")
    require(record["application_webengine"], "WebEngine must use the pinned BaseApp")
    require(record["unique_qt_providers"], "Duplicate loaded Qt provider")
    require(record["all_qt_providers_approved"], "Unexpected Qt library provider")
    require(
        record["resources"] and record["plugins"], "Missing helper/resources/plugins"
    )
    require(record["flatpak_integration_marker"], "Missing maintained sandbox marker")
    require(not record["missing_libraries"], "Unresolved ELF dependency")
    require(not record["sandbox_disabled"], "Sandbox disablement refused")
    return record


def main():
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

    modules = (
        QtCore,
        QtGui,
        QtWidgets,
        QtNetwork,
        QtWebChannel,
        QtWebEngineCore,
        QtWebEngineWidgets,
    )
    site = Path(PySide6.__file__).parent
    maps = set()
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and "libQt6" in fields[5]:
            maps.add(fields[5])
    providers = {}
    for path in sorted(maps):
        providers.setdefault(Path(path).name, []).append(path)
    web = [p for p in maps if Path(p).name.startswith("libQt6WebEngineCore.so")]
    missing = []
    elf = {}
    selected = [Path(m.__file__) for m in modules] + [
        Path("/app/bin/QtWebEngineProcess")
    ]
    for path in selected:
        result = subprocess.run(
            ["ldd", str(path)], capture_output=True, text=True, timeout=30, check=False
        )
        require(result.returncode == 0, "ELF inspection failed")
        elf[str(path)] = result.stdout
        missing += [
            line.strip() for line in result.stdout.splitlines() if "not found" in line
        ]
    marker = False
    if len(web) == 1:
        with (
            Path(web[0]).open("rb") as stream,
            mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as blob,
        ):
            marker = b"org.freedesktop.portal.Flatpak" in blob
    disabled = bool(os.environ.get("QTWEBENGINE_DISABLE_SANDBOX")) or any(
        flag in os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
        for flag in ("--no-sandbox", "--disable-seccomp", "--disable-namespace-sandbox")
    )
    record = {
        "python": list(sys.version_info[:2]),
        "pyside": PySide6.__version__,
        "shiboken": shiboken6.__version__,
        "qt": QtCore.qVersion(),
        "webengine": QtWebEngineCore.qWebEngineVersion(),
        "bindings_in_app": all(str(m.__file__).startswith("/app/") for m in modules),
        "shiboken_in_app": str(shiboken6.__file__).startswith("/app/"),
        "wheel_qt": (site / "Qt/lib").exists(),
        "runtime_qt_core": any(
            p.startswith("/usr/lib/") and Path(p).name.startswith("libQt6Core.so")
            for p in maps
        ),
        "application_webengine": len(web) == 1 and web[0].startswith("/app/lib/"),
        "unique_qt_providers": all(len(v) == 1 for v in providers.values()),
        "all_qt_providers_approved": bool(maps)
        and all(
            p.startswith("/app/lib/")
            if Path(p).name.startswith(
                ("libQt6WebEngine", "libQt6WebView", "libQt6Pdf")
            )
            else p.startswith("/usr/lib/")
            for p in maps
        ),
        "resources": all(
            Path(p).is_file()
            for p in (
                "/app/bin/QtWebEngineProcess",
                "/app/resources/qtwebengine_resources.pak",
                "/app/resources/v8_context_snapshot.bin",
                "/app/translations/qtwebengine_locales/en-US.pak",
            )
        ),
        "plugins": any(Path("/usr").glob("**/platforms/libqwayland*.so")),
        "flatpak_integration_marker": marker,
        "missing_libraries": missing,
        "sandbox_disabled": disabled,
        "loaded_qt_providers": providers,
        "elf_dependencies": elf,
        "qt_paths": {
            k: QtCore.QLibraryInfo.path(getattr(QtCore.QLibraryInfo.LibraryPath, k))
            for k in (
                "LibrariesPath",
                "PluginsPath",
                "LibraryExecutablesPath",
                "DataPath",
            )
        },
        "renderer": "NOT EXECUTED",
        "normal_launcher": "NOT EXECUTED",
    }
    verify(record)
    print(json.dumps(record), flush=True)


def static_elf():
    """SDK tools inspect payload bytes; this is separate from runtime imports."""
    paths = list(Path("/app/lib/python3.13/site-packages/PySide6").glob("Qt*.abi3.so"))
    paths += list(Path("/app/lib").glob("libQt6WebEngine*.so.6*"))
    paths += [Path("/app/bin/QtWebEngineProcess")]
    record = {}
    for path in paths:
        if path.is_symlink():
            continue
        record[str(path)] = {}
        for option in ("--dynamic", "--version-info"):
            result = subprocess.run(
                ["readelf", option, str(path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            record[str(path)][option] = result.stdout
    require(bool(record), "No candidate ELF inputs")
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    static_elf() if "--elf-only" in sys.argv else main()
