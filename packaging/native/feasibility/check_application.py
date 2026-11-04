"""Owner-only N1 edit/reopen check through the unchanged experiment launcher."""

import argparse
import hashlib
import importlib.util
import json
import os
import resource
import signal
import sqlite3
import subprocess
import sys
import time
from contextlib import closing, contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE = ROOT / "ci-output/p6-native-n1-1"
OUTPUT = ROOT / "ci-output/p6-native-n1-application-1"
RECEIPT = "7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e"
LAUNCHER = "433928adca59ca511b8b4c189dff51472197573d7267f8ddb8268b1c82cd94d1"
TITLE = "N1 GUI owner edit"
FOLDER = "N1 GUI folder"
TEXT = "N1 GUI verified"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def support(name):
    spec = importlib.util.spec_from_file_location(
        "n1_application_" + name, HERE / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preflight():
    if any(
        p.is_symlink() for path in (CANDIDATE, OUTPUT) for p in (path, *path.parents)
    ):
        raise ValueError("Symlink path refused")
    if OUTPUT.exists():
        raise ValueError("Existing application attempt preserved; do not retry")
    if (
        sha(CANDIDATE / "n1.json") != RECEIPT
        or sha(CANDIDATE / "launch.py") != LAUNCHER
    ):
        raise ValueError("Reviewed candidate or normal launcher changed")
    record = json.loads(
        (CANDIDATE / "owner-system-schemas-role-result.json").read_text()
    )
    diagnostic = record.get("diagnostic", {})
    if not (
        record.get("status") == "PASS"
        and record.get("complete") is True
        and record.get("exit_code") == 0
        and record.get("receipt_sha256") == RECEIPT
        and diagnostic.get("platform") == "wayland"
        and diagnostic.get("renderer_pid_stable") is True
        and support("sandbox_probe").security_pass(diagnostic)
    ):
        raise ValueError("Verified owner Wayland renderer PASS required")
    for path, key in (
        (HERE / "sandbox_probe.py", "probe_sha256"),
        (HERE / "run_probe.py", "supervisor_sha256"),
        (CANDIDATE / "owner-system-schemas-role.private.log", "private_log_sha256"),
    ):
        if sha(path) != record[key]:
            raise ValueError("Owner probe evidence or tooling changed")
    raw = CANDIDATE / "owner-system-schemas-role.renderer-cmdline.private"
    if sha(raw) != diagnostic["renderer_cmdline_sha256"]:
        raise ValueError("Private renderer identity evidence changed")
    profile = CANDIDATE / "client/profile"
    if (profile / "workspace/engage.sqlite3").exists() or (
        profile / "active-workspace.json"
    ).exists():
        raise ValueError(
            "Expected unused synthetic GUI workspace; preserve existing data for review"
        )
    return record


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def snapshot(data, inspector, fingerprint):
    summary = inspector(
        data
    )  # Reuse established schema/assets/relationship validation.
    with closing(
        sqlite3.connect(
            (data / "engage.sqlite3").as_uri() + "?mode=ro&immutable=1", uri=True
        )
    ) as connection:
        rows = connection.execute(
            "SELECT notes.id, document_json FROM notes JOIN folders ON notes.folder_id=folders.id "
            "WHERE notes.title=? AND folders.name=?",
            (TITLE, FOLDER),
        ).fetchall()
        if len(rows) != 1:
            raise ValueError("Create exactly one required note in the required folder")
        note_id, document = rows[0][0], json.loads(rows[0][1])
        if not any(
            TEXT in node.get("text", "") and node.get("styles", {}).get("bold") is True
            for node in walk(document)
        ):
            raise ValueError("Required bold text was not saved")
        assets = connection.execute(
            "SELECT id FROM assets WHERE note_id=?", (note_id,)
        ).fetchall()
        if not any(
            node.get("type") == "image"
            and any(
                str(node.get("props", {}).get("url", "")).endswith(
                    "/api/assets/" + asset[0]
                )
                for asset in assets
            )
            for node in walk(document)
        ):
            raise ValueError("Required screenshot is not attached to the saved note")
    return {
        "schema": summary["schema"],
        "counts": summary["counts"],
        "content_sha256": fingerprint(data),
        "asset_hashes": {
            name: value
            for name, value in summary["files"].items()
            if name.startswith("assets/")
        },
        "required_note_folder_bold_image": "PASS",
    }


def proc_state(pid):
    process = Path("/proc") / str(pid)
    status = dict(
        line.split(":", 1)
        for line in (process / "status").read_text().splitlines()
        if ":" in line
    )
    return process, status


def still_alive(pid, started, sandbox):
    try:
        process, status = proc_state(pid)
        return (
            status["State"].strip().split()[0] != "Z"
            and sandbox.process_start_time(process) == started
        )
    except (OSError, ValueError, IndexError, KeyError):
        return False


def unauthenticated_rejected():
    import urllib.error
    import urllib.request

    metadata = json.loads((CANDIDATE / "client/profile/desktop.json").read_text())
    port = metadata["port"]
    if type(port) is not int or not 0 < port <= 65535:
        raise ValueError("Invalid synthetic backend port")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://127.0.0.1:{port}/api/tree", timeout=3):
            return False
    except urllib.error.HTTPError as error:
        try:
            return error.code == 401
        finally:
            error.close()


def sample_tree(gui_pid, owned, sandbox):
    """Inspect only descendants of our retained GUI process, not global processes."""
    pending, seen = [gui_pid], set()
    found = {
        "backend": False,
        "renderer": False,
        "qt_providers": False,
        "foreign_qt": False,
    }
    helper = (
        CANDIDATE
        / ".venv/lib/python3.14/site-packages/PySide6/Qt/libexec/QtWebEngineProcess"
    )
    while pending and len(seen) < 128:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        process = Path("/proc") / str(pid)
        try:
            pending.extend(
                int(p)
                for p in (process / "task" / str(pid) / "children").read_text().split()
            )
            executable = Path(os.readlink(process / "exe"))
            started = sandbox.process_start_time(process)
            command = (process / "cmdline").read_bytes()[:65537]
            if str(
                CANDIDATE / "application/desktop/native/worker.py"
            ).encode() in command.split(b"\0"):
                owned[pid] = started
                found["backend"] = True
            if executable == helper:
                owned[pid] = started
                if sandbox.renderer_role(command, helper)["verified"]:
                    _, status = proc_state(pid)
                    found["renderer"] |= (
                        status.get("NoNewPrivs", "").strip() == "1"
                        and status.get("Seccomp", "").strip() == "2"
                        and all(
                            os.readlink(process / "ns" / key)
                            != os.readlink(Path("/proc") / str(gui_pid) / "ns" / key)
                            for key in ("user", "pid", "net")
                        )
                        and sandbox.process_start_time(process) == started
                    )
            if pid == gui_pid:
                paths = [
                    line.split(maxsplit=5)[5]
                    for line in (process / "maps").read_text().splitlines()
                    if "libQt6" in line and len(line.split(maxsplit=5)) == 6
                ]
                found["qt_providers"] = bool(paths) and all(
                    Path(p).is_relative_to(CANDIDATE / ".venv") for p in paths
                )
                found["foreign_qt"] = bool(paths) and not found["qt_providers"]
        except (OSError, ValueError, IndexError, KeyError):
            continue
    return found


@contextmanager
def child_no_core():
    previous = resource.getrlimit(resource.RLIMIT_CORE)
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, previous[1]))
        yield
    finally:
        resource.setrlimit(resource.RLIMIT_CORE, previous)


def launch(phase, environment):
    sandbox = support("sandbox_probe")
    observed = {"backend": False, "renderer": False, "qt_providers": False}
    authenticated_boundary = False
    owned = {}
    print(
        f"N1 {phase}: opening the real application; close normally when instructed. Deadline: 10 minutes.",
        flush=True,
    )
    with (OUTPUT / (phase + ".private.log")).open("xb") as log:
        with child_no_core():
            process = subprocess.Popen(
                [
                    str(CANDIDATE / ".venv/bin/python"),
                    "-B",
                    "-I",
                    str(CANDIDATE / "launch.py"),
                ],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        deadline = time.monotonic() + 600
        try:
            while process.poll() is None:
                sample = sample_tree(process.pid, owned, sandbox)
                if sample.pop("foreign_qt"):
                    raise RuntimeError("Foreign Qt provider loaded by the application")
                for key, value in sample.items():
                    if value and not observed[key]:
                        print(f"N1 {phase}: {key} observed.", flush=True)
                    observed[key] |= value
                if all(observed.values()) and not authenticated_boundary:
                    if not unauthenticated_rejected():
                        raise RuntimeError(
                            "Unauthenticated local-backend request was not rejected"
                        )
                    authenticated_boundary = True
                if time.monotonic() > deadline or log.tell() > 2 * 1024**2:
                    raise TimeoutError(
                        "Application interaction deadline or private log cap reached"
                    )
                time.sleep(0.1)
            if process.returncode != 0:
                raise RuntimeError("Normal application launcher exited unsuccessfully")
        finally:
            if process.poll() is None:
                process.terminate()  # Normal application close/flush first.
                try:
                    process.wait(15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(5)
            cleanup = time.monotonic() + 15
            while (
                any(
                    still_alive(pid, started, sandbox) for pid, started in owned.items()
                )
                and time.monotonic() < cleanup
            ):
                time.sleep(0.1)
            if any(
                still_alive(pid, started, sandbox) for pid, started in owned.items()
            ):
                raise RuntimeError("Owned application descendant cleanup incomplete")
    if not all(observed.values()):
        raise RuntimeError("Application backend/renderer/provider evidence incomplete")
    return {
        **{key: "PASS" for key in observed},
        "normal_exit": "PASS",
        "owned_process_cleanup": "PASS",
        "unauthenticated_backend_rejected": "PASS",
    }


def state(phase):
    with (OUTPUT / (phase + "-state.private.log")).open("xb") as log:
        result = subprocess.run(
            [
                str(CANDIDATE / ".venv/bin/python"),
                "-B",
                "-I",
                str(Path(__file__)),
                "--owner-host",
                "--snapshot",
                phase,
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(
            "Saved synthetic state validation failed; keep private state log"
        )
    return json.loads((OUTPUT / (phase + "-state.json")).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-host", required=True, action="store_true")
    parser.add_argument(
        "--snapshot", choices=["edit", "restart"], help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    os.umask(0o077)
    if args.snapshot:
        if (
            not (OUTPUT / "active").is_file()
            or OUTPUT.is_symlink()
            or Path(sys.prefix) != CANDIDATE / ".venv"
        ):
            parser.error(
                "Active reviewed private-interpreter application check required"
            )
        if sha(CANDIDATE / "n1.json") != RECEIPT:
            parser.error("Candidate receipt changed")
        sys.path.insert(0, str(CANDIDATE / "application/backend"))
        from app.migration import content_fingerprint, inspect

        profile = CANDIDATE / "client/profile"
        if (profile / "active-workspace.json").exists():
            raise ValueError("Workspace selection changed outside this focused test")
        value = snapshot(profile / "workspace", inspect, content_fingerprint)
        value["origin_sha256"] = hashlib.sha256(
            str(json.loads((profile / "desktop.json").read_text())["port"]).encode()
        ).hexdigest()
        (OUTPUT / (args.snapshot + "-state.json")).write_text(
            json.dumps(value, indent=2) + "\n"
        )
        return 0
    if not sys.stdin.isatty() or not os.environ.get("WAYLAND_DISPLAY"):
        parser.error(
            "Owner Wayland terminal required; no automatic confined/offscreen substitute"
        )
    try:
        preflight()
        environment, schema = support("run_probe").ubuntu_system_schema_environment(
            os.environ
        )
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    environment["QT_QPA_PLATFORM"] = "wayland"
    OUTPUT.mkdir(mode=0o700)
    (OUTPUT / "active").write_text("synthetic application verification\n")
    record = {
        "status": "FAIL",
        "complete": False,
        "scope": "N1-real-launcher-edit-and-reopen",
        "receipt_sha256": RECEIPT,
        "launcher_sha256": LAUNCHER,
        "driver_sha256": sha(Path(__file__)),
        "platform_integration": schema,
        "phases": {},
    }
    try:
        print(
            f"\nUse ONLY this synthetic feasibility window.\n1. Create folder: {FOLDER}\n2. Create a note INSIDE it titled: {TITLE}\n3. Add text: {TEXT} and make it bold.\n4. Paste a screenshot of ONLY this synthetic application into the note with Ctrl+V.\n5. Set Appearance to Dark. Wait for Saved and uploads to finish.\n6. Close normally. Do not import backups or use personal data.\n",
            flush=True,
        )
        record["stage"] = "edit-instructions"
        (OUTPUT / "progress.json").write_text(
            json.dumps({"stage": record["stage"]}) + "\n"
        )
        input("Press Enter when ready to open the first application window: ")
        record["stage"] = "edit-launch"
        (OUTPUT / "progress.json").write_text(
            json.dumps({"stage": record["stage"]}) + "\n"
        )
        record["phases"]["edit"] = launch("edit", environment)
        record["stage"] = "edit-state-validation"
        (OUTPUT / "progress.json").write_text(
            json.dumps({"stage": record["stage"]}) + "\n"
        )
        before = state("edit")
        print(
            "\nSaved database, folder, bold note and image validated.\nNext: reopen the saved note; confirm bold text, screenshot and Dark appearance remain visible. Do not edit; close normally.\n",
            flush=True,
        )
        input("Press Enter to reopen the application: ")
        record["stage"] = "restart-launch"
        (OUTPUT / "progress.json").write_text(
            json.dumps({"stage": record["stage"]}) + "\n"
        )
        record["phases"]["restart"] = launch("restart", environment)
        record["stage"] = "restart-state-validation"
        (OUTPUT / "progress.json").write_text(
            json.dumps({"stage": record["stage"]}) + "\n"
        )
        after = state("restart")
        if before != after:
            raise ValueError(
                "Saved records, images or stable origin changed during read-only reopen"
            )
        answer = input(
            "Did the native window/icon, saved note, bold text, pasted image and Dark appearance display correctly on BOTH launches? Type CONFIRM N1 GUI only if all passed: "
        )
        if " ".join(answer.split()).casefold() != "confirm n1 gui":
            raise ValueError("Owner visual confirmation not supplied")
        record.update(
            status="PASS",
            saved_content_and_images="PASS",
            stable_origin="PASS",
            owner_visual_confirmation="PASS",
        )
    except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 - safe owner evidence
        record["error_type"] = type(error).__name__
        record["error"] = (
            "Application check incomplete; preserve this synthetic run for diagnosis."
        )
    finally:
        record["complete"] = True
        (OUTPUT / "active").unlink(missing_ok=True)
        (OUTPUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record, indent=2), flush=True)
        print(
            "Evidence: " + str(OUTPUT / "result.json") + "; keep private logs local.",
            flush=True,
        )
    return 0 if record["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
