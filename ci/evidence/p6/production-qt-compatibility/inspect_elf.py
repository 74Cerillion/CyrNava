"""Read-only evidence reproducer; neither a package audit nor a native launch test."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLIENT = Path.home() / ".cache/p6/targeted-b-attempt-r12/client/flatpak"
APP = CLIENT / (
    "app/io.github._74Cerillion.CyrNava/x86_64/stable/"
    "f759380dca9aa36e4674ad6dffb24d3e2340342da5fe04537ac17031a3bada15/files"
)
OLD = CLIENT / (
    "runtime/org.kde.Platform/x86_64/6.11/"
    "76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473/files"
)
NEW = Path.home() / (
    ".cache/p6/gui-attempt-r4/client/flatpak/runtime/org.kde.Platform/x86_64/6.11/"
    "fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415/files"
)


def inspect(path):
    dynamic = subprocess.run(
        ["readelf", "--wide", "--dynamic", str(path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    symbols = subprocess.run(
        ["readelf", "--wide", "--dyn-syms", str(path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    required, exported = set(), set()
    for line in symbols.splitlines():
        fields = line.split()
        if len(fields) >= 8 and "QtPrivate_" in fields[7]:
            name = fields[7].replace("@@", "@")
            (required if fields[6] == "UND" else exported).add(name)
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "needed": re.findall(r"\(NEEDED\).*?\[(.*?)\]", dynamic),
        "rpath": re.findall(r"\(RPATH\).*?\[(.*?)\]", dynamic),
        "runpath": re.findall(r"\(RUNPATH\).*?\[(.*?)\]", dynamic),
        "private_version_requirements": sorted(required),
        "private_version_exports": sorted(exported),
    }


def collect(wheel_site):
    entries = {}
    paths = {
        "accepted/QtCore.abi3.so": APP
        / "lib/python3.13/site-packages/PySide6/QtCore.abi3.so",
        "historical/libQt6Core.so.6.11.2": OLD
        / "lib/x86_64-linux-gnu/libQt6Core.so.6.11.2",
        "updated/libQt6Core.so.6.11.3": NEW
        / "lib/x86_64-linux-gnu/libQt6Core.so.6.11.3",
        "accepted/libQt6WebEngineCore.so.6.11.1": APP
        / "lib/x86_64-linux-gnu/libQt6WebEngineCore.so.6.11.1",
        "wheel/QtCore.abi3.so": wheel_site / "PySide6/QtCore.abi3.so",
        "wheel/libQt6Core.so.6": wheel_site / "PySide6/Qt/lib/libQt6Core.so.6",
        "wheel/libQt6WebEngineCore.so.6": wheel_site
        / "PySide6/Qt/lib/libQt6WebEngineCore.so.6",
        "wheel/QtWebEngineProcess": wheel_site
        / "PySide6/Qt/libexec/QtWebEngineProcess",
        "wheel/wayland-plugin": wheel_site
        / "PySide6/Qt/plugins/platforms/libqwayland.so",
        "wheel/portal-plugin": wheel_site
        / "PySide6/Qt/plugins/platformthemes/libqxdgdesktopportal.so",
    }
    for label, path in paths.items():
        entries[label] = inspect(path)
    accepted = set(entries["accepted/QtCore.abi3.so"]["private_version_requirements"])
    wheel = set(entries["wheel/QtCore.abi3.so"]["private_version_requirements"])
    assert accepted and wheel, "Private-version requirement was not observed"
    cases = {}
    for name, requirements, provider, expected in [
        ("accepted_historical", accepted, "historical/libQt6Core.so.6.11.2", True),
        ("accepted_updated", accepted, "updated/libQt6Core.so.6.11.3", False),
        ("wheel_own_provider", wheel, "wheel/libQt6Core.so.6", True),
        (
            "wheel_wrong_historical_provider",
            wheel,
            "historical/libQt6Core.so.6.11.2",
            False,
        ),
    ]:
        missing = requirements - set(entries[provider]["private_version_exports"])
        assert (not missing) == expected, "Unexpected private-symbol boundary"
        cases[name] = {
            "matching_private_version_symbols": not missing,
            "missing": sorted(missing),
        }
    markers = [
        b"sandbox/linux/services/flatpak_sandbox.cc",
        b"org.freedesktop.portal.Flatpak",
        b"Your Flatpak version is too old",
    ]
    sandbox = {}
    for label in [
        "accepted/libQt6WebEngineCore.so.6.11.1",
        "wheel/libQt6WebEngineCore.so.6",
    ]:
        data = paths[label].read_bytes()
        sandbox[label] = {m.decode(): m in data for m in markers}
    return {
        "scope": (
            "Static readelf only; four private-symbol comparisons; "
            "no Flatpak compatibility certification"
        ),
        "entries": entries,
        "private_symbol_comparisons": cases,
        "flatpak_sandbox_markers": sandbox,
        "marker_limit": (
            "Absence is not a complete proof of unsupported sandboxing; "
            "a secure native renderer remains unverified"
        ),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel-site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.wheel_site)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print("Four static symbol comparisons matched the recorded expectations.")
