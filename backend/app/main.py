import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app.database import (
    Database,
    DeletionConflict,
    FolderNotFound,
    InvalidRelationship,
    NoteNotFound,
    RevisionConflict,
    default_database_path,
)
from app.models import (
    CreateFolder,
    CreateNote,
    DeleteFolder,
    DeleteNote,
    DeletionImpact,
    DirectoryTree,
    Folder,
    Note,
    UpdateFolder,
    UpdateNote,
)


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

    @application.exception_handler(FolderNotFound)
    async def folder_missing(_request: Request, _error: FolderNotFound):
        return JSONResponse(status_code=404, content={"detail": "Folder not found"})

    @application.exception_handler(InvalidRelationship)
    async def invalid_relationship(_request: Request, error: InvalidRelationship):
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @application.exception_handler(DeletionConflict)
    async def deletion_conflict(_request: Request, error: DeletionConflict):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @application.get("/api/tree", response_model=DirectoryTree)
    def get_tree(request: Request):
        return request.app.state.database.tree()

    @application.post("/api/folders", response_model=Folder, status_code=201)
    def create_folder(body: CreateFolder, request: Request):
        return request.app.state.database.create_folder(
            body.name, str(body.parent_id) if body.parent_id else None
        )

    @application.patch("/api/folders/{folder_id}", response_model=Folder)
    def update_folder(folder_id: UUID, body: UpdateFolder, request: Request):
        return request.app.state.database.update_folder(
            str(folder_id), body.model_dump(mode="json", exclude_unset=True)
        )

    @application.get(
        "/api/folders/{folder_id}/deletion-impact", response_model=DeletionImpact
    )
    def deletion_impact(folder_id: UUID, request: Request):
        return request.app.state.database.deletion_impact(str(folder_id))

    @application.delete("/api/folders/{folder_id}", status_code=204)
    def delete_folder(folder_id: UUID, body: DeleteFolder, request: Request):
        request.app.state.database.delete_folder(str(folder_id), body.model_dump())
        return Response(status_code=204)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/api/notes", response_model=Note, status_code=201)
    def create_note(body: CreateNote, request: Request):
        return request.app.state.database.create(
            body.title,
            body.document_json,
            body.format_version,
            str(body.folder_id) if body.folder_id else None,
        )

    @application.get("/api/notes/{note_id}", response_model=Note)
    def get_note(note_id: UUID, request: Request):
        try:
            return request.app.state.database.get(str(note_id))
        except NoteNotFound:
            raise HTTPException(status_code=404, detail="Note not found") from None

    @application.patch("/api/notes/{note_id}", response_model=Note)
    def update_note(note_id: UUID, body: UpdateNote, request: Request):
        changes = body.model_dump(mode="json", exclude_unset=True, exclude={"revision"})
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

    @application.delete("/api/notes/{note_id}", status_code=204)
    def delete_note(note_id: UUID, body: DeleteNote, request: Request):
        try:
            request.app.state.database.delete_note(str(note_id), body.revision)
        except NoteNotFound:
            raise HTTPException(status_code=404, detail="Note not found") from None
        except RevisionConflict:
            raise HTTPException(
                status_code=409, detail="Note changed. Review before deleting."
            ) from None
        return Response(status_code=204)

    return application


app = create_app()
