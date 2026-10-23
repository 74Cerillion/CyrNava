import asyncio
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app import __version__
from app.assets import MAX_BYTES, AssetStore, InvalidImage
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
from app.profile import profile_lock
from app.release import serve_frontend


def create_app(
    database_path: Path | None = None, frontend_path: Path | None = None
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        # Resolve/create data only at startup, never at module import or in tests
        # that do not enter the application's lifespan.
        database = Database(database_path or default_database_path())
        with profile_lock(database.path.parent):
            database.initialize()
            application.state.database = database
            application.state.assets = AssetStore(database)
            application.state.assets.cleanup()
            application.state.upload_slots = asyncio.Semaphore(2)
            yield

    application = FastAPI(
        title="ENGAGE",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
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
        request.app.state.assets.cleanup()
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
        request.app.state.assets.cleanup()
        return Response(status_code=204)

    @application.post("/api/assets", status_code=201)
    async def upload_asset(note_id: UUID, request: Request):
        # Raw binary keeps the body bounded without a multipart parser/spool.
        async with request.app.state.upload_slots:
            data = bytearray()
            try:
                async with asyncio.timeout(30):
                    async for chunk in request.stream():
                        if len(data) + len(chunk) > MAX_BYTES:
                            raise HTTPException(
                                413, "Image exceeds 10 MiB upload limit"
                            )
                        data.extend(chunk)
                return await run_in_threadpool(
                    request.app.state.assets.upload,
                    str(note_id),
                    bytes(data),
                    request.headers.get("content-type", "").split(";", 1)[0],
                )
            except TimeoutError:
                raise HTTPException(408, "Image upload timed out") from None
            except NoteNotFound:
                raise HTTPException(404, "Note not found") from None
            except InvalidImage as error:
                raise HTTPException(422, str(error)) from None
            except OSError:
                raise HTTPException(503, "Local image storage unavailable") from None

    @application.get("/api/assets/{asset_id}")
    def get_asset(asset_id: UUID, request: Request):
        try:
            data, mime = request.app.state.assets.retrieve(str(asset_id))
        except (FileNotFoundError, PermissionError):
            raise HTTPException(404, "Image unavailable on this computer") from None
        except OSError:
            raise HTTPException(503, "Local image storage unavailable") from None
        return Response(
            data,
            media_type=mime,
            headers={
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; sandbox",
                "Cache-Control": "no-store",
                "Content-Disposition": 'inline; filename="image"',
            },
        )

    if frontend_path is not None:
        serve_frontend(application, frontend_path, health)
    return application


app = create_app()
