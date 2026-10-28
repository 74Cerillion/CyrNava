from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.lifecycle import Sessions, Timing
from app.main import create_app


@pytest.fixture
def leases():
    now = [0.0]
    sessions = Sessions("instance", "private-secret", clock=lambda: now[0])
    return sessions, now


def test_startup_expiration_grace_and_drain_are_monotonic(leases):
    sessions, now = leases
    now[0] = 59
    assert not sessions.inspect()["draining"]
    sessions.touch("tab", 1, "heartbeat")
    now[0] = 78
    assert sessions.inspect()["sessions"] == 1
    now[0] = 79
    assert not sessions.inspect()["draining"]
    now[0] = 84
    assert sessions.inspect()["draining"]
    with pytest.raises(HTTPException) as error:
        sessions.touch("tab", 2, "heartbeat")
    assert error.value.status_code == 503


def test_startup_failure_has_bounded_grace(leases):
    sessions, now = leases
    now[0] = 60
    assert sessions.inspect() == {
        "sessions": 0,
        "draining": True,
        "reason": "startup-timeout",
        "phase": "draining",
    }


def test_other_tab_and_reconnection_cancel_shutdown(leases):
    sessions, now = leases
    sessions.touch("A", 1, "heartbeat")
    sessions.touch("B", 1, "heartbeat")
    sessions.touch("A", 2, "close")
    assert sessions.inspect()["sessions"] == 1
    sessions.touch("B", 2, "close")
    assert not sessions.inspect()["draining"]
    now[0] = 4
    sessions.touch("C", 1, "heartbeat")
    now[0] = 6
    assert sessions.inspect()["sessions"] == 1
    assert not sessions.draining


def test_delayed_heartbeat_cannot_undo_close_but_pageshow_can(leases):
    sessions, _ = leases
    sessions.touch("A", 1, "heartbeat")
    sessions.touch("A", 3, "close")
    sessions.touch("A", 2, "heartbeat")
    assert sessions.inspect()["sessions"] == 0
    sessions.touch("A", 4, "heartbeat")
    assert sessions.inspect()["sessions"] == 1


def test_expired_entries_are_bounded_and_pruned(leases):
    sessions, now = leases
    for n in range(1024):
        sessions.touch(str(n), 1, "heartbeat")
    with pytest.raises(HTTPException):
        sessions.touch("overflow", 1, "heartbeat")
    now[0] = 21
    sessions.touch("new", 1, "heartbeat")
    assert len(sessions.entries) == 1


def test_managed_routes_require_origin_identity_and_supervisor_secret(tmp_path, leases):
    sessions, now = leases
    with TestClient(
        create_app(tmp_path / "engage.sqlite3", sessions=sessions),
        base_url="http://127.0.0.1:8000",
    ) as client:
        assert client.get("/api/lifecycle").json()["managed"] is True
        path = f"/api/lifecycle/sessions/{uuid4()}"
        body = {"instance": "instance", "sequence": 1}
        assert client.post(path, json=body).status_code == 403
        assert (
            client.post(
                path, json=body, headers={"Origin": "https://unrelated.invalid"}
            ).status_code
            == 403
        )
        headers = {"Origin": "http://127.0.0.1:8000"}
        assert (
            client.post(
                path, json={**body, "instance": "old"}, headers=headers
            ).status_code
            == 409
        )
        assert (
            client.post(
                path, json={**body, "instance": "🔥"}, headers=headers
            ).status_code
            == 409
        )
        assert (
            client.post(
                path, json={**body, "sequence": True}, headers=headers
            ).status_code
            == 422
        )
        assert client.post(path, json=body, headers=headers).status_code == 200
        assert client.get("/api/lifecycle/supervisor").status_code == 403
        auth = {"X-ENGAGE-Supervisor": "private-secret"}
        assert (
            client.get("/api/lifecycle/supervisor", headers=auth).json()["sessions"]
            == 1
        )
        # New name is canonical; the old header remains a private-protocol alias.
        assert (
            client.get(
                "/api/lifecycle/supervisor",
                headers={"X-CYRNAVA-Supervisor": "private-secret"},
            ).status_code
            == 200
        )
        now[0] = 21
        client.get("/api/lifecycle/supervisor", headers=auth)
        now[0] = 26
        assert client.get("/api/lifecycle/supervisor", headers=auth).json()["draining"]
        assert client.post(path, json=body, headers=headers).status_code == 503
        assert client.post("/api/notes", json={}).status_code == 503


def test_development_server_has_no_session_watchdog(client):
    assert client.get("/api/lifecycle").json() == {"managed": False}
    assert client.get("/api/lifecycle/supervisor").status_code == 404
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    "settings",
    [
        {"heartbeat": 0},
        {"expiration": 1},
        {"grace": 0},
        {"startup": 0},
        {"startup": float("inf")},
    ],
)
def test_invalid_timing_rejected(settings):
    with pytest.raises(ValueError):
        Timing(**settings)
