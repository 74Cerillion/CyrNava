"""Owner handoff: one Wayland sandbox probe, bounded, synthetic, no installation."""

import argparse
import hashlib
import json
import os
import resource
import shutil
import signal
import stat
import subprocess
import time
from pathlib import Path

SYSTEM_SCHEMAS = Path("/usr/share/glib-2.0/schemas")
FONT_KEYS = {"font-antialiasing", "font-hinting", "font-rgba-order"}
SCHEMA_PATH_CATEGORIES = {
    Path("/usr/share/glib-2.0/schemas/gschemas.compiled"): "compiled-schemas",
    Path("/usr/share/glib-2.0/schemas"): "schema-directory",
    Path("/usr/share/glib-2.0"): "glib-data-directory",
    Path("/usr/share"): "shared-data-directory",
    Path("/usr"): "usr-directory",
    Path("/"): "filesystem-root",
}
SCHEMA_REJECTIONS = {
    "separate-os-owner-required": "System schemas require a separate OS owner",
    "symlink-refused": "System schema symlink refused",
    "metadata-unavailable": "System schema ownership metadata unavailable",
    "os-owner-mismatch": "System schemas must be protected by the OS owner",
    "group-or-world-writable": "System schemas must be protected by the OS owner",
    "compiled-file-unavailable": "Ubuntu system compiled schemas unavailable",
    "compiled-read-unavailable": "Ubuntu system compiled schemas unavailable",
}


def _diagnostic_integer(value):
    return value if type(value) is int else None


class SchemaTrustError(ValueError):
    """Fail closed with only fixed categories and numeric system metadata."""

    def __init__(self, *, path, reason, info=None, os_owner=None, error=None):
        if reason not in SCHEMA_REJECTIONS:
            raise ValueError("Unreviewed schema diagnostic reason")
        mode = _diagnostic_integer(info.st_mode) if info is not None else None
        self.diagnostic = {
            "path_category": SCHEMA_PATH_CATEGORIES.get(path, "unreviewed-path"),
            "reason": reason,
            "uid": _diagnostic_integer(info.st_uid) if info is not None else None,
            "expected_os_uid": _diagnostic_integer(os_owner),
            "mode": f"{stat.S_IMODE(mode):04o}" if mode is not None else None,
            "errno": _diagnostic_integer(error.errno) if error is not None else None,
        }
        super().__init__(
            f"{SCHEMA_REJECTIONS[reason]}: {json.dumps(self.diagnostic, sort_keys=True)}"
        )


def _schema_stat(path, os_owner=None):
    try:
        return path.stat()
    except OSError as error:
        raise SchemaTrustError(
            path=path, reason="metadata-unavailable", os_owner=os_owner, error=error
        ) from None


def _schema_bytes(path, os_owner):
    try:
        return path.read_bytes()
    except OSError as error:
        raise SchemaTrustError(
            path=path,
            reason="compiled-read-unavailable",
            os_owner=os_owner,
            error=error,
        ) from None


def ubuntu_system_schema_environment(inherited):
    """Choose Ubuntu's schemas for this child, preserving all other controls."""
    compiled = SYSTEM_SCHEMAS / "gschemas.compiled"
    # A confined read-only view can map host root to the overflow UID. Compare
    # against the filesystem root's owner, never accept the invoking user as OS owner.
    root_info = _schema_stat(Path("/"))
    os_owner = root_info.st_uid
    if os_owner == os.getuid():
        raise SchemaTrustError(
            path=Path("/"),
            reason="separate-os-owner-required",
            info=root_info,
            os_owner=os_owner,
        )
    for path in (compiled, SYSTEM_SCHEMAS, *SYSTEM_SCHEMAS.parents):
        try:
            symlink = path.is_symlink()
        except OSError as error:
            raise SchemaTrustError(
                path=path, reason="metadata-unavailable", os_owner=os_owner, error=error
            ) from None
        if symlink:
            raise SchemaTrustError(
                path=path, reason="symlink-refused", os_owner=os_owner
            )
        info = _schema_stat(path, os_owner)
        if info.st_uid != os_owner or info.st_mode & 0o022:
            raise SchemaTrustError(
                path=path,
                reason=(
                    "os-owner-mismatch"
                    if info.st_uid != os_owner
                    else "group-or-world-writable"
                ),
                info=info,
                os_owner=os_owner,
            )
    try:
        compiled_available = compiled.is_file()
    except OSError as error:
        raise SchemaTrustError(
            path=compiled,
            reason="compiled-file-unavailable",
            os_owner=os_owner,
            error=error,
        ) from None
    if not compiled_available:
        raise SchemaTrustError(
            path=compiled, reason="compiled-file-unavailable", os_owner=os_owner
        )
    digest = hashlib.sha256(_schema_bytes(compiled, os_owner)).hexdigest()
    environment = dict(inherited)
    environment["GSETTINGS_SCHEMA_DIR"] = str(SYSTEM_SCHEMAS)
    try:
        query = subprocess.run(
            ["/usr/bin/gsettings", "list-keys", "org.gnome.desktop.interface"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("System font-schema query unavailable") from error
    if query.returncode != 0 or not FONT_KEYS.issubset(query.stdout.splitlines()):
        raise ValueError("Required Ubuntu font-schema keys unavailable")
    if hashlib.sha256(_schema_bytes(compiled, os_owner)).hexdigest() != digest:
        raise ValueError("System compiled schemas changed during preflight")
    return environment, {
        "mode": "explicit-Ubuntu-system-schemas",
        "inherited_schema_override_was_set": bool(
            inherited.get("GSETTINGS_SCHEMA_DIR")
        ),
        "compiled_schema_sha256": digest,
        "required_font_keys_present": sorted(FONT_KEYS),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--owner-host", required=True, action="store_true")
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument(
        "--ubuntu-system-schemas",
        action="store_true",
        help="Explicitly select OS schemas for this probe child; preserve original outputs",
    )
    parser.add_argument(
        "--record-prefix",
        choices=["owner-system-schemas-role"],
        help="Fresh renderer-role verification output; requires --ubuntu-system-schemas",
    )
    args = parser.parse_args()
    if args.record_prefix and not args.ubuntu_system_schemas:
        parser.error("Fresh role verification requires explicit Ubuntu system schemas")
    root = args.candidate.absolute()
    os.umask(0o077)
    if root.parent != Path(__file__).resolve().parents[3] / "ci-output" or any(
        p.is_symlink() for p in (root, *root.parents)
    ):
        parser.error("Reviewed repository-local N1 experiment required")
    if shutil.disk_usage(root).free < 1536 * 1024**2:
        parser.error("Keep 1.5GiB free headroom")
    receipt = root / "n1.json"
    if hashlib.sha256(receipt.read_bytes()).hexdigest() != args.receipt_sha256:
        parser.error("Receipt differs from reviewed N1 candidate")
    identity = json.loads(receipt.read_text())
    if identity.get("kind") != "cyrnava-disposable-native-N1" or identity.get(
        "root"
    ) != str(root):
        parser.error("Not the reviewed N1 experiment")
    prefix = "owner-system-schemas" if args.ubuntu_system_schemas else "owner-sandbox"
    if args.record_prefix:
        prefix = args.record_prefix
    result = root / f"{prefix}-result.json"
    log = root / f"{prefix}.private.log"
    diagnostic_path = root / f"{prefix}.json"
    if any(
        p.exists() or p.is_symlink()
        for p in [
            result,
            log,
            diagnostic_path,
            diagnostic_path.with_suffix(".renderer-cmdline.private"),
        ]
    ):
        parser.error("Existing owner probe preserved; do not retry")
    environment, schema_record = None, None
    if args.ubuntu_system_schemas:
        try:
            environment, schema_record = ubuntu_system_schema_environment(os.environ)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print(
            "N1: this child uses Ubuntu system schemas; host settings are unchanged.",
            flush=True,
        )
    print(
        "N1: one Wayland renderer security diagnostic; "
        "no visible application window is expected.",
        flush=True,
    )
    print(
        "N1: no installation, security change, migration, download or signing.",
        flush=True,
    )
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    start = time.monotonic()
    with log.open("xb") as stream:
        child = subprocess.Popen(
            [
                str(root / ".venv/bin/python"),
                "-B",
                "-I",
                str(Path(__file__).with_name("sandbox_probe.py")),
                str(root),
                "--owner-host",
                "--record",
                diagnostic_path.name,
            ],
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=environment,
        )
        try:
            code = child.wait(25)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(child.pid, signal.SIGTERM)
            try:
                code = child.wait(5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                code = child.wait(5)
    diagnostic = (
        json.loads(diagnostic_path.read_text()) if diagnostic_path.is_file() else {}
    )
    passed = (
        code == 0
        and diagnostic.get("complete") is True
        and diagnostic.get("status") == "PASS"
        and diagnostic.get("platform") == "wayland"
        and diagnostic.get("renderer_sandbox") == "PASS"
    )
    record = {
        "status": "PASS" if passed else "BLOCKED",
        "complete": True,
        "exit_code": code,
        "seconds": round(time.monotonic() - start, 3),
        "receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(
            Path(__file__).with_name("sandbox_probe.py").read_bytes()
        ).hexdigest(),
        "private_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "normal_application_launch": "NOT EXECUTED",
        "supervisor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    if schema_record is not None:
        record["platform_integration"] = schema_record
    if diagnostic:
        record["diagnostic"] = diagnostic
    result.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
