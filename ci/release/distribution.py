"""P6 local adapter for accepted signed snapshots; no cloud credentials or PUT API.

Providers must implement hidden immutable generations plus conditional activation,
not a sequence of independently mutable summary/signature uploads. This adapter
reuses P5B's verified, durable publication instead of introducing another signer.
"""

import argparse
import contextlib
import hashlib
import http.server
import json
import re
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Protocol

import core
import trust


class SnapshotDestination(Protocol):
    root: Path

    def current(self): ...

    def activate(self, public, key, fingerprint, expected): ...


class LocalDestination:
    def __init__(self, root):
        self.root = core.outside_source(root)
        core.require(
            core.read_json(self.root / ".p5b-staging-store")
            == {"purpose": "p5b-local-staging-only"},
            "Marked disposable destination required",
        )

    def current(self):
        value = core.active_generation(self.root)
        return value.name if value else None

    def activate(self, public, key, fingerprint, expected):
        def compare():
            # Invoked while accepted publisher holds its exclusive flock.
            core.require(self.current() == expected, "Publication conflict; re-plan")

        return core.publish_local(
            public, self.root, key, fingerprint, before_activate=compare
        )


def plan(public, destination, key, fingerprint, parent):
    """Read-only source/destination verification; no activation or data upload."""
    public = core.safe_path(public)
    manifest = core.verify_seal(public, key, fingerprint, parent)
    trust.verify_current_signature(
        key, fingerprint, public / "manifest.json", public / "manifest.json.sig", parent
    )
    core.verify_repository(public / "repo", key, parent)
    previous = core.active_generation(destination.root)
    files = manifest["files"]
    if previous:
        old = core.verify_seal(previous, key, fingerprint, parent)["files"]
        core.require(
            all(
                files.get(p) == v
                for p, v in old.items()
                if p.startswith(("repo/objects/", "repo/deltas/"))
            ),
            "Historical objects would be discarded",
        )
    # This is also the required future provider upload order. Activation is ONE
    # conditional pointer update after ALL files and hashes have been verified.
    ordered = sorted(
        files,
        key=lambda p: (not p.startswith(("repo/objects/", "repo/deltas/")), p),
    )
    return {
        "format": 1,
        "mode": "DRY RUN; LOCAL ONLY",
        "expected_previous": destination.current(),
        "generation": core.sha(public / "manifest.json"),
        "files": {p: files[p] for p in ordered},
        "seal_files": {
            n: core.sha(public / n) for n in ("manifest.json", "manifest.json.sig")
        },
        "bytes": sum(v["bytes"] for v in files.values()),
        "deletions": [],
        "activation": "compare-and-swap after verified complete immutable generation",
        "public_https_verified": False,
    }


def publish(public, destination, key, fingerprint, reviewed, parent):
    actual = plan(public, destination, key, fingerprint, parent)
    core.require(actual == reviewed, "Publication plan changed; review again")
    result = destination.activate(
        public, key, fingerprint, reviewed["expected_previous"]
    )
    target = core.active_generation(destination.root)
    core.require(target.name == reviewed["generation"], "Activation mismatch")
    core.verify_seal(target, key, fingerprint, parent)
    return result


def response_policy(path, *, missing=False):
    if missing:
        return "application/octet-stream", "no-store, max-age=0"
    content_type = (
        "application/json"
        if path.endswith(".json")
        else "application/vnd.flatpak.ref"
        if path.endswith(".flatpakref")
        else "application/vnd.flatpak.repo"
        if path.endswith(".flatpakrepo")
        else "application/octet-stream"
    )
    # Only content-addressed OSTree objects are cacheable at a stable URL.
    immutable = re.fullmatch(r"repo/objects/[a-f0-9]{2}/[a-f0-9]{62}\.[a-z0-9]+", path)
    return content_type, (
        "public, max-age=31536000, immutable" if immutable else "no-store, max-age=0"
    )


def handler(destination, key, fingerprint):
    manifests = {}
    cache_lock = threading.Lock()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def serve(self, body):
            try:
                request = urllib.parse.urlsplit(self.path)
                path = urllib.parse.unquote(request.path)
                core.require(
                    not request.query
                    and not request.fragment
                    and path.startswith("/current/")
                    and ".." not in Path(path).parts
                    and "\\" not in path,
                    "Invalid route",
                )
                generation = core.active_generation(destination.root)
                core.require(generation is not None, "No active generation")
                relative = path.removeprefix("/current/")
                # A generation is immutable. Verify it once, then hash each
                # served object against the trusted cached manifest. Re-parsing
                # thousands of manifest entries for every tiny OSTree GET/HEAD
                # creates quadratic distribution cost.
                with cache_lock:
                    if generation.name not in manifests:
                        core.require(
                            core.sha(generation / "manifest.json") == generation.name,
                            "Generation identity mismatch",
                        )
                        manifest = core.verify_seal(
                            generation, key, fingerprint, destination.root
                        )
                        trust.verify_current_signature(
                            key,
                            fingerprint,
                            generation / "manifest.json",
                            generation / "manifest.json.sig",
                            destination.root,
                        )
                        manifests[generation.name] = manifest["files"]
                    manifest = manifests[generation.name]
                core.require(relative in manifest, "Unlisted object")
                target = core.safe_path(generation / relative)
                core.require(target.is_file(), "Missing object")
                expected = manifest[relative]
                core.require(
                    target.stat().st_size == expected["bytes"]
                    and core.sha(target) == expected["sha256"],
                    "Damaged object",
                )
            except (core.Rejected, OSError, ValueError, KeyError):
                self.send_response(404)
                self.send_header("Cache-Control", response_policy("", missing=True)[1])
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            content_type, cache = response_policy(relative)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(expected["bytes"]))
            self.send_header("ETag", '"' + expected["sha256"] + '"')
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if body:
                try:
                    with target.open("rb") as stream:
                        while chunk := stream.read(1024**2):
                            self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # A disconnected reader never changes publication state.

        def do_GET(self):
            self.serve(True)

        def do_HEAD(self):
            self.serve(False)

    return Handler


@contextlib.contextmanager
def loopback(destination, key, fingerprint):
    active = core.active_generation(destination.root)
    core.require(active is not None, "No verified active generation")
    core.verify_seal(active, key, fingerprint, destination.root)
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), handler(destination, key, fingerprint)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/current/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def verify_http(base, reviewed):
    """Verify actual bytes, not an unauthenticated HEAD checksum assertion."""
    url = urllib.parse.urlsplit(base)
    core.require(
        url.scheme == "http" and url.hostname == "127.0.0.1" and url.port,
        "Only loopback transport is authorized",
    )
    for name, expected in reviewed["files"].items():
        target = base + urllib.parse.quote(name, safe="/")
        with urllib.request.urlopen(target, timeout=60) as response:
            digest = hashlib.sha256()
            size = 0
            while chunk := response.read(1024**2):
                digest.update(chunk)
                size += len(chunk)
                core.require(size <= expected["bytes"], "Oversized HTTP object")
            core.require(
                size == expected["bytes"] and digest.hexdigest() == expected["sha256"],
                "HTTP object checksum mismatch",
            )
            content_type, cache = response_policy(name)
            core.require(
                response.headers["Content-Type"] == content_type
                and response.headers["Cache-Control"] == cache,
                "HTTP policy mismatch",
            )
        with urllib.request.urlopen(
            urllib.request.Request(target, method="HEAD"), timeout=30
        ) as response:
            core.require(
                int(response.headers["Content-Length"]) == size
                and response.read() == b"",
                "HEAD disagrees with GET",
            )
    return {
        "status": "PASS",
        "transport": "LOOPBACK HTTP",
        "files": len(reviewed["files"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "verify", "publish", "serve"))
    for name in ("public", "store", "key"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    destination = LocalDestination(args.store)
    reviewed = plan(args.public, destination, args.key, args.fingerprint, args.store)
    if args.mode == "publish":
        core.require(args.plan is not None, "Reviewed plan file required")
        result = publish(
            args.public,
            destination,
            args.key,
            args.fingerprint,
            core.read_json(args.plan),
            args.store,
        )
    elif args.mode in {"serve", "verify"}:
        with loopback(destination, args.key, args.fingerprint) as base:
            if args.mode == "serve":
                print(json.dumps({"url": base, "purpose": "LOCAL ONLY"}), flush=True)
                threading.Event().wait()
            result = verify_http(base, reviewed)
    else:
        result = reviewed
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
