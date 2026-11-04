import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "data" / "engage.sqlite3"


@pytest.fixture
def client(database_path):
    # Every test uses a fresh temporary database, never the default XDG location.
    with TestClient(create_app(database_path)) as test_client:
        yield test_client


@pytest.fixture
def document():
    return [
        {
            "id": "heading-1",
            "type": "heading",
            "props": {"level": 1, "textAlignment": "left"},
            "content": [{"type": "text", "text": "Engagement 日本語", "styles": {}}],
            "children": [],
        },
        {
            "id": "paragraph-1",
            "type": "paragraph",
            "props": {"textColor": "default", "backgroundColor": "default"},
            "content": [
                {"type": "text", "text": "Bold evidence", "styles": {"bold": True}},
                {
                    "type": "link",
                    "href": "https://example.invalid",
                    "content": [{"type": "text", "text": "Reference", "styles": {}}],
                },
            ],
            "children": [{"type": "bulletListItem", "content": [], "children": []}],
        },
    ]
