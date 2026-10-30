"""Production Qt shell: no prototype controls, remote debugging or native bridge."""

import configparser
import json
import os
import signal
import time
from pathlib import Path
from uuid import uuid4

from .backend import SOURCE, Backend
from .build_identity import ICON_PATH, WINDOW_TITLE
from .dialogs import choose_draft_destination, choose_images
from .policy import (
    download_allowed,
    navigation_allowed,
    notice_allowed,
    resource_allowed,
    same_origin,
)
from .storage import APP_ID, Profile


def configuration():
    info = configparser.ConfigParser()
    info.read("/.flatpak-info")
    if (
        os.environ.get("FLATPAK_ID") != APP_ID
        or info.get("Application", "name", fallback="") != APP_ID
        or SOURCE != Path("/app/share/cyrnava")
    ):
        raise ValueError(
            "This entry point requires the isolated CyrNava desktop Flatpak"
        )
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
        raise ValueError("Host networking and broad filesystem permissions are refused")
    if os.geteuid() == 0:
        raise ValueError("CyrNava must not run as root")
    for name in (
        "QTWEBENGINE_DISABLE_SANDBOX",
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "QTWEBENGINE_REMOTE_DEBUGGING",
    ):
        if os.environ.get(name):
            raise ValueError(f"Unset {name}; WebEngine security overrides are refused")
    if os.environ.get(
        "QTWEBENGINEPROCESS_PATH"
    ) != "/app/bin/QtWebEngineProcess" or Path(
        "/app/bin/QtWebEngineProcess"
    ).resolve() != Path("/app/lib/libexec/QtWebEngineProcess"):
        raise ValueError("The matching Flatpak WebEngine helper is required")
    return Path.home() / ".var/app" / APP_ID / "data/cyrnava"


def open_notice_request(request, origin, make_page):
    # Qt supplies the destination here, unlike createWindow(). Validate BEFORE
    # creating a widget so denied external links cannot leave a blank popup.
    if not request.isUserInitiated() or not notice_allowed(
        request.requestedUrl().toString(), origin
    ):
        return False
    request.openIn(make_page())
    return True


def run(*, offer_import=False):
    os.umask(0o077)
    root = configuration()
    from PySide6.QtCore import Qt, QTimer, QUrl
    from PySide6.QtWebEngineCore import (
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineSettings,
        QWebEngineUrlRequestInterceptor,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

    app = QApplication(["CyrNava"])
    app.setApplicationName("CyrNava")
    app.setOrganizationName("CyrNava")
    app.setDesktopFileName(APP_ID)
    from PySide6.QtGui import QIcon

    app.setWindowIcon(QIcon(ICON_PATH))
    try:
        profile = Profile(root)
    except BlockingIOError:
        QMessageBox.information(
            None,
            "CyrNava is running",
            "This desktop profile is already open. Switch to its existing window.",
        )
        return 0
    except (OSError, ValueError) as error:
        QMessageBox.critical(None, "CyrNava storage unavailable", str(error))
        return 1
    if offer_import and not profile.database.exists():
        answer = QMessageBox.question(
            None,
            "Welcome to CyrNava",
            "Import an existing verified CyrNava backup? Choose No to start empty.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            profile.close()
            from .maintenance import manage

            manage(app, root)
            profile = Profile(root)
    backend = Backend(profile)
    try:
        backend.start()
    except (OSError, ValueError, RuntimeError, TimeoutError) as error:
        QMessageBox.critical(None, "CyrNava could not start", str(error))
        backend.stop()
        profile.close()
        return 1

    class Interceptor(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, request):
            url = request.requestUrl().toString()
            if not resource_allowed(url, backend.origin):
                request.block(True)
            elif same_origin(url, backend.origin):
                if backend.child.poll() is not None:
                    # Never send a stale credential to a replacement listener.
                    request.block(True)
                else:
                    request.setHttpHeader(
                        b"X-CyrNava-Session", backend.token.encode("ascii")
                    )
            # Own-origin memory blobs remain available for draft export during
            # an outage; they receive no HTTP session header.

    class NoticePage(QWebEnginePage):
        def acceptNavigationRequest(self, url, _kind, main):
            return main and notice_allowed(url.toString(), backend.origin)

    def make_notice_page():
        view = QWebEngineView(window)
        view.setWindowFlag(Qt.WindowType.Window, True)
        view.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        notice = NoticePage(web_profile, view)
        view.setPage(notice)
        view.setWindowTitle("CyrNava — Third-party notices")
        view.resize(800, 650)
        view.show()
        return notice

    class Page(QWebEnginePage):
        def chooseFiles(self, mode, _old_files, _accepted_mime_types):
            if mode not in (
                QWebEnginePage.FileSelectionMode.FileSelectOpen,
                QWebEnginePage.FileSelectionMode.FileSelectOpenMultiple,
            ) or not navigation_allowed(self.url().toString(), backend.origin):
                return []
            return choose_images(
                QFileDialog,
                window,
                multiple=mode
                == QWebEnginePage.FileSelectionMode.FileSelectOpenMultiple,
            )

        def acceptNavigationRequest(self, url, _kind, main):
            return main and navigation_allowed(url.toString(), backend.origin)

        def createWindow(self, _kind):
            # Returning no page lets Qt emit newWindowRequested with its URL.
            return None

        def javaScriptConsoleMessage(self, _level, _message, _line, _source):
            pass  # Notes and credentials must never enter a desktop console log.

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.maintenance_requested = False
            self.request_id = None
            self.deadline = 0
            self.allow_close = False
            self.checking = False
            self.loaded = False
            self.setWindowTitle(WINDOW_TITLE)
            self.resize(1280, 900)
            self.view = QWebEngineView(self)
            self.page = Page(web_profile, self.view)
            self.view.setPage(self.page)
            self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            self.page.permissionRequested.connect(lambda permission: permission.deny())
            self.page.newWindowRequested.connect(
                lambda request: open_notice_request(
                    request, backend.origin, make_notice_page
                )
            )
            self.page.loadFinished.connect(self.load_finished)
            self.setCentralWidget(self.view)
            self.timer = QTimer(self)
            self.timer.setInterval(100)
            self.timer.timeout.connect(self.poll_close)
            self.timer.start()
            action = self.menuBar().addAction("Backup and recovery…")
            action.triggered.connect(self.open_maintenance)
            self.view.setUrl(QUrl(backend.origin + "/"))

        def open_maintenance(self):
            self.maintenance_requested = True
            self.close()

        def load_finished(self, success):
            self.loaded = success
            if not success:
                self.setWindowTitle("CyrNava — Could not load local workspace")

        def closeEvent(self, event):
            if self.allow_close:
                event.accept()
                return
            event.ignore()
            if self.request_id is not None:
                return
            self.request_id = uuid4().hex
            self.deadline = time.monotonic() + 45
            if not self.loaded or backend.child.poll() is not None:
                self.close_problem()
                return
            identifier = json.dumps(self.request_id)
            self.page.runJavaScript(f"window.__cyrnavaDesktop?.request({identifier})")

        def poll_close(self):
            if backend.child.poll() is not None:
                backend.token = ""
                self.statusBar().showMessage(
                    "The local backend stopped. Keep this window open to preserve or export unconfirmed drafts."
                )
            if not self.request_id or self.checking:
                return
            if time.monotonic() >= self.deadline or backend.child.poll() is not None:
                self.close_problem()
                return
            identifier = json.dumps(self.request_id)
            request_id = self.request_id
            self.checking = True

            def received(value):
                self.checking = False
                if request_id != self.request_id:
                    return
                if value == "saved":
                    self.allow_close = True
                    self.close()
                elif value == "error":
                    self.close_problem()
                # Missing/unready JS waits until the bounded deadline.

            self.page.runJavaScript(
                f"window.__cyrnavaDesktop?.state({identifier})", received
            )

        def close_problem(self):
            identifier = self.request_id
            if identifier is None:
                return
            # Clear first to prevent reentrant timer callbacks opening dialogs.
            self.request_id = None
            box = QMessageBox(self)
            box.setWindowTitle("CyrNava has unconfirmed changes")
            box.setText(
                "Saving could not be confirmed. Keep the window open to retry or export your draft.\n\nClose anyway retains recovery drafts where browser storage succeeded. Pending image bytes and unfinished library actions may be lost."
            )
            keep = box.addButton("Keep open", QMessageBox.ButtonRole.RejectRole)
            leave = box.addButton(
                "Close with recovery draft", QMessageBox.ButtonRole.DestructiveRole
            )
            box.setDefaultButton(keep)
            box.exec()
            if box.clickedButton() is leave:
                self.allow_close = True
                self.close()
            else:
                self.maintenance_requested = False
                self.page.runJavaScript(
                    f"window.__cyrnavaDesktop?.cancel({json.dumps(identifier)})"
                )

    web_profile = QWebEngineProfile("CyrNava", app)
    web_profile.setPersistentStoragePath(str(profile.qt))
    web_profile.setCachePath(str(profile.cache))
    web_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    web_profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
    )
    interceptor = Interceptor(web_profile)
    web_profile.setUrlRequestInterceptor(interceptor)
    settings = web_profile.settings()
    for name in (
        "PluginsEnabled",
        "LocalContentCanAccessRemoteUrls",
        "LocalContentCanAccessFileUrls",
        "JavascriptCanOpenWindows",
        "FullScreenSupportEnabled",
        "ScreenCaptureEnabled",
    ):
        settings.setAttribute(getattr(QWebEngineSettings.WebAttribute, name), False)
    # User-clicked target=_blank notices remain allowed by the bounded Page policy.
    window = Window()

    def download(item):
        if not download_allowed(item.url().toString(), backend.origin):
            item.cancel()
            return
        path = choose_draft_destination(QFileDialog, window)
        if not path:
            item.cancel()
            return
        destination = Path(path)
        item.setDownloadDirectory(str(destination.parent))
        item.setDownloadFileName(destination.name)
        item.accept()

    web_profile.downloadRequested.connect(download)
    # Termination signals use the same normal-close protocol; a second SIGKILL
    # cannot be made safe. Pipe EOF still stops the owned backend after GUI death.
    old_signals = {
        number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGINT)
    }
    signal.signal(signal.SIGTERM, lambda *_: window.close())
    signal.signal(signal.SIGINT, lambda *_: window.close())
    window.show()
    try:
        result = app.exec()
    finally:
        for number, handler in old_signals.items():
            signal.signal(number, handler)
        backend.stop()
        # Destroy pages before the profile and retain the lock through Qt teardown.
        from shiboken6 import delete

        window_maintenance_requested = window.maintenance_requested
        delete(window)
        delete(web_profile)
        app.processEvents()
        profile.close()

    if window_maintenance_requested:
        from .maintenance import manage

        return manage(app, root)
    return result
