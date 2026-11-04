"""N2 real signed-install fixture; never creates a production signing identity.

Uses the unchanged installer CLI and locked wheels in an isolated HOME/XDG tree.
Archive changes are the test's production-shaped build identity and the corrected
public-only verifier. This is installation evidence, not a public release.
"""

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "ci-output/native-n2-candidate-3"
MANIFEST = "a1e066a3d769319a761b8643469f055201ef04b2b80ff92c0ac9604e1a4f8d82"
ARCHIVE = "9d92a4f5d925e42f1cb8c9abdc84d913a3c111a5a52f4ed88b2d30840d36c0be"
KEY_HOME = Path("/tmp/cyrnava-n2-signature-check")


def engine_module():
    spec = importlib.util.spec_from_file_location(
        "n2_signed_engine", ROOT / "desktop/install_engine.py"
    )
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def fixture_archive(engine, output):
    """Keep app/dependency bytes except identity; carry the public-verifier fix."""
    source = CANDIDATE / "manifest.json"
    engine.require(engine.digest(source) == MANIFEST, "Reviewed manifest changed")
    manifest = copy.deepcopy(engine.validate_manifest(engine.load(source)))
    original = CANDIDATE / "CyrNava-0.1.0-n2.1-ubuntu-x86_64.zip"
    engine.require(engine.digest(original) == ARCHIVE, "Reviewed archive changed")
    archive = output / "signed-install-fixture.zip"
    changed = ["application/desktop/native/build_identity.py", "install_engine.py"]
    with zipfile.ZipFile(original) as incoming, zipfile.ZipFile(archive, "x") as target:
        for member in incoming.infolist():
            data = incoming.read(member)
            engine.require(
                hashlib.sha256(data).hexdigest()
                == manifest["files"][member.filename]["sha256"],
                "Original archive member changed",
            )
            if member.filename == changed[0]:
                engine.require(
                    data.count(engine.CANDIDATE_ID.encode()) == 1,
                    "Unexpected test build identity",
                )
                data = data.replace(
                    engine.CANDIDATE_ID.encode(), engine.APP_ID.encode()
                )
            elif member.filename == changed[1]:
                data = (ROOT / "desktop/install_engine.py").read_bytes()
            if member.filename in changed:
                manifest["files"][member.filename].update(
                    bytes=len(data), sha256=hashlib.sha256(data).hexdigest()
                )
            target.writestr(member, data)
    manifest.update(
        kind="release",
        app_id=engine.APP_ID,
        archive_sha256=engine.digest(archive),
        expanded_bytes=sum(p["bytes"] for p in manifest["files"].values()),
        verification_scope="N2 disposable signed-install fixture; NOT FOR DISTRIBUTION",
    )
    manifest["n2_source_files"]["desktop/install_engine.py"] = engine.digest(
        ROOT / "desktop/install_engine.py"
    )
    engine.validate_manifest(manifest)
    engine.durable(output / "manifest.json", manifest)
    return archive, changed


def run(output):
    engine = engine_module()
    engine.host_supported()
    output = engine.checked_path(output)
    engine.require(
        output.parent == ROOT / "ci-output"
        and re.fullmatch(r"native-n2-signed-install-[1-9][0-9]*", output.name)
        and not output.exists(),
        "Fresh reviewed signed-install output required",
    )
    engine.checked_path(KEY_HOME)
    engine.require(not KEY_HOME.exists(), "Existing signing fixture preserved")
    engine.require(
        shutil.disk_usage(output.parent).free >= 5 * 1024**3, "Keep 5GiB headroom"
    )
    output.mkdir(mode=0o700)
    started = time.monotonic()
    free_before = shutil.disk_usage(output).free
    record = {
        "status": "FAIL",
        "complete": False,
        "scope": "N2 real GPG signature and normal installer path; isolated HOME/XDG",
        "production_trust": "NOT ESTABLISHED",
        "normal_user_installation": "NOT MODIFIED",
        "original_archive_sha256": ARCHIVE,
        "original_manifest_sha256": MANIFEST,
        "checks": {},
        "driver_sha256": engine.digest(Path(__file__)),
    }
    key_created = False

    def operation(name, command, *, environment=None):
        print("N2 signed fixture: " + name, flush=True)
        record["stage"] = name
        with (output / (name + ".private.log")).open("xb") as log:
            subprocess.run(
                list(map(str, command)),
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=180,
            )

    try:
        archive, changed = fixture_archive(engine, output)
        manifest = output / "manifest.json"
        (output / "install_engine.py").write_bytes(
            (ROOT / "desktop/install_engine.py").read_bytes()
        )
        (output / "install.sh").write_bytes((CANDIDATE / "install.sh").read_bytes())
        KEY_HOME.mkdir(mode=0o700)
        key_created = True
        gpg = [
            "/usr/bin/gpg",
            "--no-options",
            "--homedir",
            KEY_HOME,
            "--batch",
            "--no-auto-key-retrieve",
            "--pinentry-mode",
            "loopback",
            "--passphrase",
            "",
        ]
        operation(
            "generate-disposable-key",
            gpg
            + [
                "--quick-generate-key",
                "CyrNava N2 disposable installation test <n2-test@example.invalid>",
                "ed25519",
                "sign",
                "1d",
            ],
        )
        identities = subprocess.run(
            list(map(str, gpg + ["--with-colons", "--list-keys"])),
            capture_output=True,
            check=True,
            timeout=15,
        )
        fingerprints = [
            r.split(":")[9]
            for r in identities.stdout.decode().splitlines()
            if r.startswith("fpr:")
        ]
        engine.require(
            len(fingerprints) == 1, "Exactly one disposable signing key required"
        )
        fingerprint = fingerprints[0]
        public = output / "test-public-key.asc"
        signature = output / "manifest.json.asc"
        operation(
            "export-public-key",
            gpg + ["--armor", "--output", public, "--export", fingerprint],
        )
        operation(
            "sign-test-manifest",
            gpg
            + [
                "--armor",
                "--digest-algo",
                "SHA256",
                "--local-user",
                fingerprint,
                "--output",
                signature,
                "--detach-sign",
                manifest,
            ],
        )
        trust = engine.verify_signature(
            manifest, signature, public, fingerprint, output
        )
        record["checks"]["real_signature_valid"] = "PASS"
        for name, path, trusted in (
            ("wrong_trusted_fingerprint_rejected", manifest, "0" * 40),
            (
                "tampered_manifest_rejected",
                output / "tampered-manifest.json",
                fingerprint,
            ),
        ):
            if path != manifest:
                path.write_bytes(manifest.read_bytes() + b" ")
            try:
                engine.verify_signature(path, signature, public, trusted, output)
            except (ValueError, subprocess.CalledProcessError):
                record["checks"][name] = "PASS"
            else:
                raise AssertionError(name)
        home = output / "home"
        home.mkdir(mode=0o700)
        data = home / ".local/share"
        data.mkdir(parents=True, mode=0o700)
        environment = dict(
            os.environ,
            HOME=str(home),
            XDG_DATA_HOME=str(data),
            XDG_CONFIG_HOME=str(home / ".config"),
            XDG_CACHE_HOME=str(home / ".cache"),
            XDG_DATA_DIRS="/usr/local/share:/usr/share",
        )
        root = data / "cyrnava-application"
        operation(
            "signed-install",
            [
                "/bin/bash",
                output / "install.sh",
                "install",
                "--archive",
                archive,
                "--manifest",
                manifest,
                "--signature",
                signature,
                "--key",
                public,
                "--fingerprint",
                fingerprint,
                "--root",
                root,
            ],
            environment=environment,
        )
        current = engine.load(root / "current.json")
        release = root / "releases" / current["release"]
        receipt, installed_manifest = engine.installed(release)
        engine.require(receipt["trust"] == trust, "Installed signed identity mismatch")
        engine.require(
            installed_manifest["archive_sha256"] == engine.digest(archive),
            "Wrong installed archive",
        )
        backend = engine.load(release / "backend-check.json")
        engine.require(backend["status"] == "PASS", "Actual installed backend failed")
        operation(
            "installed-bootstrap",
            ["/usr/bin/python3.14", "-B", "-I", root / "launch.py", "--check"],
            environment=environment,
        )
        record["checks"].update(
            normal_signed_install="PASS",
            actual_locked_dependency_install="PASS",
            actual_provider_and_ELF_checks="PASS",
            actual_backend_security_and_data="PASS",
            installed_bootstrap_without_GUI="PASS",
        )
        record.update(
            status="PASS",
            stage="complete",
            signing_fingerprint=fingerprint,
            signature_sha256=engine.digest(signature),
            public_key_sha256=engine.digest(public),
            manifest_sha256=engine.digest(manifest),
            archive_sha256=engine.digest(archive),
            installed_receipt_sha256=current["receipt_sha256"],
            provider_file_count=len(receipt["provider_files"]),
            changed_archive_paths=changed,
            backend_checks=backend["checks"],
            GUI="NOT EXECUTED; prior exact development candidate GUI evidence retained",
        )
    except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 - safe retained diagnostic
        (output / "exception.private.log").write_text(traceback.format_exc())
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            (output / "child-error.private.log").write_bytes(error.stderr)
        record["error_type"] = type(error).__name__
    finally:
        if key_created:
            subprocess.run(
                ["/usr/bin/gpgconf", "--homedir", str(KEY_HOME), "--kill", "gpg-agent"],
                capture_output=True,
                check=False,
                timeout=15,
            )
            shutil.rmtree(
                KEY_HOME
            )  # Only the fresh key home created by this execution.
        record["checks"]["disposable_private_key_removed"] = (
            "PASS" if not KEY_HOME.exists() else "FAIL"
        )
        if KEY_HOME.exists():
            record["status"] = "FAIL"
        record.update(
            complete=True,
            seconds=round(time.monotonic() - started, 3),
            filesystem_free_before=free_before,
            filesystem_free_after=shutil.disk_usage(output).free,
        )
        engine.durable(output / "result.json", record)
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "PASS" else 2


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    raise SystemExit(run(parser.parse_args().output))
