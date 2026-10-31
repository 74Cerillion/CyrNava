"""Search uses the real API/FTS5 and synthetic notes in isolated profiles."""

import copy
import json
import socket
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import Database, RevisionConflict
from app.main import create_app
from app.search import extract_text, index_note, prepare_query, verify_index
from fastapi.testclient import TestClient
from search_helpers import canonical_snapshot

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/blocknote_v1.json").read_text()
)


def block(text, kind="paragraph", **extra):
    return {
        "type": kind,
        "content": [{"type": "text", "text": text, "styles": {}}],
        **extra,
    }


def create(client, title="Neutral", document=None, folder=None):
    response = client.post(
        "/api/notes",
        json={
            "title": title,
            "document_json": document or [block("Ordinary")],
            "folder_id": folder,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def search(client, query, limit=20):
    response = client.get("/api/search", params={"q": query, "limit": limit})
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "no-store"
    return response.json()


def ids(client, query):
    return {row["note_id"] for row in search(client, query)["results"]}


@pytest.mark.parametrize("name", FIXTURES["cases"])
def test_extract_and_search_actual_editor_fixtures(client, name):
    document = FIXTURES["cases"][name]
    original = copy.deepcopy(document)
    headings, body = extract_text(document)
    saved = create(client, document=document)
    # Every supported native block has searchable user text (image caption/name).
    tokens = prepare_query(headings + " " + body)[1]
    assert tokens
    assert saved["id"] in ids(client, tokens[0])
    assert document == original
    assert client.get(f"/api/notes/{saved['id']}").json()["document_json"] == original


def test_extraction_nested_styled_runs_links_code_metadata_and_images():
    document = [
        block("Discovery", "heading", props={"level": 1}),
        {
            "type": "paragraph",
            "id": "ignoredidentifier",
            "props": {"textColor": "ignoredcolor"},
            "content": [
                {"type": "text", "text": "enu", "styles": {"bold": True}},
                {"type": "text", "text": "meration ", "styles": {}},
                {
                    "type": "link",
                    "href": "https://ignoredurl.invalid",
                    "content": [{"type": "text", "text": "reference", "styles": {}}],
                },
            ],
            "children": [
                block(
                    "Nested",
                    "bulletListItem",
                    children=[block("Completed", "checkListItem")],
                )
            ],
        },
        block("nmap -sV 127.0.0.1 日本語", "codeBlock"),
        {
            "type": "image",
            "props": {
                "url": "/api/assets/ignoredasset",
                "name": "Evidence.png",
                "caption": "Port scan",
            },
        },
    ]
    original = copy.deepcopy(document)
    headings, body = extract_text(document)
    assert headings == "Discovery"
    assert body == (
        "enumeration reference\nNested\nCompleted\nnmap -sV 127.0.0.1 日本語\n"
        "Port scan\nEvidence.png"
    )
    assert "ignored" not in headings + body
    assert document == original


@pytest.mark.parametrize(
    "document",
    [
        None,
        {},
        "text",
        [None, 4, []],
        [
            {"type": [], "content": {}},
            {"type": "paragraph", "content": [None, {}]},
            {"type": "image", "props": {"caption": [], "name": False}},
        ],
    ],
)
def test_extraction_ignores_malformed_structures(document):
    assert extract_text(document) == ("", "")


def test_extraction_bounds_cycles_and_large_text():
    recursive = block("bounded")
    recursive["children"] = [recursive]
    assert len(extract_text([recursive])[1].splitlines()) == 33
    assert len(extract_text([block("x" * 1_100_000)])[1]) == 1_048_576
    link = {"type": "link", "content": []}
    link["content"].append(link)
    assert extract_text([{"type": "paragraph", "content": [link]}]) == ("", "")


@pytest.mark.parametrize(
    "kind",
    [
        "paragraph",
        "heading",
        "codeBlock",
        "quote",
        "bulletListItem",
        "numberedListItem",
        "checkListItem",
    ],
)
def test_supported_text_matches_ascii_prefix_and_punctuation(client, kind):
    saved = create(client, document=[block("Enumeration nmap -sV 127.0.0.1", kind)])
    for query in ["ENUM", "nmap", '"nmap" -sV', "127.0.0.1"]:
        assert ids(client, query) == {saved["id"]}
    assert not ids(client, "umeration")  # Prefixes, not arbitrary substrings.


def test_nested_heading_levels_links_and_unicode(client):
    document = [
        block(
            f"Discovery{level}",
            "heading",
            props={"level": level},
            children=[block("Deep enumeration", "bulletListItem")],
        )
        for level in range(1, 7)
    ]
    document.append(block("Café 日本語"))
    saved = create(client, document=document)
    for query in ["Discovery6", "deep enum", "CAFÉ", "cafe", "日本語"]:
        assert ids(client, query) == {saved["id"]}


def test_exact_title_then_weighted_relevance_and_stable_ties(client):
    exact = create(client, "nmap")
    title = create(client, "nmap manual")
    heading = create(client, document=[block("nmap", "heading")])
    body = create(client, document=[block("nmap")])
    duplicate = create(client, document=[block("nmap")])
    result = search(client, "nmap", 4)
    ordered = [row["note_id"] for row in search(client, "nmap")["results"]]
    assert ordered == [
        exact["id"],
        title["id"],
        heading["id"],
        *sorted([body["id"], duplicate["id"]]),
    ]
    assert result["total"] == 5 and len(result["results"]) == 4
    assert all(row["score"] < 0 for row in result["results"])
    assert search(client, "nmap", 4) == result


def test_current_folder_paths_root_moves_and_renames(client):
    parent = client.post("/api/folders", json={"name": "Security"}).json()
    child = client.post(
        "/api/folders", json={"name": "Pentesting", "parent_id": parent["id"]}
    ).json()
    root = create(client, "nmap root")
    nested = create(client, "nmap nested", folder=child["id"])
    paths = {
        row["note_id"]: row["folder_path"] for row in search(client, "nmap")["results"]
    }
    assert paths == {root["id"]: [], nested["id"]: ["Security", "Pentesting"]}
    assert (
        client.patch(
            f"/api/folders/{child['id']}", json={"name": "Renamed", "parent_id": None}
        ).status_code
        == 200
    )
    assert next(
        row
        for row in search(client, "nmap")["results"]
        if row["note_id"] == nested["id"]
    )["folder_path"] == ["Renamed"]
    assert (
        client.patch(
            f"/api/notes/{nested['id']}", json={"revision": 1, "folder_id": None}
        ).status_code
        == 200
    )
    assert all(row["folder_path"] == [] for row in search(client, "nmap")["results"])


def test_rename_edit_delete_and_conflicts_update_only_committed_content(client):
    saved = create(client, "Oldtitle", [block("Oldbody")])
    path = f"/api/notes/{saved['id']}"
    changed = client.patch(
        path,
        json={"revision": 1, "title": "Newtitle", "document_json": [block("Newbody")]},
    )
    assert changed.status_code == 200
    assert not ids(client, "Oldtitle") and not ids(client, "Oldbody")
    assert ids(client, "Newtitle Newbody") == {saved["id"]}
    assert (
        client.patch(path, json={"revision": 1, "title": "Stalewrite"}).status_code
        == 409
    )
    assert (
        client.patch(path, json={"revision": 2, "document_json": []}).status_code == 422
    )
    assert (
        client.patch(
            f"/api/notes/{uuid4()}", json={"revision": 1, "title": "Missingwrite"}
        ).status_code
        == 404
    )
    assert not ids(client, "Stalewrite") and not ids(client, "Missingwrite")
    assert client.request("DELETE", path, json={"revision": 1}).status_code == 409
    assert ids(client, "Newbody") == {saved["id"]}
    assert client.request("DELETE", path, json={"revision": 2}).status_code == 204
    assert not ids(client, "Newtitle")


def test_recursive_deletion_failure_and_success(client, database_path):
    root = client.post("/api/folders", json={"name": "Root"}).json()
    child = client.post(
        "/api/folders", json={"name": "Child", "parent_id": root["id"]}
    ).json()
    notes = [
        create(client, "nmap root", folder=root["id"]),
        create(client, "nmap child", folder=child["id"]),
    ]
    impact = client.get(f"/api/folders/{root['id']}/deletion-impact").json()
    body = {
        "recursive": True,
        "expected_descendant_folders": 1,
        "expected_notes": 2,
        "impact_token": impact["token"],
    }
    database = Database(database_path)
    with database.connect() as connection:
        connection.execute("""CREATE TRIGGER fail_folder BEFORE DELETE ON folders
            BEGIN SELECT RAISE(ABORT, 'injected'); END""")
    assert (
        client.request("DELETE", f"/api/folders/{root['id']}", json=body).status_code
        == 503
    )
    assert ids(client, "nmap") == {note["id"] for note in notes}
    with database.connect() as connection:
        connection.execute("DROP TRIGGER fail_folder")
    assert (
        client.request("DELETE", f"/api/folders/{root['id']}", json=body).status_code
        == 204
    )
    assert not ids(client, "nmap")
    with database.connect() as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM note_search_documents").fetchone()[
                0
            ]
            == 0
        )
        verify_index(connection)


@pytest.mark.parametrize(
    "params",
    [
        {"q": "x" * 201},
        {"q": "word " * 17},
        {"q": "secret\x00"},
        {"q": "nmap", "limit": 0},
        {"q": "nmap", "limit": 51},
        {"q": "nmap", "limit": "nope"},
    ],
)
def test_invalid_queries_are_private_validation_errors(client, params):
    response = client.get("/api/search", params=params)
    assert response.status_code == 422
    assert response.headers["Cache-Control"] == "no-store"
    assert "secret" not in response.text
    assert "input" not in response.text
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("query", ["", "   ", '"*:^()-', "___", "🚀"])
def test_empty_and_punctuation_queries_return_empty(client, query):
    create(client)
    assert search(client, query) == {"query": query.strip(), "total": 0, "results": []}


def test_fts_operators_are_literal_words_and_sql_remains_bound(client):
    saved = create(client, "nmap", [block("nmap enumeration")])
    for query in [
        "nmap OR enumeration",
        "nmap NOT absent",
        "nmap NEAR enumeration",
        "nmap' UNION SELECT secret --",
        "'; DROP TABLE notes; --",
    ]:
        assert not ids(client, query)
    assert ids(client, 'nmap "enum') == {saved["id"]}
    assert client.get(f"/api/notes/{saved['id']}").status_code == 200


def test_plain_bounded_snippet_and_search_does_not_write_canonical_data(
    client, database_path
):
    create(
        client,
        document=[block("padding " * 100 + "<script>nmap</script> " + "tail " * 100)],
    )
    with sqlite3.connect(database_path) as connection:
        before = canonical_snapshot(connection)
    result = search(client, "nmap")["results"][0]
    assert "nmap" in result["snippet"]
    assert len(result["snippet"]) <= 282
    assert (
        "<script>" in result["snippet"]
    )  # Plain data, not generated highlight markup.
    assert set(result) == {"note_id", "title", "folder_path", "snippet", "score"}
    with sqlite3.connect(database_path) as connection:
        assert canonical_snapshot(connection) == before


@pytest.mark.parametrize("operation", ["create", "update", "template"])
def test_index_failure_rolls_back_canonical_and_derived_writes(
    client, database_path, monkeypatch, operation
):
    note = create(client, "Keeporiginal")
    with sqlite3.connect(database_path) as connection:
        before = canonical_snapshot(connection)
        index_before = connection.execute(
            "SELECT * FROM note_search_documents"
        ).fetchall()

    def fail(connection, row):
        index_note(connection, row)
        raise sqlite3.OperationalError("injected private value")

    module = "app.templates" if operation == "template" else "app.database"
    monkeypatch.setattr(module + ".index_note", fail)
    if operation == "create":
        response = client.post(
            "/api/notes",
            json={"title": "Failedwrite", "document_json": [block("Failedbody")]},
        )
    elif operation == "update":
        response = client.patch(
            f"/api/notes/{note['id']}", json={"revision": 1, "title": "Failedwrite"}
        )
    else:
        template = client.get("/api/templates").json()[0]
        response = client.post(
            f"/api/templates/{template['id']}/notes",
            json={"revision": template["revision"], "title": "Failedwrite"},
        )
    assert response.status_code == 503
    assert "private" not in response.text
    assert not ids(client, "Failedwrite") and ids(client, "Keeporiginal") == {
        note["id"]
    }
    with sqlite3.connect(database_path) as connection:
        assert canonical_snapshot(connection) == before
        assert (
            connection.execute("SELECT * FROM note_search_documents").fetchall()
            == index_before
        )
    with Database(database_path).connect() as connection:
        verify_index(connection)


def test_template_instances_searchable_but_catalog_is_not(client):
    note = create(client, document=[block("Templateterm")])
    custom = client.post(
        "/api/templates",
        json={
            "name": "Catalogonly",
            "source_note_id": note["id"],
            "source_revision": 1,
        },
    ).json()
    builtin = client.get("/api/templates").json()[0]
    for template in [custom, builtin]:
        response = client.post(
            f"/api/templates/{template['id']}/notes",
            json={"revision": template["revision"], "title": "Instantiated"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["id"] in ids(client, "Instantiated")
        if template == custom:
            assert response.json()["id"] in ids(client, "Templateterm")
    assert not ids(client, "Catalogonly")


def test_competing_revisions_only_index_winner(database_path):
    database = Database(database_path)
    database.initialize()
    note = database.create("Before", [block("Beforebody")], 1)

    def update(word):
        try:
            return database.update(note["id"], 1, {"title": word})
        except RevisionConflict:
            return None

    words = ["Winnerone", "Winnertwo", "Winnerthree", "Winnerfour"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        winners = [result for result in pool.map(update, words) if result]
    assert len(winners) == 1
    for word in words:
        assert database.search(word)["total"] == int(word == winners[0]["title"])
    with database.connect() as connection:
        verify_index(connection)
        assert (
            connection.execute(
                "SELECT indexed_revision FROM note_search_documents"
            ).fetchone()[0]
            == 2
        )


def test_restart_and_no_internet_calls(database_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("External network access attempted")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    with TestClient(create_app(database_path)) as client:
        note = create(client, "nmap offline")
    with TestClient(create_app(database_path)) as restarted:
        assert ids(restarted, "nmap") == {note["id"]}
        assert restarted.get(f"/api/notes/{note['id']}").json() == note


def test_missing_index_returns_actionable_error_without_private_details(
    client, database_path
):
    with Database(database_path).connect() as connection:
        connection.execute("DROP TABLE note_search")
    response = client.get("/api/search", params={"q": "privateterm"})
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert "rebuild" in response.text and "privateterm" not in response.text
