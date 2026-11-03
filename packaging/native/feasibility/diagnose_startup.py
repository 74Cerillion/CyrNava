"""Owner-only Qt startup backtrace; never starts WebEngine rendering or CyrNava."""

import argparse
import contextlib
import hashlib
import importlib
import json
import os
import resource
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / "ci-output/p6-native-n1-1"
OUTPUT = ROOT / "ci-output/p6-native-n1-startup-1"
RECEIPT = "7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e"
DEADLINE = 20


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight(candidate, output):
    if candidate != CANDIDATE or output != OUTPUT:
        raise ValueError(
            "Only the reviewed candidate and fresh diagnostic path are allowed"
        )
    if any(
        p.is_symlink() for path in (candidate, output) for p in (path, *path.parents)
    ):
        raise ValueError("Symlink path refused")
    if output.exists():
        raise ValueError("Existing diagnostic preserved; do not retry")
    if sha(candidate / "n1.json") != RECEIPT:
        raise ValueError("Reviewed candidate receipt changed")
    previous = json.loads((candidate / "owner-sandbox-result.json").read_text())
    if (
        previous.get("receipt_sha256") != RECEIPT
        or sha(candidate / "owner-sandbox.private.log")
        != previous["private_log_sha256"]
        or sha(Path(__file__).with_name("sandbox_probe.py")) != previous["probe_sha256"]
    ):
        raise ValueError("Original owner evidence or probe identity changed")


def debugger_command(debugger, candidate):
    commands = [
        "set startup-with-shell off",
        "set disable-randomization off",
        "set pagination off",
        "set confirm off",
        "set print frame-arguments none",
        "run",
        "bt 24",
        "info sharedlibrary",
    ]
    return (
        [
            debugger,
            "--nx",
            "--nh",
            "--batch",
            "-iex",
            "set auto-load off",
            "-iex",
            "set debuginfod enabled off",
        ]
        + [arg for command in commands for arg in ("-ex", command)]
        + [
            "--args",
            str(candidate / ".venv/bin/python"),
            "-B",
            "-I",
            str(Path(__file__).resolve()),
            "--owner-host",
            "--child",
        ]
    )


@contextlib.contextmanager
def child_limits():
    # This standalone supervisor spawns without preexec_fn. The child inherits
    # the limits; immediately restore the supervisor's original limits afterward.
    originals = {
        kind: resource.getrlimit(kind)
        for kind in (resource.RLIMIT_CORE, resource.RLIMIT_FSIZE)
    }
    try:
        resource.setrlimit(
            resource.RLIMIT_CORE, (0, originals[resource.RLIMIT_CORE][1])
        )
        soft, hard = originals[resource.RLIMIT_FSIZE]
        bounded = min(
            value
            for value in (soft, hard, 2 * 1024**2)
            if value != resource.RLIM_INFINITY
        )
        resource.setrlimit(resource.RLIMIT_FSIZE, (bounded, hard))
        yield
    finally:
        for kind, original in originals.items():
            resource.setrlimit(kind, original)


def schema_keys():
    """Read key names only, in separate processes; never read preference values."""
    record = {}
    for schema, keys in (
        (
            "org.gnome.desktop.interface",
            ("font-antialiasing", "font-hinting", "font-rgba-order"),
        ),
        (
            "org.gnome.settings-daemon.plugins.xsettings",
            ("antialiasing", "hinting", "rgba-order"),
        ),
    ):
        try:
            process = subprocess.run(
                ["/usr/bin/gsettings", "list-keys", schema],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            present = set(process.stdout.splitlines())
            record[schema] = {
                "lookup_succeeded": process.returncode == 0,
                "keys": {key: key in present for key in keys},
            }
        except (OSError, subprocess.TimeoutExpired) as error:
            record[schema] = {"error_type": type(error).__name__}
    return record


def child(candidate, output):
    """Mirror the failed probe's setup only, stopping after QApplication creation."""
    sys.path.insert(0, str(candidate / "application"))
    from desktop.native.application import configuration

    def stage(name):
        (output / "progress.json").write_text(json.dumps({"stage": name}) + "\n")

    stage("configuration")
    configuration()
    os.environ["QT_QPA_PLATFORM"] = "wayland"
    for key, name in (
        ("XDG_DATA_HOME", "data"),
        ("XDG_CONFIG_HOME", "config"),
        ("XDG_CACHE_HOME", "cache"),
    ):
        os.environ[key] = str(output / name)
    stage("qt-imports")
    for name in ("QtCore", "QtWebEngineCore", "QtWidgets"):
        module = importlib.import_module("PySide6." + name)
    stage("qapplication-construction")
    app = module.QApplication(["CyrNava N1 startup diagnostic"])
    stage("qapplication-created")
    # No event loop, WebEngine profile/page/view, backend, or application window.
    importlib.import_module("shiboken6").delete(app)
    stage("startup-only-complete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-host", required=True, action="store_true")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    os.umask(0o077)
    if args.child:
        if (
            not OUTPUT.is_dir()
            or OUTPUT.is_symlink()
            or not (OUTPUT / "active").is_file()
        ):
            parser.error("Supervisor-created diagnostic directory required")
        if sha(CANDIDATE / "n1.json") != RECEIPT:
            parser.error("Reviewed candidate changed")
        child(CANDIDATE, OUTPUT)
        return 0
    try:
        preflight(CANDIDATE, OUTPUT)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    debugger = shutil.which("gdb")
    if debugger is None:
        parser.error(
            "gdb is unavailable; do not install tools or change host security automatically"
        )
    OUTPUT.mkdir(mode=0o700)
    (OUTPUT / "active").write_text("startup-only diagnostic\n")
    log = OUTPUT / "startup.private.log"
    print(
        "N1: at most 20 seconds of Qt startup tracing; no window or renderer exercise.",
        flush=True,
    )
    result = {
        "status": "DIAGNOSTIC_ONLY",
        "complete": True,
        "scope": "QApplication-startup-only",
        "receipt_sha256": RECEIPT,
        "normal_application_launch": "NOT EXECUTED",
        "renderer_sandbox": "NOT TESTED",
        "diagnostic_sha256": sha(Path(__file__)),
        "schema_keys": schema_keys(),
        "environment_presence_only": {
            key: bool(os.environ.get(key))
            for key in (
                "GSETTINGS_SCHEMA_DIR",
                "QT_QPA_PLATFORMTHEME",
                "GTK_USE_PORTAL",
            )
        },
    }
    with log.open("xb") as stream:
        with child_limits():
            process = subprocess.Popen(
                debugger_command(debugger, CANDIDATE),
                stdout=stream,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        try:
            result["debugger_exit_code"] = process.wait(DEADLINE)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Kill this disposable diagnostic's process group, never other processes.
            import signal

            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(5)
            result["status"] = "BLOCKED"
            result["interrupted_or_deadline"] = True
    (OUTPUT / "active").unlink()
    progress = OUTPUT / "progress.json"
    result["last_stage"] = (
        json.loads(progress.read_text())["stage"]
        if progress.is_file()
        else "debugger-startup"
    )
    result["private_log_sha256"] = sha(log)
    (OUTPUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    print(
        "Keep startup.private.log private. No N1 or renderer PASS is inferred.",
        flush=True,
    )
    return 0 if result["status"] == "DIAGNOSTIC_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
