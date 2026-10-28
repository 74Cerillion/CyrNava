"""Real loopback workers, synthetic profiles and stubbed graphical utilities only."""

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

DESKTOP = Path(__file__).resolve().parents[2] / "desktop"
sys.path.insert(0, str(DESKTOP))
import launcher  # noqa: E402

spec = importlib.util.spec_from_file_location("cyrnava_install", DESKTOP / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@pytest.fixture
def setup(tmp_path):
    repo = DESKTOP.parent
    release = tmp_path / "installation with spaces/release"
    (release / "backend").mkdir(parents=True)
    (release / "frontend/dist/assets").mkdir(parents=True)
    (release / "frontend/dist/index.html").write_text('<div id="root">CyrNava</div>')
    (release / "backend/app").symlink_to(repo / "backend/app", target_is_directory=True)
    (release / "backend/.venv").symlink_to(
        repo / "backend/.venv", target_is_directory=True
    )
    state = tmp_path / "state"
    launcher.private_directory(state)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    config = {
        "release": str(release),
        "state_dir": str(state),
        "data_home": str(tmp_path / "profile"),
        "port": port,
        "opener": "/bin/true",
        "zenity": "/bin/true",
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    yield config, path
    launcher.stop(config)


def cli(path, action="start"):
    return subprocess.run(
        [sys.executable, DESKTOP / "launcher.py", "--config", path, action],
        capture_output=True,
        text=True,
        timeout=35,
    )


def test_start_reuse_repeated_clicks_stop_and_stale_recovery(setup):
    config, path = setup
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: cli(path, "open"), range(4)))
    assert all(r.returncode == 0 for r in results), [r.stderr for r in results]
    state = launcher.read_state(config)
    assert launcher.ready(config, state)
    assert cli(path, "open").returncode == 0
    assert launcher.read_state(config) == state
    launcher.stop(config)
    assert not launcher.ready(config, state)
    assert cli(path).returncode == 0
    replacement = launcher.read_state(config)
    assert replacement["nonce"] != state["nonce"]
    # Kill only the test-owned child via a pinned PID handle.
    fd = os.pidfd_open(replacement["pid"])
    signal.pidfd_send_signal(fd, signal.SIGKILL)
    os.close(fd)
    import time

    for _ in range(30):
        if not launcher.process_matches(replacement):
            break
        time.sleep(0.1)
    assert cli(path).returncode == 0
    assert launcher.read_state(config)["nonce"] != replacement["nonce"]
    assert (
        "recovering stale state"
        in (Path(config["state_dir"]) / "launcher.log").read_text()
    )


def test_port_conflict_is_not_reused_or_killed(setup):
    config, path = setup
    with socket.socket() as unrelated:
        unrelated.bind(("127.0.0.1", config["port"]))
        unrelated.listen()
        result = cli(path, "open")
        assert result.returncode == 1
        assert "unverified service" in result.stderr
        assert unrelated.getsockname()[1] == config["port"]
    assert launcher.read_state(config) is None


def test_missing_runtime_and_browser_failure_are_visible(setup):
    config, path = setup
    runtime = Path(config["release"]) / "backend/.venv"
    runtime.unlink()
    result = cli(path, "open")
    assert result.returncode == 1
    assert "Python runtime is missing" in result.stderr
    runtime.symlink_to(DESKTOP.parent / "backend/.venv", target_is_directory=True)
    config["opener"] = "/bin/false"
    path.write_text(json.dumps(config))
    result = cli(path, "open")
    assert result.returncode == 1
    assert "opener failed" in result.stderr
    assert not launcher.ready(config, launcher.read_state(config))
    assert (Path(config["state_dir"]) / "backend.log").exists()


def test_identity_and_stale_pid_checks(setup):
    config, path = setup
    assert cli(path).returncode == 0
    state = launcher.read_state(config)
    assert not launcher.ready(config, {**state, "nonce": "not-the-worker"})
    assert not launcher.process_matches({**state, "starttime": "0"})
    assert launcher.process_matches(state)
    for name in ["launcher.log", "backend.log", "instance.json", "launcher.lock"]:
        assert (Path(config["state_dir"]) / name).stat().st_mode & 0o077 == 0


def test_preflight_and_bounded_failed_start(setup):
    config, path = setup
    (Path(config["release"]) / "frontend/dist/index.html").unlink()
    with pytest.raises(launcher.LaunchError, match="build is missing"):
        launcher.start(config, path, timeout=0.1)


def test_data_survives_managed_restart_and_backup(setup):
    import io
    import urllib.request

    from PIL import Image

    config, path = setup
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(route, body=None, method=None, mime="application/json"):
        req = urllib.request.Request(
            f"http://127.0.0.1:{config['port']}{route}",
            data=body,
            method=method,
            headers={"Content-Type": mime},
        )
        with opener.open(req) as response:
            return response.read()

    assert cli(path).returncode == 0
    document = [
        {
            "type": "heading",
            "props": {"level": 1},
            "content": [
                {"type": "text", "text": "Synthetic", "styles": {"bold": True}}
            ],
            "children": [],
        }
    ]
    note = json.loads(
        request(
            "/api/notes",
            json.dumps(
                {"title": "Desktop persistence", "document_json": document}
            ).encode(),
            "POST",
        )
    )
    image = io.BytesIO()
    Image.new("RGB", (32, 32), "blue").save(image, format="PNG")
    asset = json.loads(
        request(
            f"/api/assets?note_id={note['id']}", image.getvalue(), "POST", "image/png"
        )
    )
    document.append({"type": "image", "props": {"url": asset["url"]}, "children": []})
    saved = json.loads(
        request(
            f"/api/notes/{note['id']}",
            json.dumps(
                {"revision": note["revision"], "document_json": document}
            ).encode(),
            "PATCH",
        )
    )
    bytes_before = request(asset["url"])
    launcher.stop(config)
    db = Path(config["data_home"]) / "engage/engage.sqlite3"
    before = db.read_bytes()
    assert cli(path).returncode == 0
    assert json.loads(request(f"/api/notes/{note['id']}")) == saved
    assert request(asset["url"]) == bytes_before
    launcher.stop(config)
    assert db.read_bytes() == before
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.backup",
            "backup",
            "--data-dir",
            str(db.parent),
            "--destination",
            str(db.parent.parent / "copy"),
        ],
        capture_output=True,
        text=True,
        cwd=DESKTOP.parent / "backend",
    )
    assert result.returncode == 0, result.stderr


def test_installer_entries_and_failure_preserve_existing_config(tmp_path, monkeypatch):
    assert "Name=CyrNava\n" in installer.entry(
        tmp_path, "/usr/bin/python3", tmp_path / "cyrnava.svg"
    )
    assert "Name=Stop CyrNava\n" in installer.entry(
        tmp_path, "/usr/bin/python3", tmp_path / "cyrnava.svg", stop=True
    )
    assert "Terminal=false" in installer.entry(
        tmp_path / "space dir", "/usr/bin/python3", tmp_path / "engage logo.svg"
    )
    assert f"Icon={tmp_path / 'engage logo.svg'}" in installer.entry(
        tmp_path, "/usr/bin/python3", tmp_path / "engage logo.svg"
    )
    assert "Actions=Stop;Logs;" in installer.entry(
        tmp_path, "/usr/bin/python3", tmp_path / "engage.svg"
    )
    with pytest.raises(launcher.LaunchError):
        installer.desktop_quote("/bad\npath")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = tmp_path / "data/engage-application"
    root.mkdir(parents=True)
    original = json.dumps(
        {
            "data_home": str(tmp_path / "data"),
            "state_dir": str(tmp_path / "state/engage-launcher"),
        }
    )
    (root / "config.json").write_text(original)
    monkeypatch.setattr(installer.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(
        installer.subprocess,
        "check_output",
        lambda args, **kw: "v24.19.0" if args[0].endswith("node") else "11.6.2",
    )
    monkeypatch.setattr(
        installer, "run", Mock(side_effect=OSError("simulated install failure"))
    )
    args = type("Args", (), {"port": 8000, "icon": None, "desktop_dir": None})()
    with pytest.raises(OSError, match="simulated"):
        installer.install(args)
    assert (root / "config.json").read_text() == original
    assert list((root / "releases").iterdir()) == []


def managed_request(config, route, body=None):
    origin = f"http://127.0.0.1:{config['port']}"
    request = urllib.request.Request(
        origin + route,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "Origin": origin},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=2) as response:
        return json.load(response)


def until(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline, "Lifecycle condition timed out"
        time.sleep(0.05)


def quick_lifecycle(config, path, startup=4):
    config["lifecycle"] = {
        "heartbeat": 0.1,
        "expiration": 1,
        "grace": 0.4,
        "startup": startup,
    }
    path.write_text(json.dumps(config))


def assert_stopped(config, state):
    until(lambda: not launcher.process_matches(state))
    launcher.wait_for_supervisor(config)
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", config["port"]))


def test_managed_two_tabs_refresh_grace_and_restart(setup):
    config, path = setup
    quick_lifecycle(config, path)
    assert cli(path).returncode == 0
    state = launcher.read_state(config)
    instance = managed_request(config, "/api/lifecycle")["instance"]
    a, b = str(uuid4()), str(uuid4())

    def activity(tab, n, action="heartbeat"):
        managed_request(
            config,
            f"/api/lifecycle/sessions/{tab}",
            {"instance": instance, "sequence": n, "action": action},
        )

    activity(a, 1)
    activity(b, 1)
    activity(a, 2, "close")
    time.sleep(0.5)
    activity(b, 2)
    assert launcher.ready(config, state)
    activity(b, 3, "close")
    # Refresh/new page during the shutdown grace cancels drain.
    time.sleep(0.1)
    activity(a, 3)
    time.sleep(0.5)
    assert launcher.ready(config, state)
    activity(a, 4, "close")
    assert_stopped(config, state)
    assert cli(path).returncode == 0
    assert launcher.read_state(config)["nonce"] != instance


def test_managed_crashed_browser_expires_without_close_event(setup):
    config, path = setup
    quick_lifecycle(config, path)
    assert cli(path).returncode == 0
    state = launcher.read_state(config)
    managed_request(
        config,
        f"/api/lifecycle/sessions/{uuid4()}",
        {"instance": state["nonce"], "sequence": 1},
    )
    assert_stopped(config, state)


def test_missing_browser_registration_stops_backend_and_reports_failure(setup):
    config, path = setup
    quick_lifecycle(config, path, startup=1)
    assert cli(path, "open").returncode == 0
    state = launcher.read_state(config)
    assert_stopped(config, state)
    assert (
        "did not register" in (Path(config["state_dir"]) / "launcher.log").read_text()
    )


def test_unresponsive_owned_child_is_killed_and_reaped_without_touching_other_child():
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);"
            "print('ready',flush=True);time.sleep(30)",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    other = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    try:
        assert child.stdout.readline().strip() == "ready"
        launcher.terminate_owned(child, timeout=0.1)
        assert child.returncode == -signal.SIGKILL
        assert other.poll() is None
    finally:
        launcher.terminate_owned(child)
        launcher.terminate_owned(other)


def test_browser_dispatch_failure_does_not_stop_an_existing_instance(setup):
    config, path = setup
    assert cli(path).returncode == 0
    state = launcher.read_state(config)
    config["opener"] = "/bin/false"
    path.write_text(json.dumps(config))
    assert cli(path, "open").returncode == 1
    assert launcher.ready(config, state)


def test_backend_startup_failure_is_reported_and_reaped(setup):
    config, path = setup
    database = Path(config["data_home"]) / "engage/engage.sqlite3"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"synthetic invalid database")
    result = cli(path)
    assert result.returncode == 1
    assert "Backend exited during startup" in result.stderr
    launcher.wait_for_supervisor(config)
    assert not launcher.process_matches(launcher.read_state(config))


def test_firefox_new_window_dispatch_never_waits_for_browser_lifetime(monkeypatch):
    browser = Mock()
    browser.poll.return_value = None
    spawn = Mock(return_value=browser)
    monkeypatch.setattr(launcher.subprocess, "Popen", spawn)
    monkeypatch.setattr(launcher.time, "sleep", lambda _: None)
    launcher.open_browser({"browser": "/usr/bin/firefox", "port": 8000})
    assert spawn.call_args.args[0] == [
        "/usr/bin/firefox",
        "--new-window",
        "http://127.0.0.1:8000",
    ]
    browser.wait.assert_not_called()


def test_readiness_timeout_leaves_no_owned_worker_or_supervisor(setup):
    config, path = setup
    with pytest.raises(launcher.LaunchError, match="did not become ready"):
        launcher.start(config, path, timeout=0.01)
    launcher.wait_for_supervisor(config)
    assert not launcher.process_matches(launcher.read_state(config))
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", config["port"]))
