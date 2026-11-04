"""Explicit N1 payload configuration; copied only into the disposable experiment."""

import hashlib
import json
import os
import platform
import stat
import sys
import sysconfig
from pathlib import Path

FORBIDDEN = (
    "FLATPAK_ID",
    "PYTHONPATH",
    "PYTHONHOME",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "QT_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "QML_IMPORT_PATH",
    "QTWEBENGINE_DISABLE_SANDBOX",
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "QTWEBENGINE_REMOTE_DEBUGGING",
    "QTWEBENGINEPROCESS_PATH",
    "QTWEBENGINE_RESOURCES_PATH",
    "QTWEBENGINE_LOCALES_PATH",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def private_path(path):
    path = Path(path).absolute()
    require(
        not any(p.is_symlink() for p in (path, *path.parents)),
        "N1 symlink path refused",
    )
    require(path.is_dir(), "N1 directory missing")
    require(path.stat().st_uid == os.getuid(), "N1 owner mismatch")
    require(not path.stat().st_mode & 0o077, "N1 directory must be private")
    return path


def configuration(source):
    from . import build_identity

    require(os.geteuid() != 0, "N1 must not run as root")
    require(sys.version_info[:2] == (3, 14), "N1 requires ordinary CPython3.14")
    require(
        not sysconfig.get_config_var("Py_GIL_DISABLED"),
        "N1 requires ordinary GIL Python",
    )
    require(platform.machine() == "x86_64", "N1 requires x86_64")
    require(
        build_identity.APP_ID == "org.cyrnava.CyrNava.Devel",
        "N1 development identity required",
    )
    root = private_path(build_identity.EXPERIMENT_ROOT)
    require(Path(source) == root / "application", "N1 source layout mismatch")
    require(Path(sys.prefix) == root / ".venv", "N1 private interpreter required")
    require(not Path("/.flatpak-info").exists(), "N1 is a native-host experiment")
    require(
        not any(os.environ.get(k) for k in FORBIDDEN),
        "N1 unsafe environment override refused",
    )
    raw = (root / "n1.json").read_bytes()
    require(len(raw) <= 1024 * 1024, "N1 receipt oversized")
    receipt = json.loads(raw)
    require(
        receipt.get("kind") == "cyrnava-disposable-native-N1",
        "N1 receipt identity mismatch",
    )
    require(receipt.get("root") == str(root), "N1 receipt location mismatch")
    require(
        receipt.get("synthetic_only") is True, "N1 synthetic-data boundary required"
    )
    for name, expected in receipt["application_files"].items():
        relative = Path(name)
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            "N1 unsafe receipt path",
        )
        path = root / "application" / relative
        require(
            not any(p.is_symlink() for p in (path, *path.parents)),
            "N1 source link refused",
        )
        require(path.is_file(), "N1 payload file missing")
        with path.open("rb") as stream:
            require(
                hashlib.file_digest(stream, "sha256").hexdigest() == expected,
                "N1 payload changed",
            )
    profile = private_path(root / "client" / "profile")
    relative_helper = Path(receipt["helper"])
    require(
        not relative_helper.is_absolute() and ".." not in relative_helper.parts,
        "N1 helper traversal refused",
    )
    helper = root / relative_helper
    require(
        helper.is_relative_to(root / ".venv")
        and not any(p.is_symlink() for p in (helper, *helper.parents)),
        "N1 helper path refused",
    )
    require(
        helper.is_file() and helper.stat().st_mode & stat.S_IXUSR, "N1 helper missing"
    )
    with helper.open("rb") as stream:
        require(
            hashlib.file_digest(stream, "sha256").hexdigest()
            == receipt["helper_sha256"],
            "N1 helper changed",
        )
    # Wheel's own discovery is used. No loader-path or sandbox override is set.
    return profile
