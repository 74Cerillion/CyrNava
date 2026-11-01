"""P5C real native updates of tiny synthetic fixtures; no production version bump."""

import base64
import contextlib
import http.server
import shutil
import threading
import urllib.parse
from pathlib import Path

import client
import core


@contextlib.contextmanager
def loopback(store):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def serve(self, body):
            path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
            if not path.startswith("/current/repo/") or ".." in Path(path).parts:
                self.send_error(404)
                return
            candidate = (store / path.lstrip("/")).resolve()
            if (
                not candidate.is_relative_to(store / "generations")
                or not candidate.is_file()
            ):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(candidate.stat().st_size))
            self.end_headers()
            if body:
                with candidate.open("rb") as stream:
                    shutil.copyfileobj(stream, self.wfile)

        def do_GET(self):
            self.serve(True)

        def do_HEAD(self):
            self.serve(False)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/current/repo/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def descriptor(path, url, public_key):
    path.write_text(
        "[Flatpak Ref]\nTitle=P5C SYNTHETIC ONLY\nName="
        + client.FIXTURE_ID
        + "\nBranch=stable\nIsRuntime=false\nUrl="
        + url
        + "\nGPGKey="
        + base64.b64encode(public_key.read_bytes()).decode()
        + "\n"
    )


def generation(root, label, key, fingerprint, url, previous=None):
    core.require(label in {"A", "B"}, "Only two synthetic generations permitted")
    public = root / ("public-" + label)
    public.mkdir()
    if previous:
        shutil.copytree(previous / "repo", public / "repo")
    build = root / ("build-" + label)
    (build / "files/share").mkdir(parents=True)
    (build / "files/share/p5c-generation").write_text("P5C SYNTHETIC " + label + "\n")
    (build / "metadata").write_text(
        "[Application]\nname="
        + client.FIXTURE_ID
        + "\nruntime=org.freedesktop.Platform/x86_64/24.08\ncommand=true\n"
    )
    core.call("flatpak", "build-finish", build)
    core.call(
        "flatpak",
        "build-export",
        "--gpg-homedir=" + str(key),
        "--gpg-sign=" + fingerprint,
        public / "repo",
        build,
        "stable",
    )
    core.call(
        "flatpak",
        "build-update-repo",
        "--gpg-homedir=" + str(key),
        "--gpg-sign=" + fingerprint,
        public / "repo",
    )
    commit = (
        core.call(
            "ostree",
            "--repo=" + str(public / "repo"),
            "rev-parse",
            f"app/{client.FIXTURE_ID}/x86_64/stable",
        )
        .decode()
        .strip()
    )
    core.require(core.SHA.fullmatch(commit), "Invalid synthetic commit")
    pub = public / "staging-public.gpg"
    pub.write_bytes(core.export_key(key, fingerprint))
    descriptor(public / "fixture.flatpakref", url, pub)
    (public / "release.json").write_bytes(
        core.encode(
            {
                "purpose": "P5C SYNTHETIC UPDATE ONLY",
                "generation": label,
                "commit": commit,
                "application_id": client.FIXTURE_ID,
            }
        )
    )
    core.seal(public, key, fingerprint)
    return public, commit


def expect_rejection(action, category=None, message=None):
    try:
        action()
    except client.NativeFailure as error:
        core.require(
            category is None or error.category in category,
            "Native failure did not prove the intended fault category",
        )
        return error.category
    except core.Rejected as error:
        core.require(category is None, "Native rejection required")
        core.require(message is None or str(error) == message, "Wrong policy rejection")
        return "policy"
    raise core.Rejected("Expected rejection did not occur")


def exercise(root, key, fingerprint, wrong_key, wrong_fingerprint):
    """Faults are injected only into a synthetic repo and private clients."""
    root.mkdir()
    store = core.init_store(root / "store")
    checks = {}
    with loopback(store) as url:
        a, commit_a = generation(root, "A", key, fingerprint, url)
        pubkey = a / "staging-public.gpg"
        first = core.publish_local(a, store, pubkey, fingerprint)
        receiver = client.Client(root / "client")
        receiver.install(
            a / "fixture.flatpakref", pubkey, fingerprint, client.FIXTURE_ID, commit_a
        )
        checks["install_A_via_loopback_flatpakref"] = "PASS"
        b, commit_b = generation(root, "B", key, fingerprint, url, previous=a)
        core.require(
            commit_a != commit_b, "Synthetic generations must have distinct commits"
        )

        boundary = {"reached": False}

        def interrupt():
            boundary["reached"] = True
            raise core.Rejected("P5C intended before-activation interruption")

        expect_rejection(
            lambda: core.publish_local(
                b, store, pubkey, fingerprint, before_activate=interrupt
            ),
            message="P5C intended before-activation interruption",
        )
        core.require(boundary["reached"], "Intended interruption boundary not reached")
        core.require(
            core.active_generation(store).name == first["generation"],
            "Interrupted update changed active generation",
        )
        core.require(
            receiver.commit(client.FIXTURE_ID) == commit_a,
            "Interrupted publication changed installed app",
        )
        fresh = client.Client(root / "c1")
        fresh.install(
            a / "fixture.flatpakref", pubkey, fingerprint, client.FIXTURE_ID, commit_a
        )
        checks["interruption_keeps_A_installable"] = "PASS"

        second = core.publish_local(b, store, pubkey, fingerprint)
        receiver.update(client.FIXTURE_ID, commit_b)
        checks["update_existing_client_A_to_B"] = "PASS"
        old_objects = core.tree_manifest(a / "repo/objects")
        new_objects = core.tree_manifest(core.active_generation(store) / "repo/objects")
        core.require(
            all(new_objects.get(k) == v for k, v in old_objects.items()),
            "Historical objects lost",
        )
        checks["historical_objects_retained"] = "PASS"
        expect_rejection(
            lambda: core.publish_local(a, store, pubkey, fingerprint),
            message=(
                "New generation would remove/change objects needed by existing clients"
            ),
        )
        core.require(
            core.active_generation(store).name == second["generation"],
            "Unsafe recovery changed active generation",
        )
        checks["recovery_cannot_discard_B_objects"] = "PASS"

        # Mismatching expected generation is a failure even if native update is a no-op.
        expect_rejection(
            lambda: receiver.update(client.FIXTURE_ID, commit_a),
            message="Updated application commit mismatch",
        )
        checks["stale_expected_commit_rejected"] = "PASS"
        wrong_pub = root / "wrong-public.gpg"
        wrong_pub.write_bytes(core.export_key(wrong_key, wrong_fingerprint))
        wrong_ref = root / "wrong.flatpakref"
        descriptor(wrong_ref, url, wrong_pub)
        wrong_client = client.Client(root / "c2")
        expect_rejection(
            lambda: wrong_client.install(
                wrong_ref, wrong_pub, fingerprint, client.FIXTURE_ID, commit_b
            ),
            message="Staging public key fingerprint mismatch",
        )
        checks["independent_fingerprint_rejects_wrong_key"] = "PASS"
        expect_rejection(
            lambda: wrong_client.install(
                wrong_ref, wrong_pub, wrong_fingerprint, client.FIXTURE_ID, commit_b
            ),
            {"signature"},
        )
        checks["native_wrong_key_rejected"] = "PASS"

        for index, fault in enumerate(
            ("tampered-summary", "unsigned-summary", "missing-object")
        ):
            bad = root / fault
            shutil.copytree(b, bad)
            if fault == "tampered-summary":
                for name in ("summary", "summary.idx"):
                    summary = bad / "repo" / name
                    if summary.exists():
                        summary.write_bytes(summary.read_bytes() + b"P5C TAMPER")
            elif fault == "unsigned-summary":
                for sig in [bad / "repo/summary.sig", bad / "repo/summary.idx.sig"]:
                    if sig.exists():
                        sig.unlink()
            else:
                (
                    bad / "repo/objects" / commit_b[:2] / (commit_b[2:] + ".commit")
                ).unlink()
            # Intentionally injected invalid OSTree metadata, confined to fixture store.
            # Production generation always verifies the repository before publication.
            (bad / "manifest.json").unlink()
            (bad / "manifest.json.sig").unlink()
            core.seal(bad, key, fingerprint)
            if fault == "missing-object":
                expect_rejection(
                    lambda: core.publish_local(bad, store, pubkey, fingerprint),
                    message=(
                        "New generation would remove/change objects "
                        "needed by existing clients"
                    ),
                )
                checks["publisher_rejects_dropped_object"] = "PASS"
            bad_store = core.init_store(root / ("s" + str(index)))
            core.publish_local(bad, bad_store, pubkey, fingerprint)
            victim = client.Client(root / ("n" + str(index)))
            with loopback(bad_store) as bad_url:
                bad_ref = root / (fault + ".flatpakref")
                descriptor(bad_ref, bad_url, pubkey)
                expect_rejection(
                    lambda: victim.install(
                        bad_ref, pubkey, fingerprint, client.FIXTURE_ID, commit_b
                    ),
                    (
                        {"signature", "integrity", "missing-object", "ref-unavailable"}
                        if fault == "missing-object"
                        else {"signature", "integrity"}
                    ),
                )
            core.require(
                not victim.run("list", "list", "--app", "--columns=application"),
                "Rejected fixture was installed",
            )
            core.require(
                receiver.commit(client.FIXTURE_ID) == commit_b,
                "Fault discarded existing installation",
            )
            checks[fault + "_native_rejected"] = "PASS"
            # Restoration must retain every previously visible object.
            core.publish_local(b, store, pubkey, fingerprint)
        checks["retained_B_usable"] = "PASS"
        return {
            "status": "PASS",
            "scope": "SYNTHETIC UPDATE; no production app/schema upgrade",
            "application_id": client.FIXTURE_ID,
            "commit_A": commit_a,
            "commit_B": commit_b,
            "transport": "127.0.0.1 HTTP only",
            "checks": checks,
            "client_operations": receiver.operations,
        }
