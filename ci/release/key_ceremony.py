"""Executable DISPOSABLE rehearsal of offline-primary/signing-subkey recovery.

This module cannot create a permanent identity: fixed disposable UID, one-day
expiry, exclusive outside-source root, and mandatory private-material cleanup.
Production ceremony remains an owner-executed offline procedure in the runbook.
"""

import argparse
import os
import secrets
import shutil
import subprocess
import time
from pathlib import Path

import core
import trust

UID = "CyrNava P6 DISPOSABLE CEREMONY ONLY <p6-test@invalid>"


def fingerprints(home):
    return [
        line.split(":")[9]
        for line in core.gpg(home, "--with-colons", "--list-secret-keys")
        .decode()
        .splitlines()
        if line.startswith("fpr:")
    ]


def rehearse(root):
    root = core.outside_source(root)
    root.mkdir(mode=0o700)
    (root / ".p6-disposable-ceremony").write_bytes(core.encode({"purpose": UID}))
    record = {
        "status": "FAIL",
        "complete": False,
        "checks": {},
        "production_key": False,
    }
    homes = [root / name for name in ("primary", "restored", "signer", "revoked")]
    encrypted = root / "encrypted-backup.gpg"
    password = root / "backup-password"
    start = time.monotonic()
    try:
        for home in homes:
            home.mkdir(mode=0o700)
        primary, restored, signer, revoked = homes
        options = ("--pinentry-mode", "loopback", "--passphrase", "")
        core.gpg(
            primary, *options, "--quick-generate-key", UID, "rsa3072", "cert", "1d"
        )
        fingerprint = fingerprints(primary)[0]
        core.gpg(
            primary, *options, "--quick-add-key", fingerprint, "rsa3072", "sign", "1d"
        )
        signing = fingerprints(primary)[1]
        record["primary_fingerprint"] = fingerprint
        record["signing_fingerprint"] = signing
        key = root / "public.gpg"
        key.write_bytes(core.gpg(primary, "--export", fingerprint))
        # Secret export is piped in memory straight to encryption; no plaintext
        # secret archive is written. The disposable random passphrase is removed.
        password.write_text(secrets.token_hex(32))
        password.chmod(0o600)
        secret = core.gpg(primary, *options, "--export-secret-keys", fingerprint)
        subprocess.run(
            [
                "gpg",
                "--no-options",
                "--homedir",
                str(primary),
                "--batch",
                "--pinentry-mode",
                "loopback",
                "--passphrase-file",
                str(password),
                "--cipher-algo",
                "AES256",
                "--output",
                str(encrypted),
                "--symmetric",
            ],
            input=secret,
            capture_output=True,
            check=True,
            timeout=60,
        )
        secret = b""
        recovered = core.gpg(
            primary,
            "--pinentry-mode",
            "loopback",
            "--passphrase-file",
            password,
            "--decrypt",
            encrypted,
        )
        subprocess.run(
            ["gpg", "--no-options", "--homedir", str(restored), "--batch", "--import"],
            input=recovered,
            capture_output=True,
            check=True,
            timeout=60,
        )
        recovered = b""
        core.require(
            fingerprints(restored) == [fingerprint, signing],
            "Backup restoration mismatch",
        )
        record["checks"]["encrypted_backup_restored_exact_primary_and_subkey"] = "PASS"
        # Export-subkeys intentionally replaces primary secret with a GNU stub.
        subkeys = core.gpg(restored, *options, "--export-secret-subkeys", signing + "!")
        subprocess.run(
            ["gpg", "--no-options", "--homedir", str(signer), "--batch", "--import"],
            input=subkeys,
            capture_output=True,
            check=True,
            timeout=60,
        )
        subkeys = b""
        listing = core.gpg(signer, "--with-colons", "--list-secret-keys").decode()
        primary_record = next(
            line.split(":") for line in listing.splitlines() if line.startswith("sec:")
        )
        core.require(
            primary_record[14] == "#", "Online signer still has primary secret"
        )
        record["checks"]["signer_has_primary_stub_only"] = "PASS"
        probe = root / "probe.txt"
        probe.write_text("P6 disposable signing and recovery rehearsal\n")
        signature = root / "probe.sig"
        core.gpg(
            signer,
            *options,
            "--local-user",
            signing + "!",
            "--output",
            signature,
            "--detach-sign",
            probe,
        )
        trusted = trust.verify_current_signature(
            key, fingerprint, probe, signature, root
        )
        core.require(trusted["signing_fingerprint"] == signing, "Wrong signing subkey")
        record["checks"]["restored_subkey_signature_verified"] = "PASS"
        try:
            trust.verify_current_signature(
                key, fingerprint, probe, signature, root, now=time.time() + 172800
            )
        except core.Rejected:
            record["checks"]["expired_identity_rejected"] = "PASS"
        core.require(
            "expired_identity_rejected" in record["checks"], "Expiry guard ineffective"
        )
        revocation = primary / "openpgp-revocs.d" / (fingerprint + ".rev")
        raw = revocation.read_text()
        raw = (
            raw[raw.index(":-----BEGIN PGP PUBLIC KEY BLOCK-----") :]
            .replace("\n:", "\n")
            .removeprefix(":")
        )
        core.gpg(revoked, "--import", key)
        subprocess.run(
            ["gpg", "--no-options", "--homedir", str(revoked), "--batch", "--import"],
            input=raw.encode(),
            capture_output=True,
            check=True,
            timeout=60,
        )
        revkey = root / "revoked-public.gpg"
        revkey.write_bytes(core.gpg(revoked, "--export", fingerprint))
        try:
            trust.verify_current_signature(revkey, fingerprint, probe, signature, root)
        except core.Rejected:
            record["checks"]["revoked_identity_rejected"] = "PASS"
        core.require(
            "revoked_identity_rejected" in record["checks"],
            "Revocation guard ineffective",
        )
        record["status"] = "PASS"
    except (
        core.Rejected,
        OSError,
        subprocess.SubprocessError,
        ValueError,
        IndexError,
    ) as error:
        record["error"] = (
            str(error) if isinstance(error, core.Rejected) else type(error).__name__
        )
    finally:
        cleanup_ok = True
        for home in homes:
            try:
                if home.exists():
                    core.call("gpgconf", "--homedir", home, "--kill", "gpg-agent")
                    shutil.rmtree(home)
            except (core.Rejected, OSError):
                cleanup_ok = False
        for path in (encrypted, password):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                cleanup_ok = False
        cleanup_ok = cleanup_ok and not any(
            p.exists() for p in [*homes, encrypted, password]
        )
        record["checks"]["private_material_removed"] = "PASS" if cleanup_ok else "FAIL"
        if not cleanup_ok:
            record["status"] = "FAIL"
            record["cleanup_attention_required"] = True
        record["seconds"] = round(time.monotonic() - start, 3)
        record["complete"] = True
        (root / "result.json").write_bytes(core.encode(record))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disposable-root", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    result = rehearse(args.disposable_root)
    print(core.encode(result).decode(), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
