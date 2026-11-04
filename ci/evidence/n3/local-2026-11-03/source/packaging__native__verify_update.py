"""Owner-only N3 installed GUI/reinstall check, using the existing live observer.

No automatic GUI launch or host policy changes. The client is a fixed disposable
root with a validated imported synthetic workspace, never a personal profile.
"""

import argparse
import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "ci-output/native-n3-client-1"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def saved_data(inventory):
    """Qt may update normal cache files; saved workspace/origin bytes must match."""
    return {
        n: info
        for n, info in inventory["files"].items()
        if n in {"active-workspace.json", "desktop.json"}
        or n.startswith(("workspace/", "workspaces/"))
    }


def confirmation():
    for _ in range(3):
        answer = " ".join(
            input(
                "Only if BOTH launches were correct, first imported appearance was "
                "System, you selected Dark, and Dark/note/image/icon/grouping survived "
                "reinstall: type CONFIRM N3 UPDATE (or NO): "
            ).split()
        ).casefold()
        if answer == "confirm n3 update":
            return
        if answer in {"no", "cancel"}:
            raise ValueError("Owner visual check not confirmed")
        print(
            "N3: no confirmation recorded; no PASS inferred from blank input.",
            flush=True,
        )
    raise ValueError("Owner visual confirmation missing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-host", required=True, action="store_true")
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    engine = module("n3_owner_engine", ROOT / "desktop/install_engine.py")
    observer_sha256 = engine.digest(ROOT / "packaging/native/verify_menu.py")
    engine.require(
        observer_sha256
        == "1456d268cda4654eacd1ba4f330116db5570a23a0a4ef4302ea60721c84920f2",
        "Reviewed live observer changed",
    )
    operations = module("n3_owner_operations", ROOT / "desktop/native_operations.py")
    menu = module("n3_owner_menu", ROOT / "packaging/native/verify_menu.py")
    engine.host_supported()
    engine.require(
        sys.stdin.isatty()
        and os.environ.get("WAYLAND_DISPLAY")
        and os.environ.get("XDG_SESSION_TYPE") == "wayland",
        "Owner GNOME Wayland terminal required",
    )
    output = engine.checked_path(args.output)
    engine.require(
        output.parent == ROOT / "ci-output"
        and output.name.startswith("native-n3-owner-")
        and output.name.removeprefix("native-n3-owner-").isdecimal()
        and not output.exists(),
        "Fresh direct N3 output required; earlier attempts preserved",
    )
    with engine.installation_lock(CLIENT):
        current = engine.load(CLIENT / "current.json")
        release, receipt, manifest = operations.verified(engine, CLIENT, current)
        engine.installed(release)
        engine.require(
            receipt["manifest_sha256"] == args.manifest_sha256
            and manifest.get("maintenance") == operations.CONTRACT
            and manifest["kind"] == "candidate",
            "Reviewed N3 candidate required",
        )
        for name in ("native_operations.py", "native_profile_check.py"):
            engine.require(
                engine.digest(ROOT / "desktop" / name)
                == manifest["files"][name]["sha256"],
                "Reviewed maintenance implementation changed",
            )
    profile = CLIENT / "client/profile"
    engine.require(
        receipt["profile"] == str(profile), "Disposable profile identity required"
    )
    state = operations.inventory(engine, profile)
    pointer = engine.load(profile / "active-workspace.json")
    engine.require(
        pointer["workspace"].startswith("workspaces/"),
        "Reviewed imported synthetic workspace required",
    )
    suffix = pointer["workspace"].split("/")[1]
    engine.require(
        not list((profile / ("web-profile-" + suffix)).iterdir()),
        "Initial imported Qt profile already used; preserve it for review",
    )
    check = module(
        "n3_owner_live", ROOT / "packaging/native/feasibility/check_application.py"
    )
    engine.require(
        engine.digest(ROOT / "packaging/native/feasibility/check_application.py")
        == "406e0afd6011dbf9f1e9031d8f6e8c8cdf8eb5ba3b7557b2db4fca67260584ed",
        "Accepted live security policy changed",
    )
    check.CANDIDATE = release
    check.EXPECTED_APPARMOR = engine.support(release, "apparmor_support").profile_name(
        CLIENT
    )
    check.unauthenticated_rejected = lambda: menu.unauthenticated(receipt, engine)
    expected_policy = engine.support(release, "apparmor_support").read_loaded_profile(
        check.EXPECTED_APPARMOR
    )
    engine.require(
        expected_policy.get("state") == "PRESENT"
        and expected_policy.get("mode") == "enforce",
        "Reviewed exact host profile must be loaded first; no automatic load",
    )
    desktop = CLIENT / "xdg/applications" / (manifest["app_id"] + ".desktop")
    engine.require(
        engine.digest(engine.regular(desktop)) == receipt.get("desktop_sha256"),
        "Reviewed installed Desktop Entry changed; no menu registration",
    )
    data = engine.checked_path(
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    )
    entry = data / "applications" / desktop.name
    engine.require(
        not entry.exists() and not entry.is_symlink(),
        "Existing candidate menu entry preserved",
    )
    engine.require(
        menu.find_gui(CLIENT / "launch.py") is None, "Close existing N3 candidate first"
    )
    output.mkdir(mode=0o700)
    record = {
        "status": "FAIL",
        "complete": False,
        "scope": "N3 actual installed GUI and data-preserving reinstall",
        "manifest_sha256": receipt["manifest_sha256"],
        "archive_sha256": manifest["archive_sha256"],
        "driver_sha256": engine.digest(Path(__file__)),
        "observer_sha256": observer_sha256,
        "phases": {},
        "checks": {},
    }
    registered = None

    def checkpoint(stage):
        record["stage"] = stage
        engine.durable(output / "progress.json", record)

    try:
        operations.inspect_profile(
            engine, release, profile, output / "initial-data.json"
        )
        input(
            "N3: two menu launches of the isolated candidate; no editing or new screenshot. Press Enter to register its temporary entry: "
        )
        checkpoint("menu-registration")
        registered = menu.register(engine, desktop, entry)
        discovery = menu.gio_discovery(entry)
        engine.require(
            all(discovery[k] for k in ("correct_path", "correct_id", "should_show")),
            "Menu discovery mismatch",
        )
        record["checks"]["menu_discovery"] = "PASS"
        for phase in ("imported-workspace", "after-reinstall"):
            checkpoint(phase + "-manual-launch")
            print(
                "N3: in GNOME Applications click 'CyrNava — N2 Candidate' ONCE within two minutes. Inspect N2 installed note and its image; do not edit content.",
                flush=True,
            )
            if phase == "imported-workspace":
                print(
                    "N3: imported workspace should initially select System. Choose Dark, then close normally when the live observer says CLOSE.",
                    flush=True,
                )
            else:
                print(
                    "N3: confirm Dark, saved note/image, icon and window grouping persisted. Close normally when instructed.",
                    flush=True,
                )
            record["phases"][phase] = menu.observe_menu_launch(
                check,
                CLIENT / "launch.py",
                record_observation=lambda value, phase=phase: engine.durable(
                    output / (phase + "-observation.json"), value
                ),
            )
            engine.require(
                saved_data(operations.inventory(engine, profile)) == saved_data(state),
                "Saved content, workspace or origin changed",
            )
            operations.inspect_profile(
                engine, release, profile, output / (phase + "-data.json")
            )
            if phase == "imported-workspace":
                checkpoint("stopped-uninstall-reinstall")
                before = operations.inventory(engine, profile)
                record["uninstall"] = operations.uninstall(
                    engine, CLIENT, disposable=True
                )
                record["reinstall"] = operations.restore_installation(
                    engine, CLIENT, disposable=True, reuse_preserved_data=True
                )
                engine.require(
                    operations.inventory(engine, profile) == before,
                    "Reinstall changed profile/preferences/drafts",
                )
                record["checks"]["exact_profile_preserved_through_reinstall"] = "PASS"
                print(
                    "N3: uninstall/reinstall preserved EVERY profile byte. One final menu launch remains.",
                    flush=True,
                )
        checkpoint("owner-visual-confirmation")
        confirmation()
        record["checks"].update(
            owner_visual_and_appearance="PASS", saved_data_workspace_origin="PASS"
        )
        record.update(status="PASS", stage="complete")
    except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 - private raw diagnostic
        (output / "exception.private.log").write_text(traceback.format_exc())
        record["error_type"] = type(error).__name__
    finally:
        if registered is not None:
            try:
                menu.unregister(engine, entry, registered)
                record["checks"]["temporary_menu_entry_removed"] = "PASS"
            except (OSError, ValueError):
                record.update(
                    status="FAIL",
                    menu_cleanup="CHANGED ENTRY PRESERVED; REVIEW REQUIRED",
                )
        record["complete"] = True
        engine.durable(output / "result.json", record)
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "PASS" else 2


if __name__ == "__main__":
    os.umask(0o077)
    raise SystemExit(main())
