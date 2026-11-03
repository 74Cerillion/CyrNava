"""N3 stopped-client transactions. Stdlib only; called by the shared installer.

No downloads, host-policy loading, data migration, data purge or automatic
rollback. All profile/browser bytes are checkpointed before changing selection.
"""

import base64
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import uuid
from pathlib import Path

CONTRACT = {
    "format": 1,
    "schema": 5,
    "document_format": 1,
    "profile_format": 1,
    "portable_backup_format": 2,
}
MAX_PROFILE = 4 * 1024**3
MAX_FILES = 50000


def version_key(value):
    core, _, suffix = value.partition("-")
    return (
        tuple(map(int, core.split("."))),
        not bool(suffix),
        tuple((0, int(p)) if p.isdecimal() else (1, p) for p in suffix.split(".")),
    )


def inventory(engine, root):
    """Hash an owned, private, link-free stopped profile without opening Qt/SQLite."""
    if not root.exists():
        return {"exists": False, "files": {}, "directories": [], "bytes": 0}
    root = engine.private_directory(root)
    result = {"exists": True, "files": {}, "directories": [], "bytes": 0}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            p = engine.checked_path(Path(directory) / name)
            info = p.lstat()
            engine.require(
                info.st_uid == os.getuid()
                and not info.st_mode & 0o077
                and info.st_dev == root.stat().st_dev,
                "Unsafe profile owner, permissions or mount",
            )
            relative = str(p.relative_to(root))
            if stat.S_ISDIR(info.st_mode):
                result["directories"].append(relative)
            else:
                engine.regular(p)
                result["bytes"] += info.st_size
                engine.require(
                    len(result["files"]) < MAX_FILES and result["bytes"] <= MAX_PROFILE,
                    "Stopped profile exceeds bounded checkpoint capacity",
                )
                result["files"][relative] = {
                    "sha256": engine.digest(p),
                    "bytes": info.st_size,
                }
    result["directories"].sort()
    return result


@contextlib.contextmanager
def stopped(engine, profile):
    """Use the existing GUI/backend locks; never initialize or migrate user data."""
    with contextlib.ExitStack() as stack:
        if profile.exists():
            inventory(engine, profile)
            locks = [profile / ".instance.lock"]
            locks += sorted(profile.glob("workspace/.engage.lock"))
            locks += sorted(profile.glob("workspaces/*/.engage.lock"))
            for path in locks:
                if not path.exists():
                    continue
                stream = stack.enter_context(engine.regular(path, 1024).open("rb"))
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise ValueError(
                        "Save and close all CyrNava processes first"
                    ) from None
        yield


def verified(engine, root, active):
    """Verify retained releases too; no temporary active-pointer substitution."""
    engine.require(active.get("format") == 1, "Invalid release selection")
    name = engine.member_name(active.get("release", ""))
    engine.require(
        re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?-[0-9a-f]{16}", name),
        "Invalid release selection",
    )
    engine.require((root / "releases" / name).is_dir(), "Retained release missing")
    release = engine.private_directory(root / "releases" / name)
    engine.require(
        engine.digest(engine.regular(release / "installed.json"))
        == active.get("receipt_sha256"),
        "Retained receipt changed",
    )
    receipt = engine.load(release / "installed.json")
    manifest = engine.validate_manifest(engine.load(release / "manifest.json"))
    engine.require(
        receipt["root"] == str(root)
        and receipt["release"] == name
        and receipt["manifest_sha256"] == engine.digest(release / "manifest.json"),
        "Retained deployment identity changed",
    )
    for relative, info in manifest["files"].items():
        engine.require(
            engine.digest(engine.regular(release / relative)) == info["sha256"],
            "Retained application changed",
        )
    engine.require(receipt["provider_files"], "Provider inventory missing")
    for relative, checksum in receipt["provider_files"].items():
        engine.member_name(relative)
        engine.require(
            relative.startswith(".venv/")
            and engine.digest(engine.regular(release / relative)) == checksum,
            "Retained dependency changed",
        )
    return release, receipt, manifest


def compatible(engine, old, new):
    """Initial support boundary: unchanged schema/Qt/profile/application contract.

    The N3 launcher/maintenance engine may change. Backend/storage/frontend bytes
    remain exactly the accepted ones. Schema evolution needs its own reviewed
    migration policy; it cannot be enabled by a claimed version string.
    """
    engine.require(
        new.get("maintenance") == CONTRACT, "Unsupported maintenance contract"
    )
    engine.require(
        old["app_id"] == new["app_id"]
        and old["kind"] == new["kind"]
        and old["target"] == new["target"]
        and old.get("apparmor") == new.get("apparmor")
        and old.get("n1_receipt_sha256") == new.get("n1_receipt_sha256"),
        "Update changed deployment or security identity",
    )
    for name, info in old["files"].items():
        if name.startswith("application/") or name in {
            "requirements.lock",
            "dependencies.json",
            "launch.py",
            "cyrnava-native",
            "apparmor_support.py",
            "system_schemas.py",
        }:
            engine.require(
                new["files"].get(name) == info, "Unsupported data/Qt/bootstrap change"
            )


def inspect_profile(engine, release, profile, output):
    """Run unchanged domain auditors in the verified target environment, no GUI."""
    helper = Path(__file__).with_name("native_profile_check.py")
    engine.require(helper.is_file(), "Verified profile auditor missing")
    print("N3: read-only stopped-profile audit", flush=True)
    with (output.with_suffix(".private.log")).open("xb") as log:
        try:
            subprocess.run(
                [
                    release / ".venv/bin/python",
                    "-B",
                    "-I",
                    helper,
                    "--application",
                    release / "application",
                    "--profile",
                    profile,
                    "--output",
                    output,
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                timeout=120,
                check=True,
                env=dict(
                    os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(release / "tmp")
                ),
            )
        except subprocess.SubprocessError as error:
            raise ValueError(
                "Operation failed: stopped-profile-audit; retain private log"
            ) from error
    record = engine.load(output)
    engine.require(record.get("status") == "PASS", "Stopped profile validation failed")
    return record


def checkpoint(engine, root, profile, before, identifier):
    parent = engine.private_directory(root / "checkpoints")
    destination = parent / identifier
    destination.mkdir(mode=0o700)
    if before["exists"]:
        copy = destination / "profile"
        copy.mkdir(mode=0o700)
        for name in before["directories"]:
            (copy / name).mkdir(parents=True, mode=0o700, exist_ok=True)
        for name in before["files"]:
            target = copy / name
            with (
                engine.regular(profile / name).open("rb") as src,
                target.open("xb") as dst,
            ):
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
            target.chmod(0o600)
        engine.require(
            inventory(engine, copy) == before, "Profile checkpoint verification failed"
        )
        for directory, _, _ in os.walk(copy, topdown=False):
            engine.sync_directory(Path(directory))
    engine.durable(destination / "manifest.json", before)
    engine.sync_directory(destination)
    engine.sync_directory(parent)
    return destination


def finish(engine, root, journal):
    """Keep the completed transaction and checkpoints; remove only its live marker."""
    target = root / ("completed-" + journal["id"] + ".json")
    engine.require(not target.exists(), "Completed transaction already present")
    os.replace(root / "transaction.json", target)
    engine.sync_directory(root)


def update(
    engine,
    archive,
    manifest_path,
    root,
    *,
    disposable=False,
    candidate_sha256=None,
    signature=None,
    key=None,
    fingerprint=None,
    reinstall=False,
):
    engine.host_supported()
    root = engine.checked_path(root)
    profile, applications = engine.deployment_paths(root, disposable)
    manifest_pin = engine.digest(engine.regular(manifest_path))
    new = engine.validate_manifest(engine.load(manifest_path))
    with engine.installation_lock(root), stopped(engine, profile):
        engine.require(
            not (root / "transaction.json").exists(),
            "Interrupted transaction retained; recover first",
        )
        active = engine.load(root / "current.json")
        old_release, old_receipt, old = verified(engine, root, active)
        engine.installed(old_release)
        engine.require(
            old_receipt["profile"] == str(profile), "Data-root identity changed"
        )
        compatible(engine, old, new)
        for helper in ("native_operations.py", "native_profile_check.py"):
            engine.require(
                helper in new["files"]
                and engine.digest(Path(__file__).with_name(helper))
                == new["files"][helper]["sha256"],
                "Maintenance helper differs from authenticated manifest",
            )
        engine.require(
            new["kind"] == ("candidate" if disposable else "release"),
            "Deployment kind mismatch",
        )
        if disposable:
            engine.require(
                engine.hash_string(candidate_sha256)
                and engine.digest(manifest_path) == candidate_sha256,
                "Explicit reviewed candidate manifest checksum required",
            )
            trust = {
                "mode": "disposable-checksum-only",
                "production_signature": "NOT VERIFIED",
            }
        else:
            engine.require(
                signature and key and fingerprint, "Owner-trusted signature required"
            )
            engine.require(
                old_receipt["trust"].get("primary") == fingerprint,
                "Signing key transition requires separate trust approval",
            )
            trust = engine.verify_signature(
                manifest_path, signature, key, fingerprint, root
            )
        engine.require(
            engine.digest(manifest_path) == manifest_pin
            and engine.load(manifest_path) == new,
            "Manifest changed during authentication",
        )
        same = engine.digest(manifest_path) == old_receipt["manifest_sha256"]
        engine.require(
            same
            if reinstall
            else version_key(new["version"]) > version_key(old["version"]),
            "Use explicit same-artifact reinstall; downgrade or changed same-version update refused",
        )
        engine.require(
            not reinstall or same, "Reinstall requires the exact installed artifact"
        )
        engine.require(
            engine.digest(engine.regular(archive, engine.MAX_ARCHIVE))
            == new["archive_sha256"],
            "Archive checksum mismatch",
        )
        before = inventory(engine, profile)
        required = (
            (0 if reinstall else new["expanded_bytes"] * 4)
            + before["bytes"] * 2
            + engine.HEADROOM
        )
        engine.require(
            shutil.disk_usage(root).free >= required,
            "Insufficient update/checkpoint headroom",
        )
        identifier = uuid.uuid4().hex
        audit = engine.private_directory(root / "maintenance") / identifier
        audit.mkdir(mode=0o700)
        inspect_profile(engine, old_release, profile, audit / "before.json")
        desktop = applications / (new["app_id"] + ".desktop")
        expected_desktop = (
            old_receipt.get("desktop_sha256")
            or hashlib.sha256(
                engine.desktop_entry(
                    old_release, old["app_id"], disposable, native="apparmor" in old
                )
            ).hexdigest()
        )
        engine.require(
            engine.digest(engine.regular(desktop)) == expected_desktop,
            "Changed desktop entry preserved",
        )
        journal = {
            "format": 3,
            "id": identifier,
            "operation": "reinstall" if reinstall else "update",
            "root": str(root),
            "before": active,
            "after": None,
            "profile": str(profile),
            "profile_inventory": before,
            "desktop": str(desktop),
            "desktop_sha256": expected_desktop,
        }
        engine.journal_checkpoint(root, journal, "preparing-checkpoint")
        saved = checkpoint(engine, root, profile, before, identifier)
        journal["checkpoint"] = str(saved)
        engine.journal_checkpoint(root, journal, "checkpoint-verified")
        if reinstall:
            journal["after"] = active
            engine.journal_checkpoint(root, journal, "verified-reinstall")
        else:
            release = (
                root / "releases" / (new["version"] + "-" + new["archive_sha256"][:16])
            )
            engine.require(
                not release.exists(),
                "Existing version retained; explicit recovery required",
            )
            release.mkdir(mode=0o700)
            engine.extract(archive, release, new)
            engine.atomic(
                release / "manifest.json", engine.regular(manifest_path).read_bytes()
            )
            engine.require(
                engine.digest(release / "manifest.json") == manifest_pin,
                "Manifest changed during staging",
            )
            (release / "tmp").mkdir(mode=0o700)
            providers = engine.setup_environment(release)
            engine.run_operation(
                release,
                "synthetic-backend",
                [
                    release / ".venv/bin/python",
                    "-B",
                    "-I",
                    release / "backend_check.py",
                    release,
                ],
                timeout=90,
            )
            engine.require(
                engine.load(release / "backend-check.json").get("status") == "PASS",
                "Synthetic security/data check failed",
            )
            inspect_profile(engine, release, profile, audit / "target.json")
            engine.require(
                inventory(engine, profile) == before,
                "Profile changed while staging; no activation",
            )
            receipt = {
                "format": 1,
                "root": str(root),
                "release": release.name,
                "manifest_sha256": engine.digest(release / "manifest.json"),
                "profile": str(profile),
                "trust": trust,
                "provider_files": providers["provider_files"],
                "desktop_sha256": expected_desktop,
                "previous": active,
            }
            engine.durable(release / "installed.json", receipt)
            engine.sync_directory(root / "releases")
            journal["after"] = {
                "format": 1,
                "release": release.name,
                "receipt_sha256": engine.digest(release / "installed.json"),
            }
            engine.journal_checkpoint(root, journal, "verified")
            engine.durable(
                root / "current.json", dict(journal["after"], previous=active)
            )
        engine.journal_checkpoint(root, journal, "activated")
        finish(engine, root, journal)
        return {
            "status": "PASS",
            "scope": "N3 stopped-client " + journal["operation"],
            "release": journal["after"]["release"],
            "checkpoint": str(saved),
            "profile_bytes_unchanged": True,
            "native_GUI": "NOT EXECUTED",
            "previous_release_retained": True,
            "host_policy_changed": False,
        }


def recover(engine, root, *, disposable=False):
    root = engine.checked_path(root)
    profile, _ = engine.deployment_paths(root, disposable)
    with engine.installation_lock(root), stopped(engine, profile):
        journal = engine.load(root / "transaction.json", limit=32 * 1024**2)
        engine.require(
            journal.get("format") == 3 and journal["root"] == str(root),
            "Wrong maintenance journal",
        )
        engine.require(
            journal["operation"]
            in {"update", "reinstall", "rollback", "uninstall", "restore-installation"},
            "Unsupported recovery operation",
        )
        if journal["operation"] in {"uninstall", "restore-installation"}:
            engine.require(
                inventory(engine, profile) == journal["profile_inventory"],
                "Data changed; automatic recovery refused",
            )
            apply_targets(
                engine, root, disposable, journal["targets"], direction="before"
            )
            engine.journal_checkpoint(root, journal, "recovered")
            finish(engine, root, journal)
            return {
                "status": "PASS",
                "scope": "N3 registration transaction recovery",
                "profile_unchanged": True,
            }
        before = journal["before"]
        verified(engine, root, before)
        engine.require(
            inventory(engine, profile) == journal["profile_inventory"],
            "Data changed; automatic binary recovery refused",
        )
        current = engine.load(root / "current.json")
        engine.require(
            {k: current.get(k) for k in ("format", "release", "receipt_sha256")}
            in [
                {k: s.get(k) for k in ("format", "release", "receipt_sha256")}
                for s in (before, journal.get("after"))
                if s
            ],
            "Changed selection preserved",
        )
        engine.durable(root / "current.json", before)
        journal["recovery"] = "previous-selection-restored-with-unchanged-data"
        engine.journal_checkpoint(root, journal, "recovered")
        finish(engine, root, journal)
        return {
            "status": "PASS",
            "scope": "N3 interrupted activation recovery",
            "profile_unchanged": True,
            "staged_release_and_checkpoint": "RETAINED",
        }


def encoded(data):
    return base64.b64encode(data).decode() if data is not None else None


def apply_targets(engine, root, disposable, targets, *, direction):
    """Validate the entire exact activation set before any change; no tree deletion."""
    _, applications = engine.deployment_paths(root, disposable)
    allowed = {
        root / n
        for n in (
            "current.json",
            "launch.py",
            "cyrnava-native",
            "apparmor-profile",
            "uninstalled.json",
        )
    }
    allowed.add(
        applications
        / ((engine.CANDIDATE_ID if disposable else engine.APP_ID) + ".desktop")
    )
    engine.require(len(targets) <= len(allowed), "Unexpected activation target count")
    paths = set()
    for target in targets:
        path = engine.checked_path(Path(target["path"]))
        engine.require(
            path in allowed and path not in paths, "Unexpected activation target"
        )
        paths.add(path)
        current = engine.regular(path).read_bytes() if path.exists() else None
        engine.require(
            encoded(current) in (target["before"], target["after"]),
            "Changed activation target preserved",
        )
        engine.require(
            target["mode"] in {0o600, 0o644, 0o700}, "Unsafe activation permissions"
        )
    for target in targets:
        path = Path(target["path"])
        current = engine.regular(path).read_bytes() if path.exists() else None
        engine.require(
            encoded(current) in (target["before"], target["after"]),
            "Activation target changed during transaction; preserved",
        )
        wanted = target[direction]
        if wanted is None:
            if path.exists():
                path.unlink()
                engine.sync_directory(path.parent)
        else:
            data = base64.b64decode(wanted, validate=True)
            engine.atomic(path, data, target["mode"])


def uninstall(engine, root, *, disposable=False):
    """Remove exact launch/desktop activation; retain version payloads and all data.

    Retaining payloads is deliberate: explicit reinstall can reuse verified bytes
    without a network/signing operation. No implicit purge or disk-reclaim claim.
    """
    engine.host_supported()
    root = engine.checked_path(root)
    profile, applications = engine.deployment_paths(root, disposable)
    with engine.installation_lock(root), stopped(engine, profile):
        engine.require(
            not (root / "transaction.json").exists(),
            "Interrupted transaction retained; recover first",
        )
        engine.require(
            not (root / "uninstalled.json").exists(),
            "Existing uninstall record preserved",
        )
        active = engine.load(root / "current.json")
        release, receipt, manifest = verified(engine, root, active)
        engine.installed(release)
        engine.require(receipt["profile"] == str(profile), "Data-root identity changed")
        desktop = applications / (manifest["app_id"] + ".desktop")
        expected = (
            receipt.get("desktop_sha256")
            or hashlib.sha256(
                engine.desktop_entry(
                    release,
                    manifest["app_id"],
                    disposable,
                    native="apparmor" in manifest,
                )
            ).hexdigest()
        )
        engine.require(
            engine.digest(engine.regular(desktop)) == expected,
            "Changed desktop entry preserved",
        )
        before = inventory(engine, profile)
        engine.require(
            shutil.disk_usage(root).free >= before["bytes"] * 2 + engine.HEADROOM,
            "Insufficient checkpoint headroom",
        )
        targets = []
        for path in [
            desktop,
            root / "launch.py",
            *(
                [root / "cyrnava-native", root / "apparmor-profile"]
                if "apparmor" in manifest
                else []
            ),
            root / "current.json",
        ]:
            targets.append(
                {
                    "path": str(path),
                    "before": encoded(engine.regular(path).read_bytes()),
                    "after": None,
                    "mode": stat.S_IMODE(path.stat().st_mode),
                }
            )
        saved = {
            "format": 1,
            "active": active,
            "profile": str(profile),
            "profile_inventory": before,
            "targets": targets,
        }
        targets = [
            *targets,
            {
                "path": str(root / "uninstalled.json"),
                "before": None,
                "after": encoded(
                    (json.dumps(saved, sort_keys=True, indent=2) + "\n").encode()
                ),
                "mode": 0o600,
            },
        ]
        journal = {
            "format": 3,
            "id": uuid.uuid4().hex,
            "operation": "uninstall",
            "root": str(root),
            "profile_inventory": before,
            "targets": targets,
        }
        engine.journal_checkpoint(root, journal, "prepared-uninstall")
        checkpoint(engine, root, profile, before, journal["id"])
        apply_targets(engine, root, disposable, targets, direction="after")
        engine.journal_checkpoint(root, journal, "unregistered")
        finish(engine, root, journal)
        return {
            "status": "PASS",
            "scope": "N3 data-preserving uninstall",
            "program_activation": "REMOVED",
            "profile_backups_and_versions": "RETAINED",
            "host_policy": "UNCHANGED; separate exact removal only",
            "disk_reclaim_claimed": False,
        }


def restore_installation(engine, root, *, disposable=False, reuse_preserved_data=False):
    engine.host_supported()
    root = engine.checked_path(root)
    profile, _ = engine.deployment_paths(root, disposable)
    engine.require(reuse_preserved_data, "Explicit reuse of preserved data required")
    with engine.installation_lock(root), stopped(engine, profile):
        engine.require(
            not (root / "transaction.json").exists(),
            "Interrupted transaction retained; recover first",
        )
        saved = engine.load(root / "uninstalled.json", limit=32 * 1024**2)
        verified(engine, root, saved["active"])
        engine.require(
            saved["profile"] == str(profile)
            and inventory(engine, profile) == saved["profile_inventory"],
            "Preserved data changed; explicit recovery review required",
        )
        targets = [dict(t, before=None, after=t["before"]) for t in saved["targets"]]
        targets += [
            {
                "path": str(root / "uninstalled.json"),
                "before": encoded((root / "uninstalled.json").read_bytes()),
                "after": None,
                "mode": 0o600,
            }
        ]
        journal = {
            "format": 3,
            "id": uuid.uuid4().hex,
            "operation": "restore-installation",
            "root": str(root),
            "profile_inventory": saved["profile_inventory"],
            "targets": targets,
        }
        engine.journal_checkpoint(root, journal, "prepared-restore-installation")
        apply_targets(engine, root, disposable, targets, direction="after")
        engine.journal_checkpoint(root, journal, "restored-installation")
        finish(engine, root, journal)
        return {
            "status": "PASS",
            "scope": "N3 reinstall retained identical release",
            "profile_bytes_unchanged": True,
            "GUI": "NOT EXECUTED",
        }


def rollback(engine, root, *, disposable=False):
    """Explicit binary selection only for the identical data and Qt consumers."""
    engine.host_supported()
    root = engine.checked_path(root)
    profile, _ = engine.deployment_paths(root, disposable)
    with engine.installation_lock(root), stopped(engine, profile):
        engine.require(
            not (root / "transaction.json").exists(),
            "Interrupted transaction retained; recover first",
        )
        current = engine.load(root / "current.json")
        release, _receipt, manifest = verified(engine, root, current)
        engine.installed(release)
        previous = current.get("previous")
        engine.require(
            isinstance(previous, dict), "No verified prior release selection"
        )
        _, _, old_manifest = verified(engine, root, previous)
        if manifest.get("maintenance") == CONTRACT:
            compatible(engine, old_manifest, manifest)
        else:
            compatible(engine, manifest, old_manifest)
        before = inventory(engine, profile)
        engine.require(
            shutil.disk_usage(root).free >= before["bytes"] * 2 + engine.HEADROOM,
            "Insufficient rollback checkpoint headroom",
        )
        identifier = uuid.uuid4().hex
        audit = engine.private_directory(root / "maintenance") / identifier
        audit.mkdir(mode=0o700)
        inspect_profile(engine, release, profile, audit / "before.json")
        journal = {
            "format": 3,
            "id": identifier,
            "operation": "rollback",
            "root": str(root),
            "before": current,
            "after": previous,
            "profile_inventory": before,
        }
        engine.journal_checkpoint(root, journal, "preparing-checkpoint")
        saved = checkpoint(engine, root, profile, before, identifier)
        journal["checkpoint"] = str(saved)
        engine.journal_checkpoint(root, journal, "verified")
        engine.require(
            inventory(engine, profile) == before, "Data changed before rollback"
        )
        selection = {k: previous[k] for k in ("format", "release", "receipt_sha256")}
        selection["previous"] = {
            k: current[k] for k in ("format", "release", "receipt_sha256")
        }
        engine.durable(root / "current.json", selection)
        engine.journal_checkpoint(root, journal, "activated")
        finish(engine, root, journal)
        return {
            "status": "PASS",
            "scope": "N3 compatible binary rollback only",
            "profile_bytes_unchanged": True,
            "database_rollback": "NOT PERFORMED",
            "GUI": "NOT EXECUTED",
            "checkpoint": str(saved),
        }
