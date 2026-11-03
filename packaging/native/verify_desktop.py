"""Owner-only N2 Desktop Entry edit/reopen, using the accepted N1 live checks."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import traceback
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
REVIEWED_EDIT_RESULT = (
    "7a85ddb0ae9ead9a096bb66a197396bcc49474fc33bde9479fae3d4be10a62b2"
)
REVIEWED_EDIT_LOG = "98e6924d96b781ebfcfe67bc0a6926434ef7b4a0bb81b5c8c7cdee357a192c45"
REVIEWED_EDIT_DRIVER = (
    "e4eb3402216e4cb963ff615d6e762029d5113fa9c0349945cba8033196e126ad"
)
REVIEWED_EDIT_BASELINE = (
    "d8c6d0c18fd263fcd8463624e078c4ed7ab9d79642d9425c7ad9144546145ece"
)
PHASE_CHECKS = {
    "backend",
    "renderer",
    "qt_providers",
    "normal_exit",
    "owned_process_cleanup",
    "unauthenticated_backend_rejected",
}


class StateValidationError(ValueError):
    def __init__(self, check):
        if check not in {
            "required_note_and_folder",
            "required_bold_marker",
            "attached_image",
            "saved_state",
        }:
            check = "saved_state"
        self.check = check
        super().__init__("Saved-state check failed: " + check)


def state_snapshot(check, data, inspector, fingerprint):
    """N2 human marker ignores case; canonical records/assets remain byte exact."""
    expected = check.TEXT
    with closing(
        sqlite3.connect(
            (data / "engage.sqlite3").as_uri() + "?mode=ro&immutable=1", uri=True
        )
    ) as connection:
        rows = connection.execute(
            "SELECT document_json FROM notes JOIN folders ON notes.folder_id=folders.id "
            "WHERE notes.title=? AND folders.name=?",
            (check.TITLE, check.FOLDER),
        ).fetchall()
    if len(rows) != 1:
        raise StateValidationError("required_note_and_folder")
    texts = [
        node["text"]
        for node in check.walk(json.loads(rows[0][0]))
        if isinstance(node.get("text"), str)
        and node.get("styles", {}).get("bold") is True
        and expected.casefold() in node["text"].casefold()
    ]
    if not texts:
        raise StateValidationError("required_bold_marker")
    # The reused N1 checker stays unchanged. Bind its exact marker to the actual
    # matching bold span for this N2 snapshot, then restore verifier-local state.
    check.TEXT = texts[0]
    try:
        value = check.snapshot(data, inspector, fingerprint)
    except ValueError as error:
        category = (
            "attached_image"
            if str(error) == "Required screenshot is not attached to the saved note"
            else "saved_state"
        )
        raise StateValidationError(category) from error
    finally:
        check.TEXT = expected
    value["marker_policy"] = (
        "case-insensitive-human-marker; exact-canonical-fingerprint"
    )
    value["matched_bold_span_sha256"] = hashlib.sha256(texts[0].encode()).hexdigest()
    return value


def reviewed_edit(engine, source, profile, manifest, manifest_sha256, desktop):
    """Resume ONLY the independently reviewed attempt 2, with its data unchanged."""
    source = attempt_path(engine, source)
    engine.require(
        source == ROOT / "ci-output/native-n2-owner-2",
        "Only reviewed owner attempt 2 can continue",
    )
    engine.require(
        engine.digest(source / "result.json") == REVIEWED_EDIT_RESULT
        and engine.digest(source / "edit-state.private.log") == REVIEWED_EDIT_LOG,
        "Reviewed edit evidence changed",
    )
    result = engine.load(source / "result.json")
    engine.require(
        result.get("status") == "FAIL"
        and result.get("complete") is True
        and result.get("stage") == "edit-state-validation"
        and result.get("error_type") == "CalledProcessError"
        and result.get("driver_sha256") == REVIEWED_EDIT_DRIVER
        and result.get("manifest_sha256") == manifest_sha256
        and result.get("archive_sha256") == manifest["archive_sha256"]
        and result.get("desktop_sha256") == engine.digest(desktop)
        and result.get("gio_adapter_sha256")
        == engine.digest(Path(__file__).with_name("desktop_process.py"))
        and result.get("phases") == {"edit": dict.fromkeys(PHASE_CHECKS, "PASS")},
        "Reviewed first phase or installed identity mismatch",
    )
    baseline = ROOT / "ci/evidence/n2/owner-2-state-validation/review.json"
    engine.require(
        engine.digest(baseline) == REVIEWED_EDIT_BASELINE,
        "Reviewed data baseline changed",
    )
    expected = engine.load(baseline)["workspace_files_sha256"]
    data = profile / "workspace"
    engine.require(
        not (profile / "active-workspace.json").exists(),
        "Unexpected workspace selection",
    )
    actual = {
        str(path.relative_to(data)): engine.digest(engine.regular(path))
        for path in data.rglob("*")
        if not path.is_dir()
    }
    engine.require(
        actual == expected, "Reviewed saved workspace changed; preserve for review"
    )
    return {
        "source_attempt": str(source.relative_to(ROOT)),
        "result_sha256": REVIEWED_EDIT_RESULT,
        "edit_checks": result["phases"]["edit"],
        "scope": "INHERITED from reviewed owner attempt 2",
    }


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def attempt_path(engine, path):
    output = engine.checked_path(path)
    engine.require(
        output.parent == ROOT / "ci-output"
        and re.fullmatch(r"native-n2-owner-[1-9][0-9]*", output.name),
        "Direct repository ci-output/native-n2-owner-N attempt required",
    )
    return output


def configure_monitor(check, desktop, desktop_support):
    class Spawn:
        def __new__(cls, _command, *, env, stdout, **_kwargs):
            return desktop_support.DesktopProcess(desktop, env, stdout)

    # Keep the exact subprocess interface used by the unchanged live monitor.
    # The constructor alone changes to GIO; stream and timeout semantics do not.
    check.subprocess = SimpleNamespace(
        Popen=Spawn,
        DEVNULL=subprocess.DEVNULL,
        STDOUT=subprocess.STDOUT,
        TimeoutExpired=subprocess.TimeoutExpired,
    )


def failure_details(error):
    result = {"error_type": type(error).__name__}
    if isinstance(error, StateValidationError):
        result["failed_check"] = error.check
    if isinstance(error, AttributeError) and error.name in {
        "Popen",
        "STDOUT",
        "DEVNULL",
        "TimeoutExpired",
    }:
        result["missing_adapter_attribute"] = error.name
    frames = traceback.extract_tb(error.__traceback__)
    for frame in reversed(frames):
        name = Path(frame.filename).name
        if name in {"verify_desktop.py", "check_application.py", "desktop_process.py"}:
            result["failed_source"] = {"file": name, "line": frame.lineno}
            break
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-host", action="store_true", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument(
        "--resume-after-edit",
        type=Path,
        help="Restart-only continuation of reviewed owner attempt 2; never edits its evidence",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "ci-output/native-n2-owner-1",
        help="Fresh repository ci-output/native-n2-owner-N directory; never overwrites",
    )
    parser.add_argument(
        "--snapshot", choices=["edit", "restart"], help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    engine = module("n2_owner_engine", ROOT / "desktop/install_engine.py")
    engine.host_supported()
    root = engine.checked_path(args.root)
    engine.deployment_paths(root, True)
    active = engine.load(root / "current.json")
    release = root / "releases" / engine.member_name(active["release"])
    receipt, manifest = engine.installed(release)
    engine.require(
        receipt["manifest_sha256"] == args.manifest_sha256,
        "Wrong reviewed installation",
    )
    engine.require(manifest["kind"] == "candidate", "Disposable candidate required")
    output = attempt_path(engine, args.output)
    profile = Path(receipt["profile"])
    old = ROOT / "packaging/native/feasibility/check_application.py"
    engine.require(
        engine.digest(old)
        == "406e0afd6011dbf9f1e9031d8f6e8c8cdf8eb5ba3b7557b2db4fca67260584ed",
        "Accepted live verifier changed",
    )
    check = module("n2_reused_n1_checks", old)
    # Only the verification module's target/constants change. No application or
    # Qt classes are patched and no JavaScript is injected.
    check.CANDIDATE, check.OUTPUT = release, output
    check.TITLE, check.FOLDER, check.TEXT = (
        "N2 installed note",
        "N2 installed folder",
        "N2 desktop verified",
    )
    if args.snapshot:
        engine.require(
            (output / "active").is_file() and Path(sys.prefix) == release / ".venv",
            "Active private-interpreter snapshot required",
        )
        engine.require(
            not (profile / "active-workspace.json").exists(),
            "Unexpected workspace selection",
        )
        sys.path.insert(0, str(release / "application/backend"))
        from app.migration import content_fingerprint, inspect

        try:
            value = state_snapshot(
                check, profile / "workspace", inspect, content_fingerprint
            )
        except StateValidationError as error:
            engine.durable(
                output / (args.snapshot + "-state-error.json"), failure_details(error)
            )
            raise
        value["origin_sha256"] = hashlib.sha256(
            str(engine.load(profile / "desktop.json")["port"]).encode()
        ).hexdigest()
        engine.durable(output / (args.snapshot + "-state.json"), value)
        return 0
    engine.require(
        sys.stdin.isatty() and os.environ.get("WAYLAND_DISPLAY"),
        "Owner Wayland terminal required",
    )
    engine.require(
        not output.exists(), "Existing owner attempt preserved; do not retry"
    )
    desktop = root / "xdg/applications" / (manifest["app_id"] + ".desktop")
    engine.require(
        desktop.read_bytes() == engine.desktop_entry(release, manifest["app_id"], True),
        "Desktop entry changed",
    )
    inherited = None
    if args.resume_after_edit:
        with engine.installation_lock(root):
            inherited = reviewed_edit(
                engine,
                args.resume_after_edit,
                profile,
                manifest,
                args.manifest_sha256,
                desktop,
            )
    else:
        engine.require(
            not profile.exists(),
            "Fresh disposable GUI profile required; preserve existing data",
        )
    environment, schemas = engine.support(
        release, "system_schemas"
    ).ubuntu_system_schema_environment(os.environ)
    desktop_support = module(
        "n2_gio_child", Path(__file__).with_name("desktop_process.py")
    )

    # Reuse N1's unchanged monitor/exit/auth/cleanup policy, but launch through
    # GDesktopAppInfo so actual Desktop Entry parsing/Exec expansion is exercised.
    configure_monitor(check, desktop, desktop_support)

    def unauthenticated():
        import urllib.error
        import urllib.request

        port = engine.load(profile / "desktop.json")["port"]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(f"http://127.0.0.1:{port}/api/tree", timeout=3):
                return False
        except urllib.error.HTTPError as error:
            error.close()
            return error.code == 401

    check.unauthenticated_rejected = unauthenticated
    output.mkdir(mode=0o700)
    (output / "active").write_text("N2 synthetic GUI owner verification\n")
    record = {
        "status": "FAIL",
        "complete": False,
        "scope": "N2-installed-GIO-desktop-entry-edit-reopen",
        "manifest_sha256": args.manifest_sha256,
        "archive_sha256": manifest["archive_sha256"],
        "driver_sha256": engine.digest(Path(__file__)),
        "desktop_sha256": engine.digest(desktop),
        "gio_adapter_sha256": engine.digest(
            Path(__file__).with_name("desktop_process.py")
        ),
        "platform_integration": schemas,
        "phases": {},
    }
    if inherited:
        record["scope"] = "N2-installed-desktop-restart-continuation"
        record["inherited_edit_phase"] = inherited

    def snapshot(phase):
        command = [
            release / ".venv/bin/python",
            "-B",
            "-I",
            Path(__file__),
            "--owner-host",
            "--root",
            root,
            "--manifest-sha256",
            args.manifest_sha256,
            "--output",
            output,
            "--snapshot",
            phase,
        ]
        with (output / (phase + "-state.private.log")).open("xb") as log:
            result = subprocess.run(
                list(map(str, command)),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=30,
                check=False,
            )
        if result.returncode:
            error_path = output / (phase + "-state-error.json")
            if error_path.exists():
                raise StateValidationError(engine.load(error_path).get("failed_check"))
            raise subprocess.CalledProcessError(
                result.returncode, "private saved-state subprocess"
            )
        return engine.load(output / (phase + "-state.json"))

    try:
        if not inherited:
            print(
                "N2: two real launches through the isolated installed Desktop Entry. No normal menu or personal data changed.",
                flush=True,
            )
            print(
                "Create folder N2 installed folder; note N2 installed note; bold text N2 desktop verified (capitalization may vary). Paste a screenshot of ONLY the synthetic window. Set Dark; wait Saved/uploads; close normally.",
                flush=True,
            )
            input("Press Enter to launch the installed desktop entry: ")
            record["stage"] = "edit-desktop-launch"
            record["phases"]["edit"] = check.launch("edit", environment)
        else:
            print(
                "N2: restart-only continuation. Original edit checks are inherited from reviewed attempt 2, not rerun. Saved workspace hashes match. Do not edit or recreate the note.",
                flush=True,
            )
        record["stage"] = "edit-state-validation"
        before = snapshot("edit")
        print(
            "Reopen without editing; confirm folder/note/bold/image/Dark, correct icon and window grouping; close normally.",
            flush=True,
        )
        input("Press Enter to reopen the saved installed application: ")
        record["stage"] = "restart-desktop-launch"
        record["phases"]["restart"] = check.launch("restart", environment)
        record["stage"] = "restart-state-validation"
        after = snapshot("restart")
        engine.require(
            before == after, "Installed data or stable origin changed on restart"
        )
        rounds = (
            "the original editing round AND this reopen"
            if inherited
            else "BOTH launches"
        )
        answer = input(
            f"Only if {rounds}, window/icon/grouping, editor/image and Dark persistence were correct, type CONFIRM N2 GUI: "
        )
        engine.require(
            " ".join(answer.split()).casefold() == "confirm n2 gui",
            "Owner visual confirmation missing",
        )
        record.update(
            status="PASS",
            stage="complete",
            saved_data_and_origin="PASS",
            owner_visual_confirmation="PASS",
        )
    except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 - safe owner diagnostic
        with (output / "driver-exception.private.log").open("x") as log:
            traceback.print_exc(file=log)
        record.update(
            **failure_details(error),
            error="Preserve attempt and private logs; no automatic retry",
        )
    finally:
        record["complete"] = True
        (output / "active").unlink(missing_ok=True)
        engine.durable(output / "result.json", record)
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "PASS" else 2


if __name__ == "__main__":
    os.umask(0o077)
    raise SystemExit(main())
