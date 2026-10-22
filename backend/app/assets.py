"""Validated raster images: filesystem bytes, SQLite ownership, no editor dependency."""

import io
import logging
import os
import re
import sqlite3
import warnings
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from app.database import NoteNotFound

MAX_BYTES = 10 * 1024 * 1024
MAX_DIMENSION = 8192
MAX_PIXELS = 20_000_000
FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
ASSET_NAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
logger = logging.getLogger(__name__)


class InvalidImage(Exception):
    pass


def validate_image(data: bytes, claimed_mime: str) -> tuple[bytes, str]:
    if not data or len(data) > MAX_BYTES:
        raise InvalidImage("Image must be between 1 byte and 10 MiB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=list(FORMATS)) as image:
                actual = image.format
                if claimed_mime != FORMATS[actual]:
                    raise InvalidImage(
                        "Image content does not match its declared "
                        "PNG, JPEG or WebP type"
                    )
                if (
                    max(image.size) > MAX_DIMENSION
                    or image.width * image.height > MAX_PIXELS
                ):
                    raise InvalidImage(
                        "Image exceeds 8192 pixels per side or 20 million pixels"
                    )
                if getattr(image, "n_frames", 1) != 1:
                    raise InvalidImage("Animated images are not supported")
                image.verify()
            with Image.open(io.BytesIO(data), formats=list(FORMATS)) as image:
                image.load()  # Full decode catches truncated image payloads.
                # Re-encode pixels only: strip metadata, trailers and embedded payloads.
                clean = Image.frombytes(image.mode, image.size, image.tobytes())
                if actual == "JPEG":
                    clean = clean.convert("RGB")
                elif clean.mode not in ("RGB", "RGBA"):
                    clean = image.convert("RGBA")
                    clean.info.clear()
                result = io.BytesIO()
                clean.save(
                    result,
                    format=actual,
                    **({"lossless": True} if actual == "WEBP" else {}),
                )
        encoded = result.getvalue()
        if len(encoded) > MAX_BYTES:
            raise InvalidImage("Decoded image exceeds the 10 MiB storage limit")
        return encoded, FORMATS[actual]
    except InvalidImage:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise InvalidImage(
            "Malformed or unsupported image; choose a valid PNG, JPEG or WebP"
        ) from None


class AssetStore:
    def __init__(self, database):
        self.database = database
        self.root = database.path.parent / "assets"
        repository = Path(__file__).resolve().parents[2]
        if self.root.resolve().is_relative_to(repository) or self.root.is_symlink():
            raise ValueError(
                "Asset storage must be outside the repository and not a symlink"
            )
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def path(self, name):
        if not ASSET_NAME.fullmatch(name):
            raise FileNotFoundError
        path = self.root / name
        if path.is_symlink() or path.resolve().parent != self.root.resolve():
            raise FileNotFoundError
        return path

    @staticmethod
    def _write(path, data):
        # Exclusive creation, private permissions, durable file before metadata commit.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise

    def upload(self, note_id, data, mime):
        encoded, mime = validate_image(data, mime)
        identifier = str(uuid4())
        path = self.path(identifier)
        created = False
        try:
            with self.database.connect() as connection:
                # Also serializes uploads, note deletion and reconciliation.
                connection.execute("BEGIN IMMEDIATE")
                if not connection.execute(
                    "SELECT 1 FROM notes WHERE id = ?", (note_id,)
                ).fetchone():
                    raise NoteNotFound
                self._write(path, encoded)
                created = True
                connection.execute(
                    """INSERT INTO assets
                    (id, note_id, mime_type, byte_size, disk_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        identifier,
                        note_id,
                        mime,
                        len(encoded),
                        identifier,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        except BaseException:
            if created:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Asset cleanup deferred until next startup")
            raise
        return {
            "id": identifier,
            "note_id": note_id,
            "mime_type": mime,
            "byte_size": len(encoded),
            "url": f"/api/assets/{identifier}",
        }

    def retrieve(self, identifier):
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM assets WHERE id = ?", (identifier,)
            ).fetchone()
            if (
                row is None
                or row["disk_path"] != identifier
                or row["mime_type"] not in FORMATS.values()
            ):
                raise FileNotFoundError
            path = self.path(row["disk_path"])
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as stream:
                data = stream.read(MAX_BYTES + 1)
            if len(data) != row["byte_size"] or len(data) > MAX_BYTES:
                raise FileNotFoundError
            return data, row["mime_type"]

    def cleanup(self):
        try:
            self._cleanup()
        except (OSError, sqlite3.Error):
            # Note deletion has already committed. A cleanup failure must not
            # misreport that durable deletion as failed; retry at startup.
            logger.warning("Asset reconciliation deferred until next startup")

    def _cleanup(self):
        # Only unowned, generated filenames. Never remove an upload owned by a
        # live note: its document save may still be pending or may have failed.
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            live = {
                row[0] for row in connection.execute("SELECT disk_path FROM assets")
            }
            for path in self.root.iterdir():
                if ASSET_NAME.fullmatch(path.name) and path.name not in live:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        logger.warning("Asset cleanup deferred until next startup")
