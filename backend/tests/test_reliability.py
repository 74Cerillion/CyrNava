from concurrent.futures import ThreadPoolExecutor

from app.database import Database, RevisionConflict


def test_failed_note_update_rolls_back_document_title_and_revision(
    client, database_path, document
):
    original = client.post(
        "/api/notes", json={"title": "Keep", "document_json": document}
    ).json()
    with Database(database_path).connect() as connection:
        connection.execute("""CREATE TRIGGER fail_note_update AFTER UPDATE ON notes
            BEGIN SELECT RAISE(ABORT, 'injected write failure'); END""")
    failed = client.patch(
        f"/api/notes/{original['id']}",
        json={
            "revision": 1,
            "title": "Must not persist",
            "document_json": [{"type": "paragraph", "content": []}],
        },
    )
    assert failed.status_code == 503
    assert "injected" not in failed.text
    assert client.get(f"/api/notes/{original['id']}").json() == original


def test_competing_updates_with_one_expected_revision_have_exactly_one_winner(
    database_path, document
):
    database = Database(database_path)
    database.initialize()
    note = database.create("Before", document, 1)

    def update(title):
        try:
            return database.update(note["id"], 1, {"title": title})
        except RevisionConflict:
            return None

    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(update, ["One", "Two", "Three", "Four"]))
    winners = [result for result in results if result]
    assert len(winners) == 1
    assert database.get(note["id"]) == winners[0]
    assert winners[0]["revision"] == 2
    assert winners[0]["document_json"] == document


def test_recursive_delete_failure_preserves_asset_metadata_and_files(
    client, database_path, document
):
    import io

    from PIL import Image

    root = client.post("/api/folders", json={"name": "Retain all"}).json()
    child = client.post(
        "/api/folders", json={"name": "Nested", "parent_id": root["id"]}
    ).json()
    note = client.post(
        "/api/notes",
        json={"title": "Evidence", "folder_id": child["id"], "document_json": document},
    ).json()
    stream = io.BytesIO()
    Image.new("RGB", (8, 8), "green").save(stream, format="PNG")
    asset = client.post(
        f"/api/assets?note_id={note['id']}",
        content=stream.getvalue(),
        headers={"Content-Type": "image/png"},
    ).json()
    before_tree = client.get("/api/tree").json()
    before_bytes = client.get(asset["url"]).content
    with Database(database_path).connect() as connection:
        # Failure happens after the descendant note/asset rows were deleted.
        connection.execute(f"""CREATE TRIGGER fail_root BEFORE DELETE ON folders
            WHEN OLD.id = '{root["id"]}'
            BEGIN SELECT RAISE(ABORT, 'injected delete failure'); END""")
    impact = client.get(f"/api/folders/{root['id']}/deletion-impact").json()
    response = client.request(
        "DELETE",
        f"/api/folders/{root['id']}",
        json={
            "recursive": True,
            "expected_descendant_folders": 1,
            "expected_notes": 1,
            "impact_token": impact["token"],
        },
    )
    assert response.status_code == 503
    assert client.get("/api/tree").json() == before_tree
    assert client.get(f"/api/notes/{note['id']}").json() == note
    assert client.get(asset["url"]).content == before_bytes
