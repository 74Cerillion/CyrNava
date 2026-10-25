"""Version 1 document contract. Preserve JSON; validate the supported editor shape."""

from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StrictBool,
    StrictInt,
    StringConstraints,
    model_validator,
)

from app.documents import validate_document

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Document = Annotated[list[dict[str, JsonValue]], AfterValidator(validate_document)]


class CreateNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Title
    document_json: Document
    format_version: Annotated[StrictInt, Field(ge=1, le=1)] = 1
    folder_id: UUID | None = None


class UpdateNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: Annotated[StrictInt, Field(ge=1)]
    title: Title | None = None
    document_json: Document | None = None
    folder_id: UUID | None = None

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        changed = self.model_fields_set - {"revision"}
        if not changed or any(
            getattr(self, field) is None for field in changed if field != "folder_id"
        ):
            raise ValueError("Provide a non-null title and/or document_json")
        return self


class Note(BaseModel):
    id: str
    folder_id: str | None
    title: str
    document_json: list[dict[str, JsonValue]]
    format_version: int
    revision: int
    created_at: str
    updated_at: str


class CreateFolder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Title
    parent_id: UUID | None = None


class UpdateFolder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Title | None = None
    parent_id: UUID | None = None

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        if not self.model_fields_set or (
            "name" in self.model_fields_set and self.name is None
        ):
            raise ValueError("Provide a name and/or parent_id")
        return self


class Folder(BaseModel):
    id: str
    parent_id: str | None
    name: str
    sort_order: int
    created_at: str
    updated_at: str


class NoteSummary(BaseModel):
    id: str
    folder_id: str | None
    title: str
    revision: int
    created_at: str
    updated_at: str


class DirectoryTree(BaseModel):
    folders: list[Folder]
    notes: list[NoteSummary]


class DeletionImpact(BaseModel):
    folder_id: str
    name: str
    descendant_folders: int
    notes: int
    token: str


class DeleteFolder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recursive: StrictBool = False
    expected_descendant_folders: Annotated[StrictInt, Field(ge=0)]
    expected_notes: Annotated[StrictInt, Field(ge=0)]
    impact_token: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class DeleteNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: Annotated[StrictInt, Field(ge=1)]
