"""Timed, fail-closed local/CI commands. Synthetic test profiles only."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_TESTS = [
    "tests",
    "../packaging/flatpak/test_verify_outage.py",
    "../packaging/flatpak/test_run_portal_verification.py",
    "../packaging/flatpak/test_run_migration_verification.py",
    "../packaging/flatpak/production/test_packaging.py",
    "../ci/test_ci.py",
    "../ci/release",
]


def run_steps(steps, result_path, *, preconditions=None):
    record = {"status": "FAIL", "complete": False, "steps": []}
    if preconditions is not None:
        record["preconditions"] = preconditions
    result_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    code = 1
    try:
        for name, command, cwd in steps:
            step = {"name": name, "status": "FAIL"}
            record["steps"].append(step)
            then = time.monotonic()
            print("CI: " + name, flush=True)
            try:
                subprocess.run(command, cwd=cwd, check=True)
            finally:
                step["seconds"] = round(time.monotonic() - then, 3)
            step["status"] = "PASS"
        code = 0
        record["status"] = "PASS"
    except (OSError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        record["error_type"] = type(error).__name__
        if isinstance(error, subprocess.CalledProcessError):
            record["exit_code"] = error.returncode
        # No environment dumps or exception strings containing credentials.
    finally:
        record.update(complete=True, seconds=round(time.monotonic() - started, 3))
        result_path.write_text(json.dumps(record, indent=2) + "\n")
    return code


def steps_for(job, destination):
    python = str(ROOT / "backend/.venv/bin/python")
    if job == "backend":
        return [
            (
                "python-lint",
                [
                    python,
                    "-m",
                    "ruff",
                    "check",
                    "--config",
                    "backend/pyproject.toml",
                    "backend/app",
                    "backend/tests",
                    "ci",
                ],
                ROOT,
            ),
            (
                "frontend-install-for-backend",
                ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                ROOT / "frontend",
            ),
            (
                "frontend-production-build-for-backend",
                ["npm", "run", "build"],
                ROOT / "frontend",
            ),
            (
                "backend-security-lifecycle-migration-packaging",
                [
                    python,
                    "-m",
                    "pytest",
                    "-q",
                    *BACKEND_TESTS,
                    "--junitxml=" + str(destination / "backend-junit.xml"),
                ],
                ROOT / "backend",
            ),
        ]
    return [
        ("frontend-lint", ["npm", "run", "lint"], ROOT / "frontend"),
        ("frontend-unit", ["npm", "test"], ROOT / "frontend"),
        ("typescript-production-build", ["npm", "run", "build"], ROOT / "frontend"),
        (
            "chromium-production-integration",
            ["npm", "run", "test:release", "--", "--reporter=list,junit"],
            ROOT / "frontend",
        ),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", choices=("backend", "frontend"))
    parser.add_argument("--output", type=Path, default=ROOT / "ci-output")
    parser.add_argument(
        "--require-clean-frontend",
        action="store_true",
        help="Backend CI regression: require frontend/dist to be absent at entry",
    )
    args = parser.parse_args()
    if args.require_clean_frontend and args.job != "backend":
        parser.error("--require-clean-frontend applies only to backend verification")
    destination = args.output.resolve()
    preconditions = None
    if args.job == "backend":
        preconditions = {
            "frontend_dist_initially_absent": not (ROOT / "frontend/dist").exists(),
            "clean_frontend_required": args.require_clean_frontend,
        }
        if (
            args.require_clean_frontend
            and not preconditions["frontend_dist_initially_absent"]
        ):
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "backend.json").write_text(
                json.dumps(
                    {
                        "status": "FAIL",
                        "complete": True,
                        "steps": [],
                        "error_type": "FrontendAssetsAlreadyPresent",
                        "preconditions": preconditions,
                    },
                    indent=2,
                )
                + "\n"
            )
            print(
                "Clean-checkout regression requires absent frontend/dist",
                file=sys.stderr,
            )
            return 1
    return run_steps(
        steps_for(args.job, destination),
        destination / (args.job + ".json"),
        preconditions=preconditions,
    )


if __name__ == "__main__":
    sys.exit(main())
