"""Disposable P1 experiment, not a production launcher or security boundary."""

import argparse
import configparser
import fcntl
import json
import os
import resource
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

SOURCE = Path(__file__).resolve().parents[2]
ROOT = Path("/tmp/cyrnava-p1")
MARKER = ".p1-prototype.json"
P1B_ID = "org.cyrnava.P1B"
FLATPAK_INFO = Path("/.flatpak-info")


def configure_flatpak():
    """P1B only: trust the packaged app, never a host-supplied personal path."""
    global ROOT
    info = configparser.ConfigParser()
    info.read(FLATPAK_INFO)
    if (
        os.environ.get("FLATPAK_ID") != P1B_ID
        or info.get("Application", "name", fallback="") != P1B_ID
        or SOURCE != Path("/app/share/cyrnava")
    ):
        raise ValueError("P1B requires its own installed Flatpak and packaged source")
    shared = info.get("Context", "shared", fallback="").split(";")
    files = info.get("Context", "filesystems", fallback="").split(";")
    if "network" in shared or any(
        item
        and not item.startswith("!")
        and (
            item.split(":")[0] in ("host", "home", "host-os", "host-etc")
            or item.startswith("/")
        )
        for item in files
    ):
        raise ValueError("P1B refuses host networking or broad host filesystem grants")
    # Stable across parent and worker even after run() redirects the XDG variables.
    ROOT = Path.home() / ".var/app" / P1B_ID / "data/p1b-profiles"
    # -I workers deliberately ignore PYTHONPATH. Only this read-only app prefix is added.
    modules = f"/app/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    sys.path.insert(0, modules)


def default_flatpak_workspace():
    # A marked, stable synthetic workspace; /tmp is unsuitable for restart acceptance.
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    if ROOT.is_symlink() or ROOT.stat().st_uid != os.getuid():
        raise ValueError("Unsafe P1B root")
    ROOT.chmod(0o700)
    lock = os.open(ROOT / ".init.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        default = ROOT / "workspace-p1b"
        if not default.exists():
            fresh = workspace_path()
            fresh.rename(default)
        return workspace_path(default)
    finally:
        os.close(lock)


def process_evidence(pid):
    """Raw observations, never an automatic assertion of renderer isolation."""
    result = {"pid": pid}
    try:
        status = Path(f"/proc/{pid}/status").read_text()
        result["status"] = {
            key: value.strip()
            for line in status.splitlines()
            for key, _, value in [line.partition(":")]
            if key
            in ("Name", "PPid", "NSpid", "NoNewPrivs", "Seccomp", "Seccomp_filters")
        }
        result["namespaces"] = {
            name: os.readlink(f"/proc/{pid}/ns/{name}")
            for name in ("user", "pid", "net", "mnt")
        }
    except OSError as error:
        result["unavailable"] = str(error)
    return result


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def workspace_path(value=None):
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    if ROOT.is_symlink() or ROOT.stat().st_uid != os.getuid():
        raise ValueError("Prototype root must be owned by you and not a symlink")
    ROOT.chmod(0o700)
    if value is None:
        path = Path(tempfile.mkdtemp(prefix="workspace-", dir=ROOT))
        write_json(path / MARKER, {"prototype": "cyrnava-p1", "version": 1, "port": 0})
    else:
        path = Path(value).absolute()
    if path.is_symlink() or path.resolve().parent != ROOT.resolve():
        raise ValueError(
            "Only direct disposable workspaces under the prototype root are allowed"
        )
    if not path.name.startswith("workspace-") or path.stat().st_uid != os.getuid():
        raise ValueError("Not an owned P1 workspace")
    marker = path / MARKER
    if (
        marker.is_symlink()
        or json.loads(marker.read_text()).get("prototype") != "cyrnava-p1"
    ):
        raise ValueError("Not a marked P1 workspace")
    for relative in (
        "data",
        "data/engage",
        "data/engage/engage.sqlite3",
        "data/engage/assets",
        "qt-data",
        "qt-cache",
        "config",
        "cache",
    ):
        if (path / relative).is_symlink():
            raise ValueError("Prototype storage cannot be a symbolic link")
    path.chmod(0o700)
    return path


def check_environment(p1b=False):
    if os.geteuid() == 0:
        raise ValueError("Do not run the prototype as root")
    for name in (
        "QTWEBENGINE_DISABLE_SANDBOX",
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "QTWEBENGINE_REMOTE_DEBUGGING",
        "QTWEBENGINEPROCESS_PATH",
    ):
        if os.environ.get(name):
            if (
                p1b
                and name == "QTWEBENGINEPROCESS_PATH"
                and os.environ[name] == "/app/bin/QtWebEngineProcess"
                and Path(os.environ[name]).resolve()
                == Path("/app/lib/libexec/QtWebEngineProcess")
                and Path(os.environ[name]).is_file()
            ):
                continue
            raise ValueError(
                f"Unset {name}; the prototype refuses inherited WebEngine overrides"
            )


def bind_backend(workspace):
    marker = json.loads((workspace / MARKER).read_text())
    port = marker["port"]
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("Invalid prototype port")
    listener = socket.socket()
    try:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(128)
        marker["port"] = listener.getsockname()[1]
        write_json(workspace / MARKER, marker)
        return listener
    except BaseException:
        listener.close()
        raise


def backend(workspace, listener_fd, death_fd, nonce):
    # This entry point is used only by the retained desktop Popen child.
    sys.path.insert(0, str(SOURCE / "backend"))
    import uvicorn
    from app.main import create_app

    application = create_app(
        database_path=workspace / "data/engage/engage.sqlite3",
        frontend_path=SOURCE / "frontend/dist",
    )

    @application.get("/api/p1-ready", include_in_schema=False)
    def ready():
        return {"prototype": "cyrnava-p1", "nonce": nonce}

    server = uvicorn.Server(
        uvicorn.Config(application, access_log=False, timeout_graceful_shutdown=8)
    )

    def parent_disappeared():
        # EOF also stops the backend if the GUI is killed without finally/Qt cleanup.
        try:
            os.read(death_fd, 1)
        finally:
            server.should_exit = True
            os.close(death_fd)

    threading.Thread(target=parent_disappeared, daemon=True).start()
    with socket.socket(fileno=listener_fd) as listener:
        server.run(sockets=[listener])


def stop_child(child):
    if child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=12)
    except subprocess.TimeoutExpired:
        child.kill()  # Only this retained, owned child. Never a PID from disk.
        child.wait(timeout=5)


def run(args):
    check_environment(args.p1b_flatpak)
    if args.p1b_flatpak and args.test_cdp:
        raise ValueError("P1B native verification does not enable remote debugging")
    if args.p1b_flatpak and args.workspace is None:
        args.workspace = default_flatpak_workspace()
    workspace = workspace_path(args.workspace)
    lock = os.open(
        workspace / ".desktop.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    listener = bind_backend(workspace)
    origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
    # Preserve the same origin and web profile when explicitly reopening a workspace.
    for name, relative in (
        ("XDG_DATA_HOME", "data"),
        ("XDG_CONFIG_HOME", "config"),
        ("XDG_CACHE_HOME", "cache"),
    ):
        os.environ[name] = str(workspace / relative)
    if args.test_cdp:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            debug_port = probe.getsockname()[1]
        os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = f"127.0.0.1:{debug_port}"
    else:
        debug_port = None
    from PySide6 import __version__ as qt_binding_version
    from PySide6.QtCore import (
        QCoreApplication,
        QEvent,
        QSocketNotifier,
        Qt,
        QTimer,
        QUrl,
        qVersion,
    )
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineCore import (
        QWebEngineLoadingInfo,
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineSettings,
        QWebEngineUrlRequestInterceptor,
        qWebEngineChromiumVersion,
        qWebEngineVersion,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    app = QApplication([sys.argv[0]])
    app.setApplicationName("CyrNava P1 Prototype")
    app.setOrganizationName("CyrNavaPrototype")
    started = time.perf_counter()
    metrics = {
        "workspace": str(workspace),
        "origin": origin,
        "parent_pid": os.getpid(),
        "pyside": qt_binding_version,
        "qt": qVersion(),
        "webengine": qWebEngineVersion(),
        "chromium": qWebEngineChromiumVersion(),
        "flatpak_id": os.environ.get("FLATPAK_ID"),
        "platform": app.platformName(),
        "test_cdp": debug_port,
        "blocked_requests": [],
        "console_errors": [],
    }
    nonce = str(uuid4())
    death_read, death_write = os.pipe()
    log = (workspace / "backend.log").open("ab")
    child = subprocess.Popen(
        [
            sys.executable,
            "-B",
            "-I",
            str(Path(__file__).resolve()),
            "--worker",
            str(workspace),
            str(listener.fileno()),
            str(death_read),
            nonce,
        ],
        pass_fds=(listener.fileno(), death_read),
        cwd=workspace,
        stdout=log,
        stderr=log,
        env={**os.environ, "PYTHONNOUSERSITE": "1"},
    )
    os.close(death_read)
    listener.close()
    metrics["backend_pid"] = child.pid

    class LocalRequests(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, info):
            url = info.requestUrl()
            same_origin = (
                url.scheme() == "http"
                and url.host() == "127.0.0.1"
                and url.port() == int(origin.rsplit(":", 1)[1])
            )
            if not same_origin and url.scheme() not in ("data", "blob"):
                info.block(True)
                metrics["blocked_requests"].append(url.scheme() + "://" + url.host())

    class LocalPage(QWebEnginePage):
        def acceptNavigationRequest(self, url, kind, main_frame):
            return url.toString().split("#", 1)[0] == origin + "/"

        def javaScriptConsoleMessage(self, level, message, line, source):
            if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
                metrics["console_errors"].append(message[:500])

        def createWindow(self, kind):
            return None

    profile = QWebEngineProfile("cyrnava-p1", app)
    profile.setPersistentStoragePath(str(workspace / "qt-data"))
    profile.setCachePath(str(workspace / "qt-cache"))
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    profile.setDownloadPath(str(workspace / "downloads"))
    interceptor = LocalRequests(profile)
    profile.setUrlRequestInterceptor(interceptor)
    page = LocalPage(profile)
    page.settings().setAttribute(
        QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False
    )
    page.settings().setAttribute(
        QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False
    )
    page.permissionRequested.connect(lambda permission: permission.deny())
    if not args.p1b_flatpak:
        profile.downloadRequested.connect(lambda download: download.cancel())
    view = QWebEngineView()
    view.setPage(page)

    class Window(QMainWindow):
        closing = False
        checking_close = False
        close_dialog = None

        def confirm_unavailable_save(self):
            dialog = QMessageBox(self)
            self.close_dialog = dialog
            dialog.setWindowTitle("Close disposable prototype?")
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setText(
                "Saving is not confirmed. You can still close this prototype."
            )
            dialog.setInformativeText(
                "The temporary profile will be retained for reopening. Only drafts already "
                "written to local recovery storage can be recovered; unfinished uploads "
                "may be lost. This does not affect your installed CyrNava."
            )
            keep = dialog.addButton("Keep open", QMessageBox.ButtonRole.RejectRole)
            close = dialog.addButton(
                "Close prototype", QMessageBox.ButtonRole.AcceptRole
            )
            dialog.setDefaultButton(keep)
            dialog.setEscapeButton(keep)

            def chosen(_result):
                self.close_dialog = None
                if dialog.clickedButton() == close:
                    self.closing = True
                    self.close()
                dialog.deleteLater()

            dialog.finished.connect(chosen)
            dialog.open()

        def closeEvent(self, event):
            if self.closing:
                event.accept()
                return
            event.ignore()
            if self.close_dialog is not None:
                self.close_dialog.raise_()
                return
            if self.checking_close:
                return
            if child.poll() is not None:
                self.confirm_unavailable_save()
                return
            self.checking_close = True

            def checked(value):
                if not self.checking_close:
                    return
                self.checking_close = False
                if value:
                    self.closing = True
                    self.close()
                else:
                    self.confirm_unavailable_save()

            # An unresponsive renderer must not trap the owner in this window either.
            QTimer.singleShot(2000, lambda: checked(False))
            page.runJavaScript(
                "(() => { const s=document.querySelector('.save-state'); return (!s || s.dataset.state==='Saved') && !document.body.innerText.includes('Uploading image'); })()",
                checked,
            )

    window = Window()
    window.setWindowTitle(
        "CyrNava — P1B disposable Flatpak"
        if args.p1b_flatpak
        else "CyrNava — P1 disposable desktop prototype"
    )
    body = QWidget()
    layout = QVBoxLayout(body)
    status = QLabel(
        "P1: synthetic data only. Unauthenticated loopback API. Starting backend…"
    )
    status.setWordWrap(True)
    layout.addWidget(status)
    if args.p1b_flatpak:
        tools = QHBoxLayout()
        evidence_button = QPushButton("Save P1B evidence…")
        outage_button = QPushButton("Stop test backend…")
        tools.addWidget(evidence_button)
        tools.addWidget(outage_button)
        tools.addStretch()
        layout.addLayout(tools)
    layout.addWidget(view, 1)
    window.setCentralWidget(body)
    window.resize(1280, 960)
    window.show()

    def emit(event, **values):
        print(json.dumps({"event": event, **values}), flush=True)

    def snapshot():
        samples = [process_evidence(os.getpid()), process_evidence(child.pid)]
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                command = (entry / "cmdline").read_bytes().split(b"\0")
                if command and b"QtWebEngineProcess" in command[0]:
                    samples.append(process_evidence(int(entry.name)))
            except OSError:
                continue
        metrics["process_evidence"] = samples
        metrics["backend_running"] = child.poll() is None
        if args.p1b_flatpak:
            metrics["flatpak_info"] = FLATPAK_INFO.read_text()
            try:
                metrics["network_interfaces"] = [
                    line.split(":")[0].strip()
                    for line in Path("/proc/net/dev").read_text().splitlines()[2:]
                ]
                metrics["tcp_listeners"] = []
                for line in Path("/proc/net/tcp").read_text().splitlines()[1:]:
                    fields = line.split()
                    if fields[3] == "0A":
                        address, port = fields[1].split(":")
                        metrics["tcp_listeners"].append(
                            {
                                "address": socket.inet_ntoa(
                                    bytes.fromhex(address)[::-1]
                                ),
                                "port": int(port, 16),
                            }
                        )
                metrics.pop("network_evidence_unavailable", None)
            except OSError as error:
                metrics.pop("network_interfaces", None)
                metrics.pop("tcp_listeners", None)
                metrics["network_evidence_unavailable"] = str(error)
        write_json(workspace / "evidence.json", metrics)
        return metrics

    if args.p1b_flatpak:

        def save_evidence():
            filename, _ = QFileDialog.getSaveFileName(
                window,
                "Save synthetic P1B evidence",
                "cyrnava-p1b-evidence.json",
                "JSON (*.json)",
            )
            if filename:
                try:
                    Path(filename).write_text(json.dumps(snapshot(), indent=2) + "\n")
                except OSError as error:
                    QMessageBox.warning(window, "Evidence export failed", str(error))

        def stop_for_outage():
            if (
                QMessageBox.question(
                    window,
                    "Stop synthetic backend?",
                    "Stop only this test window's backend to verify offline draft recovery?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                == QMessageBox.StandardButton.Yes
            ):
                stop_child(child)
                snapshot()

        def save_download(download):
            # Only an in-app blob export may request a user-chosen portal destination.
            if download.url().scheme() != "blob" or download.page() != page:
                download.cancel()
                return
            name = Path(download.suggestedFileName()).name or "cyrnava-export.json"
            filename, _ = QFileDialog.getSaveFileName(
                window, "Save synthetic CyrNava export", name, "JSON (*.json)"
            )
            if not filename:
                download.cancel()
                return
            download.setDownloadDirectory(str(Path(filename).parent))
            download.setDownloadFileName(Path(filename).name)
            download.accept()

        evidence_button.clicked.connect(save_evidence)
        outage_button.clicked.connect(stop_for_outage)
        profile.downloadRequested.connect(save_download)

    def loaded(ok):
        if ok:
            metrics["frontend_loaded_ms"] = round(
                (time.perf_counter() - started) * 1000, 2
            )
            emit("frontend-loaded", **metrics)

    view.loadFinished.connect(loaded)

    def failed_load(info):
        if info.status() == QWebEngineLoadingInfo.LoadStatus.LoadFailedStatus:
            metrics["last_load_error"] = {
                "url": info.url().toString(),
                "code": info.errorCode(),
                "description": info.errorString(),
            }
            emit("frontend-load-failed", **metrics["last_load_error"])
            if args.p1b_flatpak:
                status.setText(
                    "P1B frontend load failed: "
                    + info.errorString()
                    + ". Save evidence and stop for review."
                )
                snapshot()

    page.loadingChanged.connect(failed_load)
    network = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def poll():
        if child.poll() is not None:
            status.setText(
                "Prototype backend exited. Preserve drafts; inspect this workspace's backend.log."
            )
            return
        if "backend_ready_ms" in metrics:
            return
        try:
            with network.open(origin + "/api/p1-ready", timeout=0.15) as response:
                if json.load(response) != {"prototype": "cyrnava-p1", "nonce": nonce}:
                    raise ValueError("Unexpected backend identity")
        except (OSError, ValueError):
            if time.perf_counter() - started > 20:
                status.setText(
                    "Backend startup timed out. Close prototype and inspect backend.log."
                )
                stop_child(child)
            return
        metrics["backend_ready_ms"] = round((time.perf_counter() - started) * 1000, 2)
        status.setText(
            "P1 synthetic data only • Unauthenticated API • Wait for Saved before closing"
            + (
                " • Qt namespace sandbox incomplete"
                if "NOT adequately sandboxed" in metrics.get("sandbox_diagnostic", "")
                else ""
            )
        )
        view.setUrl(QUrl(origin + "/"))
        if args.p1b_flatpak:
            snapshot()
        emit("backend-ready", **metrics)

    timer = QTimer(app)
    timer.timeout.connect(poll)
    timer.start(100)

    # Independent diagnostic page. Read actual Chromium sandbox status, not flags alone.
    diagnostic = QWebEnginePage(app)

    def record_sandbox(text):
        metrics["sandbox_diagnostic"] = text
        (workspace / "sandbox.txt").write_text(text)
        if args.p1b_flatpak:
            snapshot()
        emit("sandbox", text=text)
        if "NOT adequately sandboxed" in text:
            status.setText(
                "P1 synthetic data only • Unauthenticated API • Qt namespace sandbox incomplete • Not production-secure"
            )

    diagnostic.loadFinished.connect(lambda ok: diagnostic.toPlainText(record_sandbox))
    diagnostic.setUrl(QUrl("chrome://sandbox"))

    if args.test_cdp:
        # Test-only stdin controls. No JavaScript/native bridge or arbitrary paths/commands.
        notifier = QSocketNotifier(0, QSocketNotifier.Type.Read, app)
        buffer = bytearray()

        def control():
            chunk = os.read(0, 256)
            if not chunk:
                notifier.setEnabled(False)
                return
            buffer.extend(chunk)
            while b"\n" in buffer:
                line, _, rest = buffer.partition(b"\n")
                buffer[:] = rest
                if line == b"PASTE_SCREENSHOT":
                    image = QImage(64, 48, QImage.Format.Format_RGB32)
                    image.fill(QColor("#2879ca"))
                    image.save(str(workspace / "synthetic-screenshot.png"))
                    app.clipboard().setImage(image)
                    view.setFocus()
                    QTest.keyClick(
                        view.focusProxy() or view,
                        Qt.Key.Key_V,
                        Qt.KeyboardModifier.ControlModifier,
                    )
                    emit("screenshot-pasted")
                elif line == b"CAPTURE":

                    def capture():
                        window.grab().save(str(workspace / "desktop.png"))
                        emit("captured")

                    # Let the web compositor present the preceding React update.
                    QTimer.singleShot(250, capture)
                elif line == b"CLOSE":
                    window.close()
                elif line in (b"CLOSE_KEEP_OPEN", b"CLOSE_RETAIN_DRAFT"):
                    choice = line
                    window.close()

                    def choose_close(choice=choice, attempts=0):
                        dialog = window.close_dialog
                        if dialog is None:
                            if attempts < 30:
                                QTimer.singleShot(
                                    100, lambda: choose_close(choice, attempts + 1)
                                )
                            return
                        expected = (
                            "Keep open"
                            if choice == b"CLOSE_KEEP_OPEN"
                            else "Close prototype"
                        )
                        emit(
                            "close-choice",
                            choice=expected,
                            default=dialog.defaultButton().text(),
                        )
                        next(
                            button
                            for button in dialog.buttons()
                            if button.text() == expected
                        ).click()

                    QTimer.singleShot(0, choose_close)
            if len(buffer) > 256:
                buffer.clear()

        notifier.activated.connect(control)

    # OS termination is distinct from an interactive close: don't open a modal
    # Saved warning while stopping. Existing synchronous draft storage is retained.
    signal.signal(signal.SIGTERM, lambda number, _frame: app.exit(128 + number))
    signal.signal(signal.SIGINT, lambda number, _frame: app.exit(128 + number))
    try:
        emit("started", **metrics)
        return app.exec()
    finally:
        began = time.perf_counter()
        os.close(death_write)
        stop_child(child)
        metrics["shutdown_ms"] = round((time.perf_counter() - began) * 1000, 2)
        metrics["backend_exit_code"] = child.returncode
        if args.p1b_flatpak:
            snapshot()
        write_json(workspace / "metrics.json", metrics)
        log.close()
        # Destroy pages before their persistent profile so storage flushes cleanly.
        timer.stop()
        if args.test_cdp:
            notifier.setEnabled(False)
        window.closing = True
        view.deleteLater()
        diagnostic.deleteLater()
        page.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        profile.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        os.close(lock)
        emit("stopped", **metrics)


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if "--p1b-flatpak" in sys.argv or os.environ.get("FLATPAK_ID") == P1B_ID:
        try:
            configure_flatpak()
        except (OSError, ValueError) as error:
            print(f"P1B refused: {error}", file=sys.stderr)
            return 1
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        workspace = workspace_path(sys.argv[2])
        backend(workspace, int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--p1b-flatpak",
        action="store_true",
        help="P1B only: require the disposable Flatpak",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Reopen only a marked /tmp/cyrnava-p1/workspace-* profile",
    )
    parser.add_argument(
        "--test-cdp",
        action="store_true",
        help="TEST ONLY: unauthenticated loopback CDP and fixed stdin test controls",
    )
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError) as error:
        print(f"Prototype stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
