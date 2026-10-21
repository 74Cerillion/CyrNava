import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database import Database, NoteNotFound, RevisionConflict, default_database_path
from app.models import CreateNote, Note, UpdateNote


def create_app(database_path: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        # Resolve/create data only at startup, never at module import or in tests
        # that do not enter the application's lifespan.
        database = Database(database_path or default_database_path())
        database.initialize()
        application.state.database = database
        yield

    application = FastAPI(
        lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
    )

    @application.exception_handler(sqlite3.Error)
    async def database_error(_request: Request, _error: sqlite3.Error):
        return JSONResponse(
            status_code=503, content={"detail": "Local database unavailable"}
        )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/api/notes", response_model=Note, status_code=201)
    def create_note(body: CreateNote, request: Request):
        return request.app.state.database.create(
            body.title, body.document_json, body.format_version
        )

    @application.get("/api/notes/{note_id}", response_model=Note)
    def get_note(note_id: UUID, request: Request):
        try:
            return request.app.state.database.get(str(note_id))
        except NoteNotFound:
            raise HTTPException(status_code=404, detail="Note not found") from None

    @application.patch("/api/notes/{note_id}", response_model=Note)
    def update_note(note_id: UUID, body: UpdateNote, request: Request):
        changes = body.model_dump(exclude_unset=True, exclude={"revision"})
        try:
            return request.app.state.database.update(
                str(note_id), body.revision, changes
            )
        except NoteNotFound:
            raise HTTPException(status_code=404, detail="Note not found") from None
        except RevisionConflict:
            raise HTTPException(
                status_code=409,
                detail="Note changed since this revision. Reload before editing again.",
            ) from None

    return application


app = create_app()
