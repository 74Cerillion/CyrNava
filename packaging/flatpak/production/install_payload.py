"""Install the audited production payload; no host profiles or sandbox execution."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

APP_ID = "io.github._74Cerillion.CyrNava"


def install(prefix, inputs):
    prefix, inputs = Path(prefix), Path(inputs)
    target = prefix / "share/cyrnava"
    if target.exists():
        raise ValueError("Refuse to overlay an existing application payload")
    shutil.copytree(inputs / "application", target)
    # Explicit production module, never runtime text substitution or env override.
    shutil.copyfile(
        inputs / "build_identity.py", target / "desktop/native/build_identity.py"
    )
    binary = prefix / "bin"
    binary.mkdir(exist_ok=True)
    shutil.copyfile(inputs / "cyrnava", binary / "cyrnava")
    (binary / "cyrnava").chmod(0o755)
    for directory, filename in (
        ("applications", APP_ID + ".desktop"),
        ("metainfo", APP_ID + ".metainfo.xml"),
    ):
        dest = prefix / "share" / directory
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inputs / filename, dest / filename)
    for size in (16, 32, 48, 64, 128, 256, 512):
        dest = prefix / f"share/icons/hicolor/{size}x{size}/apps"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inputs / f"icons/cyrnava-{size}.png", dest / (APP_ID + ".png"))
    # Audited equivalent of the pinned BaseApp's development cleanup. Keep ALL
    # WebEngine resources, helper, runtime libraries, plugins, translations/licenses.
    for name in (
        "include",
        "mkspecs",
        "lib/cmake",
        "lib/pkgconfig",
        "lib/metatypes",
        "lib/modules",
        "lib/debug",
        "lib/plugins/designer",
    ):
        shutil.rmtree(prefix / name, ignore_errors=True)
    for name in (
        "cleanup-BaseApp.sh",
        "cleanup-BaseApp-QtWebEngine.sh",
        "manifest.json",
        "manifest-base-1.json",
    ):
        (prefix / name).unlink(missing_ok=True)
    for path in binary.iterdir():
        if path.name not in ("cyrnava", "QtWebEngineProcess"):
            path.unlink()
    site = prefix / "lib/python3.13/site-packages"
    for pattern in (
        "build",
        "build-*.dist-info",
        "pyproject_hooks*",
        "patchelf*",
        "shiboken6_generator*",
        "PySide6/scripts",
        "PySide6/doc",
    ):
        for path in site.glob(pattern):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
    for pattern in (
        "**/__pycache__",
        "**/tests",
        "**/test",
        "**/.agents",
        "**/.github",
    ):
        for path in list(site.glob(pattern)):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
    # Preserve upstream license texts; omit only metadata for other applications.
    for name in ("share/metainfo", "share/app-info"):
        dest = prefix / name
        if dest.exists():
            for path in dest.iterdir():
                if path.name != APP_ID + ".metainfo.xml":
                    shutil.rmtree(path) if path.is_dir() else path.unlink()
    (target / "build-inputs.json").write_bytes(
        (inputs / "build-inputs.json").read_bytes()
    )
    # Installable in both user and system installations; no dependence on the
    # build user's UID or private staging umask. This touches payload files only.
    for path in prefix.rglob("*"):
        if not path.is_symlink():
            path.chmod(0o755 if path.is_dir() or path.stat().st_mode & 0o111 else 0o644)
    return audit(prefix)


def audit(prefix):
    prefix = Path(prefix)
    prohibited = {
        ".git",
        ".aws",
        ".codex",
        ".agents",
        ".venv",
        "node_modules",
        "__pycache__",
        "tests",
        "test",
        "fixtures",
        "evidence",
        ".pytest_cache",
        ".ruff_cache",
        "_pytest",
        "pytest",
        "ruff",
        "verification",
    }
    entries = []
    for path in sorted(prefix.rglob("*")):
        rel = path.relative_to(prefix)
        if (
            prohibited.intersection(rel.parts)
            or path.suffix.lower()
            in {
                ".sqlite",
                ".sqlite3",
                ".db",
                ".key",
                ".pem",
                ".log",
                ".webm",
                ".pcap",
                ".pyc",
            }
            or path.name.startswith(".env")
        ):
            raise ValueError("Prohibited package content: " + str(rel))
        if path.is_symlink():
            link = path.readlink()
            if link.is_absolute():
                if not str(link).startswith(("/app/", "/usr/lib/")):
                    raise ValueError("Unexpected absolute link: " + str(rel))
            elif not path.resolve().is_relative_to(prefix.resolve()):
                raise ValueError("Escaping relative link: " + str(rel))
            entries.append({"path": str(rel), "symlink": str(link)})
        elif path.is_file():
            entries.append(
                {
                    "path": str(rel),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.file_digest(
                        path.open("rb"), "sha256"
                    ).hexdigest(),
                }
            )
    return {
        "status": "PASS",
        "files": entries,
        "logical_bytes": sum(e.get("bytes", 0) for e in entries),
    }


if __name__ == "__main__":
    result = install(Path(sys.argv[1]), Path(sys.argv[2]))
    print(
        json.dumps(
            {
                "audit": result["status"],
                "files": len(result["files"]),
                "logical_bytes": result["logical_bytes"],
            }
        )
    )
