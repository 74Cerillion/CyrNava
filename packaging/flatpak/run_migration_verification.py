"""Host supervisor for synthetic-only P3 native verification; no real-profile access."""

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

REQUIRED = {
    "prepare": {"real_backup_export_and_readback", "document_portal_destination"},
    "import": {
        "real_native_import",
        "schema_upgrade",
        "source_unchanged",
        "database_and_images_preserved",
    },
    "edit": {
        "native_application_closed",
        "owner_title_saved",
        "additional_image_saved",
    },
    "restart": {
        "native_application_closed",
        "owner_title_saved",
        "additional_image_saved",
    },
    "verify": {
        "saved_edit_and_screenshot_after_restart",
        "source_unchanged",
        "backend_restart_and_reaping",
        "invalid_restore_preserves_active",
        "verified_restore_and_rollback",
        "invalid_backup_rejected",
    },
}


def valid_record(evidence, phase):
    return (
        isinstance(evidence, dict)
        and isinstance(evidence.get("checks"), dict)
        and evidence.get("status") == "PASS"
        and evidence.get("complete") is True
        and evidence.get("phase") == phase
        and REQUIRED[phase].issubset(evidence["checks"])
        and all(value == "PASS" for value in evidence["checks"].values())
    )


def main(resume=None):
    os.umask(0o077)
    if resume is not None and not re.fullmatch(r"run-[0-9a-f]{12}", resume):
        raise ValueError("Invalid disposable run ID")
    run_id = resume or "run-" + uuid4().hex[:12]
    root = (
        Path.home() / ".var/app/org.cyrnava.CyrNava.Devel/data/p3-verification" / run_id
    )
    instructions = {
        "prepare": "The first window is a native Save FILE dialog, not the migration manager. Keep the suggested .cyrnava filename, select Downloads, then click Save at the top right. Migration prompts follow after this save succeeds.",
        "import": "Click the SECOND button: Import backup into a new workspace. Do not click Create verified backup: this destination is still empty. Choose the synthetic .cyrnava file just saved, confirm the summary, wait for Completed and verified, then close the manager.",
        "edit": "Open a synthetic note. Set its title to P3 owner edit. Paste a screenshot of ONLY this synthetic workspace with Ctrl+V. Wait for Saved, then close normally.",
        "restart": "Confirm that the edited title and screenshot remain visible, then close normally.",
        "verify": "Automatic synthetic integrity, backup/restore, failure and recovery verification.",
    }
    helper = Path(__file__).with_name("verify_migration.py").read_bytes()
    helper_hash = hashlib.sha256(helper).hexdigest()
    outcome = {
        "run_id": run_id,
        "status": "FAIL",
        "complete": False,
        "phases": {},
        "helper_sha256": helper_hash,
    }
    if resume:
        # Reuse only independently recorded successful portal/import phases.
        for phase in ("prepare", "import"):
            if not valid_record(
                json.loads((root / (phase + ".json")).read_text()), phase
            ):
                raise ValueError("Resume requires verified prepare and import records")
        history = root / ("before-resume-" + uuid4().hex[:12])
        history.mkdir(mode=0o700)
        for phase in (*instructions, "supervisor-result"):
            prior = root / (phase + ".json")
            if prior.is_file():
                shutil.copyfile(prior, history / prior.name)
        outcome["resumed_from"] = str(history)
        outcome["phases"].update({"prepare": "PASS", "import": "PASS"})
    print("Synthetic run: " + run_id, flush=True)
    for phase, instruction in instructions.items():
        if resume and phase in ("prepare", "import"):
            continue
        print("\n" + phase.upper() + ": " + instruction, flush=True)
        try:
            child = subprocess.Popen(
                [
                    "flatpak",
                    "run",
                    "--branch=p2",
                    "--command=python3",
                    "org.cyrnava.CyrNava.Devel",
                    "-u",
                    "-",
                    phase,
                    run_id,
                ],
                stdin=subprocess.PIPE,
            )
            child.communicate(helper, timeout=600)
            evidence = json.loads((root / (phase + ".json")).read_text())
            if child.returncode or not valid_record(evidence, phase):
                if isinstance(evidence, dict) and evidence.get("reason"):
                    outcome["reason"] = evidence["reason"]
                raise ValueError("Incomplete or failed native phase")
            outcome["phases"][phase] = "PASS"
        except (
            OSError,
            ValueError,
            TypeError,
            subprocess.TimeoutExpired,
            KeyboardInterrupt,
        ):
            # Preserve any outstanding native recovery dialog on timeout.
            outcome["child_still_running"] = (
                child.poll() is None if "child" in locals() else False
            )
            outcome["phases"][phase] = "FAIL"
            break
    else:
        outcome["status"] = "PASS"
    outcome["complete"] = True
    if root.is_dir():
        (root / "supervisor-result.json").write_text(
            json.dumps(outcome, indent=2) + "\n"
        )
        print("Evidence: " + str(root / "supervisor-result.json"))
    print(json.dumps(outcome, indent=2), flush=True)
    return 0 if outcome["status"] == "PASS" else 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resume", help="Resume EDIT after recorded successful prepare/import"
    )
    args = parser.parse_args()
    raise SystemExit(main(args.resume))
