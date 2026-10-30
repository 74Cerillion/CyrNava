"""Retained child ownership, inherited socket and anonymous credential/death pipes."""

import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from .storage import Profile, open_private

SOURCE = Path(__file__).resolve().parents[2]


class Backend:
    def __init__(self, profile: Profile, source=SOURCE):
        self.profile, self.source = profile, source
        self.child = None
        self.death_write = None
        self.token = secrets.token_urlsafe(32)
        self.origin = ""

    def start(self, timeout=20):
        listener = socket.socket()
        read, write = os.pipe()
        death_read, self.death_write = os.pipe()
        log_fd = None
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", self.profile.port))
            listener.listen(128)
            port = listener.getsockname()[1]
            self.profile.remember_port(port)
            self.origin = f"http://127.0.0.1:{port}"
            log_fd = open_private(self.profile.root / "backend.log")
            os.lseek(log_fd, 0, os.SEEK_END)
            self.child = subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    "-I",
                    str(Path(__file__).with_name("worker.py")),
                    str(listener.fileno()),
                    str(read),
                    str(death_read),
                    str(self.profile.lock),
                ],
                pass_fds=(listener.fileno(), read, death_read, self.profile.lock),
                stdin=subprocess.DEVNULL,
                stdout=log_fd,
                stderr=log_fd,
                cwd=self.source,
                start_new_session=True,
            )
            # Never in argv, environment, URL, a cookie or persistent profile.
            with os.fdopen(write, "w") as stream:
                write = None
                json.dump(
                    {
                        "origin": self.origin,
                        "token": self.token,
                        "database": str(self.profile.database),
                        "source": str(self.source),
                    },
                    stream,
                )
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if self.child.poll() is not None:
                    raise RuntimeError(
                        "Owned backend exited during startup; inspect private backend.log"
                    )
                try:
                    request = urllib.request.Request(
                        self.origin + "/api/health",
                        headers={"X-CyrNava-Session": self.token},
                    )
                    with opener.open(request, timeout=0.3) as response:
                        if response.status == 200 and json.load(response) == {
                            "status": "ok"
                        }:
                            return
                except (OSError, ValueError, urllib.error.URLError):
                    time.sleep(0.05)
            raise TimeoutError("Owned backend did not become ready")
        except BaseException:
            self.stop()
            raise
        finally:
            listener.close()
            for fd in (read, write, death_read, log_fd):
                if fd is not None:
                    os.close(fd)

    def stop(self):
        if self.death_write is not None:
            os.close(self.death_write)
            self.death_write = None
        if self.child is not None:
            if self.child.poll() is None:
                self.child.terminate()
                try:
                    self.child.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    self.child.kill()  # Only the retained Popen child, never a saved PID.
            self.child.wait(timeout=5)
        self.token = ""


def worker(listener_fd, credential_fd, death_fd, lock_fd):
    # Keep the instance lock inherited until this child exits, including GUI death.
    os.fstat(lock_fd)
    with os.fdopen(credential_fd) as stream:
        configuration = json.loads(stream.read(8192))
    source = Path(configuration["source"])
    sys.path.insert(0, str(source / "backend"))
    if Path("/.flatpak-info").is_file():
        sys.path.insert(
            0,
            f"/app/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
        )
    import uvicorn
    from app.desktop_security import DesktopSession
    from app.main import create_app

    session = DesktopSession(configuration["origin"], configuration.pop("token"))
    application = create_app(
        Path(configuration["database"]),
        source / "frontend/dist",
        desktop_session=session,
    )
    server = uvicorn.Server(
        uvicorn.Config(
            application,
            access_log=False,
            proxy_headers=False,
            timeout_graceful_shutdown=8,
            log_level="warning",
        )
    )

    def parent_gone():
        try:
            os.read(death_fd, 1)
        finally:
            os.close(death_fd)
            server.should_exit = True

    threading.Thread(target=parent_gone, daemon=True).start()
    try:
        with socket.socket(fileno=listener_fd) as listener:
            server.run(sockets=[listener])
    finally:
        session.revoke()
