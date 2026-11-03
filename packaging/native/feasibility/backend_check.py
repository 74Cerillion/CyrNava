"""Real target-Python backend/security/persistence check, synthetic data only."""

import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

root = Path(sys.argv[1]).absolute()
sys.path.insert(0, str(root / "application"))
from PIL import Image  # noqa: E402 - explicit experiment import root

from desktop.native.backend import Backend  # noqa: E402
from desktop.native.storage import Profile  # noqa: E402

output = root / "backend-check.json"
if output.exists():
    raise SystemExit("Preserve existing backend check")
profile_root = root / "backend-synthetic-profile"
if profile_root.exists():
    raise SystemExit("Fresh synthetic backend profile required")
record = {
    "status": "FAIL",
    "complete": False,
    "python": list(sys.version_info[:2]),
    "checks": {},
}
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request(backend, path, body=None, *, binary=False, token=None, origin=None):
    headers = {
        "X-CyrNava-Session": backend.token if token is None else token,
        "Origin": backend.origin if origin is None else origin,
        "Content-Type": "image/png" if binary else "application/json",
    }
    req = urllib.request.Request(
        backend.origin + path,
        data=body
        if binary
        else (json.dumps(body).encode() if body is not None else None),
        headers=headers,
    )
    with opener.open(req, timeout=3) as response:
        data = response.read()
        return data if binary else json.loads(data)


profile = Profile(profile_root)
backend = Backend(profile)
try:
    backend.start()
    port = profile.port
    token = backend.token
    for key, kwargs, expected in [
        ("unauthenticated", {"token": "invalid"}, 401),
        ("wrong_origin", {"origin": "https://example.invalid"}, 403),
    ]:
        try:
            request(backend, "/api/tree", **kwargs)
        except urllib.error.HTTPError as error:
            assert error.code == expected
        else:
            raise AssertionError(key)
        record["checks"][key] = "PASS"
    folder = request(backend, "/api/folders", {"name": "N1 synthetic folder"})
    note = request(
        backend,
        "/api/notes",
        {
            "title": "N1 synthetic note",
            "folder_id": folder["id"],
            "format_version": 1,
            "document_json": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "N1 persisted text",
                            "styles": {"bold": True},
                        }
                    ],
                }
            ],
        },
    )
    image = io.BytesIO()
    Image.new("RGB", (16, 16), (20, 80, 140)).save(image, format="PNG")
    asset = request(
        backend, "/api/assets?note_id=" + note["id"], image.getvalue(), binary=True
    )
    # Binary response is JSON here; decode without ever logging private contents.
    asset = json.loads(asset)
    document = note["document_json"] + [
        {
            "type": "image",
            "props": {"url": asset["url"], "caption": "N1 synthetic raster"},
        }
    ]
    req = urllib.request.Request(
        backend.origin + "/api/notes/" + note["id"],
        method="PATCH",
        data=json.dumps(
            {"revision": note["revision"], "document_json": document}
        ).encode(),
        headers={
            "Origin": backend.origin,
            "X-CyrNava-Session": backend.token,
            "Content-Type": "application/json",
        },
    )
    with opener.open(req, timeout=3) as response:
        saved = json.load(response)
    data = request(backend, asset["url"], binary=True)
    digest = hashlib.sha256(data).hexdigest()
    record["checks"]["folder_note_rich_text_image_saved"] = "PASS"
    backend.stop()
    assert backend.child.poll() is not None
    profile.close()
    record["checks"]["owned_backend_reaped"] = "PASS"
    profile = Profile(profile_root)
    backend = Backend(profile)
    backend.start()
    assert profile.port == port and backend.token != token
    assert request(backend, "/api/notes/" + note["id"]) == saved
    assert (
        hashlib.sha256(request(backend, asset["url"], binary=True)).hexdigest()
        == digest
    )
    try:
        request(backend, "/api/tree", token=token)
    except urllib.error.HTTPError as error:
        assert error.code == 401
    else:
        raise AssertionError("Stale credential accepted")
    record["checks"]["restart_and_data_integrity"] = "PASS"
    record["checks"]["stable_origin_and_token_revocation"] = "PASS"
    record["status"] = "PASS"
except (Exception, KeyboardInterrupt) as error:
    record["error_type"] = type(error).__name__
    import traceback

    traceback.print_exc()
finally:
    backend.stop()
    profile.close()
    record["complete"] = True
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
raise SystemExit(0 if record["status"] == "PASS" else 1)
