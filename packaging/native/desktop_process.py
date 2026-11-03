"""Verification-only GIO Desktop Entry launcher with an owned, waitable child.

Uses GNOME's real Exec expansion; no shell, substitute application or D-Bus
activation. API: docs.gtk.org/gio-unix/method.DesktopAppInfo.launch_uris_as_manager_with_fds.html
"""

import ctypes
import os
import signal
import subprocess
import time


class DesktopProcess:
    def __init__(self, desktop, environment, log):
        gio = ctypes.CDLL("libgio-2.0.so.0")
        objects = ctypes.CDLL("libgobject-2.0.so.0")
        pointer = ctypes.c_void_p
        gio.g_desktop_app_info_new_from_filename.argtypes = [ctypes.c_char_p]
        gio.g_desktop_app_info_new_from_filename.restype = pointer
        gio.g_app_launch_context_new.restype = pointer
        gio.g_app_launch_context_setenv.argtypes = [
            pointer,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        objects.g_object_unref.argtypes = [pointer]
        child_setup = ctypes.CFUNCTYPE(None, pointer)
        callback = ctypes.CFUNCTYPE(None, pointer, ctypes.c_int, pointer)
        launch = gio.g_desktop_app_info_launch_uris_as_manager_with_fds
        launch.argtypes = [
            pointer,
            pointer,
            pointer,
            ctypes.c_int,
            child_setup,
            pointer,
            callback,
            pointer,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            pointer,
        ]
        launch.restype = ctypes.c_int
        app = gio.g_desktop_app_info_new_from_filename(os.fsencode(desktop))
        if not app:
            raise ValueError("GIO rejected the desktop entry")
        context = gio.g_app_launch_context_new()
        for key, value in environment.items():
            gio.g_app_launch_context_setenv(
                context, os.fsencode(key), os.fsencode(value)
            )
        pids = []
        # Single-threaded verification parent. setsid is async-signal-safe; this
        # establishes the same owned process-group boundary as N1 Popen.
        setup = child_setup(lambda _data: os.setsid())
        pid_callback = callback(lambda _app, pid, _data: pids.append(pid))
        try:
            with open(os.devnull, "rb") as incoming:
                # G_SPAWN_DO_NOT_REAP_CHILD=2: caller retains waitpid ownership.
                accepted = launch(
                    app,
                    None,
                    context,
                    2,
                    setup,
                    None,
                    pid_callback,
                    None,
                    incoming.fileno(),
                    log.fileno(),
                    log.fileno(),
                    None,
                )
        finally:
            objects.g_object_unref(context)
            objects.g_object_unref(app)
        if not accepted or len(pids) != 1:
            raise ValueError("Exactly one owned desktop child required")
        self.pid = pids[0]
        self.returncode = None
        if os.getpgid(self.pid) != self.pid:
            os.kill(self.pid, signal.SIGTERM)
            os.waitpid(self.pid, 0)
            raise ValueError("Desktop child process-group isolation missing")

    def poll(self):
        if self.returncode is None:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.returncode = os.waitstatus_to_exitcode(status)
        return self.returncode

    def wait(self, timeout=None):
        deadline = time.monotonic() + timeout if timeout is not None else float("inf")
        while self.poll() is None:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired("owned desktop child", timeout)
            time.sleep(0.05)
        return self.returncode

    def terminate(self):
        os.kill(self.pid, signal.SIGTERM)
