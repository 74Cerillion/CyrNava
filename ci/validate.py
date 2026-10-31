"""Parse the workflow and enforce the bounded CI security/dependency contract."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow(path):
    # PyYAML follows YAML 1.1 (where 'on' is a bool); Actions uses YAML 1.2.
    class Loader(yaml.SafeLoader):
        pass

    Loader.yaml_implicit_resolvers = {
        key: [
            (tag, pattern) for tag, pattern in values if tag != "tag:yaml.org,2002:bool"
        ]
        for key, values in Loader.yaml_implicit_resolvers.items()
    }
    Loader.add_implicit_resolver(
        "tag:yaml.org,2002:bool", re.compile(r"^(true|false)$", re.I), list("tTfF")
    )
    return yaml.load(path.read_text(), Loader=Loader)


def validate(value, pins):
    if value.get("permissions") != {"contents": "read"}:
        raise ValueError("Workflow requires read-only contents permissions")
    triggers = value.get("on", {})
    if set(triggers) != {"push", "pull_request", "workflow_dispatch"}:
        raise ValueError("Unexpected workflow event")
    if set(triggers["push"]["branches"]) != {
        "desktop/p2-production-integration",
        "main",
    } or triggers["pull_request"]["branches"] != ["main"]:
        raise ValueError("Incorrect branch triggers")
    if any(
        "paths" in (event or {}) or "paths-ignore" in (event or {})
        for event in triggers.values()
    ):
        raise ValueError("Required checks must not be path-filtered")
    jobs = value["jobs"]
    if set(jobs) != {"validate", "backend", "frontend", "flatpak", "required"}:
        raise ValueError("Unexpected job graph")
    for name, job in jobs.items():
        if (
            job.get("runs-on") != "ubuntu-24.04"
            or not 0 < job.get("timeout-minutes", 0) <= 45
        ):
            raise ValueError("Unexpected runner or unbounded job")
        if any(
            key in job
            for key in (
                "permissions",
                "environment",
                "container",
                "services",
                "continue-on-error",
            )
        ):
            raise ValueError("Unexpected privileged/optional job configuration")
        for step in job["steps"]:
            if "continue-on-error" in step:
                raise ValueError("Required steps must fail closed")
            if "uses" in step:
                action, _, commit = step["uses"].partition("@")
                if pins.get(action) != commit or not re.fullmatch(
                    r"[0-9a-f]{40}", commit
                ):
                    raise ValueError("Unreviewed action or mutable pin")
                options = step.get("with", {})
                if (
                    action == "actions/checkout"
                    and options.get("persist-credentials") is not False
                ):
                    raise ValueError("Checkout must not persist credentials")
                if action == "actions/upload-artifact":
                    if (
                        options.get("retention-days") != 7
                        or options.get("if-no-files-found") != "error"
                    ):
                        raise ValueError("Artifact retention/failure policy mismatch")
                    if "github.sha" not in options.get("name", ""):
                        raise ValueError("Artifact must identify source commit")
            run = step.get("run", "")
            if "${{" in run or "secrets." in json.dumps(step):
                raise ValueError("Shell interpolation or secrets are not permitted")
    if (
        jobs["backend"].get("needs") != "validate"
        or jobs["frontend"].get("needs") != "validate"
    ):
        raise ValueError("Test jobs require workflow validation")
    if set(jobs["flatpak"].get("needs", [])) != {"backend", "frontend"}:
        raise ValueError("Build must wait for both test jobs")
    gate = jobs["required"]
    if gate.get("if") != "always()" or set(gate.get("needs", [])) != set(jobs) - {
        "required"
    }:
        raise ValueError("Final required check must cover all jobs, including failures")
    steps = jobs["flatpak"]["steps"]
    audit = next(
        i for i, s in enumerate(steps) if "ci/flatpak.py audit" in s.get("run", "")
    )
    package = next(
        i
        for i, s in enumerate(steps)
        if s.get("with", {}).get("path") == "ci-output/flatpak/artifacts/"
    )
    if package <= audit or "if" in steps[package]:
        raise ValueError("Package upload must be gated by successful audit")
    return True


if __name__ == "__main__":
    validate(
        workflow(ROOT / ".github/workflows/ci.yml"),
        json.loads((ROOT / "ci/tools.json").read_text())["actions"],
    )
    print("Workflow security/dependency contract: PASS")
