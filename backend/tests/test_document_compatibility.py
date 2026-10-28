"""Real editor fixtures through the real API, with temporary databases only."""

import copy
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backup import create_backup, restore_backup
from app.database import Database
from app.documents import CONTRACT, validate_document
from app.main import create_app

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/blocknote_v1.json").read_text()
)


@pytest.mark.parametrize("name", FIXTURES["cases"])
def test_every_native_editor_block_through_create_update_get(client, name):
    document = FIXTURES["cases"][name]
    created = client.post("/api/notes", json={"title": name, "document_json": document})
    assert created.status_code == 201, created.text
    note = created.json()
    assert note["document_json"] == document
    path = f"/api/notes/{note['id']}"
    assert client.get(path).json()["document_json"] == document
    changed = copy.deepcopy(document)
    changed[-1]["content"] = [
        {"type": "text", "text": "Edited 🚀", "styles": {"bold": True}}
    ]
    if name == "image":
        changed[0]["props"].update(
            showPreview=False, previewWidth=128, caption="Edited caption"
        )
    response = client.patch(path, json={"revision": 1, "document_json": changed})
    assert response.status_code == 200, response.text
    assert response.json()["revision"] == 2
    assert client.get(path).json()["document_json"] == changed


def test_contract_covers_current_native_fixtures():
    types = {block["type"] for case in FIXTURES["cases"].values() for block in case}
    assert types == set(CONTRACT["blocks"])
    assert CONTRACT["format_version"] == 1
    assert CONTRACT["blocknote_version"] == FIXTURES["blocknote_version"]


def test_mixed_uploaded_image_restart_and_backup(database_path, tmp_path):
    document = copy.deepcopy(FIXTURES["mixed"])
    with TestClient(create_app(database_path)) as client:
        response = client.post(
            "/api/notes", json={"title": "Mixed", "document_json": document}
        )
        assert response.status_code == 201
        note = response.json()
        image = io.BytesIO()
        Image.new("RGB", (20, 12), "blue").save(image, format="PNG")
        uploaded = client.post(
            f"/api/assets?note_id={note['id']}",
            content=image.getvalue(),
            headers={"content-type": "image/png"},
        )
        assert uploaded.status_code == 201
        url = uploaded.json()["url"]
        next(block for block in document if block["type"] == "image")["props"][
            "url"
        ] = url
        updated = client.patch(
            f"/api/notes/{note['id']}", json={"revision": 1, "document_json": document}
        )
        assert updated.status_code == 200
        assert updated.json()["document_json"] == document
        stored_image = client.get(url).content
    with TestClient(create_app(database_path)) as restarted:
        assert (
            restarted.get(f"/api/notes/{note['id']}").json()["document_json"]
            == document
        )
        assert restarted.get(url).content == stored_image
    backup = tmp_path / "backup"
    restored = tmp_path / "restored"
    create_backup(database_path.parent, backup)
    restore_backup(backup, restored)
    with TestClient(create_app(restored / "engage.sqlite3")) as recovered:
        assert (
            recovered.get(f"/api/notes/{note['id']}").json()["document_json"]
            == document
        )
    with Database(database_path).connect() as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
        assert (
            json.loads(
                connection.execute("SELECT document_json FROM notes").fetchone()[0]
            )
            == document
        )


@pytest.mark.parametrize(
    "bad",
    [
        [{"type": "table", "content": {"type": "tableContent", "rows": []}}],
        [{"type": "heading", "props": {"level": True}}],
        [{"type": "heading", "props": {"level": "4"}}],
        [{"type": "heading", "props": {"level": 7}}],
        [{"type": "heading", "props": {"isToggleable": "true"}}],
        [{"type": "checkListItem", "props": {"checked": 1}}],
        [{"type": "paragraph", "props": {"textAlignment": "unsafe"}}],
        [{"type": "paragraph", "content": [{"type": "mention", "text": "x"}]}],
        [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "secret-note-value",
                        "styles": {"bold": "yes"},
                    }
                ],
            }
        ],
        [
            {
                "type": "paragraph",
                "content": [
                    {"type": "link", "href": "java\nscript:alert(1)", "content": []}
                ],
            }
        ],
        [
            {
                "type": "paragraph",
                "content": [
                    {"type": "link", "href": "data:text/html,bad", "content": []}
                ],
            }
        ],
        [
            {
                "type": "codeBlock",
                "content": [
                    {"type": "link", "href": "https://example.invalid", "content": []}
                ],
            }
        ],
        [{"type": "image", "props": {"url": "https://example.invalid/image.png"}}],
        [{"type": "image", "props": {"previewWidth": "wide"}}],
        [{"type": "paragraph", "children": {}}],
    ],
)
def test_invalid_changes_leave_note_unchanged_and_do_not_echo_content(client, bad):
    document = FIXTURES["cases"]["heading_4"]
    note = client.post(
        "/api/notes", json={"title": "Valid", "document_json": document}
    ).json()
    path = f"/api/notes/{note['id']}"
    response = client.patch(path, json={"revision": 1, "document_json": bad})
    assert response.status_code == 422
    assert "secret-note-value" not in response.text
    assert all(
        "input" not in issue and "ctx" not in issue
        for issue in response.json()["detail"]
    )
    assert client.get(path).json() == note


def test_json_resource_limits_and_lossless_metadata(client):
    document = copy.deepcopy(FIXTURES["cases"]["paragraph"])
    document[0]["metadata"] = {
        "annotation": {"source": "local", "flags": [True, None, 5]}
    }
    document[0]["props"]["futureProperty"] = {"preserve": ["native", 2]}
    response = client.post(
        "/api/notes", json={"title": "Metadata", "document_json": document}
    )
    assert response.status_code == 201
    assert response.json()["document_json"] == document
    deep = {}
    value = deep
    for _ in range(140):
        value["nested"] = {}
        value = value["nested"]
    for bad in (
        [{"type": "paragraph", "metadata": deep}],
        [{"type": "paragraph", "props": {"future": float("inf")}}],
        [{"type": "paragraph", "metadata": [0] * 100_001}],
        [{"type": "paragraph"}] * 5001,
    ):
        with pytest.raises(ValueError):
            validate_document(bad)


@pytest.mark.parametrize(
    ("kind", "name", "value"),
    [
        (kind, name, value)
        for kind, block in CONTRACT["blocks"].items()
        for name, prop in block["propSchema"].items()
        for value in prop.get("values", [])
    ],
)
def test_every_installed_property_enum_value(client, kind, name, value):
    document = [{"type": kind, "props": {name: value}, "content": []}]
    response = client.post(
        "/api/notes", json={"title": "Property", "document_json": document}
    )
    assert response.status_code == 201
    path = f"/api/notes/{response.json()['id']}"
    assert client.get(path).json()["document_json"] == document
