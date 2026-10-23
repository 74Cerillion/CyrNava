import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import __version__
from app.main import create_app


def test_release_serves_only_build_and_api(tmp_path, document):
    build = tmp_path / "build"
    (build / "assets").mkdir(parents=True)
    (build / "index.html").write_text(
        '<!doctype html><title>ENGAGE</title><div id="root"></div>'
    )
    (build / "assets/app-123.js").write_text('console.log("local")')
    (build / "private.txt").write_text("not served")
    with TestClient(create_app(tmp_path / "profile/engage.sqlite3", build)) as client:
        assert client.get("/").status_code == 200
        assert "ENGAGE" in client.get("/").text
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.get("/health").status_code == 200
        assert client.get("/assets/app-123.js").status_code == 200
        assert client.get("/private.txt").status_code == 404
        assert client.get("/api/not-a-route").status_code == 404
        assert client.get("/assets/%2e%2e/private.txt").status_code == 404
        page = client.get("/")
        assert "script-src 'self';" in page.headers["content-security-policy"]
        assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
        assert page.headers["x-content-type-options"] == "nosniff"
        assert page.headers["cache-control"] == "no-store"
        created = client.post(
            "/api/notes", json={"title": "Release", "document_json": document}
        ).json()
        assert (
            client.get(f"/api/notes/{created['id']}").json()["document_json"]
            == document
        )


def test_missing_build_fails_with_actionable_message(tmp_path):
    with pytest.raises(RuntimeError, match="npm run build"):
        create_app(tmp_path / "profile/engage.sqlite3", tmp_path / "missing")
    assert not (tmp_path / "profile").exists()


def test_release_versions_agree():
    package = Path(__file__).resolve().parents[2] / "frontend/package.json"
    assert json.loads(package.read_text())["version"] == __version__ == "0.1.0"


def test_launcher_rejects_invalid_port_without_starting():
    result = subprocess.run(
        [sys.executable, "-m", "app", "--port", "0"], capture_output=True, text=True
    )
    assert result.returncode == 2
    assert "between 1 and 65535" in result.stderr
