"""Bounded, native format-1 JSON validated against the installed editor contract.

Tests check the contract against the frontend schema. Extra metadata/properties
remain intact; new block, inline and style types require a contract update.
"""

import json
import math
import re
from pathlib import Path

CONTRACT = json.loads(Path(__file__).with_name("document_format_v1.json").read_text())
ASSET_URL = re.compile(
    r"/api/assets/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
# Matches the editor's safe link protocols. Links are stored, never fetched.
LINK_SCHEMES = {
    "http",
    "https",
    "ftp",
    "ftps",
    "mailto",
    "tel",
    "callto",
    "sms",
    "cid",
    "xmpp",
}


def invalid(path, reason):
    # No note text, URLs, IDs or submitted values in diagnostics.
    raise ValueError(f"{path}: {reason}")


def validate_document(document):
    if not isinstance(document, list) or not document:
        invalid("document", "must contain at least one block")
    # Bound ALL JSON, including opaque metadata, before serializing/recursing.
    pending = [(document, 0)]
    nodes = 0
    while pending:
        value, depth = pending.pop()
        nodes += 1
        if depth > 128 or nodes > 100_000:
            invalid("document", "JSON nesting or item limit exceeded")
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                invalid("document", "JSON object keys must be strings")
            pending.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)
        elif isinstance(value, float) and not math.isfinite(value):
            invalid("document", "numbers must be finite")
        elif value is not None and type(value) not in (str, bool, int, float):
            invalid("document", "invalid JSON value")
    if (
        len(json.dumps(document, ensure_ascii=False, allow_nan=False).encode())
        > 1_048_576
    ):
        invalid("document", "exceeds the 1 MiB limit")

    def scalar(value, specification, path):
        expected = specification.get("type")
        if expected is None:
            expected = {
                str: "string",
                int: "number",
                float: "number",
                bool: "boolean",
            }.get(type(specification.get("default")))
        valid = (
            (expected == "string" and isinstance(value, str))
            or (expected == "boolean" and type(value) is bool)
            or (expected == "number" and type(value) in (int, float))
        )
        if not valid or (
            "values" in specification and value not in specification["values"]
        ):
            invalid(path, "invalid property type or value for document format 1")

    def inline(items, path, *, plain=False, inside_link=False):
        if not isinstance(items, list):
            invalid(path, "inline content must be an array")
        for index, item in enumerate(items):
            here = f"{path}[{index}]"
            if not isinstance(item, dict):
                invalid(here, "inline content must be objects")
            kind = item.get("type")
            if kind == "text":
                if not isinstance(item.get("text"), str) or not isinstance(
                    item.get("styles", {}), dict
                ):
                    invalid(here, "invalid text or styles")
                for name, value in item.get("styles", {}).items():
                    spec = CONTRACT["styles"].get(name)
                    if spec is None or plain:
                        invalid(here + ".styles", "unsupported style in this content")
                    scalar(value, {"type": spec["propSchema"]}, here + ".styles")
            elif kind == "link" and not plain and not inside_link:
                href = item.get("href")
                if not isinstance(href, str):
                    invalid(here, "invalid link")
                scheme = re.match(
                    r"^([a-z][a-z0-9+.-]*):",
                    re.sub(r"[\s\x00-\x1f\x7f]", "", href).lower(),
                )
                if scheme and scheme[1] not in LINK_SCHEMES:
                    invalid(here, "unsafe or unsupported link scheme")
                inline(item.get("content"), here + ".content", inside_link=True)
            else:
                invalid(here, "unsupported inline content for document format 1")

    ids = set()
    count = 0

    def blocks(items, path="document", depth=0):
        nonlocal count
        if not isinstance(items, list) or depth > 32:
            invalid(path, "invalid block nesting")
        for index, block in enumerate(items):
            here = f"{path}[{index}]"
            count += 1
            if count > 5000:
                invalid("document", "too many blocks")
            kind = block.get("type") if isinstance(block, dict) else None
            spec = CONTRACT["blocks"].get(kind) if isinstance(kind, str) else None
            if spec is None:
                invalid(here, "unsupported block type for document format 1")
            if "id" in block:
                identifier = block["id"]
                if (
                    not isinstance(identifier, str)
                    or not identifier
                    or identifier in ids
                ):
                    invalid(here, "block identifiers must be unique nonempty strings")
                ids.add(identifier)
            props = block.get("props", {})
            if not isinstance(props, dict):
                invalid(here, "block properties must be an object")
            for name, value in props.items():
                if name in spec["propSchema"]:
                    scalar(value, spec["propSchema"][name], here + ".props." + name)
            if kind == "image":
                url = props.get("url", "")
                if not isinstance(url, str) or (url and not ASSET_URL.fullmatch(url)):
                    invalid(here, "images require a local CyrNava asset URL")
            if spec["content"] == "none":
                if block.get("content") not in (None, []):
                    invalid(here, "this block cannot contain inline content")
            else:
                inline(
                    block.get("content", []),
                    here + ".content",
                    plain=spec["content"] == "plain",
                )
            blocks(block.get("children", []), here + ".children", depth + 1)

    blocks(document)
    return document
