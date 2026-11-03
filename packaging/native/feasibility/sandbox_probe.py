"""One bounded native renderer diagnostic; imports never count as sandbox success."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def renderer_role(command_line, expected_helper):
    """Recognize argv or Chromium's flattened argv[0] process title.

    Only an exact role switch counts. A title must name the helper and place its
    role first; arbitrary argument values are never searched for a substring.
    The caller independently verifies the executable and the page's renderer PID.
    """
    result = {"verified": False, "format": "unrecognized", "type": "unknown"}
    if not command_line or len(command_line) > 65536:
        result["reason"] = "missing-or-oversized-command-line"
        return result
    arguments = [part for part in command_line.split(b"\0") if part]
    if not arguments:
        result["reason"] = "empty-command-line"
        return result
    switches = arguments[1:]
    result["format"] = "nul-delimited-argv"
    if len(arguments) == 1:
        result["format"] = "chromium-process-title"
        for program in (os.fsencode(expected_helper), b"QtWebEngineProcess"):
            prefix = program + b" "
            if arguments[0].startswith(prefix):
                switches = arguments[0][len(prefix) :].split()
                break
        else:
            result["reason"] = "unrecognized-title-program"
            return result
        if not switches or not switches[0].startswith(b"--type="):
            result["reason"] = "title-role-must-be-first-switch"
            return result
    if b"--type" in switches:
        result["reason"] = "ambiguous-unassigned-role-switch"
        return result
    roles = [
        value.removeprefix(b"--type=")
        for value in switches
        if value.startswith(b"--type=")
    ]
    if len(roles) != 1:
        result["reason"] = "missing-or-ambiguous-role"
        return result
    result["type"] = "renderer" if roles[0] == b"renderer" else "other"
    result["verified"] = roles[0] == b"renderer"
    result["reason"] = (
        "exact-renderer-role" if result["verified"] else "non-renderer-role"
    )
    return result


def process_start_time(process):
    # comm can contain spaces/parentheses; fields after its closing ')' start at 3.
    return process.joinpath("stat").read_text().rsplit(")", 1)[1].split()[19]


def capture_role(process, expected_helper, private_path):
    with process.joinpath("cmdline").open("rb") as stream:
        command_line = stream.read(65537)
    descriptor = os.open(
        private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(command_line)
    evidence = renderer_role(command_line, expected_helper)
    return {
        "renderer_cmdline_sha256": hashlib.sha256(command_line).hexdigest(),
        "renderer_cmdline_bytes": len(command_line),
        "renderer_role_evidence": evidence,
        "renderer_role_verified": evidence["verified"],
    }


def security_pass(record):
    lines = record.get("sandbox_diagnostic", [])
    status = record.get("process_status", {})
    namespaces = record.get("namespace_separation", {})
    return bool(
        record.get("qt_providers_coherent")
        and record.get("renderer_helper_matches")
        and record.get("renderer_role_verified")
        and status.get("NoNewPrivs") == "1"
        and status.get("Seccomp") == "2"
        and all(namespaces.get(k) for k in ["user", "pid", "net"])
        and any("Layer 1 Sandbox" in s and "Namespace" in s for s in lines)
        and "PID namespaces\tYes" in lines
        and "Network namespaces\tYes" in lines
        and "Seccomp-BPF sandbox\tYes" in lines
        and not any("NOT adequately sandboxed" in s for s in lines)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--owner-host", action="store_true")
    parser.add_argument("--record", default="sandbox-probe.json")
    args = parser.parse_args()
    root = args.candidate.absolute()
    if "/" in args.record or not args.record.endswith(".json"):
        parser.error("Simple candidate-local JSON basename required")
    output = root / args.record
    private_command_line = output.with_suffix(".renderer-cmdline.private")
    if any(p.exists() or p.is_symlink() for p in (output, private_command_line)):
        raise SystemExit("Preserve existing diagnostic")
    sys.path.insert(0, str(root / "application"))
    from desktop.native.application import configuration

    configuration()
    # Host mode is explicit and only exercised by the owner. Never auto-connect
    # Codex execution to the owner desktop to replace an offscreen failure.
    os.environ["QT_QPA_PLATFORM"] = "wayland" if args.owner_host else "offscreen"
    for key, value in [
        ("XDG_DATA_HOME", "data"),
        ("XDG_CONFIG_HOME", "config"),
        ("XDG_CACHE_HOME", "cache"),
    ]:
        os.environ[key] = str(root / "client" / value)
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
    from PySide6.QtWidgets import QApplication

    record = {
        "status": "BLOCKED",
        "complete": False,
        "scope": "Wayland-owner" if args.owner_host else "offscreen-confined",
        "normal_launcher": "NOT EXECUTED",
        "renderer_sandbox": "NOT VERIFIED",
    }
    app = QApplication(["CyrNava N1 sandbox diagnostic"])
    record["platform"] = app.platformName()
    record["parent_confinement"] = Path("/proc/self/attr/current").read_text().strip()
    profile = QWebEngineProfile(app)
    page = QWebEnginePage(profile)

    def finish():
        record["renderer_sandbox"] = "PASS" if security_pass(record) else "FAIL"
        record["status"] = "PASS" if security_pass(record) else "BLOCKED"
        record["complete"] = True
        output.write_text(json.dumps(record, indent=2) + "\n")
        app.quit()

    def loaded(ok):
        if not ok:
            finish()
            return

        def got(text):
            record["sandbox_diagnostic"] = [
                s.strip()
                for s in str(text).splitlines()
                if any(
                    word in s
                    for word in [
                        "Sandbox",
                        "sandbox",
                        "namespace",
                        "Seccomp",
                        "SUID",
                        "TSYNC",
                    ]
                )
            ]
            maps = set()
            for line in Path("/proc/self/maps").read_text().splitlines():
                fields = line.split(maxsplit=5)
                if len(fields) == 6 and (
                    "libQt6" in fields[5] or "/platforms/libq" in fields[5]
                ):
                    maps.add(fields[5])
            record["qt_providers_coherent"] = bool(maps) and all(
                Path(path).is_relative_to(root / ".venv") for path in maps
            )
            record["loaded_qt_paths"] = [
                p.replace(str(root), "<candidate>") for p in sorted(maps)
            ]
            pid = page.renderProcessPid()
            record["renderer_pid"] = pid
            record["renderer_pid_source"] = "QWebEnginePage.renderProcessPid"
            process = Path("/proc") / str(pid)
            try:
                started = process_start_time(process)
                expected = (
                    root
                    / ".venv/lib/python3.14/site-packages"
                    / "PySide6/Qt/libexec/QtWebEngineProcess"
                )
                if Path(os.readlink(process / "exe")) != expected:
                    raise OSError("Renderer identity unavailable")
                record["renderer_helper_matches"] = True
                record.update(capture_role(process, expected, private_command_line))
                status = process.joinpath("status").read_text()
                record["process_status"] = {
                    key: value.strip()
                    for key, value in (
                        line.split(":", 1) for line in status.splitlines()
                    )
                    if key
                    in {"Name", "NSpid", "NoNewPrivs", "Seccomp", "Seccomp_filters"}
                }
                record["namespace_separation"] = {
                    name: os.readlink(process / "ns" / name)
                    != os.readlink(Path("/proc/self/ns") / name)
                    for name in ["user", "pid", "net", "mnt"]
                }
                record["uid_map"] = process.joinpath("uid_map").read_text().strip()
                record["renderer_pid_stable"] = (
                    page.renderProcessPid() == pid
                    and process_start_time(process) == started
                    and Path(os.readlink(process / "exe")) == expected
                )
                if not record["renderer_pid_stable"]:
                    record["renderer_role_verified"] = False
            except (OSError, ValueError, IndexError) as error:
                record["process_evidence_error"] = type(error).__name__
                record["renderer_role_verified"] = False
            finish()

        page.toPlainText(got)

    page.loadFinished.connect(loaded)
    QTimer.singleShot(15000, finish)
    page.setUrl(QUrl("chrome://sandbox"))
    app.exec()
    from shiboken6 import delete

    delete(page)
    delete(profile)
    app.processEvents()
    return 0 if record["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
