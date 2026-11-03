"""P6 time-bounded trust checks in addition to accepted cryptographic verification."""

import tempfile
import time
from pathlib import Path

import core


def verify_current_signature(key, fingerprint, path, signature, parent, *, now=None):
    core.verify_signature(key, fingerprint, path, signature, parent)
    now = int(time.time() if now is None else now)
    with tempfile.TemporaryDirectory(prefix="trust-", dir=parent) as directory:
        home = Path(directory)
        home.chmod(0o700)
        core.gpg(home, "--import", key)
        listing = core.gpg(home, "--with-colons", "--list-keys").decode()
        identities = {}
        pending = None
        for line in listing.splitlines():
            fields = line.split(":")
            if fields[0] in {"pub", "sub"}:
                pending = fields
            elif fields[0] == "fpr" and pending:
                identities[fields[9]] = pending
                pending = None
        status = core.gpg(
            home, "--status-fd", "1", "--verify", signature, path
        ).decode()
        core.require(
            not any(
                f"[GNUPG:] {bad} " in status
                for bad in ("EXPKEYSIG", "EXPSIG", "REVKEYSIG", "BADSIG", "ERRSIG")
            ),
            "Expired, revoked or invalid signing identity",
        )
        signer = next(
            line.split()[2]
            for line in status.splitlines()
            if line.startswith("[GNUPG:] VALIDSIG ")
        )
        for identity in {fingerprint, signer}:
            record = identities.get(identity)
            core.require(record is not None, "Signature identity absent from trust key")
            core.require(
                record[1] not in {"r", "e", "d"}
                and int(record[5]) <= now
                and (not record[6] or int(record[6]) > now),
                "Expired, revoked or not-yet-valid signing identity",
            )
    return {"primary_fingerprint": fingerprint, "signing_fingerprint": signer}
