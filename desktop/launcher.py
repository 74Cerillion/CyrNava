#!/usr/bin/python3
"""Linux desktop supervisor. Standard library only until the worker loads FastAPI."""

import argparse
import fcntl
import json
import logging
import logging.handlers
import os
import secrets
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path


class LaunchError(Exception):
    pass


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or path.stat().st_uid != os.getuid():
        raise LaunchError("Application directory must be owned by you, not a symlink.")
    path.chmod(0o700)


@contextmanager
def locked(path, *, blocking=True):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield
    finally:
        os.close(fd)


def read_state(config):
    try:
        return json.loads((Path(config["state_dir"]) / "instance.json").read_text())
    except (OSError, ValueError):
        return None


def process_matches(state):
    if not state:
        return False
    try:
        # starttime guards PID reuse; the worker nonce also occurs in its argv.
        stat = Path(f"/proc/{state['pid']}/stat").read_text().rsplit(")", 1)[1].split()
        args = Path(f"/proc/{state['pid']}/cmdline").read_bytes().split(b"\0")
        return (
            stat[0] != "Z"
            and stat[19] == state["starttime"]
            and state["nonce"].encode() in args
        )
    except (OSError, KeyError, TypeError):
        return False


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def ready(config, state):
    if not process_matches(state):
        return False
    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )
        url = f"http://127.0.0.1:{config['port']}/api/desktop-ready"
        with opener.open(url, timeout=0.4) as response:
            result = json.load(response)
        if result != {
            "application": "ENGAGE",
            "instance": state["nonce"],
            "lifecycle": 1,
        }:
            return False
        with opener.open(f"http://127.0.0.1:{config['port']}/", timeout=0.4) as page:
            return page.status == 200 and b'id="root"' in page.read(65536)
    except (OSError, ValueError, urllib.error.URLError):
        return False


def preflight(config):
    runtime = Path(config["release"]) / "backend/.venv/bin/python"
    build = Path(config["release"]) / "frontend/dist"
    if not runtime.is_file():
        raise LaunchError("Python runtime is missing. Re-run the ENGAGE installer.")
    if not (build / "index.html").is_file() or not (build / "assets").is_dir():
        raise LaunchError("Frontend build is missing. Re-run the ENGAGE installer.")
    return runtime


def start(config, config_path, *, timeout=20):
    state = read_state(config)
    if ready(config, state):
        logging.info("Reusing healthy ENGAGE instance")
        return state
    if process_matches(state):
        raise LaunchError(
            "ENGAGE is running but not ready. Use Stop ENGAGE, then retry."
        )
    if state:
        logging.warning(
            "Previous managed process is no longer running; recovering stale state"
        )
    wait_for_supervisor(config)
    runtime = preflight(config)
    # Probe only; worker bind is authoritative if another process races this check.
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", config["port"]))
        except OSError:
            raise LaunchError(
                f"Port {config['port']} is occupied by an unverified service. "
                "Stop that service in its own application or select another port "
                "when installing. No process was terminated."
            ) from None
    nonce = str(uuid.uuid4())
    state_dir = Path(config["state_dir"])
    fd = os.open(
        state_dir / "backend.log",
        os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,
        0o600,
    )
    try:
        # Bound growth between launches; an individual running session may grow.
        if os.fstat(fd).st_size > 2 * 1024 * 1024:
            os.ftruncate(fd, 0)
        child = subprocess.Popen(
            [
                str(runtime),
                str(Path(__file__).resolve()),
                "--config",
                str(config_path),
                "supervise",
                "--nonce",
                nonce,
            ],
            stdin=subprocess.DEVNULL,
            stdout=fd,
            stderr=fd,
            start_new_session=True,
            close_fds=True,
            cwd=Path(config["release"]) / "backend",
            env={
                **os.environ,
                "XDG_DATA_HOME": config["data_home"],
                "PYTHONUNBUFFERED": "1",
            },
        )
    finally:
        os.close(fd)
    logging.info("Started backend; waiting for application readiness")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = read_state(config)
        if state and state.get("nonce") == nonce and ready(config, state):
            return state
        if child.poll() is not None:
            raise LaunchError("Backend exited during startup. See backend.log.")
        time.sleep(0.15)
    # Give the owning supervisor time to drain/reap its worker before any
    # escalation. Killing it after only five seconds could orphan that worker.
    terminate_owned(child, timeout=17)
    raise LaunchError("ENGAGE did not become ready within 20 seconds; startup stopped.")


def wait_for_supervisor(config, timeout=5):
    deadline = time.monotonic() + timeout
    while True:
        try:
            with locked(Path(config["state_dir"]) / "supervisor.lock", blocking=False):
                return
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise LaunchError(
                    "Previous ENGAGE supervisor is still stopping. Retry shortly."
                ) from None
            time.sleep(0.05)


def stop(config):
    state = read_state(config)
    if not process_matches(state):
        logging.info("No live managed backend; stale state ignored")
        wait_for_supervisor(config)
        return
    # pidfd pins the process identity while rechecking /proc before signaling.
    try:
        fd = os.pidfd_open(state["pid"])
    except ProcessLookupError:
        return
    try:
        if not process_matches(state):
            raise LaunchError("Process identity changed. Refusing to signal it.")
        signal.pidfd_send_signal(fd, signal.SIGTERM)
        deadline = time.monotonic() + 12
        while process_matches(state) and time.monotonic() < deadline:
            time.sleep(0.1)
        if process_matches(state):
            raise LaunchError("Backend has not stopped. Inspect logs before retrying.")
        logging.info("Backend stopped cleanly")
        wait_for_supervisor(config)
    finally:
        os.close(fd)


def terminate_owned(child, *, timeout=10):
    """Only a retained Popen child is eligible for forced termination."""
    if child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        logging.error("Owned backend exceeded shutdown timeout; terminating it")
        child.kill()
        child.wait(timeout=5)


def supervise(config, config_path, nonce):
    """Detached launcher lifetime. Owns/reaps exactly one backend subprocess."""
    with locked(Path(config["state_dir"]) / "supervisor.lock", blocking=False):
        secret = secrets.token_urlsafe(32)
        child = None
        stopping = False

        def interrupted(_signal, _frame):
            nonlocal stopping
            stopping = True

        old_term = signal.signal(signal.SIGTERM, interrupted)
        old_int = signal.signal(signal.SIGINT, interrupted)
        last_contact = time.monotonic()
        last_phase = None
        try:
            # Install handlers before spawning: SIGTERM during startup must
            # still reach the finally block that owns and reaps this child.
            child = subprocess.Popen(
                [
                    str(preflight(config)),
                    str(Path(__file__).resolve()),
                    "--config",
                    str(config_path),
                    "worker",
                    "--nonce",
                    nonce,
                ],
                cwd=Path(config["release"]) / "backend",
                env={**os.environ, "ENGAGE_SUPERVISOR_SECRET": secret},
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({}), NoRedirect()
            )
            while child.poll() is None and not stopping:
                try:
                    request = urllib.request.Request(
                        f"http://127.0.0.1:{config['port']}/api/lifecycle/supervisor",
                        headers={"X-ENGAGE-Supervisor": secret},
                    )
                    with opener.open(request, timeout=1) as response:
                        status = json.load(response)
                    last_contact = time.monotonic()
                    if status["phase"] != last_phase:
                        logging.info("Session lifecycle: %s", status["phase"])
                        last_phase = status["phase"]
                    if status["draining"]:
                        logging.info("Session drain claimed: %s", status["reason"])
                        terminate_owned(child)
                        if status["reason"] == "startup-timeout":
                            report_error(
                                config,
                                "Firefox did not register an ENGAGE session within "
                                "the startup grace period. Backend stopped. "
                                "Try launching again.",
                            )
                        break
                except (OSError, ValueError, KeyError, urllib.error.URLError):
                    if time.monotonic() - last_contact >= 25:
                        raise LaunchError(
                            "Managed backend stopped responding; "
                            "stopping the owned process."
                        )
                time.sleep(0.25)
        finally:
            if child is not None:
                terminate_owned(child)
            signal.signal(signal.SIGTERM, old_term)
            signal.signal(signal.SIGINT, old_int)
        logging.info("Supervisor reaped backend and exited")


def worker(config, nonce):
    state_dir = Path(config["state_dir"])
    with locked(state_dir / "backend.lock", blocking=False):
        sys.path.insert(0, str(Path(config["release"]) / "backend"))
        import uvicorn

        from app.lifecycle import Sessions, Timing
        from app.main import create_app

        sessions = Sessions(
            nonce,
            os.environ.pop("ENGAGE_SUPERVISOR_SECRET"),
            Timing(**config.get("lifecycle", {})),
        )
        application = create_app(
            frontend_path=Path(config["release"]) / "frontend/dist",
            sessions=sessions,
        )

        @application.get("/api/desktop-ready", include_in_schema=False)
        def desktop_ready():
            if sessions.draining:
                from fastapi import HTTPException

                raise HTTPException(503, "ENGAGE is stopping")
            return {"application": "ENGAGE", "instance": nonce, "lifecycle": 1}

        state = {
            "pid": os.getpid(),
            "nonce": nonce,
            "starttime": Path("/proc/self/stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()[19],
        }
        temporary = state_dir / "instance.tmp"
        temporary.write_text(json.dumps(state))
        temporary.chmod(0o600)
        temporary.replace(state_dir / "instance.json")
        try:
            uvicorn.run(
                application,
                host="127.0.0.1",
                port=config["port"],
                access_log=False,
                log_level="info",
                timeout_graceful_shutdown=8,
            )
        finally:
            if read_state(config) == state:
                (state_dir / "instance.json").unlink(missing_ok=True)


def desktop_command(config, key, argument):
    try:
        result = subprocess.run(
            [config[key], argument],
            timeout=15,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode:
            raise LaunchError(
                "Default browser/file opener failed. Check desktop defaults."
            )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LaunchError("Desktop opener failed; check desktop defaults.") from error


def open_browser(config):
    url = f"http://127.0.0.1:{config['port']}"
    if not config.get("browser"):
        # Existing configurations keep working until the next installation.
        return desktop_command(config, "opener", url)
    try:
        browser = subprocess.Popen(
            [config["browser"], "--new-window", url],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(0.2)
        if browser.poll() not in (None, 0):
            raise LaunchError("Firefox failed to open ENGAGE.")
        # Firefox may reuse an existing process or keep this one alive. Neither
        # result tells us whether an ENGAGE window remains; leases do that.
    except OSError as error:
        raise LaunchError("Firefox could not start; check its installation.") from error


def report_error(config, message):
    state = Path(config["state_dir"])
    message = f"{message}\n\nDiagnostics: {state}/launcher.log and backend.log"
    logging.error("%s", message)
    print(message, file=sys.stderr)
    try:
        result = subprocess.run(
            [
                config["zenity"],
                "--error",
                "--title=ENGAGE",
                "--no-markup",
                "--text=" + message,
            ],
            timeout=120,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode not in (0, 1):
            raise OSError("dialog unavailable")
    except (OSError, subprocess.TimeoutExpired):
        # Opening the log is useful even when a dialog implementation is unavailable.
        try:
            desktop_command(config, "opener", str(state / "launcher.log"))
        except LaunchError:
            print(
                "Graphical diagnostics unavailable; inspect launcher.log.",
                file=sys.stderr,
            )


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="ENGAGE desktop launcher")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "action", choices=["open", "start", "stop", "logs", "worker", "supervise"]
    )
    parser.add_argument("--nonce")
    args = parser.parse_args()
    config = None
    try:
        config = json.loads(args.config.read_text())
        private_directory(Path(config["state_dir"]))
        handler = logging.handlers.RotatingFileHandler(
            Path(config["state_dir"]) / "launcher.log",
            maxBytes=1024 * 1024,
            backupCount=2,
        )
        logging.basicConfig(
            level=logging.INFO,
            handlers=[handler],
            format="%(asctime)s %(levelname)s %(message)s",
        )
        logging.info("Launcher action: %s", args.action)
        if args.action == "worker":
            worker(config, args.nonce)
            return 0
        if args.action == "supervise":
            supervise(config, args.config.resolve(), args.nonce)
            return 0
        if args.action == "logs":
            desktop_command(config, "opener", config["state_dir"])
            return 0
        with locked(Path(config["state_dir"]) / "launcher.lock"):
            if args.action == "stop":
                confirmation = subprocess.run(
                    [
                        config["zenity"],
                        "--question",
                        "--title=Stop ENGAGE",
                        "--no-markup",
                        "--text=Wait for Saved and all image uploads before stopping. "
                        "Stop ENGAGE now?",
                    ],
                    timeout=120,
                    check=False,
                )
                if confirmation.returncode == 0:
                    stop(config)
                elif confirmation.returncode != 1:
                    raise LaunchError(
                        "Stop confirmation could not open. Backend left running."
                    )
            else:
                previous = read_state(config)
                owned = start(config, args.config.resolve())
                if args.action == "open":
                    try:
                        open_browser(config)
                    except LaunchError:
                        if previous != owned:
                            stop(config)
                        raise
        return 0
    except (
        LaunchError,
        OSError,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
    ) as error:
        if config:
            report_error(config, str(error))
        else:
            report_error(
                {
                    "state_dir": str(args.config.parent),
                    "zenity": "/usr/bin/zenity",
                    "opener": "/usr/bin/xdg-open",
                },
                "Installation configuration is missing or invalid. "
                "Re-run the installer.",
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
