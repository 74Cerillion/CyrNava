"""In-memory leases for desktop launches only. No notes or browser data here."""

import secrets
import time
from dataclasses import dataclass
from math import isfinite
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class Timing:
    heartbeat: float = 5
    expiration: float = 20
    grace: float = 5
    startup: float = 60

    def __post_init__(self):
        if not (
            all(isfinite(value) for value in vars(self).values())
            and 0 < self.heartbeat < self.expiration
            and self.grace > 0
            and self.startup > 0
        ):
            raise ValueError("Invalid lifecycle timing")


class Sessions:
    """Called on the ASGI event loop: drain decisions and leases are atomic."""

    def __init__(
        self, instance: str, secret: str, timing=Timing(), clock=time.monotonic
    ):
        self.instance, self.secret, self.timing, self.clock = (
            instance,
            secret,
            timing,
            clock,
        )
        self.started = clock()
        self.entries: dict[str, tuple[float, int, bool]] = {}
        self.ever_registered = False
        self.empty_since: float | None = None
        self.draining = False
        self.reason: str | None = None

    def prune(self):
        now = self.clock()
        self.entries = {
            key: value
            for key, value in self.entries.items()
            if now - value[0] < self.timing.expiration
        }

    def touch(self, identifier: str, sequence: int, action: str):
        self.prune()
        if self.draining:
            raise HTTPException(
                503, "ENGAGE is stopping. Launch it again, then reconnect."
            )
        previous = self.entries.get(identifier)
        # A delayed heartbeat must not undo a later close beacon.
        if previous and sequence <= previous[1]:
            return
        if identifier not in self.entries and len(self.entries) >= 1024:
            raise HTTPException(503, "Too many local browser sessions")
        self.entries[identifier] = (self.clock(), sequence, action == "close")
        self.ever_registered = True
        if action != "close":
            self.empty_since = None

    def inspect(self):
        self.prune()
        now = self.clock()
        count = sum(not entry[2] for entry in self.entries.values())
        reason = None
        if not self.draining:
            if count:
                self.empty_since = None
            elif not self.ever_registered:
                if now - self.started >= self.timing.startup:
                    self.draining, reason = True, "startup-timeout"
            else:
                if self.empty_since is None:
                    self.empty_since = now
                if now - self.empty_since >= self.timing.grace:
                    self.draining, reason = True, "last-session-ended"
        if reason:
            self.reason = reason
        phase = (
            "draining"
            if self.draining
            else "active"
            if count
            else ("grace" if self.ever_registered else "startup")
        )
        return {
            "sessions": count,
            "draining": self.draining,
            "reason": self.reason,
            "phase": phase,
        }


class Activity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instance: str = Field(max_length=64)
    sequence: int = Field(strict=True, ge=0, le=2**53 - 1)
    action: Literal["heartbeat", "close"] = "heartbeat"


def install_lifecycle(application: FastAPI, sessions: Sessions | None):
    @application.get("/api/lifecycle", include_in_schema=False)
    async def configuration():
        if sessions is None:
            return {"managed": False}
        if sessions.draining:
            raise HTTPException(503, "ENGAGE is stopping")
        return {
            "managed": True,
            "instance": sessions.instance,
            "heartbeat_ms": int(sessions.timing.heartbeat * 1000),
        }

    if sessions is None:
        return

    @application.middleware("http")
    async def refuse_during_drain(request: Request, call_next):
        # Already accepted handlers may finish. New mutations/leases cannot
        # connect to a half-stopped process after the supervisor claims drain.
        if sessions.draining and request.method not in ("GET", "HEAD"):
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=503, content={"detail": "ENGAGE is stopping"}
            )
        return await call_next(request)

    @application.post("/api/lifecycle/sessions/{identifier}", include_in_schema=False)
    async def activity(identifier: UUID, body: Activity, request: Request):
        # JSON + exact Origin, without CORS, rejects other websites and simple
        # cross-origin form/beacon traffic. Loopback is not an authentication system.
        origin = request.headers.get("origin")
        if (
            request.url.hostname != "127.0.0.1"
            or origin != f"http://{request.headers.get('host')}"
            or request.headers.get("sec-fetch-site", "same-origin")
            not in ("same-origin", "none")
        ):
            raise HTTPException(403, "Same-origin ENGAGE session required")
        if not secrets.compare_digest(
            body.instance.encode(), sessions.instance.encode()
        ):
            raise HTTPException(409, "ENGAGE instance changed; reconnect")
        sessions.touch(str(identifier), body.sequence, body.action)
        return {"registered": body.action != "close"}

    @application.get("/api/lifecycle/supervisor", include_in_schema=False)
    async def inspect(request: Request):
        if not secrets.compare_digest(
            request.headers.get("x-engage-supervisor", "").encode(),
            sessions.secret.encode(),
        ):
            raise HTTPException(403, "Supervisor access required")
        return sessions.inspect()
