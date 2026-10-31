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
]


def run_steps(steps, result_path):
    record = {"status": "FAIL", "complete": False, "steps": []}
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
    args = parser.parse_args()
    destination = args.output.resolve()
    return run_steps(
        steps_for(args.job, destination), destination / (args.job + ".json")
    )


if __name__ == "__main__":
    sys.exit(main())
