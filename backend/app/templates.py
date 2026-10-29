"""Native note templates and independent image snapshots in the existing SQLite DB."""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.assets import ASSET_NAME, FORMATS, validate_image
from app.database import Database, InvalidRelationship, NoteNotFound, RevisionConflict
from app.documents import validate_document
from app.search import index_note

# Data, not commands: code sections start empty and nothing is executed.
STARTERS = (
    (
        "general",
        "General Penetration Testing Notes",
        (
            "Objective",
            "Scope",
            "Environment",
            "Methodology",
            "Commands Executed",
            "Observations",
            "Findings",
            "Evidence",
            "Next Steps",
        ),
    ),
    (
        "enumeration",
        "Enumeration Notes",
        (
            "Target Information",
            "Discovery Methodology",
            "Open Ports",
            "Identified Services",
            "Service Versions",
            "Commands Executed",
            "Enumeration Results",
            "Potential Attack Surface",
            "Screenshots / Evidence",
            "Next Steps",
        ),
    ),
    (
        "exploitation",
        "Exploitation Notes",
        (
            "Target",
            "Vulnerability Description",
            "Preconditions",
            "Exploitation Methodology",
            "Commands / Payloads",
            "Results",
            "Evidence",
            "Limitations",
            "Remediation Considerations",
        ),
    ),
    (
        "privilege-escalation",
        "Privilege Escalation Notes",
        (
            "Initial Access Context",
            "Current User / Privileges",
            "System Information",
            "Enumeration",
            "Potential Escalation Paths",
            "Exploitation Steps",
            "Resulting Privileges",
            "Evidence",
            "Lessons Learned",
        ),
    ),
    (
        "lab",
        "HTB / TryHackMe Lab Notes",
        (
            "Lab Name",
            "Platform",
            "Difficulty",
            "Learning Objectives",
            "Target Information",
            "Enumeration",
            "Exploitation",
            "Privilege Escalation",
            "Flags / Completion",
            "Lessons Learned",
            "Additional Research",
        ),
    ),
)
MAX_TEMPLATE_IMAGE_BYTES = 50 * 1024 * 1024


class TemplateNotFound(Exception):
    pass


class ProtectedTemplate(Exception):
    pass


def builtin_templates():
    result = {}
    for key, name, sections in STARTERS:
        document = []
        for section in sections:
            document.append(
                {
                    "type": "heading",
                    "props": {"level": 2},
                    "content": [{"type": "text", "text": section, "styles": {}}],
                    "children": [],
                }
            )
            document.append(
                {
                    "type": "codeBlock",
                    "props": {"language": "text"},
                    "content": [],
                    "children": [],
                }
                if section in ("Commands Executed", "Commands / Payloads")
                else {"type": "paragraph", "content": [], "children": []}
            )
        result[f"builtin:{key}"] = {
            "id": f"builtin:{key}",
            "name": name,
            "revision": 1,
            "builtin": True,
            "document_json": document,
        }
    return result


def blocks(document):
    for block in document:
        yield block
        yield from blocks(block.get("children", []))


def image_ids(document):
    return {
        block["props"]["url"].rsplit("/", 1)[-1]
        for block in blocks(document)
        if block["type"] == "image" and block.get("props", {}).get("url")
    }


def validate_snapshots(document, images):
    validate_document(document)
    if image_ids(document) != {row["asset_id"] for row in images}:
        raise InvalidRelationship("Template image snapshots do not match its document")
    if sum(len(row["data"]) for row in images) > MAX_TEMPLATE_IMAGE_BYTES:
        raise InvalidRelationship("Template images exceed the 50 MiB total limit")
    for row in images:
        if (
            not ASSET_NAME.fullmatch(row["asset_id"])
            or row["mime_type"] not in FORMATS.values()
        ):
            raise InvalidRelationship("Invalid template image metadata")
        validate_image(bytes(row["data"]), row["mime_type"])


def stored_images(connection, identifier):
    # Bound reads before materializing BLOBs, including during backup validation.
    size = connection.execute(
        "SELECT COALESCE(SUM(length(data)), 0) FROM template_images "
        "WHERE template_id=?",
        (identifier,),
    ).fetchone()[0]
    if size > MAX_TEMPLATE_IMAGE_BYTES:
        raise InvalidRelationship("Template images exceed the 50 MiB total limit")
    return connection.execute(
        "SELECT * FROM template_images WHERE template_id=?", (identifier,)
    ).fetchall()


class TemplateStore:
    def __init__(self, database, assets):
        self.database, self.assets = database, assets

    @staticmethod
    def summary(row):
        return {key: row[key] for key in ("id", "name", "revision")} | {
            "builtin": False
        }

    def list(self):
        builtins = [
            {key: row[key] for key in ("id", "name", "revision", "builtin")}
            for row in builtin_templates().values()
        ]
        with self.database.connect() as connection:
            custom = [
                self.summary(row)
                for row in connection.execute(
                    "SELECT id, name, revision FROM templates "
                    "ORDER BY name COLLATE NOCASE, id"
                )
            ]
        return builtins + custom

    @staticmethod
    def custom(connection, identifier, revision):
        if identifier in builtin_templates():
            raise ProtectedTemplate
        row = connection.execute(
            "SELECT * FROM templates WHERE id = ?", (identifier,)
        ).fetchone()
        if row is None:
            raise TemplateNotFound
        if row["revision"] != revision:
            raise RevisionConflict
        return row

    def capture(self, name, note_id, revision):
        identifier, now = str(uuid4()), datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            # Capture the exact confirmed revision; concurrent edits/deletion
            # cannot change its document or image ownership halfway through.
            connection.execute("BEGIN IMMEDIATE")
            source = connection.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if source is None:
                raise NoteNotFound
            if source["revision"] != revision:
                raise RevisionConflict
            document = json.loads(source["document_json"])
            Database._check_images(connection, note_id, document)
            images = []
            for asset_id in sorted(image_ids(document)):
                try:
                    data, mime = self.assets.retrieve(asset_id)
                except (OSError, FileNotFoundError):
                    raise InvalidRelationship(
                        "A source image is unavailable; template was not saved"
                    ) from None
                images.append({"asset_id": asset_id, "mime_type": mime, "data": data})
                if sum(len(row["data"]) for row in images) > MAX_TEMPLATE_IMAGE_BYTES:
                    raise InvalidRelationship(
                        "Template images exceed the 50 MiB total limit"
                    )
            validate_snapshots(document, images)
            connection.execute(
                """INSERT INTO templates
                (id, name, document_json, format_version, revision,
                 created_at, updated_at)
                VALUES (?, ?, ?, 1, 1, ?, ?)""",
                (identifier, name, source["document_json"], now, now),
            )
            connection.executemany(
                """INSERT INTO template_images
                (template_id, asset_id, mime_type, data) VALUES (?, ?, ?, ?)""",
                [
                    (identifier, row["asset_id"], row["mime_type"], row["data"])
                    for row in images
                ],
            )
        return {"id": identifier, "name": name, "revision": 1, "builtin": False}

    def rename(self, identifier, revision, name):
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self.custom(connection, identifier, revision)
            connection.execute(
                "UPDATE templates SET name=?, revision=revision+1, updated_at=? "
                "WHERE id=?",
                (name, datetime.now(timezone.utc).isoformat(), identifier),
            )
            return self.summary(
                connection.execute(
                    "SELECT * FROM templates WHERE id=?", (identifier,)
                ).fetchone()
            )

    def delete(self, identifier, revision):
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self.custom(connection, identifier, revision)
            connection.execute("DELETE FROM templates WHERE id=?", (identifier,))

    def instantiate(self, identifier, revision, title, folder_id):
        created_paths = []
        try:
            with self.database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                builtin = builtin_templates().get(identifier)
                if builtin:
                    if revision != 1:
                        raise RevisionConflict
                    document, images = builtin["document_json"], []
                else:
                    row = self.custom(connection, identifier, revision)
                    document = json.loads(row["document_json"])
                    images = stored_images(connection, identifier)
                validate_snapshots(document, images)
                Database._check_parent(connection, folder_id)
                note_id, now = str(uuid4()), datetime.now(timezone.utc).isoformat()
                remap = {row["asset_id"]: str(uuid4()) for row in images}
                for block in blocks(document):
                    block["id"] = str(uuid4())
                    if block["type"] == "image" and block.get("props", {}).get("url"):
                        old_id = block["props"]["url"].rsplit("/", 1)[-1]
                        block["props"]["url"] = f"/api/assets/{remap[old_id]}"
                validate_document(document)
                connection.execute(
                    """INSERT INTO notes
                    (id, folder_id, title, document_json, format_version,
                     revision, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, 1, ?, ?)""",
                    (
                        note_id,
                        folder_id,
                        title,
                        json.dumps(document, ensure_ascii=False),
                        now,
                        now,
                    ),
                )
                for row in images:
                    asset_id = remap[row["asset_id"]]
                    path = self.assets.path(asset_id)
                    self.assets._write(path, bytes(row["data"]))
                    created_paths.append(path)
                    connection.execute(
                        """INSERT INTO assets
                        (id, note_id, mime_type, byte_size, disk_path, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            asset_id,
                            note_id,
                            row["mime_type"],
                            len(row["data"]),
                            asset_id,
                            now,
                        ),
                    )
                Database._check_images(connection, note_id, document)
                saved = connection.execute(
                    "SELECT * FROM notes WHERE id=?", (note_id,)
                ).fetchone()
                index_note(connection, saved)
            return Database._note(saved)
        except BaseException:
            # SQL rollback removes partial records. Generated files are removed
            # now, or by established orphan reconciliation after a process crash.
            for path in created_paths:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass  # Existing startup reconciliation retries orphan cleanup.
            raise


def validate_saved_templates(connection):
    """Used by offline backup validation, without migrating its source DB."""
    for row in connection.execute("SELECT * FROM templates"):
        UUID(row["id"])
        if (
            not row["name"].strip()
            or len(row["name"]) > 200
            or row["format_version"] != 1
            or row["revision"] < 1
        ):
            raise InvalidRelationship("Invalid template metadata")
        images = stored_images(connection, row["id"])
        validate_snapshots(json.loads(row["document_json"]), images)
