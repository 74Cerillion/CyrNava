"""Exact proposed P5C workflow policy. No registration/settings/write operations."""

import argparse
import json
import os

import core
import github
import workflow_policy

WORKFLOW = ".github/workflows/p5c.yml"


def validate(value):
    core.require(
        set(value["on"]) == {"workflow_dispatch"}
        and value["permissions"] == {"contents": "read", "actions": "read"},
        "P5C requires manual-only read-only workflow",
    )
    core.require(
        set(value["jobs"]) == {"eligibility", "staging"}
        and value["jobs"]["staging"]["needs"] == "eligibility"
        and value["jobs"]["staging"]["environment"] == "p5b-staging",
        "P5C eligibility and exact staging environment required",
    )
    install = (
        "python -m pip install --require-hashes --only-binary=:all:"
        " -r ci/requirements.lock"
    )
    pins = core.read_json(core.ROOT / "ci/tools.json")["actions"]
    for job in value["jobs"].values():
        core.require(
            job.get("runs-on") == "ubuntu-24.04"
            and 0 < job.get("timeout-minutes", 0) <= 30
            and not {
                "permissions",
                "continue-on-error",
                "container",
                "services",
            }.intersection(job),
            "Unreviewed P5C runner capability",
        )
        for step in job["steps"]:
            core.require(
                "continue-on-error" not in step and "secrets." not in json.dumps(step),
                "P5C cannot bypass checks or access production secrets",
            )
            if "uses" in step:
                action, _, digest = step["uses"].partition("@")
                core.require(pins.get(action) == digest, "Unreviewed P5C action pin")
            if "run" in step:
                core.require("${{" not in step["run"], "Unsafe P5C shell interpolation")
        checkout = job["steps"][0]
        core.require(
            checkout["with"]
            == {
                "ref": "${{ github.sha }}",
                "persist-credentials": False,
                "fetch-depth": 0,
            },
            "P5C requires full immutable credential-free history in every job",
        )
        commands = "\n".join(s.get("run", "") for s in job["steps"])
        core.require(
            0 <= commands.find(install) < commands.find("python ci/release/"),
            "Every independent Python job must install locked dependencies first",
        )
    expected = core.read_json(core.HERE / "p5c-workflow-contract.json")
    core.require(value == expected, "P5C workflow differs from exact reviewed contract")
    # Keep the accepted P5B contract separately intact.
    workflow_policy.validate(
        workflow_policy.read_workflow(core.ROOT / ".github/workflows/release.yml")
    )
    return True


def context_eligible(context, checkout, approved):
    policy = core.policy()
    ref = "refs/heads/" + policy["workflow_branch"]
    core.require(
        github.re_full_sha(approved or "") and approved == checkout,
        "Exact owner-approved P5C tooling commit required",
    )
    core.require(
        context.get("GITHUB_ACTIONS") == "true"
        and context.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and context.get("GITHUB_REPOSITORY") == policy["repository"]
        and context.get("GITHUB_REF") == ref
        and context.get("GITHUB_ACTOR", "").lower() == policy["staging_owner"].lower()
        and context.get("GITHUB_TRIGGERING_ACTOR", "").lower()
        == policy["staging_owner"].lower()
        and context.get("GITHUB_RUN_ATTEMPT") == "1"
        and context.get("GITHUB_SHA") == checkout
        and context.get("GITHUB_WORKFLOW_SHA") == checkout
        and context.get("GITHUB_WORKFLOW_REF")
        == policy["repository"] + "/" + WORKFLOW + "@" + ref
        and context.get("P5C_AUTHORIZATION")
        == "P5C-owner-authorized-disposable-integration-only",
        (
            "Unauthorized P5C workflow identity, ref, owner, attempt or"
            " authorization reference"
        ),
    )
    return True


def check_execution(approved):
    checkout = core.call("git", "-C", core.ROOT, "rev-parse", "HEAD").decode().strip()
    context_eligible(os.environ, checkout, approved)
    actual = core.ROOT / WORKFLOW
    core.require(
        actual.read_bytes() == (core.HERE / "p5c-workflow.yml").read_bytes(),
        "Registered P5C workflow differs from reviewed proposal",
    )
    validate(workflow_policy.read_workflow(actual))
    core.require(
        not core.call("git", "-C", core.ROOT, "status", "--porcelain"),
        "Hosted tooling checkout must be clean",
    )
    github.check_environment()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--tooling-commit")
    args = parser.parse_args()
    validate(workflow_policy.read_workflow(core.HERE / "p5c-workflow.yml"))
    if args.preflight:
        check_execution(args.tooling_commit)
        github.live_evidence(core.policy()["approved_staging_sources"][0])
    print("P5C exact workflow policy: PASS; no dispatch or configuration change")
