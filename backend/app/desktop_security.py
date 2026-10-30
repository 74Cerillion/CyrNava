"""Authorization for the native desktop's private HTTP session.

The legacy development/Firefox entry points deliberately do not opt into this
mode. The desktop authenticates *every* path, including static assets and health.
"""

import secrets
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from starlette.responses import JSONResponse

HEADER = b"x-cyrnava-session"


@dataclass(repr=False)
class DesktopSession:
    origin: str
    token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    active: bool = True

    def __post_init__(self):
        url = urlsplit(self.origin)
        if (
            url.scheme != "http"
            or url.hostname != "127.0.0.1"
            or not url.port
            or self.origin != f"http://127.0.0.1:{url.port}"
            or len(self.token) < 32
            or not self.token.isascii()
        ):
            raise ValueError("Invalid desktop session configuration")
        self.host = url.netloc.encode("ascii")

    def revoke(self):
        self.active = False
        self.token = ""


class DesktopAuthorization:
    def __init__(self, app, session: DesktopSession):
        self.app, self.session = app, session

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = scope["headers"]

        def values(name):
            return [value for key, value in headers if key.lower() == name]

        host, origin, credentials = values(b"host"), values(b"origin"), values(HEADER)
        metadata = values(b"sec-fetch-site")
        status, detail = 401, "Desktop session authorization required"
        if host != [self.session.host]:
            status, detail = 400, "Invalid Host"
        elif (
            (origin and origin != [self.session.origin.encode("ascii")])
            or (scope["method"] not in ("GET", "HEAD") and not origin)
            or (metadata and metadata not in ([b"same-origin"], [b"none"]))
        ):
            status, detail = 403, "Invalid Origin"
        elif (
            self.session.active
            and len(credentials) == 1
            and secrets.compare_digest(
                credentials[0], self.session.token.encode("ascii")
            )
        ):

            async def private_send(message):
                if message["type"] == "http.response.start":
                    message["headers"] = [
                        (key, value)
                        for key, value in message["headers"]
                        if key.lower() != b"cache-control"
                    ] + [(b"cache-control", b"no-store")]
                await send(message)

            await self.app(scope, receive, private_send)
            return
        await JSONResponse(
            {"detail": detail},
            status_code=status,
            headers={"Cache-Control": "no-store"},
        )(scope, receive, send)
