"""Built frontend serving for the single-origin, loopback-only release launcher."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

RELEASE_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; img-src 'self' data: blob:; media-src 'none'; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)


def serve_frontend(application: FastAPI, directory: Path, health):
    if not (directory / "index.html").is_file() or not (directory / "assets").is_dir():
        raise RuntimeError(
            "Frontend build missing. Run npm ci and npm run build in frontend first."
        )
    application.add_api_route("/api/health", health, methods=["GET"])
    application.mount(
        "/assets", StaticFiles(directory=directory / "assets"), name="frontend-assets"
    )

    @application.get("/", include_in_schema=False)
    def index():
        return FileResponse(
            directory / "index.html", headers={"Cache-Control": "no-store"}
        )

    notice = directory / "third-party-notices.txt"
    if notice.is_file():

        @application.get("/third-party-notices.txt", include_in_schema=False)
        def third_party_notices():
            return FileResponse(notice, media_type="text/plain")

    @application.middleware("http")
    async def local_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", RELEASE_CSP)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response
