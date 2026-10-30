"""Owner-host local install/update/rollback checks. Unpublished synthetic test only.

Requires production builds A and B (result.json PASS). Refuses an existing
production installation. Never uninstalls development, deletes data, or changes
Flatpak overrides/security settings. No host test code enters the package.
"""

import argparse
import configparser
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

APP_ID = "io.github._74Cerillion.CyrNava"
DEVELOPMENT_ID = "org.cyrnava.CyrNava.Devel"
HERE = Path(__file__).resolve().parent
REQUIRED = {
    "edit": {
        "production_identity_private_network_and_filesystem",
        "backend_authentication_and_origin",
        "production_window_title",
        "renderer_sandbox",
        "owned_backend_reaped",
        "saved_title_and_screenshot",
        "dark_preference_saved",
        "single_instance_lock",
        "required_title_saved",
        "screenshot_asset_saved",
        "folder_saved",
    },
    "maintenance": {
        "production_identity_private_network_and_filesystem",
        "real_native_backup_export_and_import",
    },
    "recovery": {
        "production_identity_private_network_and_filesystem",
        "verified_backup_restore",
        "incompatible_schema_refused_unchanged",
        "previous_profile_recovered",
    },
}
for phase in ("restart", "updated", "rollback"):
    REQUIRED[phase] = REQUIRED["edit"]


def checked(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()


def commit(app):
    result = subprocess.run(
        ["flatpak", "info", "--user", "--show-commit", app],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def permissions(text):
    info = configparser.ConfigParser()
    info.read_string(text)
    allowed = {
        "sockets": {"wayland"},
        "devices": {"dri"},
        "shared": {"!network"},
        "filesystems": {"!home", "!host", "xdg-config/kdeglobals:ro"},
    }
    if info.has_section("Context") and set(info["Context"]) - set(allowed):
        raise ValueError("Unexpected additional Flatpak capability")
    for key, values in allowed.items():
        actual = set(filter(None, info.get("Context", key, fallback="").split(";")))
        if not actual.issubset(values):
            raise ValueError("Unexpected effective Flatpak permission: " + key)
    permitted_bus = {
        "com.canonical.appmenu.registrar",
        "org.kde.kconfig.notify",
        "org.kde.kglobalsettings",
    }
    for key, value in (
        info.items("Session Bus Policy")
        if info.has_section("Session Bus Policy")
        else []
    ):
        if key not in permitted_bus or value != "talk":
            raise ValueError("Unexpected session-bus access")
    if info.has_section("System Bus Policy") and info.items("System Bus Policy"):
        raise ValueError("Unexpected system-bus access")
    return True


def build_result(directory):
    directory = Path(directory).resolve()
    result = json.loads((directory / "result.json").read_text())
    bundle = Path(result.get("bundle", ""))
    if result.get("status") != "PASS" or not bundle.is_file():
        raise ValueError("A complete production build is required: " + str(directory))
    with bundle.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != result.get("sha256"):
            raise ValueError("Flatpak bundle hash mismatch")
    return directory, bundle, result


def maintenance_checkpoint(root, previous):
    """Reuse only recorded complete phases, never owner-reported or partial PASS."""
    phases = ("edit", "restart", "updated", "rollback")
    checks = {
        "fresh_install_permissions",
        "local_update",
        "compatible_binary_rollback",
        *phases,
    }
    if any(previous.get("checks", {}).get(name) != "PASS" for name in checks):
        raise ValueError("Maintenance continuation requires completed update/rollback")
    digest = None
    for phase in phases:
        record = json.loads((root / (phase + ".json")).read_text())
        if (
            record.get("phase") != phase
            or record.get("status") != "PASS"
            or record.get("complete") is not True
            or not REQUIRED[phase].issubset(record.get("checks", {}))
            or any(value != "PASS" for value in record["checks"].values())
            or not record.get("preferences_sha256")
        ):
            raise ValueError("Incomplete continuation evidence: " + phase)
        if digest and digest != record["preferences_sha256"]:
            raise ValueError("Continuation preferences do not match")
        digest = record["preferences_sha256"]
    return {name: "PASS" for name in checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", type=Path, required=True)
    parser.add_argument("--b", type=Path, required=True)
    parser.add_argument(
        "--resume",
        help="Resume EDIT for an identified failed synthetic run; keep its saved work",
    )
    parser.add_argument(
        "--continue-maintenance",
        action="store_true",
        help="With --resume, reuse verified edit/restart/update/rollback records",
    )
    args = parser.parse_args()
    if args.continue_maintenance and not args.resume:
        parser.error("--continue-maintenance requires --resume")
    a, bundle_a, lock_a = build_result(args.a)
    _b, bundle_b, lock_b = build_result(args.b)
    if lock_a["ostree_commit"] == lock_b["ostree_commit"]:
        raise SystemExit("Build B must have a distinct local build ID/OSTree commit")
    real_root = Path.home() / ".var/app" / APP_ID
    os.umask(0o077)
    if args.resume and not re.fullmatch(r"run-[0-9a-f]{12}", args.resume):
        raise SystemExit("Invalid synthetic resume ID")
    run_id = args.resume or "run-" + uuid4().hex[:12]
    root = real_root / "data/p4-verification" / run_id
    previous = None
    history = None
    reused = {}
    if args.resume:
        previous = json.loads((a / ("host-" + run_id + ".json")).read_text())
        if (
            previous.get("run_id") != run_id
            or previous.get("checks", {}).get("fresh_install_permissions") != "PASS"
            or previous.get("build_A") != lock_a["ostree_commit"]
            or previous.get("build_B") != lock_b["ostree_commit"]
        ):
            raise SystemExit("Resume evidence/build identity mismatch")
        if (
            commit(APP_ID) != lock_a["ostree_commit"]
            or not root.is_dir()
            or any(p.is_symlink() for p in (root, *root.parents))
        ):
            raise SystemExit(
                "Resume requires this synthetic run and unchanged installed build A"
            )
        if (real_root / "data/cyrnava").exists():
            raise SystemExit(
                "Normal production profile exists; refuse automatic resume on this account"
            )
        if args.continue_maintenance:
            reused = maintenance_checkpoint(root, previous)
        history = root / ("before-resume-" + uuid4().hex[:12])
        history.mkdir(mode=0o700)
        for phase_name in REQUIRED:
            old = root / (phase_name + ".json")
            if old.is_file():
                shutil.copyfile(old, history / old.name)
        shutil.copyfile(a / ("host-" + run_id + ".json"), history / "host-result.json")
    elif commit(APP_ID) is not None or real_root.exists():
        raise SystemExit(
            "Existing production installation/data found; use an identified synthetic --resume or a disposable Ubuntu account"
        )
    result = {
        "status": "FAIL",
        "complete": False,
        "run_id": run_id,
        "checks": {},
        "build_A": lock_a["ostree_commit"],
        "build_B": lock_b["ostree_commit"],
        "helper_sha256": hashlib.sha256(
            (HERE / "native_check.py").read_bytes()
        ).hexdigest(),
    }
    if previous:
        result["resumed_from"] = str(history)
    if reused:
        result["checks"].update(reused)
        result["reused_checkpoint_helper_sha256"] = previous.get("helper_sha256")
        result["reused_phases"] = ["edit", "restart", "updated", "rollback"]
    devel_before = commit(DEVELOPMENT_ID)
    result["development_before"] = devel_before
    # Evidence outside application data survives uninstall; no user-data deletion.
    evidence = a / ("host-" + run_id + ".json")

    def install(bundle, expected):
        subprocess.run(
            [
                "flatpak",
                "install",
                "--user",
                "--noninteractive",
                "--reinstall",
                str(bundle),
            ],
            check=True,
        )
        assert commit(APP_ID) == expected
        text = checked("flatpak", "info", "--user", "--show-permissions", APP_ID)
        permissions(text)
        (a / ("permissions-" + run_id + ".ini")).write_text(text)

    def phase(name, prompt):
        print("\n" + name.upper() + ": " + prompt, flush=True)
        command = [
            "flatpak",
            "run",
            "--branch=stable",
            "--command=python3",
            APP_ID,
            "-u",
            "-",
            name,
            run_id,
            os.readlink("/proc/self/ns/net"),
            str(canary),
        ]
        child = subprocess.Popen(command, stdin=subprocess.PIPE)
        child.communicate((HERE / "native_check.py").read_bytes(), timeout=600)
        record = json.loads((root / (name + ".json")).read_text())
        if (
            child.returncode
            or record.get("status") != "PASS"
            or not record.get("complete")
            or not REQUIRED[name].issubset(record.get("checks", {}))
            or any(v != "PASS" for v in record["checks"].values())
        ):
            result["failed_phase"] = name
            if isinstance(record, dict) and record.get("missing_checks"):
                result["missing_checks"] = record["missing_checks"]
            raise ValueError("Native phase failed: " + name)
        if name in ("restart", "updated", "rollback"):
            original = json.loads((root / "edit.json").read_text())
            if not record.get("preferences_sha256") or record[
                "preferences_sha256"
            ] != original.get("preferences_sha256"):
                raise ValueError(
                    "Saved preferences changed after restart/update/rollback"
                )
        result["checks"][name] = "PASS"

    try:
        with tempfile.TemporaryDirectory(prefix="cyrnava-p4-host-") as tmp:
            canary = Path(tmp) / "host-only"
            canary.write_text("Synthetic host-access canary; no private content")
            if not args.resume:
                install(bundle_a, lock_a["ostree_commit"])
            else:
                permissions(
                    checked("flatpak", "info", "--user", "--show-permissions", APP_ID)
                )
            result["checks"]["fresh_install_permissions"] = "PASS"
            if not reused:
                phase(
                    "edit",
                    "In the synthetic app: create a folder, rename the note to P4 owner edit, format text, paste a new screenshot of this synthetic window with Ctrl+V, set Appearance to Dark, wait for Saved, then close. This is not your real workspace.",
                )
                phase(
                    "restart",
                    "Confirm note, formatting, screenshot and Appearance remain. Try a keyboard shortcut, then close.",
                )
                install(bundle_b, lock_b["ostree_commit"])
                result["checks"]["local_update"] = "PASS"
                phase(
                    "updated",
                    "Confirm the same synthetic note, screenshot and Appearance after update B, then close.",
                )
                install(bundle_a, lock_a["ostree_commit"])
                result["checks"]["compatible_binary_rollback"] = "PASS"
                phase(
                    "rollback",
                    "Confirm the same synthetic data after rollback A, then close.",
                )
            phase(
                "maintenance",
                "Click Create verified backup, type the FULL filename p4-backup.cyrnava including the extension, and save in Downloads. Do not extract the archive. Wait for Completed and verified. Then click the SECOND button, Import backup into a new workspace, select that same file, confirm Yes, wait for Completed and verified again, and only THEN close the manager. Export alone does not complete this test.",
            )
            phase(
                "recovery",
                "Automatic verified backup/restore and unsupported future-schema refusal on a disposable copy.",
            )
            before = {
                str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob("*")
                if p.is_file()
            }
            subprocess.run(
                [
                    "flatpak",
                    "uninstall",
                    "--user",
                    "--noninteractive",
                    APP_ID + "//stable",
                ],
                check=True,
            )
            assert commit(APP_ID) is None
            assert before == {
                str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob("*")
                if p.is_file()
            }
            result["checks"]["uninstall_preserves_synthetic_data"] = "PASS"
            install(bundle_b, lock_b["ostree_commit"])
            result["checks"]["reinstallation"] = "PASS"
            assert commit(DEVELOPMENT_ID) == devel_before
            result["checks"]["development_installation_unchanged"] = "PASS"
            result.update(status="PASS", complete=True)
    except (
        OSError,
        ValueError,
        AssertionError,
        subprocess.SubprocessError,
        KeyboardInterrupt,
    ) as error:
        result.update(
            status="FAIL",
            complete=True,
            error_type=type(error).__name__,
            error="Host verification stopped; preserve run/phase evidence. Any timed-out window remains available for normal close.",
        )
    finally:
        evidence.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
        print("Host evidence: " + str(evidence), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
