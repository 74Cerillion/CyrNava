import pytest
from app.desktop_security import DesktopSession
from app.main import create_app
from fastapi.testclient import TestClient

ORIGIN = "http://127.0.0.1:32187"


@pytest.fixture
def secured(tmp_path):
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "assets").mkdir()
    (frontend / "index.html").write_text("<html>synthetic frontend</html>")
    (frontend / "assets/test.js").write_text("/* local */")
    session = DesktopSession(ORIGIN)
    app = create_app(tmp_path / "data/test.sqlite3", frontend, desktop_session=session)
    with TestClient(app, base_url=ORIGIN) as client:
        yield client, session
    assert not session.active and session.token == ""


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/assets/test.js",
        "/health",
        "/api/health",
        "/api/tree",
        "/api/search?q=test",
        "/api/templates",
        "/api/assets/00000000-0000-0000-0000-000000000000",
        "/api/lifecycle/config",
    ],
)
def test_every_path_requires_session(secured, path):
    client, session = secured
    assert client.get(path).status_code == 401
    assert client.get(path, headers={"X-CyrNava-Session": "wrong"}).status_code == 401
    result = client.get(path, headers={"X-CyrNava-Session": session.token})
    assert result.status_code != 401
    assert result.headers["cache-control"] == "no-store"
    assert session.token not in result.text


def test_authorized_crud_and_origin(secured):
    client, session = secured
    headers = {"X-CyrNava-Session": session.token, "Origin": ORIGIN}
    body = {
        "title": "Synthetic",
        "document_json": [{"type": "paragraph", "content": []}],
        "format_version": 1,
    }
    assert client.post("/api/notes", json=body).status_code == 403
    result = client.post("/api/notes", json=body, headers=headers)
    assert result.status_code == 201
    note = result.json()
    assert client.get("/api/notes/" + note["id"], headers=headers).json() == note
    assert (
        client.patch(
            "/api/notes/" + note["id"],
            json={"revision": 1, "title": "Updated"},
            headers=headers,
        ).json()["revision"]
        == 2
    )
    assert (
        client.request(
            "DELETE", "/api/notes/" + note["id"], json={"revision": 2}, headers=headers
        ).status_code
        == 204
    )


@pytest.mark.parametrize(
    "headers, status",
    [
        ({"Host": "localhost:32187"}, 400),
        ({"Host": "evil.invalid"}, 400),
        ({"Origin": "http://evil.invalid"}, 403),
        ({"Origin": "null"}, 403),
        ({"Origin": ORIGIN + "/"}, 403),
        ({"Sec-Fetch-Site": "cross-site"}, 403),
        ({"Sec-Fetch-Site": "same-site"}, 403),
    ],
)
def test_rejects_host_origin_and_fetch_metadata(secured, headers, status):
    client, session = secured
    assert (
        client.get(
            "/api/tree", headers={"X-CyrNava-Session": session.token, **headers}
        ).status_code
        == status
    )


def test_duplicate_headers_and_revocation(secured):
    client, session = secured
    headers = [("X-CyrNava-Session", session.token)]
    assert client.get("/api/tree", headers=headers * 2).status_code == 401
    assert (
        client.get("/api/tree", headers=headers + [("Origin", ORIGIN)] * 2).status_code
        == 403
    )
    assert (
        client.get(
            "/api/tree", headers=headers + [("Host", "127.0.0.1:32187")] * 2
        ).status_code
        == 400
    )
    old = session.token
    session.revoke()
    assert (
        client.get("/api/tree", headers={"X-CyrNava-Session": old}).status_code == 401
    )
    replacement = DesktopSession(ORIGIN)
    assert replacement.token != old and len(replacement.token) >= 43
    assert old not in repr(session) and replacement.token not in repr(replacement)


def test_startup_failure_revokes_session(tmp_path):
    session = DesktopSession(ORIGIN)
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("synthetic")
    app = create_app(blocked / "test.sqlite3", desktop_session=session)
    with pytest.raises(OSError), TestClient(app):
        pass
    assert not session.active and session.token == ""


def test_authenticated_image_upload_and_retrieval(secured):
    from io import BytesIO

    from PIL import Image

    client, session = secured
    headers = {"X-CyrNava-Session": session.token, "Origin": ORIGIN}
    note = client.post(
        "/api/notes",
        headers=headers,
        json={
            "title": "Synthetic image",
            "document_json": [{"type": "paragraph", "content": []}],
            "format_version": 1,
        },
    ).json()
    image = BytesIO()
    Image.new("RGB", (2, 2), "blue").save(image, format="PNG")
    upload = client.post(
        "/api/assets",
        params={"note_id": note["id"]},
        content=image.getvalue(),
        headers={**headers, "Content-Type": "image/png"},
    )
    assert upload.status_code == 201
    url = upload.json()["url"]
    assert client.get(url).status_code == 401
    assert client.get(url, headers=headers).headers["content-type"] == "image/png"
