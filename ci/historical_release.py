"""Run unchanged Flatpak release regressions against their accepted CI fixture.

Current native CI is tested independently. No release policy, hash guard or test
is bypassed. Only this temporary unit-test source tree gets the historical CI.
"""

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI_FIXTURE = "ci/fixtures/p5b-accepted-ci.yml"
# Recovered verbatim from this owner-committed pre-native-CI baseline.
CI_FIXTURE_SOURCE = "b27e33bb0b31ecd93a3792c6b6a889686dfae575:.github/workflows/ci.yml"
CI_SHA256 = "3f11c9ab58d2f7c8cebca0b153a09ccffae06e314545067ddd6b42f7b8e809f4"
DIRECTORIES = ("ci/release", "packaging/flatpak", "backend/app")
FILES = (
    ".gitignore",
    ".github/workflows/release.yml",
    ".github/workflows/p5c.yml",
    "ci/flatpak.py",
    "ci/validate.py",
    "ci/tools.json",
    "ci/requirements.lock",
    "backend/pyproject.toml",
    "frontend/package.json",
    "frontend/package-lock.json",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture(source, destination):
    source, destination = Path(source).absolute(), Path(destination).absolute()
    if destination.exists() or any(p.is_symlink() for p in destination.parents):
        raise ValueError("Fresh non-symlink fixture required")
    historical = (source / CI_FIXTURE).read_bytes()
    policy = json.loads((source / "ci/release/policy.json").read_text())
    if digest(historical) != CI_SHA256 or policy["ci_workflow_sha256"] != CI_SHA256:
        raise ValueError("Accepted historical CI fixture hash mismatch")
    paths = list(FILES)
    for name in DIRECTORIES:
        for path in sorted((source / name).rglob("*")):
            if "__pycache__" not in path.parts and path.suffix in {
                ".py",
                ".json",
                ".yml",
                ".yaml",
                ".txt",
                ".lock",
                ".sh",
            }:
                paths.append(str(path.relative_to(source)))
    contents = {}
    for name in paths:
        path = source / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("Fixture source symlink refused")
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("Regular fixture source required")
        contents[name] = path.read_bytes()
    if sum(map(len, contents.values())) > 8 * 1024**2:
        raise ValueError("Unit fixture exceeds 8 MiB source budget")
    contents[".github/workflows/ci.yml"] = historical
    destination.mkdir(mode=0o700)
    for name, data in contents.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {name: digest(data) for name, data in sorted(contents.items())}


def run(output):
    output = output.absolute()
    record_path = output.with_suffix(".json")
    if output.exists() or record_path.exists() or not output.parent.is_dir():
        raise ValueError("Fresh historical test evidence required")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_DATE="2000-01-01T00:00:00Z",
        GIT_COMMITTER_DATE="2000-01-01T00:00:00Z",
        PYTHONDONTWRITEBYTECODE="1",
    )
    with (
        tempfile.TemporaryDirectory(
            prefix=".historical-unit-",
            dir=output.parent,
        ) as temporary,
        tempfile.TemporaryDirectory(prefix="cyrnava-unit-", dir="/tmp") as short,
    ):
        work = Path(temporary)
        source = work / "source"
        hashes = fixture(ROOT, source)
        # This synthetic test-only Git history serves fresh-interpreter identity
        # tests. It has no remote, hooks, signing or accepted-artifact identity.
        git = ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false"]
        for args in (
            ["init", "--quiet", source],
            ["-C", source, "add", "--force", "."],
            [
                "-C",
                source,
                "-c",
                "user.name=Synthetic unit fixture",
                "-c",
                "user.email=synthetic@invalid.example",
                "commit",
                "--quiet",
                "--no-gpg-sign",
                "-m",
                "Historical release unit-test fixture",
            ],
        ):
            subprocess.run(git + list(map(str, args)), env=env, check=True, timeout=30)
        # GPG's Unix-domain sockets need short paths; synthetic data must also
        # stay outside the fixture source. This child-only path changes no host
        # environment and is removed after the unit-test process exits.
        temp = Path(short)
        env.update(TMPDIR=str(temp), PYTHONPATH=str(source / "backend"))
        print(
            "CI: historical release tests; current code + "
            "hash-verified accepted CI fixture",
            flush=True,
        )
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-q",
                "../ci/release",
                "--basetemp=" + str(temp / "pytest"),
                "--junitxml=" + str(output),
            ],
            cwd=source / "backend",
            env=env,
            timeout=300,
        )
        unchanged = all(
            digest((source / n).read_bytes()) == h for n, h in hashes.items()
        )
        record_path.write_text(
            json.dumps(
                {
                    "status": "PASS"
                    if result.returncode == 0 and unchanged
                    else "FAIL",
                    "scope": "unchanged current release regressions; "
                    "historical CI fixture only",
                    "historical_CI_sha256": CI_SHA256,
                    "historical_CI_source": CI_FIXTURE_SOURCE,
                    "source_hashes": hashes,
                    "fixture_source_unchanged": unchanged,
                    "exit_code": result.returncode,
                    "native_execution_or_production_release": "NOT EXECUTED",
                    "cryptography": "disposable one-day synthetic unit fixtures only",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if result.returncode == 0 and unchanged else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.output))
