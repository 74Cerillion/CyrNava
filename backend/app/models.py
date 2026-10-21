"""Version 1 document contract. Preserve JSON; validate the supported editor shape."""

import json
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StrictInt,
    StringConstraints,
    model_validator,
)

BLOCK_TYPES = {
    "paragraph",
    "heading",
    "bulletListItem",
    "numberedListItem",
    "checkListItem",
    "quote",
}


def validate_document(document: list[dict[str, JsonValue]]) -> list[dict]:
    if not document:
        raise ValueError("Document must contain at least one block")
    if (
        len(json.dumps(document, ensure_ascii=False, allow_nan=False).encode())
        > 1_048_576
    ):
        raise ValueError("Document exceeds the 1 MiB M1 limit")
    ids = set()
    count = 0

    def inline(items, depth=0):
        if not isinstance(items, list) or depth > 32:
            raise ValueError("Invalid inline content")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Inline content must be objects")
            if item.get("type") == "text":
                if not isinstance(item.get("text"), str) or not isinstance(
                    item.get("styles", {}), dict
                ):
                    raise ValueError("Invalid text content")
            elif item.get("type") == "link":
                if not isinstance(item.get("href"), str):
                    raise ValueError("Invalid link")
                inline(item.get("content"), depth + 1)
            else:
                raise ValueError("Unsupported inline content")

    def blocks(items, depth=0):
        nonlocal count
        if not isinstance(items, list) or depth > 32:
            raise ValueError("Invalid block nesting")
        for block in items:
            count += 1
            if count > 5000:
                raise ValueError("Too many document blocks")
            if not isinstance(block, dict) or (
                not isinstance(block.get("type"), str)
                or block["type"] not in BLOCK_TYPES
            ):
                raise ValueError("Unsupported block type")
            if "id" in block:
                identifier = block["id"]
                if (
                    not isinstance(identifier, str)
                    or not identifier
                    or identifier in ids
                ):
                    raise ValueError(
                        "Block identifiers must be unique nonempty strings"
                    )
                ids.add(identifier)
            if not isinstance(block.get("props", {}), dict):
                raise ValueError("Invalid block properties")
            if block["type"] == "heading" and (
                block.get("props", {}).get("level", 1) not in (1, 2, 3)
            ):
                raise ValueError("Invalid heading level")
            inline(block.get("content", []))
            blocks(block.get("children", []), depth + 1)

    blocks(document)
    return document


Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Document = Annotated[list[dict[str, JsonValue]], AfterValidator(validate_document)]


class CreateNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Title
    document_json: Document
    format_version: Annotated[StrictInt, Field(ge=1, le=1)] = 1


class UpdateNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: Annotated[StrictInt, Field(ge=1)]
    title: Title | None = None
    document_json: Document | None = None

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        changed = self.model_fields_set - {"revision"}
        if not changed or any(getattr(self, field) is None for field in changed):
            raise ValueError("Provide a non-null title and/or document_json")
        return self


class Note(BaseModel):
    id: str
    folder_id: None
    title: str
    document_json: list[dict[str, JsonValue]]
    format_version: int
    revision: int
    created_at: str
    updated_at: str
