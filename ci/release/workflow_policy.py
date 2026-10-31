"""Fail-closed policy for the P5B manual, staging-only workflow."""

import importlib.util
import json

from core import HERE, ROOT, policy, require


def read_workflow(path):
    spec = importlib.util.spec_from_file_location(
        "accepted_ci_validator", ROOT / "ci/validate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.workflow(path)


def validate(value):
    require(
        policy()["authorization_model"] == "single-maintainer-manual-staging",
        "Owner-approved staging authorization model required",
    )
    require(
        set(value["on"]) == {"workflow_dispatch"},
        "Release may only be manually dispatched",
    )
    require(
        value["permissions"] == {"contents": "read", "actions": "read"},
        "Release workflow requires read-only permissions",
    )
    require(
        value["on"]["workflow_dispatch"]["inputs"]["channel"]["options"] == ["staging"],
        "Production publication must remain disabled",
    )
    jobs = value["jobs"]
    require(
        set(jobs) == {"eligibility", "staging"}
        and jobs["staging"].get("needs") == "eligibility"
        and "if" not in jobs["staging"]
        and jobs["staging"].get("environment") == policy()["environment"],
        "Signing requires eligibility and a protected staging environment",
    )
    pins = json.loads((ROOT / "ci/tools.json").read_text())["actions"]
    for job in jobs.values():
        require(
            job.get("runs-on") == "ubuntu-24.04"
            and 0 < job.get("timeout-minutes", 0) <= 30,
            "Unexpected or unbounded runner",
        )
        require(
            not {
                "permissions",
                "continue-on-error",
                "container",
                "services",
            }.intersection(job),
            "Unreviewed job capability",
        )
        for step in job["steps"]:
            require("continue-on-error" not in step, "Release checks must fail closed")
            text = json.dumps(step)
            require(
                "secrets." not in text and "pull_request_target" not in text,
                "Production secrets or untrusted privileged execution forbidden",
            )
            if "run" in step:
                require("${{" not in step["run"], "Unsafe shell interpolation")
            if "uses" in step:
                action, _, digest = step["uses"].partition("@")
                require(
                    pins.get(action) == digest, "Action must use accepted immutable pin"
                )
                if action == "actions/checkout":
                    require(
                        step["with"]
                        == {"ref": "${{ github.sha }}", "persist-credentials": False},
                        "Checkout must be immutable without persisted credentials",
                    )
    # Exact reviewed command/inputs/upload surfaces prevent accidental additions
    # escaping the semantic checks. Updating this contract requires source review.
    contract = json.loads((HERE / "workflow-contract.json").read_text())
    require(value == contract, "Release workflow differs from reviewed contract")
    return True


if __name__ == "__main__":
    validate(read_workflow(ROOT / ".github/workflows/release.yml"))
    print("P5B staging workflow security contract: PASS")
